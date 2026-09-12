"""Bounded training, common evaluations and report; preserve failed stages."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--start-at',choices=['train','evaluate','report'],default='train');args=p.parse_args()
    stages=['train','evaluate','report']
    for stage in stages[stages.index(args.start_at):]:
        print('P4-02 stage '+stage,flush=True)
        code=subprocess.run([sys.executable,f'scripts/p4_02_{stage}.py'],cwd=ROOT).returncode
        if code:sys.exit(code)
