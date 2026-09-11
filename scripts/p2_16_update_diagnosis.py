"""Descriptive checkpoint drift and terminal gates; no causal KL inference."""
import hashlib
import json
from pathlib import Path
import torch
ROOT = Path(__file__).resolve().parents[1]


def main():
    rows, gates = [], []
    for seed in range(4):
        base = ROOT/'artifacts'/f'p2-16-deck-seed{seed}'
        previous = None
        for update in range(100,1601,100):
            path = base/f'checkpoint-{update:06d}.pt'
            side = json.loads(path.with_suffix('.json').read_text())
            assert hashlib.sha256(path.read_bytes()).hexdigest() == side['sha256']
            d = torch.load(path,map_location='cpu',weights_only=False)
            actor = torch.cat([v.flatten() for k,v in d['model'].items() if k.startswith('actor.')])
            norm = d['normalizer']
            row = {'seed':seed,'update':update,'learning_rate':d['learning_rate'],
                   'optimizer_lrs':[g['lr'] for g in d['optimizer']['param_groups']],
                   'action_std_mean':float(d['model']['std'].mean()),
                   'normalizer_count':int(norm['count']), 'normalizer_std_min':float(norm['_std'].min())}
            if previous:
                row['actor_relative_l2_change'] = float((actor-previous['actor']).norm()/previous['actor'].norm())
                shift = (norm['_mean']-previous['mean'])/previous['std'].clamp_min(1e-6)
                row['normalizer_mean_shift_previous_std_rms'] = float(shift.square().mean().sqrt())
            rows.append(row)
            previous = {'actor':actor,'mean':norm['_mean'],'std':norm['_std']}
        for update in (800,1200,1600):
            suffix='__final-evaluation' if update==1600 else f'__checkpoint-{update:06d}-evaluation'
            report=json.loads((base.with_name(base.name+suffix)/'evaluation.json').read_text())
            r=report['results']
            gates.append({'seed':seed,'update':update,'successes':report['successes'],
                          'terminal_no_all_contact':sum(not x['final_contact_all'] for x in r),
                          'terminal_not_supported':sum(not x['final_supported'] for x in r),
                          'terminal_feet_outside_radius':sum(not x['final_all_feet_in_radius'] for x in r),
                          'terminal_vz_outside':sum(abs(x['final_vz_m_s'])>.15 for x in r),
                          'terminal_omega_outside':sum(x['final_angular_speed_rad_s']>1 for x in r),
                          'terminal_height_outside':sum(abs(x['final_height_error_m'])>.06 for x in r)})
    out={'checkpoint_rows':rows,'terminal_gates':gates,
         'limitations':'Checkpoint learning rate is an endpoint, not within-update maxima or measured KL. Parameter/normalizer drift is descriptive and does not isolate optimizer or curriculum causation. Terminal gates are final samples, not whole-episode causes.'}
    (ROOT/'docs/p2-16-update-diagnosis.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'checkpoints':[r for r in rows if r['update'] in (800,1200,1600)],'terminal_gates':gates},indent=2))


if __name__=='__main__':main()
