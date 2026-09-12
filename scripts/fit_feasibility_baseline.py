"""CPU logistic baseline, leave-one-map-out; no controller deployment."""
from pathlib import Path
import argparse,json,sys,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.feasibility_features import features,FEATURE_CONTRACT

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 import torch
 torch.set_num_threads(1);torch.manual_seed(1)
 m=json.loads((a.dataset/'manifest.json').read_text())
 for name,sha in m['artifacts'].items():
  if digest(a.dataset/name)!=sha:raise ValueError('Dataset hash mismatch')
 if len(m['policies'])!=1:raise ValueError('Fit one frozen Tracker at a time')
 contexts={c['context_id']:c for c in json.loads((a.dataset/'contexts.json').read_text())}
 rows=[json.loads(l) for l in (a.dataset/'labels.jsonl').read_text().splitlines()]
 rows=[r for r in rows if r['censored_count']==0]
 x=torch.tensor([features(contexts[r['context_id']],r) for r in rows]);y=torch.tensor([r['success_count']/r['replicas'] for r in rows])
 groups=sorted(set(r['episode_group'] for r in rows));pred=torch.zeros_like(y);base=torch.zeros_like(y);folds=[]
 def fit(ids):
  mean=x[ids].mean(0);std=x[ids].std(0).clamp_min(.05);z=(x[ids]-mean)/std
  model=torch.nn.Linear(x.shape[1],1);opt=torch.optim.Adam(model.parameters(),lr=.01)
  for _ in range(500):
   loss=torch.nn.functional.binary_cross_entropy_with_logits(model(z).squeeze(1),y[ids])+.01*model.weight.square().sum()
   opt.zero_grad();loss.backward();opt.step()
  return model,mean,std
 for group in groups:
  test=torch.tensor([r['episode_group']==group for r in rows]);train=~test
  model,mean,std=fit(train)
  with torch.no_grad():pred[test]=model((x[test]-mean)/std).squeeze(1).sigmoid();base[test]=y[train].mean()
  folds.append({'held_out_map':group,'candidate_groups':int(test.sum()),'brier':float((pred[test]-y[test]).square().mean()),'constant_brier':float((base[test]-y[test]).square().mean())})
 selected=pred>=.8;selected_rows=[r for r,k in zip(rows,selected.tolist()) if k]
 failure=sum(r['failure_count'] for r in selected_rows);total=sum(r['replicas'] for r in selected_rows)
 report={'feature_contract':FEATURE_CONTRACT,'feature_count':x.shape[1],'candidate_groups':len(rows),'independent_map_groups':len(groups),
  'validation':'leave-one-map-out; correlated replica counts aggregated into one target per candidate',
  'brier':float((pred-y).square().mean()),'constant_baseline_brier':float((base-y).square().mean()),'folds':folds,
  'threshold':.8,'selected_candidate_groups':int(selected.sum()),'selected_replica_failures':failure,'selected_replica_count':total,
  'scope':'Development pilot on three maps. Not calibrated or approved for plan admission; no robot controller is changed.'}
 a.out.mkdir(parents=True,exist_ok=False);model,mean,std=fit(torch.ones(len(rows),dtype=torch.bool))
 torch.save({'model':model.state_dict(),'mean':mean,'std':std,'feature_contract':FEATURE_CONTRACT,'tracker_sha256':m['policies'][0]},a.out/'linear.pt')
 (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 (a.out/'predictions.jsonl').write_text(''.join(json.dumps({**r,'held_out_prediction':float(v)})+'\n' for r,v in zip(rows,pred)))
 (a.out/'manifest.json').write_text(json.dumps({'research_tags':['phase:P3','step:p3-64-feasibility-baseline'],'dataset':str(a.dataset),'dataset_manifest_sha256':digest(a.dataset/'manifest.json'),'artifacts':{n:digest(a.out/n) for n in ('linear.pt','report.json','predictions.jsonl')},'deployment':'none'},indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
