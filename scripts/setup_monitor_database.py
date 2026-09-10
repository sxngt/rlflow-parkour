#!/usr/bin/env python3
"""Initialize the monitor's isolated PostgreSQL cluster; never modifies the host cluster."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
state=root/'.monitor';state.mkdir(mode=0o700,exist_ok=True)
socket=state/'socket';socket.mkdir(mode=0o700,exist_ok=True)
data=state/'postgres'
if (data/'PG_VERSION').exists():
    print('Existing monitor cluster retained:',data)
else:
    subprocess.run(['/usr/lib/postgresql/12/bin/initdb','-D',str(data),'--auth-local=peer','--auth-host=reject','--no-locale','-E','UTF8'],check=True)
    with (data/'postgresql.conf').open('a') as f:
        f.write(f"\nlisten_addresses = ''\nport = 55432\nunix_socket_directories = '{socket}'\nmax_connections = 30\nshared_buffers = '128MB'\n")
