"""Export hash-verified four-surface rollout labels, preserving context/replica groups."""
from pathlib import Path
import argparse,json,hashlib
from audit_artifacts import audit

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def export(sources,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=False);contexts=[];rows=[]
 for source in map(Path,sources):
  audit(source);run=json.loads((source/'run.json').read_text());report=json.loads((source/'planner-rollouts.json').read_text())
  if report['contract']['horizon']!=4:raise ValueError('Dataset contract requires four-surface labels')
  state=json.loads((source/'source-state.json').read_text());context=digest(source/'source-state.json')
  checkpoint=report['checkpoint_sha256'];group=report['source']
  contexts.append({'context_id':context,'policy_sha256':checkpoint,'episode_group':group,'source_assay':str(source),
    'source_artifacts':run['artifacts'],'terrain':run.get('evaluation_support',run['config']['terrain_contract']), 'state':state})
  for cid,offset in enumerate(report['contract']['offsets_surface_xy_m']):
   episodes=[r for r in report['episodes'] if r['candidate_id']==cid]
   rows.append({'context_id':context,'policy_sha256':checkpoint,'episode_group':group,'candidate_id':cid,'offset_surface_xy_m':offset,
    'horizon':4,'start_surface':report['contract']['start_surface'],'success_count':sum(r['horizon_reached'] for r in episodes),
    'failure_count':sum(r['failure'] and not r['horizon_reached'] for r in episodes),
    'censored_count':sum(not r['failure'] and not r['horizon_reached'] for r in episodes),'replicas':len(episodes)})
 (out/'contexts.json').write_text(json.dumps(contexts,indent=2)+'\n')
 (out/'labels.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 manifest={'schema_version':1,'contexts':len(contexts),'candidate_groups':len(rows),'policies':sorted(set(r['policy_sha256'] for r in rows)),
  'split':'development_collection_unassigned','split_rule':'Hold out complete source episodes/maps, never individual correlated replicas; fit separately per Tracker hash.',
  'scope':'Physics-assay labels only; no learned feasibility model or accuracy claim. Budget exhaustion is censored, not failure.',
  'artifacts':{name:digest(out/name) for name in ('contexts.json','labels.jsonl')}}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('sources',nargs='+');a=p.parse_args();print(json.dumps(export(a.sources,a.out)))
