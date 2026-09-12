"""Execute bounded learning, matched evaluation, and audited reporting in order."""
import argparse
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--start-at', choices=['train','evaluate','report'], default='train')
args=parser.parse_args()
stages=['train','evaluate','report']
for stage in stages[stages.index(args.start_at):]:
    script='p3_08_'+stage+'.py'
    print('Starting '+script,flush=True)
    code=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT).returncode
    if code:
        print('Stopped at '+script+' with exit '+str(code),flush=True)
        raise SystemExit(code)
print('P3-08 pipeline complete; model promotion not automatic',flush=True)
