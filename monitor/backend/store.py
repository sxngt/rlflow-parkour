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
