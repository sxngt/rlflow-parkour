#!/usr/bin/env python3
"""Validate completed P0 artifact lineage without starting the simulator."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(directory):
    directory = Path(directory)
    run = json.loads((directory / "run.json").read_text())
    assert run["status"] == "SUCCEEDED", (directory, run["status"])
    supervisor = json.loads(directory.with_suffix(".supervisor.json").read_text())
    assert supervisor["exit_code"] == 0 and supervisor["resource_released"]
    assert not supervisor["remaining_gpu_processes"]
    for line in directory.with_suffix(".gpu.jsonl").read_text().splitlines():
        for row in json.loads(line)["worker_gpu_processes"]:
            assert row["gpu_uuid"] == supervisor["gpu_uuid"], "Cross-GPU allocation"
    if run["kind"] == "train":
        rows = [json.loads(line) for line in (directory / "metrics.jsonl").read_text().splitlines()]
        assert rows and all(b["iteration"] == a["iteration"] + 1 for a, b in zip(rows, rows[1:]))
        for cp in directory.glob("checkpoint-*.pt"):
            sidecar = json.loads(cp.with_suffix(".json").read_text())
            assert digest(cp) == sidecar["sha256"] and cp.stat().st_size == sidecar["bytes"]
        cp = run["checkpoint"]
        assert digest(directory / cp["path"]) == cp["sha256"]
        if "parent_checkpoint" in run:
            parent = run["parent_checkpoint"]
            assert digest(Path(parent["path"])) == parent["sha256"]
            state = json.loads(Path(parent["path"]).with_suffix(".json").read_text())
            assert rows[0]["iteration"] == state["completed_iterations"] + 1
    else:
        report = json.loads((directory / "evaluation.json").read_text())
        scenarios = json.loads((directory / "scenarios.json").read_text())
        assert len(report["results"]) == len(scenarios["episodes"]) == report["episodes"]
        assert [row["scenario_id"] for row in report["results"]] == [row["id"] for row in scenarios["episodes"]]
        for row in report["results"]:
            assert sum(bool(row[key]) for key in ("success", "failure", "timeout")) == 1
        for name, expected in run["artifacts"].items():
            assert digest(directory / name) == expected
    return {"run": str(directory), "kind": run["kind"], "gpu_uuid": supervisor["gpu_uuid"], "audit": "passed"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directories", nargs="+")
    args = p.parse_args()
    for path in args.directories:
        print(json.dumps(audit(path)))
