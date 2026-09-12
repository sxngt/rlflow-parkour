"""Terrain forks preserve learned input/action meaning and checkpoint lineage."""
import copy,json,unittest
from pathlib import Path
from types import SimpleNamespace
import torch
from parkour.policy_fork import validate_fork_configs,initialize_fork
from parkour.learning import make_algorithm
from parkour.shared_terrain import build_long_shared_course

class ContinuousForkTest(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]
        self.parent=json.loads((root/'configs/p3-25-either-foot-progression.json').read_text())
        self.target=copy.deepcopy(self.parent)
        self.target['terrain_contract']['layout']=build_long_shared_course('medium',7)
        self.target['terrain_contract']['geometry_seed']=7
        self.target['research_tags']=['phase:P3','difficulty:medium']
        self.target['contact_curriculum']['stages']=[{'start_update':0,'radius_m':.12},{'start_update':100,'radius_m':.06}]
        self.target['exploration']['stages']=[{'start_update':0,'max_std':.25}]

    def test_generated_difficulty_and_schedules_allowed(self):
        validate_fork_configs(self.parent,self.target)

    def test_region_is_explicit_new_success_contract(self):
        self.target['contact_target_mode']='surface_region'
        with self.assertRaises(ValueError):validate_fork_configs(self.parent,self.target)
        self.target.pop('contact_curriculum')
        validate_fork_configs(self.parent,self.target)
        self.target['contact_target_mode']='anything'
        with self.assertRaises(ValueError):validate_fork_configs(self.parent,self.target)

    def test_incompatible_contracts_and_unversioned_geometry_rejected(self):
        for key,value in [('seed',42),('action_limit',4),('body_progress_weight',20),('pair_contact_quorum','both'),('initial_rear_target','own_stance'),('success_radius_m',.12),('episode_seconds',40)]:
            with self.subTest(key=key):
                bad=copy.deepcopy(self.target);bad[key]=value
                with self.assertRaises(ValueError):validate_fork_configs(self.parent,bad)
        bad=copy.deepcopy(self.target)
        bad['terrain_contract']['layout']['surfaces'][1]['top_center_m'][2]+=.01
        with self.assertRaises(ValueError):validate_fork_configs(self.parent,bad)

    def test_copy_full_105_channel_policy_and_normalization(self):
        env=SimpleNamespace(cfg=SimpleNamespace(observation_space=105),device='cpu',num_envs=2)
        source,norm=make_algorithm(self.parent,env)
        dest,dnorm=make_algorithm(self.target,env)
        data={'config':self.parent,'model':copy.deepcopy(source.policy.state_dict()),'normalizer':copy.deepcopy(norm.state_dict()),'completed_iterations':800,'total_environment_steps':19660800}
        rng=torch.get_rng_state().clone()
        lineage=initialize_fork(data,self.target,dest,dnorm)
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        self.assertFalse(dest.optimizer.state)
        for key,value in dest.policy.state_dict().items():
            if key not in ('std_cap','std_floor'):self.assertTrue(torch.equal(value,data['model'][key]),key)
        for key,value in dnorm.state_dict().items():self.assertTrue(torch.equal(value,data['normalizer'][key]),key)
        self.assertAlmostEqual(float(dest.policy.std_cap),.25)
        self.assertEqual(lineage['initial_completed_iterations'],0)
