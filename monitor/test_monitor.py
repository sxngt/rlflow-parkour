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
            runs={r['id']:r for r in client.get('/api/runs').json()['items']}
            self.assertEqual(runs['unrelated-evaluation-name']['training_run'],'train')
            self.assertIsNone(runs['train']['training_run'])

    def test_distance_override_summary_corrected_without_source_mutation(self):
        records=[{'scenario_id':str(i),'goal_forward_m':d,'success':True,
                  'launch_in_region':True,'distance_requirement_met':True,
                  'first_touch_all_within':True,'stabilized_once':True}
                 for i,d in enumerate([0.,.15])]
        scenarios=[{'id':r['scenario_id'],'goal_forward_m':r['goal_forward_m']} for r in records]
        raw=json.dumps({'episodes':2,'successes':2,'results':records,'by_distance':{}})
        (self.run/'evaluation.json').write_text(raw)
        (self.run/'scenarios.json').write_text(json.dumps({'episodes':scenarios}))
        self.scan()
        with TestClient(api.app) as client:
            detail=client.get('/api/runs/train/evaluation').json()
            listing=client.get('/api/runs').json()['items'][0]['evaluation']
            self.assertEqual(set(detail['by_distance']),{'0.0','0.15'})
            self.assertEqual(detail['by_distance'],listing['by_distance'])
            self.assertIn('summary_derivation',detail)
        self.assertEqual((self.run/'evaluation.json').read_text(),raw)

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
            self.assertEqual(len(client.get('/api/runs?tag=phase:P1&tag=step:01').json()['items']),1)
            self.assertEqual(client.get('/api/runs?tag=phase:P2').json()['items'],[])
            self.assertEqual(len(client.get('/api/videos?tag=step:01').json()['items']),1)
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

    def test_single_follow_trace_channels(self):
        p=self.root/'result/replay.json'
        p.write_text(json.dumps({'layout':'third_person_follow','visible_env_ids':[0], 'trace':[
            {'sim_time_s':.04,'root_state_w':[1,2,.3]+[0]*10,'foot_positions_w':[[0,0,.02]]*4,
             'accepted_indices':[3,2],'target_indices':[4,3],'measured_jump_count':2,
             'foot_normal_force_N':[10,20,0,0],'actions':[.1]*12}]}))
        with TestClient(api.app) as client:
            result=client.get('/api/replay',params={'path':'result/replay.json'}).json()
            row=result['samples'][0]
            self.assertEqual(row['root_z'],.3);self.assertEqual(row['accepted_indices'],[3,2])
            self.assertEqual(row['measured_jump_count'],2);self.assertEqual(row['feet_z'],[.02]*4)
            self.assertIn('actions',result['available_channels'])

    def test_server_pagination_search_and_small_video_payload(self):
        with store.connect() as db:
            for i in range(65):
                store.put(db,'run',f'job-{i:03}',{'id':f'job-{i:03}','kind':'train',
                    'task':'jump','status':'SUCCEEDED','started_at':1,
                    'run':{'config':{'research_tags':['phase:P2' if i%2 else 'phase:P1']}}})
                store.put(db,'video',f'video-{i:03}',{'id':f'video-{i:03}','title':f'Jump {i}',
                    'video_episodes':[{'huge':'x'*10000}], 'video_episode':{'huge':'y'*10000}})
        with TestClient(api.app) as client:
            first=client.get('/api/runs').json()
            second=client.get('/api/runs?offset=24').json()
            self.assertEqual(first['total'],65)
            self.assertEqual(len(first['items']),24)
            self.assertFalse({r['id'] for r in first['items']} & {r['id'] for r in second['items']})
            self.assertEqual(first['items'][0]['id'],'job-064')
            self.assertEqual(client.get('/api/runs?tag=phase:P2&limit=1').json()['total'],32)
            found=client.get('/api/runs?q=job-001').json()
            self.assertEqual([r['id'] for r in found['items']],['job-001'])
            empty=client.get('/api/runs?offset=99').json()
            self.assertEqual(empty['items'],[]);self.assertEqual(empty['total'],65)
            self.assertEqual(client.get('/api/videos?limit=101').status_code,422)
            videos=client.get('/api/videos')
            self.assertLess(len(videos.content),20000)
            self.assertNotIn('video_episodes',videos.json()['items'][0])

    def test_thumbnail_is_bounded_cached_and_keeps_original(self):
        from PIL import Image
        import io
        source=self.root/'result/preview.png'
        Image.new('RGB',(1280,720),'navy').save(source)
        original=source.read_bytes()
        with TestClient(api.app) as client:
            first=client.get('/api/thumbnail',params={'path':'result/preview.png'})
            self.assertEqual(first.status_code,200)
            self.assertIn('max-age',first.headers['cache-control'])
            picture=Image.open(io.BytesIO(first.content))
            self.assertEqual(picture.size,(480,270))
            second=client.get('/api/thumbnail',params={'path':'result/preview.png'})
            self.assertEqual(first.content,second.content)
            self.assertEqual(len(list((self.root/'.monitor/thumbnails').glob('*.jpg'))),1)
            self.assertEqual(source.read_bytes(),original)
            self.assertEqual(client.get('/api/thumbnail',params={'path':'/etc/passwd'}).status_code,403)

if __name__=='__main__':unittest.main()
