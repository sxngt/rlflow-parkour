import unittest
from types import SimpleNamespace
from parkour.planner_states import environment_hash,restore_airborne_state,capture_prediction_state
class PredictionContractTests(unittest.TestCase):
 def test_forecast_is_not_training_reset(self):
  env=SimpleNamespace(physics_dt=.005,step_dt=.02,planner_rollout_only=False)
  payload={'contract':{'schema_version':1,'environment_hash':environment_hash({}),'checkpoint_sha256':'x','physics_dt_s':.005,'control_dt_s':.02,'planner_only':True}}
  with self.assertRaisesRegex(ValueError,'only initialize lean'):restore_airborne_state(env,payload,0,{},'x')
  with self.assertRaisesRegex(ValueError,'requires planner mode'):capture_prediction_state(env,{},'x',0,0)
 def test_non_airborne_forecast_rejected_before_reset(self):
  env=SimpleNamespace(physics_dt=.005,step_dt=.02,planner_rollout_only=True)
  payload={'contract':{'schema_version':1,'environment_hash':environment_hash({}),'checkpoint_sha256':'x','physics_dt_s':.005,'control_dt_s':.02,'planner_only':True},'states':[{'physical_airborne_check':{'foot_force_max_N':3,'nonfoot_force_max_N':0}}]}
  with self.assertRaisesRegex(ValueError,'not clean airborne'):restore_airborne_state(env,payload,0,{},'x')
