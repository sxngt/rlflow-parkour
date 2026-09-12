import unittest
from types import SimpleNamespace as NS
import torch
from parkour.support_geometry import build_full_platform_gap
from parkour.launch_support import LaunchSupportHistory
from parkour.mapped_contact import mapped_contact_gate_reference,mapped_contact_gate_vectorized

class FullGapTest(unittest.TestCase):
    def test_geometry_launch_and_landing(self):
        names=['FL','FR','RL','RR'];xy=[[.114,.16],[.114,-.16],[-.258,.16],[-.258,-.16]]
        layout=build_full_platform_gap(names,xy)
        self.assertAlmostEqual(layout['gap_width_m'],.088)
        dep,land=layout['surfaces'];self.assertLess(dep['bounds_xy_m'][1],land['bounds_xy_m'][0])
        with self.assertRaises(ValueError):build_full_platform_gap(names,xy,.3)
        feet=torch.tensor([[[x,y,.02] for x,y in xy]]).repeat(2,1,1)
        forces=torch.zeros(2,4,3);forces[:,:,2]=20
        history=LaunchSupportHistory(2,'cpu');history.update(forces,feet,torch.zeros(2,dtype=torch.bool))
        self.assertTrue(history.departure_valid(dep).all())
        landing=feet.clone();landing[:,:,0]+=.5
        history.update(forces,landing,torch.tensor([True,False]))
        self.assertEqual(history.departure_valid(dep).tolist(),[True,False])
        history.reset(torch.tensor([0]));self.assertFalse(history.departure_valid(dep).any())
        env=NS(num_envs=2,device='cpu',foot_names=names,foot_ids=list(range(4)),contact_ids=list(range(4)),
            targets=landing.clone(),scene=NS(env_origins=torch.zeros(2,3)),robot=NS(data=NS(body_pos_w=landing)),
            contacts=NS(data=NS(net_forces_w=forces)),first_touch=NS(positions=landing[:,:,:2].clone(),seen=torch.ones(2,4,dtype=torch.bool)),
            cfg=NS(support_contract={'layout':layout}))
        self.assertTrue(mapped_contact_gate_reference(env).all())
        env.first_touch.positions[1,0]=feet[1,0,:2]
        self.assertEqual(mapped_contact_gate_reference(env).tolist(),[True,False])
        self.assertTrue(torch.equal(mapped_contact_gate_reference(env),mapped_contact_gate_vectorized(env)))
        forces[0,0,2]=-20
        self.assertFalse(mapped_contact_gate_reference(env).any())
