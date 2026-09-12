"""Execute bounded learning, matched evaluation, and audited reporting in order."""
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for script in ('p3_08_train.py','p3_08_evaluate.py','p3_08_report.py'):
    print('Starting '+script,flush=True)
    code=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT).returncode
    if code:
        print('Stopped at '+script+' with exit '+str(code),flush=True)
        raise SystemExit(code)
print('P3-08 pipeline complete; model promotion not automatic',flush=True)
