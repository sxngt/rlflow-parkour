import copy,json,unittest
from pathlib import Path
from parkour.evaluation_distance import distance_override
from parkour.scenarios import directed_jump_scenarios
ROOT=Path(__file__).resolve().parents[1]
class EvaluationDistanceTest(unittest.TestCase):
    def test_preserves_training_config_and_matches_existing_regression(self):
        config=json.loads((ROOT/'configs/p2-29-split.json').read_text())
        original=copy.deepcopy(config)
        support=json.loads((ROOT/'configs/p2-29-continuous.json').read_text())['terrain_contract']
        manifest,change=distance_override(config,support,[0,.05,.1,.15],64)
        previous=json.loads((ROOT/'configs/p2-27-continuous.json').read_text())
        self.assertEqual(manifest['episodes'],directed_jump_scenarios(64,previous['jump'])['episodes'])
        self.assertEqual(config,original)
        self.assertEqual(change['from'],[.15])
        for distances in ([.2],[float('nan')],[.1,.1],[-.1],[]):
            with self.assertRaises(ValueError):distance_override(config,support,distances,64)
        with self.assertRaises(ValueError):distance_override(config,config['terrain_contract'],[0,.05],64)
