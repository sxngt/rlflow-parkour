import copy,json,unittest
from pathlib import Path
from parkour.evaluation_distance import distance_override
from parkour.scenarios import directed_jump_scenarios
ROOT=Path(__file__).resolve().parents[1]
class EvaluationDistanceTest(unittest.TestCase):
    def test_deck_override_preserves_scenarios_and_rejects_outside_goals(self):
        config=json.loads((ROOT/'configs/p2-34-chain.json').read_text())
        original=copy.deepcopy(config)
        support=config['terrain_contract']
        manifest,_=distance_override(config,support,[0.,.05,.1,.15],64)
        continuous=json.loads((ROOT/'configs/p2-29-continuous.json').read_text())['terrain_contract']
        reference,_=distance_override(config,continuous,[0.,.05,.1,.15],64)
        self.assertEqual(manifest['episodes'],reference['episodes'])
        self.assertEqual(config,original)
        with self.assertRaises(ValueError): distance_override(config,support,[2.],64)

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

    def test_split_zero_and_fifteen_override_without_gap_goals(self):
        config=json.loads((ROOT/'configs/p2-29-split.json').read_text())
        original=copy.deepcopy(config)
        manifest,change=distance_override(config,config['terrain_contract'],[0.,.15],64)
        self.assertEqual(config,original)
        self.assertEqual(change['to'],[0.,.15])
        self.assertEqual(sum(s['goal_forward_m']==0 for s in manifest['episodes']),32)
        for values in ([.05],[.1],[0.,.05,.15]):
            with self.assertRaises(ValueError):distance_override(config,config['terrain_contract'],values,64)
