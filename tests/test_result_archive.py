import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('collect_results',Path(__file__).resolve().parents[1]/'scripts/collect_results.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ResultArchiveTests(unittest.TestCase):
    def fixture(self, root):
        evaluation=root/'artifacts'/'test-eval'
        evaluation.mkdir(parents=True)
        episode={'scenario_id':'t0-dev-10000','success':False,'failure':False,'timeout':True,'length':200}
        report={'episodes':1,'successes':0,'mean_final_error_m':.05,'results':[episode]}
        for name,payload in {'evaluation.mp4':b'local test video bytes','first-frame.png':b'local test frame bytes',
            'evaluation.json':json.dumps(report).encode(),'replay.json':json.dumps({'episode':episode}).encode(),
            'scenarios.json':b'{"split":"development"}'}.items():
            (evaluation/name).write_bytes(payload)
        run={'kind':'evaluate','status':'SUCCEEDED','config':{'task':'a1_t0_foothold_v1'},
             'baseline':'zero','finished_unix_s':1789026760,
             'artifacts':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in evaluation.iterdir()}}
        (evaluation/'run.json').write_text(json.dumps(run))
        evaluation.with_suffix('.supervisor.json').write_text(json.dumps({'exit_code':0,'resource_released':True}))
        return evaluation

    def test_copy_is_idempotent_and_index_has_one_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            evaluation=self.fixture(root)
            folder=module.collect(evaluation,root/'result')
            self.assertEqual(folder,module.collect(evaluation,root/'result'))
            manifest=json.loads((folder/'manifest.json').read_text())
            self.assertEqual((folder/manifest['video']).read_bytes(),(evaluation/'evaluation.mp4').read_bytes())
            self.assertEqual(len(list((root/'result').glob('*/manifest.json'))),1)
            self.assertIn('시간초과',(folder/'README.md').read_text())

    def test_corrupt_source_rejected_before_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); evaluation=self.fixture(root)
            (evaluation/'evaluation.mp4').write_bytes(b'changed')
            with self.assertRaises(ValueError):module.collect(evaluation,root/'result')
            self.assertFalse((root/'result').exists())

    def test_failed_execution_not_presented_as_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); evaluation=self.fixture(root)
            supervisor=evaluation.with_suffix('.supervisor.json')
            supervisor.write_text(json.dumps({'exit_code':1,'resource_released':True}))
            with self.assertRaises(ValueError):module.collect(evaluation,root/'result')

if __name__=='__main__':unittest.main()
