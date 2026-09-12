import copy
import json
from pathlib import Path
import tempfile
import unittest
from parkour.evaluation_summary import by_distance, load_report

class EvaluationSummaryTest(unittest.TestCase):
    def data(self):
        scenarios=[{'id':str(i),'goal_forward_m':d} for i,d in enumerate([0.,.05,.1,.15])]
        records=[{'scenario_id':s['id'],'goal_forward_m':s['goal_forward_m']+1e-9,
                  'success':i!=1,'launch_in_region':True,'distance_requirement_met':True,
                  'first_touch_all_within':True,'stabilized_once':True} for i,s in enumerate(scenarios)]
        return records,scenarios
    def test_override_groups_and_nonmutating_archive_view(self):
        records,scenarios=self.data();summary=by_distance(records,scenarios)
        self.assertEqual(len(summary),4);self.assertEqual(summary['0.05']['successes'],0)
        report={'episodes':4,'successes':3,'results':records,'by_distance':{'0.15':summary['0.15']}}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);raw=json.dumps(report)
            (p/'evaluation.json').write_text(raw);(p/'scenarios.json').write_text(json.dumps({'episodes':scenarios}))
            derived=load_report(p)
            self.assertEqual((p/'evaluation.json').read_text(),raw)
            self.assertEqual(derived['results'],records);self.assertEqual(derived['successes'],3)
            self.assertEqual(sum(r['episodes'] for r in derived['by_distance'].values()),4)
            self.assertIn('summary_derivation',derived)
    def test_reject_missing_duplicate_and_wrong_distance(self):
        records,scenarios=self.data()
        with self.assertRaises(ValueError):by_distance(records[:-1],scenarios)
        for key,value in [('scenario_id','wrong'),('goal_forward_m',.2),('goal_forward_m',float('nan'))]:
            bad=copy.deepcopy(records);bad[0][key]=value
            with self.assertRaises(ValueError):by_distance(bad,scenarios)
        with self.assertRaises(ValueError):by_distance([records[0]]*2,[scenarios[0]]*2)
