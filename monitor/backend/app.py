from __future__ import annotations
import asyncio
import json
from src.parkour.evaluation_summary import load_report
import time
import hashlib
import tempfile
from threading import BoundedSemaphore
from PIL import Image
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from .tags import catalog, annotate, matches
from .store import ROOT, connect, init, record, records, safe_path, read_json, listing

@asynccontextmanager
async def lifespan(app):
    init()
    yield

app=FastAPI(title='parkour Research Monitor',lifespan=lifespan)
thumbnail_workers=BoundedSemaphore(2)

@app.middleware('http')
async def headers(request, call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    if request.url.path.startswith('/api'):
        response.headers['Cache-Control']='private, max-age=300' if request.url.path=='/api/thumbnail' else 'no-store'
    return response

def resolve(path):
    try:return safe_path(path)
    except ValueError as e:raise HTTPException(403,str(e))
    except FileNotFoundError:raise HTTPException(404,'File not found')

def require_run(id):
    run=record('run',id)
    if not run:raise HTTPException(404,'Run not found')
    return run

def display_seed(r):
    # Evaluation's config seed controls scenarios, not the trained policy.
    if r['kind']=='evaluate':
        r['evaluation_seed']=r.get('seed')
        checkpoint=r.get('run',{}).get('checkpoint') or {}
        r['seed']=checkpoint.get('training_seed')
        if r['seed'] is None and checkpoint.get('path'):
            parent=Path(checkpoint['path']).parent.name
            source=record('run',parent)
            if source and source['kind']=='train':r['seed']=source.get('seed')
    return r

@app.get('/api/health')
def health():
    data=record('collector','health')
    return {'ok':bool(data and time.time()-data['last_scan']<15),'collector':data}

@app.get('/api/overview')
def overview():
    health=record('collector','health'); system=record('system','latest')
    with connect() as db:
        counts=db.execute("""SELECT count(*) FILTER (WHERE kind='run') AS runs,
            count(*) FILTER (WHERE kind='video') AS videos,
            count(*) FILTER (WHERE kind='run' AND payload->>'kind'='train') AS train,
            count(*) FILTER (WHERE kind='run' AND payload->>'kind'='evaluate') AS evaluate,
            count(*) FILTER (WHERE kind='run' AND payload->>'status'='RUNNING') AS running,
            count(*) FILTER (WHERE kind='run' AND payload->>'status' IN ('FAILED','LOST')) AS failed FROM records""").fetchone()
        active=db.execute("SELECT id,payload#>>'{run,pid}' AS pid FROM records WHERE kind='run' AND payload->>'status'='RUNNING'").fetchall()
    for gpu in (system or {}).get('gpus',[]):
        pids={str(p['pid']) for p in gpu.get('processes',[])}
        gpu['runs']=[r['id'] for r in active if r['pid'] in pids]
    return {'system':system,'collector':health,'counts':counts}

@app.get('/api/runs')
def runs(tag: list[str] = Query(default=[]), limit:int=Query(24,ge=1,le=100),
         offset:int=Query(0,ge=0),q:str=Query('',max_length=200),kind:str='',status:str='',training_run:str=''):
    return listing('run',catalog(),limit,offset,q,tag,kind,status,training_run)

@app.get('/api/runs/{id}')
def run_detail(id:str):
    r=display_seed(require_run(id)); annotate(r,id,r.get('run',{}).get('config')); directory=resolve(r['path'])
    r['files']=[{'name':p.name,'path':str(p.relative_to(ROOT)),'size':p.stat().st_size} for p in sorted(directory.iterdir()) if p.is_file() and not p.is_symlink()]
    with connect() as db:
        r['related_videos']=[row['payload'] for row in db.execute("SELECT payload - 'video_episodes' - 'video_episode' AS payload FROM records WHERE kind='video' AND (payload->>'evaluation_run'=%s OR payload->>'training_run'=%s) ORDER BY id DESC LIMIT 24",(id,id))]
    return r

@app.get('/api/runs/{id}/metrics')
def metrics(id:str, after:int=-1, limit:int=Query(2000,ge=1,le=10000)):
    require_run(id)
    with connect() as db:
        rows=db.execute('SELECT byte_offset,payload FROM metrics WHERE run_id=%s AND byte_offset>%s ORDER BY byte_offset LIMIT %s',(id,after,limit)).fetchall()
    return {'rows':[dict(r['payload'],cursor=r['byte_offset']) for r in rows],'next_cursor':rows[-1]['byte_offset'] if rows else after,'has_more':len(rows)==limit}

@app.get('/api/runs/{id}/evaluation')
def evaluation(id:str):
    r=require_run(id); p=resolve(r['path']+'/evaluation.json')
    report=read_json(p)
    if report.get('results') and 'goal_forward_m' in report['results'][0]:
        return load_report(p.parent)
    return report

@app.get('/api/runs/{id}/log')
def logs(id:str, offset:int=Query(-1,ge=-1)):
    r=require_run(id)
    try:p=resolve(r['path']+'.log')
    except HTTPException as e:
        if e.status_code==404:return {'text':'로그 파일이 없습니다.','next_offset':0}
        raise
    size=p.stat().st_size
    start=max(0,size-65536) if offset<0 else (0 if offset>size else offset)
    with p.open('rb') as f:f.seek(start); data=f.read(65536); end=f.tell()
    return {'text':data.decode('utf8',errors='replace'),'start_offset':start,'next_offset':end,'size':size}

@app.get('/api/videos')
def videos(tag: list[str] = Query(default=[]),limit:int=Query(24,ge=1,le=100),
           offset:int=Query(0,ge=0),q:str=Query('',max_length=200)):
    return listing('video',catalog(),limit,offset,q,tag)

@app.get('/api/tags')
def tags():
    rules=catalog();counts={t:0 for t in rules.get('tags',{})}
    with connect() as db:
        rows=db.execute("SELECT id,payload->>'task' AS task,COALESCE(payload->'research_tags',payload#>'{run,config,research_tags}') AS research_tags FROM records WHERE kind='run'").fetchall()
    for r in rows:
        for tag in annotate(r,r['id'],r.get('run',{}).get('config'),rules)['research_tags']:
            counts[tag]=counts.get(tag,0)+1
    return {'schema_version':rules.get('schema_version'), 'tags':[{'id':t,'label':rules.get('tags',{}).get(t,t),'run_count':n} for t,n in sorted(counts.items())]}

@app.get('/api/runs/{id}/diagnostics')
def diagnostics(id:str):
    r=require_run(id)
    return read_json(resolve(r['path']+'/diagnostics.json'))

@app.get('/api/replay')
def replay(path:str, env:int=Query(0,ge=0), limit:int=Query(3000,ge=1,le=10000)):
    p=resolve(path)
    if p.suffix!='.json' or 'replay' not in p.name:raise HTTPException(400,'Replay JSON required')
    if p.stat().st_size>64*1024*1024:raise HTTPException(413,'Replay too large for interactive preview; download original')
    data=read_json(p); trace=data.pop('trace',[])
    ids=data.get('visible_env_ids',[0])
    if env>=len(ids):raise HTTPException(400,'Unknown visible environment')
    rows=[]
    stride=max(1,(len(trace)+limit-1)//limit)
    for row in trace[::stride]:
        parallel='visible_env_ids' in row
        def get(key):
            value=row.get(key)
            return value[env] if parallel and isinstance(value,list) and len(value)>env else value
        root=get('root_state_w'); feet=get('foot_positions_w'); targets=get('targets_w')
        rows.append({'time':row.get('sim_time_s'),'stage':get('stage'),'phase':get('phase'),
            'root_z':root[2] if root else None,'feet_z':[x[2] for x in feet] if feet else None,
            'foot_positions':feet,'targets':targets,'learning_iteration':row.get('learning_iteration'),
            'first_episode_finished':get('first_episode_finished'),
            'foot_normal_force_N':get('foot_normal_force_N'),'contact_state':get('contact_state'),
            'root_vz':get('root_vz'),'actions':get('actions')})
    return {'metadata':data,'env_id':ids[env],'samples':rows,'stride':stride,
        'available_channels':[key for key in ['root_z','feet_z','stage','phase','foot_normal_force_N','contact_state','root_vz','actions'] if any(r.get(key) is not None for r in rows)],'unavailable_channels':['impact']}

@app.get('/api/telemetry')
def telemetry(hours:float=Query(1,gt=0,le=168)):
    with connect() as db:
        rows=db.execute('SELECT payload FROM telemetry WHERE sampled_at>%s ORDER BY sampled_at',(time.time()-hours*3600,)).fetchall()
    stride=max(1,(len(rows)+899)//900)
    return [r['payload'] for r in rows[::stride]]

@app.get('/api/files')
def files(path:str='artifacts',tag:list[str]=Query(default=[]),limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0)):
    p=resolve(path)
    if not p.is_dir():raise HTTPException(400,'Directory required')
    items=[]
    rules=catalog()
    with connect() as db:
        rows=db.execute("SELECT kind,id,payload->>'task' AS task,payload->>'evaluation_run' AS evaluation_run,COALESCE(payload->'research_tags',payload#>'{run,config,research_tags}') AS research_tags FROM records WHERE kind IN ('run','video')").fetchall()
    run_tags={r['id']:annotate(r,r['id'],rules=rules)['research_tags'] for r in rows if r['kind']=='run'}
    video_tags={r['id']:annotate(r,r.get('evaluation_run') or r['id'],rules=rules)['research_tags'] for r in rows if r['kind']=='video'}
    for child in p.iterdir():
        if child.name.startswith('.') or child.is_symlink():continue
        relative=child.relative_to(ROOT).parts
        inherited=[]
        if relative[0]=='artifacts' and len(relative)>1:
            candidates=[rid for rid in run_tags if relative[1]==rid or relative[1].startswith(rid+'.')]
            if candidates:inherited=run_tags[max(candidates,key=len)]
        elif relative[0]=='result' and len(relative)>1:inherited=video_tags.get(relative[1],[])
        if tag and relative[0] in ('artifacts','result') and not all(t in inherited for t in tag):continue
        st=child.stat(); items.append({'research_tags':inherited,'name':child.name,'path':str(child.relative_to(ROOT)),
            'directory':child.is_dir(),'size':st.st_size,'modified_at':st.st_mtime})
    items.sort(key=lambda x:(not x['directory'],x['name']))
    return {'path':str(p.relative_to(ROOT)),'entries':items[offset:offset+limit],'total':len(items),'limit':limit,'offset':offset,'has_more':offset+limit<len(items)}

@app.get('/api/preview')
def preview(path:str):
    p=resolve(path)
    if p.suffix not in {'.json','.jsonl','.log','.md','.txt','.yaml','.yml','.toml','.csv','.py'}:raise HTTPException(415,'Download this format')
    with p.open('rb') as f:data=f.read(262144)
    return {'text':data.decode('utf8',errors='replace'),'truncated':p.stat().st_size>len(data),'size':p.stat().st_size}

@app.get('/api/file')
def file(path:str,download:bool=False):
    p=resolve(path)
    if not p.is_file():raise HTTPException(400,'File required')
    inline={'.mp4':'video/mp4','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg'}
    media=inline.get(p.suffix,'application/octet-stream')
    return FileResponse(p,media_type=media,filename=p.name,content_disposition_type='attachment' if download or p.suffix not in inline else 'inline')

@app.get('/api/thumbnail')
def thumbnail(path:str):
    source=resolve(path)
    if source.suffix.lower() not in ('.png','.jpg','.jpeg'):
        raise HTTPException(415,'Image required')
    stat=source.stat()
    key=hashlib.sha256(f'{source}:{stat.st_mtime_ns}:{stat.st_size}:480-v1'.encode()).hexdigest()
    cache=ROOT/'.monitor/thumbnails';cache.mkdir(parents=True,exist_ok=True)
    target=cache/(key+'.jpg')
    with thumbnail_workers:
        if not target.exists():
            with Image.open(source) as picture:
                picture.thumbnail((480,270))
                with tempfile.NamedTemporaryFile(dir=cache,suffix='.tmp',delete=False) as temporary:
                    tmp=Path(temporary.name)
                try:
                    picture.convert('RGB').save(tmp,format='JPEG',quality=75,optimize=True)
                    tmp.replace(target)
                finally:
                    tmp.unlink(missing_ok=True)
    return FileResponse(target,media_type='image/jpeg')

@app.get('/api/events')
async def events(request:Request):
    async def stream():
        while not await request.is_disconnected():
            try:
                state=await asyncio.to_thread(record,'collector','health')
                yield 'event: refresh\ndata: '+json.dumps(state)+'\n\n'
            except Exception:yield 'event: unavailable\ndata: {}\n\n'
            await asyncio.sleep(2)
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'X-Accel-Buffering':'no','Cache-Control':'no-cache'})

DIST=ROOT/'web/dist'
if (DIST/'assets').exists():app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
@app.get('/')
def index():
    if not (DIST/'index.html').exists():raise HTTPException(503,'Build web first')
    return FileResponse(DIST/'index.html')
