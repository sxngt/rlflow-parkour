"""Render recorded online-executor articulation states without physics re-execution."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.runtime import begin_run,finish_run,launch_app,sha256,atomic_json

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();source=json.loads((a.source/'run.json').read_text())
 if source['status']!='SUCCEEDED' or sha256(a.source/'state-playback.json')!=source['artifacts']['state-playback.json']:raise ValueError('Invalid source trace')
 c=dict(source['config']);c['num_envs']=1;c['research_tags']=['phase:P3','step:p3-57-online-planner','purpose:state-playback-follow']
 meta=begin_run(a.out,c,'probe')
 try:
  launch_app(True)
  import torch
  from parkour.learning import make_env
  from parkour.media import FollowRecorder
  env=make_env(c,evaluation_support=source.get('evaluation_support'));env.reset();rec=FollowRecorder(env,a.out)
  frames=json.loads((a.source/'state-playback.json').read_text())['frames']
  if frames and 'planned_contacts' not in frames[0]:
   rec.plan_markers.set_visibility(False);rec.plan_markers=None
  for row in frames:
   if row['step']%2:continue
   root=torch.tensor([row['root']],device=env.device);q=torch.tensor([row['q']],device=env.device);dq=torch.tensor([row['dq']],device=env.device)
   env.robot.write_root_state_to_sim(root);env.robot.write_joint_state_to_sim(q,dq);env.sim.forward()
   env.progress.target[0]=torch.tensor(row['target'],device=env.device);env._sync_targets()
   if 'planned_contacts' in row:env.follow_planned_contacts_override=row['planned_contacts']
   elif getattr(env,'candidate_plan',None) is not None:raise ValueError('Historical candidate playback needs recorded planned contacts')
   rec.capture(row['step'])
   r=rec.trace[-1]
   # Sensor data come from the execution trace, never the non-stepped renderer.
   for key in ('foot_normal_force_N','contact_state','actions','accepted_indices','measured_jump_count'):r.pop(key,None)
   if 'forces' in row:r.update(foot_normal_force_N=row['forces'],contact_state=row['contact_on'],actions=row['actions'],accepted_indices=row['accepted'],measured_jump_count=row['jumps'],targets_w=row['targets_w'])
  rec.close(artifact_type='recorded_state_playback',source_run=str(a.source),source_sha256=sha256(a.source/'state-playback.json'),
    scope='Articulation states captured during asynchronous execution; rendered afterward with no physics steps. Not original camera frames or a new evaluation.')
  meta['artifacts']={p.name:sha256(p) for p in a.out.iterdir() if p.is_file() and p.name not in ('run.json','config.json')}
  finish_run(a.out,meta)
 except BaseException as error:finish_run(a.out,meta,error)
if __name__=='__main__':main()
