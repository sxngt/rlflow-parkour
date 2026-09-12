import unittest
from types import SimpleNamespace
import numpy as np
import torch
from parkour.prefix_replay import PrefixReplay
class PrefixTests(unittest.TestCase):
    def test_rejects_single_diverged_branch(self):
        replay=PrefixReplay.__new__(PrefixReplay);replay.steps=1;replay.metadata={}
        replay.root_state=[0,0,0,1,0,0,0,0,0,0,0,0,0]
        replay.trace={k:np.zeros((5,1,n),dtype=np.float32) for k,n in [('root_pos',3),('root_velocity_world',3),('joint_position',12),('joint_velocity',12),('target_indices',2)]}
        data=SimpleNamespace(root_pos_w=torch.zeros(9,3),root_lin_vel_w=torch.zeros(9,3),root_ang_vel_w=torch.zeros(9,3),root_quat_w=torch.tensor([[1.,0,0,0]]).repeat(9,1),joint_pos=torch.zeros(9,12),joint_vel=torch.zeros(9,12))
        replay.env=SimpleNamespace(device='cpu',robot=SimpleNamespace(data=data),scene=SimpleNamespace(env_origins=torch.zeros(9,3)),progress=SimpleNamespace(target=torch.zeros(9,2,dtype=torch.long)))
        self.assertTrue(replay.validate())
        data.joint_vel[-1,0]=1.
        self.assertFalse(replay.validate())
        self.assertEqual(replay.metadata['errors']['joint_velocity_rad_s'],1.)
