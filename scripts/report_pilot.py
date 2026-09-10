"""Regenerate the T0 pilot table/figure from saved evaluation artifacts."""
import json
import statistics
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1]
rows = []
zero = json.loads((root / "artifacts/t0-zero-dev/evaluation.json").read_text())
for seed in range(4):
    normal = json.loads((root / f"artifacts/t0-eval500-seed{seed}/evaluation.json").read_text())
    shuffled = json.loads((root / f"artifacts/t0-shuffle500-seed{seed}/evaluation.json").read_text())
    rows.append((seed, normal, shuffled))
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
x = list(range(4))
for shift, column, label, color in ((-0.18, 1, "PPO: correct targets", "#2367a6"), (0.18, 2, "PPO: shuffled targets", "#c07135")):
    axes[0].bar([i+shift for i in x], [row[column]["success_rate"]*100 for row in rows], width=.34, label=label, color=color)
    axes[1].bar([i+shift for i in x], [row[column]["mean_final_error_m"]*100 for row in rows], width=.34, color=color)
axes[1].axhline(zero["mean_final_error_m"]*100, color="#777", linestyle="--", label="Constant-pose baseline")
for ax in axes:
    ax.set_xticks(x, [str(i) for i in x])
    ax.set_xlabel("Training seed")
    ax.spines[["top", "right"]].set_visible(False)
axes[0].set_ylabel("Development success (%)")
axes[0].set_ylim(0, 100)
axes[0].legend(fontsize=8)
axes[1].set_ylabel("Mean final foot XY error (cm)")
axes[1].legend(fontsize=8)
fig.suptitle("A1 T0 static foothold pilot: 64 fixed scenarios per seed, 500 PPO updates")
folder = root / "docs/figures"
folder.mkdir(exist_ok=True)
fig.savefig(folder / "t0-pilot.png", dpi=160)
plt.close(fig)
lines = ["| 모델 | 목표 접촉 성공 | 낙상/실패 | 평균 최종 발 오차 | 목표 셔플 성공 / 오차 |", "|---|---:|---:|---:|---:|"]
lines.append(f"| 기본 자세 | {zero['successes']}/64 | {zero['failure_rate']*100:.1f}% | {zero['mean_final_error_m']*100:.2f} cm | — |")
for seed, n, s in rows:
    lines.append(f"| PPO seed {seed} | {n['successes']}/64 ({n['success_rate']*100:.1f}%) | {n['failure_rate']*100:.1f}% | {n['mean_final_error_m']*100:.2f} cm | {s['successes']}/64 / {s['mean_final_error_m']*100:.2f} cm |")
text = '\n'.join(lines)
(root / "docs/pilot-table.md").write_text(text + '\n')
print(text)
