"""Integration tests use an isolated PostgreSQL schema and temporary research roots."""
import json
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
import psycopg
from fastapi.testclient import TestClient
from monitor.backend import store, collector, tags as tagstore, app as api

class MonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema='monitor_test_'+uuid.uuid4().hex
        cls.dsn=store.DSN
        with psycopg.connect(cls.dsn) as db:db.execute('CREATE SCHEMA '+cls.schema)
        cls.dsnpatch=patch.object(store,'DSN',cls.dsn+' options=-csearch_path='+cls.schema);cls.dsnpatch.start()
        store.init()
    @classmethod
    def tearDownClass(cls):
        cls.dsnpatch.stop()
        with psycopg.connect(cls.dsn) as db:db.execute('DROP SCHEMA '+cls.schema+' CASCADE')
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        for name in ['artifacts','result','docs','configs']:(self.root/name).mkdir()
        self.patches=[patch.object(m,'ROOT',self.root) for m in [store,collector,api,tagstore]]
        for p in self.patches:p.start()
        with store.connect() as db:
            for table in ['records','metrics','cursors','telemetry']:db.execute('DELETE FROM '+table)
        self.run=self.root/'artifacts/train';self.run.mkdir()
        (self.run/'run.json').write_text(json.dumps({'kind':'train','status':'RUNNING','config':{'task':'test','seed':0}}))
        self.metrics=self.run/'metrics.jsonl'
        self.col=collector.Collector()
        self.telemetry=patch.object(collector,'telemetry',return_value={'sampled_at':1,'gpus':[]});self.telemetry.start()
    def tearDown(self):
        self.telemetry.stop()
        for p in self.patches:p.stop()
        self.tmp.cleanup()
    def scan(self):
        # Unique timestamps for isolated repeated scans.
        self.telemetry.stop()
        with patch.object(collector,'telemetry',return_value={'sampled_at':__import__('time').time(),'gpus':[]}):return self.col.scan()
    def test_partial_append_restart_and_rotation(self):
        self.metrics.write_bytes(b'{"iteration":1}\n{"iteration":')
        self.scan()
        with store.connect() as db:self.assertEqual(db.execute('SELECT count(*) AS n FROM metrics').fetchone()['n'],1)
        with self.metrics.open('ab') as f:f.write(b'2}\n')
        self.col=collector.Collector();self.scan();self.scan()
        with store.connect() as db:self.assertEqual(db.execute('SELECT count(*) AS n FROM metrics').fetchone()['n'],2)
        replacement=self.run/'replacement';replacement.write_text('{"iteration":9}\n');replacement.replace(self.metrics)
        self.scan()
        self.assertEqual(store.record('run','train')['latest']['iteration'],9)
        with store.connect() as db:self.assertEqual(db.execute('SELECT count(*) AS n FROM metrics').fetchone()['n'],1)
    def test_corrupt_metadata_preserves_last_good_record_and_reports_error(self):
        self.scan();(self.run/'run.json').write_text('{')
        self.assertEqual(len(self.scan()),1)
        self.assertEqual(store.record('run','train')['status'],'RUNNING')
        self.assertEqual(len(store.record('collector','health')['errors']),1)
    def test_http_range_confinement_preview_and_metric_cursor(self):
        self.metrics.write_text('{"iteration":1}\n{"iteration":2}\n');self.scan()
        media=self.run/'test.mp4';media.write_bytes(bytes(range(256)))
        (self.root/'result/escape').symlink_to('/etc/passwd')
        with TestClient(api.app) as client:
            self.assertEqual(client.get('/api/runs').status_code,200)
            first=client.get('/api/runs/train/metrics?limit=1').json()
            second=client.get('/api/runs/train/metrics',params={'after':first['next_cursor']}).json()
            self.assertEqual([r['iteration'] for r in second['rows']],[2])
            r=client.get('/api/file',params={'path':'artifacts/train/test.mp4'},headers={'Range':'bytes=20-39'})
            self.assertEqual(r.status_code,206);self.assertEqual(r.content,bytes(range(20,40)))
            self.assertEqual(r.headers['content-range'],'bytes 20-39/256')
            for path in ['../../etc/passwd','/etc/passwd','result/escape','.env']:
                self.assertEqual(client.get('/api/file',params={'path':path}).status_code,403)
            self.assertEqual(client.get('/api/preview',params={'path':'artifacts/train/run.json'}).status_code,200)
            self.assertEqual(client.get('/api/runs/unknown').status_code,404)
    def test_evaluation_links_by_checkpoint_not_run_name(self):
        self.scan()
        evaluation=self.root/'artifacts/unrelated-evaluation-name'
        evaluation.mkdir()
        (evaluation/'run.json').write_text(json.dumps({
            'kind':'evaluate','status':'SUCCEEDED','config':{},
            'checkpoint':{'path':str(self.run/'checkpoint-000100.pt')}
        }))
        self.scan()
        with TestClient(api.app) as client:
            runs={r['id']:r for r in client.get('/api/runs').json()}
            self.assertEqual(runs['unrelated-evaluation-name']['training_run'],'train')
            self.assertIsNone(runs['train']['training_run'])

    def test_phase_tags_filter_runs_and_videos_without_rewriting_sources(self):
        (self.root/'configs/research-tags.json').write_text(json.dumps({'schema_version':1,
            'tags':{'phase:P1':'P1','step:01':'Diagnosis'},'task_defaults':{'test':['phase:P1']}}))
        (self.run/'run.json').write_text(json.dumps({'kind':'train','status':'SUCCEEDED',
            'config':{'task':'test','research_tags':['phase:P1','step:01']}}))
        source=(self.run/'run.json').read_bytes()
        self.scan()
        with store.connect() as db:
            store.put(db,'video','example',{'id':'example','evaluation_run':'train','task':'test','research_tags':['phase:P1','step:01']})
        with TestClient(api.app) as client:
            self.assertEqual(len(client.get('/api/runs?tag=phase:P1&tag=step:01').json()),1)
            self.assertEqual(client.get('/api/runs?tag=phase:P2').json(),[])
            self.assertEqual(len(client.get('/api/videos?tag=step:01').json()),1)
            self.assertEqual(len(client.get('/api/files?path=artifacts&tag=step:01').json()['entries']),1)
            self.assertEqual(client.get('/api/files?path=artifacts&tag=phase:P2').json()['entries'],[])
            self.assertEqual(client.get('/api/tags').json()['tags'][0]['run_count'],1)
        self.assertEqual((self.run/'run.json').read_bytes(),source)

    def test_parallel_replay_environment_selection(self):
        p=self.root/'result/replay.json'
        p.write_text(json.dumps({'visible_env_ids':[3,7],'trace':[{'sim_time_s':0,'visible_env_ids':[3,7],
            'root_state_w':[[0,0,.2],[0,0,.4]],'stage':[1,2],'phase':[0,1]}]}))
        with TestClient(api.app) as client:
            r=client.get('/api/replay',params={'path':'result/replay.json','env':1}).json()
            self.assertEqual(r['env_id'],7);self.assertEqual(r['samples'][0]['root_z'],.4)
            self.assertEqual(r['samples'][0]['stage'],2)
            self.assertEqual(client.get('/api/replay',params={'path':'result/replay.json','env':3}).status_code,400)

if __name__=='__main__':unittest.main()
