#!/usr/bin/env python3
"""Install user services for the local parkour monitor (after dependency/database setup)."""
import argparse
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--private-host',help='Optional private interface address, e.g. Tailscale IP');args=p.parse_args()
if args.private_host:
    import ipaddress
    address=ipaddress.ip_address(args.private_host)
    if address.version!=4 or not (address.is_private or address in ipaddress.ip_network('100.64.0.0/10')):
        raise SystemExit('Use a private IPv4 address')
units=Path.home()/'.config/systemd/user';units.mkdir(parents=True,exist_ok=True)
py=root/'.monitor-venv/bin/python'
common=f'WorkingDirectory={root}\nRestart=on-failure\nRestartSec=5\n'
db=f'''[Unit]
Description=parkour monitor PostgreSQL
[Service]
Type=simple
{common}ExecStart=/usr/lib/postgresql/12/bin/postgres -D {root}/.monitor/postgres
KillSignal=SIGINT
TimeoutStopSec=60
[Install]
WantedBy=default.target
'''
collector=f'''[Unit]
Description=parkour research file and GPU collector
After=parkour-monitor-db.service
Requires=parkour-monitor-db.service
[Service]
{common}ExecStart={py} -m monitor.backend.collector
[Install]
WantedBy=default.target
'''
api=f'''[Unit]
Description=parkour monitoring web
After=parkour-monitor-db.service
Requires=parkour-monitor-db.service
[Service]
{common}ExecStart={py} -m monitor.backend.serve --host 127.0.0.1{(' --host '+args.private_host) if args.private_host else ''} --port 8710
[Install]
WantedBy=default.target
'''
for name,content in [('db',db),('collector',collector),('web',api)]:
    (units/f'parkour-monitor-{name}.service').write_text(content)
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
subprocess.run(['systemctl','--user','enable','--now','parkour-monitor-db','parkour-monitor-collector','parkour-monitor-web'],check=True)
print('Monitor services installed. http://127.0.0.1:8710')
if args.private_host:print(f'Private interface: http://{args.private_host}:8710')
