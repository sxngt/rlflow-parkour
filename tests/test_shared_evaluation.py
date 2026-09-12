import json,copy,unittest
from pathlib import Path
from parkour.shared_evaluation import override_course
class SharedEvaluationTest(unittest.TestCase):
    def test_override_preserves_training_geometry(self):
        original=json.loads(Path('configs/p3-19-long-easy.json').read_text())['terrain_contract'];before=copy.deepcopy(original)
        for level in ['easy','medium','hard']:
            changed=override_course(original,level,101)
            self.assertEqual(len(changed['layout']['surfaces']),11)
            self.assertEqual(changed['geometry_seed'],101)
            self.assertEqual(changed['calibration'],before['calibration'])
        self.assertEqual(original,before)
        with self.assertRaises(ValueError):override_course(original,'easy',-1)
