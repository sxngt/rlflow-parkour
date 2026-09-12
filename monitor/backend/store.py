from __future__ import annotations
import json
import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(os.environ.get('PARKOUR_ROOT', Path(__file__).resolve().parents[2])).resolve()
DSN = os.environ.get('PARKOUR_DATABASE_URL', f'host={ROOT}/.monitor/socket port=55432 dbname=postgres')

def connect():
    return psycopg.connect(DSN, row_factory=dict_row, connect_timeout=3)

def init():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS records (
            kind text NOT NULL, id text NOT NULL, payload jsonb NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(kind,id))''')
        db.execute('''CREATE TABLE IF NOT EXISTS metrics (
            run_id text NOT NULL, byte_offset bigint NOT NULL, payload jsonb NOT NULL,
            PRIMARY KEY(run_id,byte_offset))''')
        db.execute('''CREATE TABLE IF NOT EXISTS cursors (
            path text PRIMARY KEY, inode bigint NOT NULL, offset_bytes bigint NOT NULL,
            mtime_ns bigint NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS telemetry (
            sampled_at double precision PRIMARY KEY, payload jsonb NOT NULL)''')

def put(db, kind, id, payload):
    db.execute('''INSERT INTO records(kind,id,payload) VALUES (%s,%s,%s)
        ON CONFLICT(kind,id) DO UPDATE SET payload=excluded.payload,updated_at=now()
        WHERE records.payload IS DISTINCT FROM excluded.payload''', (kind,id,Jsonb(payload)))

def records(kind):
    with connect() as db:
        return [r['payload'] for r in db.execute('SELECT payload FROM records WHERE kind=%s ORDER BY id', (kind,))]

def record(kind, id):
    with connect() as db:
        row=db.execute('SELECT payload FROM records WHERE kind=%s AND id=%s',(kind,id)).fetchone()
        return row['payload'] if row else None

def listing(kind, rules, limit=24, offset=0, q='', tags=(), run_kind='', status='', training_run=''):
    """Filter/order/page inside PostgreSQL; transfer only list-card fields."""
    fields = ('id kind status task seed num_envs started_at finished_at latest evaluation path'.split()
              if kind == 'run' else 'id title task seed updates path video_path preview_path evaluation_run training_run video_layout training_video aggregate'.split())
    projection = ','.join("'%s',payload->'%s'" % (f, f) for f in fields)
    identity = 'id' if kind == 'run' else "COALESCE(payload->>'evaluation_run',id)"
    cte = f"""WITH listing AS (
        SELECT id,payload,COALESCE(%s::jsonb->'run_overrides'->({identity}),
          NULLIF(payload->'research_tags','[]'::jsonb),NULLIF(payload#>'{{run,config,research_tags}}','[]'::jsonb),
          %s::jsonb->'task_defaults'->(payload->>'task'),'[]'::jsonb) AS tags,
          regexp_replace(COALESCE(payload#>>'{{run,checkpoint,path}}',''),'^.*/([^/]+)/[^/]+$', '\\1') AS source
        FROM records WHERE kind=%s)
    """
    where = " WHERE tags @> %s::jsonb AND (%s='' OR (id||' '||COALESCE(payload->>'title','')||' '||COALESCE(payload->>'task','')) ILIKE %s)"
    params = [Jsonb(rules), Jsonb(rules), kind, Jsonb(list(tags)), q, '%' + q + '%']
    for field, value in [('kind', run_kind), ('status', status)]:
        if value and value != 'all':
            where += f" AND payload->>'{field}'=%s"; params.append(value)
    if training_run:
        where += ' AND source=%s'; params.append(training_run)
    order = "COALESCE((payload->>'started_at')::double precision,0) DESC,id DESC" if kind == 'run' else 'id DESC'
    with connect() as db:
        total = db.execute(cte + 'SELECT count(*) AS n FROM listing' + where, params).fetchone()['n']
        rows = db.execute(cte + f"SELECT jsonb_build_object({projection}) AS item,tags,source FROM listing" + where + f' ORDER BY {order} LIMIT %s OFFSET %s', params + [limit,offset]).fetchall()
        for row in rows:
            item = row['item']; item['research_tags'] = row['tags']
            if kind == 'run':
                item['training_run'] = row['source'] or None if item['kind'] == 'evaluate' else None
                if item['kind'] == 'evaluate':
                    # Only indexed seed fields, never hydrate parent run payloads.
                    item['evaluation_seed'] = item['seed']
                    source = db.execute("SELECT payload->'seed' AS seed FROM records WHERE kind='run' AND id=%s", (row['source'],)).fetchone()
                    item['seed'] = source['seed'] if source else None
    return {'items':[r['item'] for r in rows], 'total':total, 'limit':limit, 'offset':offset, 'has_more':offset+len(rows)<total}

def safe_path(relative: str):
    p=(ROOT/relative).resolve()
    try: rel=p.relative_to(ROOT)
    except ValueError: raise ValueError('Research folders only')
    if not rel.parts or rel.parts[0] not in {'artifacts','result','docs','configs'}:
        raise ValueError('Research folders only')
    if any(part.startswith('.') for part in rel.parts): raise ValueError('Hidden files are not exposed')
    if not p.exists(): raise FileNotFoundError(relative)
    return p

def read_json(p):
    return json.loads(p.read_text())
