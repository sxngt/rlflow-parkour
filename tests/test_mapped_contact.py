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

    def test_vectorized_matches_reference_at_boundaries_and_changed_map(self):
        from parkour.mapped_contact import mapped_contact_gate_reference, mapped_contact_gate_vectorized
        import copy
        names=['FL','FR','RL','RR'];xy=[[.114,.16],[.114,-.16],[-.258,.16],[-.258,-.16]]
        for dtype in (torch.float32,torch.float64):
            torch.manual_seed(3);count=256
            layout=build_support_layout(names,xy,mode='course',course_hops=8)
            origins=torch.randn(count,3,dtype=dtype)*10
            goal=torch.tensor([[[x+.15,y,.02] for x,y in xy]],dtype=dtype).repeat(count,1,1)
            feet=goal.clone();feet[:,:,:2]+=torch.randn(count,4,2,dtype=dtype)*.008
            first=feet[:,:,:2].clone();first[::7,0,0]+=.05;feet[::11,:,2]+=.1
            forces=torch.zeros(count,4,3,dtype=dtype);forces[:,:,2]=20;forces[::13,0,2]=0
            seen=torch.ones(count,4,dtype=torch.bool);seen[::17,1]=False
            surface=next(s for s in layout['surfaces'] if s['id']=='FL_station_1')
            limit=surface['bounds_xy_m'][0]+.02-1e-6
            for index,shift in enumerate((-1e-7,0.,1e-7)):
                goal[index,0,0]=limit+shift
            env=NS(num_envs=count,device='cpu',foot_names=names,foot_ids=list(range(4)),contact_ids=list(range(4)),
                targets=goal+origins[:,None,:],scene=NS(env_origins=origins),
                robot=NS(data=NS(body_pos_w=feet+origins[:,None,:])),contacts=NS(data=NS(net_forces_w=forces)),
                first_touch=NS(positions=first,seen=seen),cfg=NS(support_contract={'layout':layout}))
            reference=mapped_contact_gate_reference(env);self.assertGreater(reference.sum(),0)
            self.assertTrue(torch.equal(reference,mapped_contact_gate_vectorized(env)))
            env.cfg.support_contract['layout']=copy.deepcopy(layout)
            env.cfg.support_contract['layout']['surfaces']=[s for s in layout['surfaces'] if s['id']!='FL_station_1']
            self.assertTrue(torch.equal(mapped_contact_gate_reference(env),mapped_contact_gate_vectorized(env)))
