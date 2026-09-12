"""Read-only control-step reward accounting for complete first episodes."""
import numpy as np
import torch
from parkour.runtime import atomic_json

class RewardAudit:
    def __init__(self):
        self.names=None
        self.values=[]
        self.rewards=[]
        self.active=[]
        self.max_error=0.

    def collect(self, reward, components, done):
        names=list(components)
        if self.names is None:self.names=names
        if names != self.names:raise ValueError('Reward component contract changed during evaluation')
        values=torch.stack([components[k] for k in names],dim=-1)
        if not torch.isfinite(values).all() or not torch.isfinite(reward).all():
            raise ValueError('Nonfinite reward accounting')
        error=(values.sum(dim=-1)-reward).abs()
        if not torch.allclose(values.sum(dim=-1),reward,atol=2e-5,rtol=2e-6):
            raise ValueError('Reward components do not reconstruct simulator reward')
        self.max_error=max(self.max_error,float(error.max()))
        self.values.append(values.detach().cpu().numpy().copy())
        self.rewards.append(reward.detach().cpu().numpy().copy())
        self.active.append((~done).detach().cpu().numpy().copy())

    def close(self, directory, scenarios, step_dt):
        values=np.stack(self.values);rewards=np.stack(self.rewards);active=np.stack(self.active)
        totals=(values*active[:,:,None]).sum(axis=0,dtype=np.float64)
        actual=(rewards*active).sum(axis=0,dtype=np.float64)
        np.savez_compressed(directory/'reward-components.npz',components=values,reward=rewards,active=active)
        atomic_json(directory/'reward-components.json',dict(schema_version=1,names=self.names,
            control_step_seconds=step_dt,max_step_reconstruction_error=self.max_error,
            scope='control-step grouped rewards; first episodes only; dense includes all continuous costs',
            episodes=[dict(scenario_id=s['id'],steps=int(active[:,i].sum()),
                components=dict(zip(self.names,totals[i].tolist())),actual_return=float(actual[i]))
                for i,s in enumerate(scenarios)]))
