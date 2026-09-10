"""Single writer: reconcile research files and incrementally ingest JSONL every 2s."""
from __future__ import annotations
import csv
import io
import json
import logging
import time
import subprocess
import psutil
from psycopg.types.json import Jsonb
from .store import ROOT, connect, init, put, read_json, safe_path

log=logging.getLogger('parkour.collector')

def ingest_metrics(db, path, run_id):
    st=path.stat()
    key=str(path.relative_to(ROOT))
    cursor=db.execute('SELECT * FROM cursors WHERE path=%s',(key,)).fetchone()
    offset=cursor['offset_bytes'] if cursor else 0
    if cursor and (cursor['inode']!=st.st_ino or st.st_size<offset or (st.st_size==offset and cursor['mtime_ns']!=st.st_mtime_ns)):
        db.execute('DELETE FROM metrics WHERE run_id=%s',(run_id,)); offset=0
    if st.st_size==offset and cursor and cursor['mtime_ns']==st.st_mtime_ns:return
    with path.open('rb') as f:
        f.seek(offset)
        for _ in range(10000):
            start=f.tell(); line=f.readline()
            if not line or not line.endswith(b'\n'): break
            data=json.loads(line)
            db.execute('INSERT INTO metrics VALUES (%s,%s,%s) ON CONFLICT DO NOTHING', (run_id,start,Jsonb(data)))
            offset=f.tell()
    db.execute('''INSERT INTO cursors VALUES (%s,%s,%s,%s) ON CONFLICT(path) DO UPDATE
        SET inode=excluded.inode,offset_bytes=excluded.offset_bytes,mtime_ns=excluded.mtime_ns''', (key,st.st_ino,offset,st.st_mtime_ns))

def number(value):
    try:return float(value)
    except (ValueError,TypeError):return None

def telemetry():
    now=time.time(); gpus=[]; error=None
    fields=['index','uuid','name','utilization.gpu','memory.used','memory.total','temperature.gpu','power.draw','clocks.sm']
    try:
        out=subprocess.run(['nvidia-smi','--query-gpu='+','.join(fields),'--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3,check=True)
        for row in csv.reader(io.StringIO(out.stdout),skipinitialspace=True):
            gpus.append(dict(zip(['index','uuid','name','utilization','memory_used_mb','memory_total_mb','temperature_c','power_w','clock_mhz'],[row[0],row[1],row[2]]+[number(x) for x in row[3:]])))
        apps=subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3,check=True)
        for gpu in gpus:
            gpu['processes']=[{'pid':int(r[1]),'memory_mb':number(r[2])} for r in csv.reader(io.StringIO(apps.stdout),skipinitialspace=True) if len(r)==3 and r[0]==gpu['uuid']]
    except (subprocess.SubprocessError,FileNotFoundError,ValueError) as e:error=str(e)
    mem=psutil.virtual_memory(); disk=psutil.disk_usage(ROOT)
    return {'sampled_at':now,'gpus':gpus,'gpu_error':error,'cpu_percent':psutil.cpu_percent(),
        'ram_used_bytes':mem.used,'ram_total_bytes':mem.total,'disk_free_bytes':disk.free,'disk_total_bytes':disk.total}

class Collector:
    def __init__(self):self.signatures={}
    def changed(self, paths):
        return tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in paths if p.exists())
    def scan(self):
        errors=[]; present_runs=[]; present_videos=[]
        with connect() as db:
            for directory in sorted((ROOT/'artifacts').iterdir()):
                if not directory.is_dir() or not (directory/'run.json').exists():continue
                rid=directory.name; present_runs.append(rid)
                try:
                    safe_path(str(directory.relative_to(ROOT)))
                    paths=[directory/'run.json',directory/'evaluation.json',directory.with_suffix('.supervisor.json'),directory/'metrics.jsonl']
                    sig=self.changed(paths)
                    with db.transaction():
                        if sig!=self.signatures.get(rid):
                            run=read_json(paths[0]); evaluation=read_json(paths[1]) if paths[1].exists() else None
                            supervisor=read_json(paths[2]) if paths[2].exists() else None
                            if paths[3].exists():ingest_metrics(db,paths[3],rid)
                            last=db.execute('SELECT payload FROM metrics WHERE run_id=%s ORDER BY byte_offset DESC LIMIT 1',(rid,)).fetchone()
                            summary={k:v for k,v in (evaluation or {}).items() if k!='results'}
                            config=run.get('config',{})
                            put(db,'run',rid,{'id':rid,'kind':run.get('kind','unknown'),'status':run.get('status','UNKNOWN'),
                                'task':config.get('task','unknown'),'seed':config.get('seed'),'num_envs':config.get('num_envs'),
                                'started_at':run.get('started_unix_s'),'finished_at':run.get('finished_unix_s'),
                                'latest':last['payload'] if last else None,'evaluation':summary or None,
                                'supervisor':supervisor,'run':run,'path':str(directory.relative_to(ROOT))})
                    self.signatures[rid]=sig
                except Exception as e: errors.append({'path':str(directory.relative_to(ROOT)),'error':str(e)})
            for manifest in sorted((ROOT/'result').glob('*/manifest.json')):
                vid=manifest.parent.name; present_videos.append(vid)
                try:
                    sig=self.changed([manifest])
                    if sig!=self.signatures.get('video:'+vid):
                        safe_path(str(manifest.relative_to(ROOT)))
                        data=read_json(manifest); base=manifest.parent.relative_to(ROOT)
                        data.update(id=vid,path=str(base),video_path=str(base/data['video']),preview_path=str(base/'preview.png'))
                        with db.transaction():put(db,'video',vid,data)
                        self.signatures['video:'+vid]=sig
                except Exception as e:errors.append({'path':str(manifest.relative_to(ROOT)),'error':str(e)})
            db.execute("DELETE FROM records WHERE kind='run' AND NOT (id=ANY(%s))",(present_runs,))
            db.execute("DELETE FROM records WHERE kind='video' AND NOT (id=ANY(%s))",(present_videos,))
            sample=telemetry()
            put(db,'system','latest',sample)
            db.execute('INSERT INTO telemetry VALUES (%s,%s)',(sample['sampled_at'],Jsonb(sample)))
            db.execute('DELETE FROM telemetry WHERE sampled_at<%s',(time.time()-7*86400,))
            put(db,'collector','health',{'last_scan':time.time(),'errors':errors,'run_count':len(present_runs),'video_count':len(present_videos),'interval_seconds':2})
        return errors

def main():
    logging.basicConfig(level=logging.INFO)
    init(); collector=Collector()
    while True:
        started=time.monotonic()
        try:
            errors=collector.scan()
            if errors:log.warning('Index warnings: %s',errors)
        except Exception:
            collector.signatures.clear()
            log.exception('Scan failed; retrying')
        time.sleep(max(.1,2-(time.monotonic()-started)))

if __name__=='__main__':main()
