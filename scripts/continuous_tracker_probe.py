"""Physics/observation smoke for new continuous Tracker; zero actions, not learned performance."""
import argparse,json,copy,sys,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from parkour.runtime import begin_run,finish_run,launch_app,atomic_json,sha256
from parkour.shared_terrain import build_shared_course
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
config={'task':'continuous_tracker_smoke_v1','research_tags':['phase:P3','step:p3-18-continuous-tracker','purpose:implementation-check'],
        'num_envs':64,'steps':200,'policy':'zero_actions','scope':'Interface/physics smoke; no trained policy'}
meta=begin_run(args.out,config,'probe')
try:
    launch_app(True)
    import torch
    from parkour.continuous_tracker_task import ContinuousTrackerCfg,ContinuousTrackerEnv
    from parkour.media import ParallelRecorder
    from parkour.collision_contract import inspect_collision_contract
    reference=json.loads(Path('artifacts/p2-11-curriculum-seed0__final-evaluation/run.json').read_text())
    cfg=ContinuousTrackerCfg();cfg.scene.num_envs=64;cfg.scene.env_spacing=7.;cfg.seed=71000
    cfg.support_contract={'mode':'shared-course','matched_material':True,'foot_names':['FL_foot','FR_foot','RL_foot','RR_foot'],
        'layout':build_shared_course(),'calibration':reference['stance_calibration']}
    env=ContinuousTrackerEnv(cfg,render_mode='rgb_array');obs,_=env.reset()
    assert obs['policy'].shape==(64,105) and torch.isfinite(obs['policy']).all()
    atomic_json(args.out/'collision-contract.json',inspect_collision_contract(env))
    atomic_json(args.out/'terrain.json',env.layout);atomic_json(args.out/'target-script.json',env.target_script)
    recorder=ParallelRecorder(env,args.out,name='smoke',count=64,camera_side=4)
    rows=[]
    for step in range(200):
        obs,reward,term,trunc,extra=env.step(torch.zeros(64,12,device=env.device))
        assert torch.isfinite(obs['policy']).all() and torch.isfinite(reward).all()
        rows.append({'step':step+1,'terminations':int(term.sum()),'truncations':int(trunc.sum()),
            'front_target_min':int(env.progress.target[:,0].min()),'front_target_max':int(env.progress.target[:,0].max()),
            'rear_target_min':int(env.progress.target[:,1].min()),'rear_target_max':int(env.progress.target[:,1].max()),
            'mean_reward':float(reward.mean())})
        recorder.capture(step)
    recorder.close(scope=config['scope'],policy='zero_actions')
    atomic_json(args.out/'probe.json',{'rows':rows,'observation_dimension':105,'finite_observations_rewards':True,'scope':config['scope']})
    names=['collision-contract.json','terrain.json','target-script.json','smoke.mp4','smoke-preview.png','smoke-replay.json','probe.json']
    meta['artifacts']={name:sha256(args.out/name) for name in names};finish_run(args.out,meta)
except BaseException as error:traceback.print_exc();finish_run(args.out,meta,error)
