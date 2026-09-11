"""Fixed, complete first-episode evaluation, with optional original-frame MP4."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import traceback
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from parkour.runtime import begin_run, finish_run, launch_app, atomic_json, sha256
from parkour.scenarios import development_scenarios


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("configs/t0-ppo.json"))
    p.add_argument("--checkpoint", type=Path)
    p.add_argument("--baseline", choices=["zero", "policy", "shuffled-target"], default="policy")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--episodes", type=int, default=64)
    p.add_argument("--video", action="store_true")
    p.add_argument("--video-envs", type=int, default=16)
    p.add_argument("--diagnostics", action="store_true")
    p.add_argument("--research-tag", action="append", default=[])
    args = p.parse_args()
    if args.baseline != "zero" and not args.checkpoint:
        p.error("policy evaluation requires checkpoint")
    config = json.loads(args.config.read_text())
    if args.research_tag:config["research_tags"] = args.research_tag
    manifest = development_scenarios(args.episodes, config["target_offset_m"], config.get('sequence'))
    if config.get('jump'):
        from parkour.scenarios import jump_scenarios
        manifest=jump_scenarios(args.episodes,config['jump'])
    manifest["task"] = config["task"]
    if config.get("sequence"):manifest["sequence_contract"] = config["sequence"]
    config["num_envs"] = args.episodes
    config["seed"] = 10000
    meta = begin_run(args.out, config, "evaluate")
    recorder = None
    try:
        launch_app(args.video)
        import numpy as np
        import torch
        from parkour.learning import make_env, make_algorithm, read_checkpoint, restore
        torch.manual_seed(10000)
        env = make_env(config)
        alg, norm = make_algorithm(config, env)
        if args.checkpoint:
            data = read_checkpoint(args.checkpoint)
            restore(data, config, alg, norm, env, training=False)
            meta["checkpoint"] = {"path": str(args.checkpoint.resolve()), "sha256": sha256(args.checkpoint)}
            meta['checkpoint'].update(training_seed=data['config']['seed'], completed_iterations=data['completed_iterations'],
                                      total_environment_steps=data['total_environment_steps'])
        alg.policy.eval()
        norm.eval()
        env.reset()
        offsets = torch.tensor([episode["foot_offsets_xy_m"] for episode in manifest["episodes"]], device=env.device)
        if hasattr(env, 'set_sequence_offsets'):
            orders=None
            if 'episode_order_indices' in manifest['episodes'][0]:
                orders=torch.tensor([e['episode_order_indices'] for e in manifest['episodes']],device=env.device)
            env.set_sequence_offsets(offsets,episode_orders=orders)
            if config.get('jump'):
                env.required_apex[:]=torch.tensor([e['required_apex_m'] for e in manifest['episodes']],device=env.device)
            meta['stance_calibration'] = env.calibration
        else:
            env.targets[:, :, :2] = env.scene.env_origins[:, None, :2] + env.nominal_xy + offsets
        atomic_json(args.out / "scenarios.json", manifest)
        meta["scenario_sha256"] = sha256(args.out / "scenarios.json")
        meta["baseline"] = args.baseline
        meta["nominal_foot_xy_m"] = env.nominal_xy.tolist()
        raw = env._get_observations()["policy"]
        done = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        records = [None] * env.num_envs
        diagnostics = None
        if args.diagnostics:
            from parkour.diagnostics import MotionDiagnostics
            diagnostics = MotionDiagnostics(env, done)
        if args.video:
            from parkour.media import ParallelRecorder
            recorder = ParallelRecorder(env,args.out,count=args.video_envs)
        with torch.inference_mode():
            for step in range(env.max_episode_length + 1):
                if args.baseline == "zero":
                    action = torch.zeros(env.num_envs, 12, device=env.device)
                else:
                    policy_obs = raw.clone()
                    if args.baseline == "shuffled-target":
                        # Replace only target channels; the true task/reward remains unchanged.
                        policy_obs[:, 45:57] = torch.roll(policy_obs[:, 45:57], 1, dims=0)
                    action = alg.policy.act_inference(norm(policy_obs))
                if recorder and not bool(done[recorder.ids].all()):
                    recorder.capture(step,finished=done)
                raw_dict, _, term, trunc, extras = env.step(action)
                raw = raw_dict["policy"]
                newly_done = (term | trunc) & ~done
                for index in newly_done.nonzero().flatten().tolist():
                    metrics = extras["terminal_metrics"]
                    records[index] = {"scenario_id": manifest["episodes"][index]["id"],
                        **{key: val[index].item() for key, val in metrics.items()}}
                    if 'active_foot' in manifest['episodes'][index]:
                        records[index]['active_foot']=manifest['episodes'][index]['active_foot']
                done |= newly_done
                if bool(done.all()):
                    break
        if not bool(done.all()) or any(record is None for record in records):
            raise RuntimeError("Evaluation incomplete; missing scenario results")
        if recorder:
            recorder.close(episode=records[0], episodes=[records[i] for i in recorder.ids],
                           recording_kind='parallel_evaluation',
                           video_stop_rule='last visible first episode; subsequent auto-resets shown but excluded from metrics')
            recorder = None
        if diagnostics:
            diagnostics.close(args.out, [s["id"] for s in manifest["episodes"]])
        count = len(records)
        successes = sum(row["success"] for row in records)
        rate = successes / count
        # Wilson interval describes episode sampling only, not independent training seeds.
        z = 1.96
        center = (rate + z*z/(2*count)) / (1 + z*z/count)
        half = z * ((rate*(1-rate)/count + z*z/(4*count*count))**0.5) / (1 + z*z/count)
        report = {"split": "development", "episodes": count, "successes": successes,
                  "success_rate": rate, "success_wilson95": [center-half, center+half],
                  "failure_rate": sum(row["failure"] for row in records) / count,
                  "timeout_rate": sum(row["timeout"] for row in records) / count,
                  "mean_final_error_m": sum(row["final_error_m"] for row in records) / count,
                  "mean_episode_seconds": sum(row["length"] for row in records) * env.step_dt / count,
                  "results": records}
        if 'completed_contacts' in records[0]:
            report['required_contacts'] = 4 if config.get('jump') else config.get('sequence',{}).get('sequence_length',4)
            report['mean_completed_contacts'] = sum(row['completed_contacts'] for row in records)/count
        if 'valid_flight' in records[0]:
            report['valid_flights']=sum(r['valid_flight'] for r in records)
            report['landed_episodes']=sum(r['landed'] for r in records)
            report['mean_flight_apex_rise_m']=sum(r['flight_apex_rise_m'] for r in records)/count
            report['nonfoot_collisions']=sum(r['nonfoot_collision'] for r in records)
        if 'active_foot' in records[0]:
            report['by_foot']={}
            for foot in env.foot_names:
                subset=[r for r in records if r['active_foot']==foot]
                if subset:
                    report['by_foot'][foot]={'episodes':len(subset),'successes':sum(r['success'] for r in subset),
                        'placed':sum(r['completed_contacts']==report['required_contacts'] for r in subset),
                        'failures':sum(r['failure'] for r in subset),'timeouts':sum(r['timeout'] for r in subset)}
        atomic_json(args.out / "evaluation.json", report)
        meta["evaluation"] = {key: value for key, value in report.items() if key != "results"}
        meta["artifacts"] = {file.name: sha256(file) for file in args.out.iterdir()
                             if file.suffix in (".mp4", ".png") or file.name in ("evaluation.json", "scenarios.json", "replay.json", "diagnostics.json", "motion-trace.npz")}
        finish_run(args.out, meta)
    except BaseException as exc:
        if recorder and recorder.writer:
            recorder.writer.close()
        traceback.print_exc()
        finish_run(args.out, meta, exc)


if __name__ == "__main__":
    main()
