import unittest,torch
from types import SimpleNamespace as NS
from parkour.terminal_pose import TerminalPoseHold

class TerminalPoseTest(unittest.TestCase):
    def test_dwell_blend_and_no_early_handoff(self):
        data=NS(default_joint_pos=torch.zeros(1,12),root_pos_w=torch.zeros(1,3),root_lin_vel_w=torch.zeros(1,3),root_ang_vel_b=torch.zeros(1,3),projected_gravity_b=torch.tensor([[0.,0.,-1.]]))
        env=NS(num_envs=1,device='cpu',robot=NS(data=data),calibrated_joint_pos=torch.full((12,),.2),cfg=NS(action_scale=.5,action_limit=1.),scene=NS(env_origins=torch.zeros(1,3)),goal=torch.zeros(3),progress=NS(accepted=torch.tensor([[9,9]]),target_count=11),current_valid=torch.ones(1,4,dtype=torch.bool))
        controller=TerminalPoseHold(env);action=torch.full((1,12),-.5);done=torch.tensor([False])
        for step in range(3):self.assertTrue(torch.equal(controller.apply(None,action,step,done),action))
        env.progress.accepted[:]=10
        for step in (3,4):self.assertTrue(torch.equal(controller.apply(None,action,step,done),action))
        first=controller.apply(None,action,5,done)
        self.assertTrue(controller.latched[0]);self.assertEqual(controller.steps[0],5)
        self.assertTrue((first>action).all());self.assertTrue((first<.4).all())
        self.assertTrue(torch.allclose(controller.apply(None,action,19,done),torch.full((1,12),.4)))
        capture=TerminalPoseHold(env,'contact-capture')
        data.root_ang_vel_b[0,0]=6.
        capture.apply(None,action,20,done)
        self.assertTrue(capture.latched[0])
        settled=TerminalPoseHold(env)
        settled.apply(None,action,20,done)
        self.assertFalse(settled.latched[0])
