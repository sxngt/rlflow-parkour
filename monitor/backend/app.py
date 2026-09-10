from __future__ import annotations
import asyncio
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from .store import ROOT, connect, init, record, records, safe_path, read_json

@asynccontextmanager
async def lifespan(app):
    init()
    yield

app=FastAPI(title='parkour Research Monitor',lifespan=lifespan)

@app.middleware('http')
async def headers(request, call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    if request.url.path.startswith('/api'):response.headers['Cache-Control']='no-store'
    return response

def resolve(path):
    try:return safe_path(path)
    except ValueError as e:raise HTTPException(403,str(e))
    except FileNotFoundError:raise HTTPException(404,'File not found')

def require_run(id):
    run=record('run',id)
    if not run:raise HTTPException(404,'Run not found')
    return run

@app.get('/api/health')
def health():
    data=record('collector','health')
    return {'ok':bool(data and time.time()-data['last_scan']<15),'collector':data}

@app.get('/api/overview')
def overview():
    runs=records('run'); health=record('collector','health'); system=record('system','latest')
    for gpu in (system or {}).get('gpus',[]):
        pids={p['pid'] for p in gpu.get('processes',[])}
        gpu['runs']=[r['id'] for r in runs if r['run'].get('pid') in pids and r['status']=='RUNNING']
    return {'system':system,'collector':health,'counts':{'runs':len(runs),'train':sum(r['kind']=='train' for r in runs),
        'evaluate':sum(r['kind']=='evaluate' for r in runs),'running':sum(r['status']=='RUNNING' for r in runs),
        'failed':sum(r['status'] in ('FAILED','LOST') for r in runs),'videos':len(records('video'))}}

@app.get('/api/runs')
def runs():
    items=records('run')
    for r in items:r.pop('run',None)
    return sorted(items,key=lambda r:r.get('started_at') or 0,reverse=True)

@app.get('/api/runs/{id}')
def run_detail(id:str):
    r=require_run(id); directory=resolve(r['path'])
    r['files']=[{'name':p.name,'path':str(p.relative_to(ROOT)),'size':p.stat().st_size} for p in sorted(directory.iterdir()) if p.is_file() and not p.is_symlink()]
    r['related_videos']=[v for v in records('video') if v.get('evaluation_run')==id or v.get('training_run')==id]
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
    return read_json(p)

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
def videos():return sorted(records('video'),key=lambda r:r['id'],reverse=True)

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
            'first_episode_finished':get('first_episode_finished')})
    return {'metadata':data,'env_id':ids[env],'samples':rows,'stride':stride,
        'available_channels':['root_z','feet_z','stage','phase'],'unavailable_channels':['contact_force','impact','action']}

@app.get('/api/telemetry')
def telemetry(hours:float=Query(1,gt=0,le=168)):
    with connect() as db:
        rows=db.execute('SELECT payload FROM telemetry WHERE sampled_at>%s ORDER BY sampled_at',(time.time()-hours*3600,)).fetchall()
    stride=max(1,(len(rows)+899)//900)
    return [r['payload'] for r in rows[::stride]]

@app.get('/api/files')
def files(path:str='artifacts'):
    p=resolve(path)
    if not p.is_dir():raise HTTPException(400,'Directory required')
    items=[]
    for child in p.iterdir():
        if child.name.startswith('.') or child.is_symlink():continue
        st=child.stat(); items.append({'name':child.name,'path':str(child.relative_to(ROOT)),
            'directory':child.is_dir(),'size':st.st_size,'modified_at':st.st_mtime})
    return {'path':str(p.relative_to(ROOT)),'entries':sorted(items,key=lambda x:(not x['directory'],x['name']))}

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
