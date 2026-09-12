"""Describe the fixed follow robot's gap progress and airborne intervals."""
import argparse,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from parkour.flight_trace import reconstruct_flights
from parkour.runtime import sha256

def analyze(directory):
    directory=Path(directory)
    run=json.loads((directory/'run.json').read_text())
    report=json.loads((directory/'evaluation.json').read_text())
    layout=json.loads((directory/'terrain.json').read_text())
    # Some task archives wrap the exact evaluated layout in a support contract.
    layout=layout.get('layout',layout)
    with np.load(directory/'motion-trace.npz') as data:
        valid=data['valid'][:,0]
        trace={key:data[key][valid,0] for key in ('root_pos','root_velocity_world',
            'force','nonfoot_force_max','target_indices','accepted_indices')}
        times=data['time'][valid]
    events=reconstruct_flights(trace['force'],trace['root_pos'][:,2],
        trace['root_velocity_world'][:,2],trace['nonfoot_force_max'],.005)
    for event in events:
        start,end=event['takeoff_sample'],event['landing_sample']
        event['takeoff_s']=float(times[start]);event['landing_s']=float(times[end])
        event['horizontal_displacement_m']=float(np.linalg.norm(trace['root_pos'][end,:2]-trace['root_pos'][max(0,start-1),:2]))
    gaps=[]
    for gap in layout.get('gap_locations',[]):
        target=gap['arrival_surface_index'];accepted=[]
        for pair in range(2):
            indices=np.flatnonzero(trace['accepted_indices'][:,pair]>=target)
            accepted.append(float(times[indices[0]]) if len(indices) else None)
        linked=[]
        for event in events:
            start,end=event['takeoff_sample'],event['landing_sample']
            if event['air_seconds']>=.02-1e-7 and (trace['target_indices'][start:end+1]==target).any():
                linked.append(event)
        gaps.append({**gap,'front_accepted_s':accepted[0],'rear_accepted_s':accepted[1],
            'both_pairs_accepted':all(t is not None for t in accepted),'airborne_intervals':linked})
    return {'kind':'fixed_follow_robot_gap_diagnostics','source':str(directory.resolve()),
        'evaluation_sha256':sha256(directory/'evaluation.json'),'trace_sha256':sha256(directory/'motion-trace.npz'),
        'robot_env_index':0,'episode':report['results'][0],
        'reconstructed_jump_count':sum(e['counted_jump'] for e in events),'gaps':gaps,
        'scope':'Target-index association, not proof of physical gap crossing. Only completed recontact intervals >=20ms listed per gap; drops and rejected jumps remain visible. Fixed first robot, no success selection.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args();report=analyze(args.directory)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(args.out)
