"""Synchronized GPU microbenchmark; no simulator or PPO condition changes."""
import argparse
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from parkour.mapped_contact import mapped_contact_gate_reference as reference,mapped_contact_gate_vectorized as vectorized
from parkour.runtime import begin_run,atomic_json,sha256,finish_run

p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
config={'research_tags':['phase:P3','purpose:contact-gate-profiling'],'benchmark':'mapped_contact_gpu_v1','repeats':100,'warmup':10}
meta=begin_run(args.out,config,'probe')
try:
    import numpy as np
    source=Path('artifacts/p3-11-mapped-seed2-hops8')
    run=json.loads((source/'run.json').read_text())
    with np.load(source/'motion-trace.npz') as z:
        # One real fixed valid sample per environment, tiled for larger batch.
        end=z['valid'].sum(axis=0)-1;indices=np.arange(64)
        positions=z['foot_pos'][end,indices];forces=z['force'][end,indices]
        goals=z['target_xy'][end,indices]
    rows=[]
    for count in (64,1024):
        tensor=lambda a:torch.as_tensor(a,device='cuda:0').repeat(count//64,1,1)
        feet=tensor(positions);force=tensor(forces);goal=tensor(goals)
        targets=torch.cat([goal,torch.full((count,4,1),.02,device='cuda:0')],dim=2)
        env=NS(num_envs=count,device='cuda:0',foot_names=run['evaluation_support']['foot_names'],foot_ids=list(range(4)),contact_ids=list(range(4)),targets=targets,
               scene=NS(env_origins=torch.zeros(count,3,device='cuda:0')),robot=NS(data=NS(body_pos_w=feet)),contacts=NS(data=NS(net_forces_w=force)),
               first_touch=NS(positions=feet[:,:,:2].clone(),seen=torch.ones(count,4,device='cuda:0',dtype=torch.bool)),cfg=NS(support_contract=run['evaluation_support']))
        assert torch.equal(reference(env),vectorized(env))
        timings={}
        for name,function in [('reference',reference),('vectorized',vectorized),('vectorized_repeat',vectorized),('reference_repeat',reference)]:
            for _ in range(10):function(env)
            torch.cuda.synchronize();start=time.perf_counter()
            for _ in range(100):function(env)
            torch.cuda.synchronize();timings[name]=(time.perf_counter()-start)*1000/100
        rows.append({'environments':count,'milliseconds_per_call':timings,'outputs_exact':True})
    report={'source':str(source),'trace_sha256':sha256(source/'motion-trace.npz'),'gpu':torch.cuda.get_device_name(0),'measurements':rows,
            'scope':'Synchronized host+GPU gate microbenchmark using tiled recorded states; not whole simulator or PPO throughput.'}
    atomic_json(args.out/'benchmark.json',report);meta['artifacts']={'benchmark.json':sha256(args.out/'benchmark.json')};print(json.dumps(report),flush=True);finish_run(args.out,meta)
except Exception as error:finish_run(args.out,meta,error)
