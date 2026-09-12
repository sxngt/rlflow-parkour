import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import torch
from parkour.observation_contract import validate_history
from parkour.observation_history import ObservationHistory, HistoryNormalization
from parkour.learning import make_algorithm
from parkour.policy_fork import initialize_fork

ROOT=Path(__file__).resolve().parents[1]
def specification(mode='stack'):
    return {'schema_version':1,'frames':8,'base_observation_dim':66,'normalization':'shared_current_frame','reset':'episode_boundary','mode':mode}

class HistoryTest(unittest.TestCase):
    def test_clock_reset_and_duplicate_reads(self):
        h=ObservationHistory(2,'cpu',specification())
        a=torch.ones(2,66);clock=torch.zeros(2,dtype=torch.long)
        first=h.encode(a,clock);self.assertEqual(first.shape,(2,535));self.assertEqual(first[:,528:].sum(),0)
        second=h.encode(2*a,clock+1)
        self.assertTrue(torch.equal(second[:,66:132],a));self.assertTrue(torch.equal(second[:,528],torch.ones(2)))
        repeated=h.encode(3*a,clock+1)
        self.assertTrue(torch.equal(repeated[:,66:],second[:,66:]));self.assertTrue(torch.equal(repeated[:,:66],3*a))
        h.reset(torch.tensor([0]));after=h.encode(4*a,torch.tensor([0,2]))
        self.assertEqual(after[0,528:].sum(),0);self.assertEqual(after[1,528:].sum(),2)
        skipped=h.encode(5*a,torch.tensor([4,5]));self.assertEqual(skipped[:,528:].sum(),0)
    def test_shared_normalization_updates_current_only_and_masks_padding(self):
        spec=specification();norm=HistoryNormalization(spec);h=ObservationHistory(2,'cpu',spec)
        for step in range(3):
            raw=torch.randn(2,66);encoded=h.encode(raw,torch.full((2,),step,dtype=torch.long))
            normalized=norm(encoded)
            self.assertEqual(int(norm.count),(step+1)*2)
            self.assertTrue(torch.allclose(normalized[:,:66],(raw-norm._mean)/(norm._std+norm.eps)))
            self.assertEqual(normalized[:,66:528].reshape(2,7,66)[:,step:].abs().sum(),0)
        zero=ObservationHistory(2,'cpu',specification('zero_control')).encode(raw,torch.zeros(2,dtype=torch.long))
        self.assertEqual(norm(zero)[:,66:].abs().sum(),0)
    def test_fork_preserves_initial_mean_and_parameter_count(self):
        parent=json.loads((ROOT/'configs/p3-08-mapped.json').read_text())
        env=lambda n:SimpleNamespace(cfg=SimpleNamespace(observation_space=n),device='cpu',num_envs=2)
        source,source_norm=make_algorithm(parent,env(66));source_norm.eval()
        data={'config':parent,'model':copy.deepcopy(source.policy.state_dict()),'normalizer':copy.deepcopy(source_norm.state_dict()),'completed_iterations':800,'total_environment_steps':1}
        counts=[]
        for mode in ('stack','zero_control'):
            target=copy.deepcopy(parent);target['observation_history']=specification(mode);validate_history(target)
            dest,norm=make_algorithm(target,env(535));initialize_fork(data,target,dest,norm);norm.eval()
            buffer=ObservationHistory(2,'cpu',target['observation_history'])
            for step in range(4):
                raw=torch.randn(2,66);encoded=buffer.encode(raw,torch.full((2,),step,dtype=torch.long))
                self.assertTrue(torch.allclose(dest.policy.actor(norm(encoded)),source.policy.actor(source_norm(raw)),atol=1e-6,rtol=1e-6))
            counts.append(sum(p.numel() for p in dest.policy.parameters()))
            self.assertEqual(dest.policy.actor[0].weight[:,66:].abs().sum(),0)
        self.assertEqual(counts[0],counts[1])
