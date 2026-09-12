import unittest,torch
from types import SimpleNamespace as S
from parkour.execution_trace import ExecutionTrace
class TraceTests(unittest.TestCase):
 def test_snapshot_and_replay_shapes_without_aliasing(self):
  e=S(robot=S(data=S(root_state_w=torch.arange(13.)[None],joint_pos=torch.zeros(1,12),joint_vel=torch.ones(1,12))),progress=S(target=torch.tensor([[2,1]]),accepted=torch.tensor([[1,0]])),targets=torch.arange(12.).reshape(1,2,2,3),contacts=S(data=S(net_forces_w=torch.arange(12.).reshape(1,4,3))),contact_ids=[0,1,2,3],contact_on=torch.tensor([[True,False,True,False]]),actions=torch.zeros(1,12),flights=S(count=torch.tensor([7])))
  t=ExecutionTrace(1);t.capture(e);e.robot.data.root_state_w.zero_();r=t.serialize()[0]
  self.assertEqual(r['root'],list(range(13)));self.assertEqual(r['targets_w'],[[[0,1,2],[3,4,5]],[[6,7,8],[9,10,11]]]);self.assertEqual(r['jumps'],7);self.assertEqual(r['forces'],[2,5,8,11]);self.assertEqual(r['target'],[2,1]);self.assertEqual(r['contact_on'],[True,False,True,False])
  with self.assertRaises(RuntimeError):t.capture(e)
