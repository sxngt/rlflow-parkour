import unittest
from types import SimpleNamespace as NS
import torch
from parkour.support_geometry import build_support_layout
from parkour.mapped_contact import mapped_contact_gate

class ContactTest(unittest.TestCase):
    def test_surface_checks_reject_wrong_first_contact_and_missing_support(self):
        names=['FL','FR','RL','RR'];xy=[[.114,.16],[.114,-.16],[-.258,.16],[-.258,-.16]]
        layout=build_support_layout(names,xy,mode='course')
        feet=torch.tensor([[[x+.15,y,.02] for x,y in xy]])
        forces=torch.zeros(1,4,3);forces[:,:,2]=20
        env=NS(num_envs=1,device='cpu',foot_names=names,foot_ids=list(range(4)),contact_ids=list(range(4)),
            targets=feet.clone(),scene=NS(env_origins=torch.zeros(1,3)),
            robot=NS(data=NS(body_pos_w=feet.clone())),
            contacts=NS(data=NS(net_forces_w=forces)),
            first_touch=NS(positions=feet[:,:,:2].clone(),seen=torch.ones(1,4,dtype=torch.bool)),
            cfg=NS(support_contract={'layout':layout}))
        self.assertTrue(mapped_contact_gate(env).item())
        env.first_touch.positions[0,0,0]+=.04
        self.assertFalse(mapped_contact_gate(env).item())
        env.first_touch.positions=feet[:,:,:2].clone();forces[0,0,2]=0
        self.assertFalse(mapped_contact_gate(env).item())
