"""Read-only moving-duration audit of recorded first episodes (including old runs)."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def summarize(name):
    root=ROOT/'artifacts'/name
    report=json.loads((root/'evaluation.json').read_text())
    with np.load(root/'motion-trace.npz') as data:
        active=(np.linalg.norm(data['root_velocity'],axis=-1)>.15)&data['valid']
        seconds=active.sum(axis=0)*.005
        travel=(active&~(data['target_indices']==report['required_final_index']).all(axis=-1)).sum(axis=0)*.005
    return {'run':name,'successes':report['successes'],'episodes':report['episodes'],
        'contact_target_mode':report.get('contact_target_mode','point'),
        'required_transfers':report['required_final_index'],'mean_completed_transfers':report['mean_completed_surface_transfers'],
        'mean_actual_jumps':report['mean_measured_jump_count'],'mean_episode_seconds':report['mean_episode_seconds'],
        'mean_active_motion_seconds':float(seconds.mean()),'first_robot_active_motion_seconds':float(seconds[0]),
        'mean_travel_motion_seconds':float(travel.mean()),'first_robot_travel_motion_seconds':float(travel[0]),
        'first_robot_success':report['results'][0]['success'],
        'motion_contract':'200Hz speed norm >0.15m/s from original trace; read-only reanalysis, original report unchanged'}
if __name__=='__main__':
    rows=[summarize(name) for name in sys.argv[1:]]
    out=ROOT/'docs/long-course-motion-analysis.json';out.write_text(json.dumps(rows,indent=2)+'\n')
    for row in rows:print(json.dumps(row))
