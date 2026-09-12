"""Real process regression: leader exits while a descendant ignores SIGTERM."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from process_group import live_group_members, stop_process_group


class ProcessGroupTest(unittest.TestCase):
    def test_exited_wrapper_stubborn_child_and_unrelated_process(self):
        with tempfile.TemporaryDirectory() as directory:
            ready=Path(directory)/'ready'
            code='''import os,signal,time,sys
child=os.fork()
if child==0:
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 open(sys.argv[1],'w').write(str(os.getpid()))
 while True:time.sleep(.1)
while True:time.sleep(.1)
'''
            wrapper=subprocess.Popen([sys.executable,'-c',code,str(ready)],start_new_session=True)
            unrelated=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
            try:
                deadline=time.monotonic()+5
                while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)
                self.assertTrue(ready.exists())
                child=int(ready.read_text())
                os.killpg(wrapper.pid,signal.SIGTERM)
                wrapper.wait(timeout=3)
                self.assertIn(child,live_group_members(wrapper.pid))
                result=stop_process_group(wrapper,grace_seconds=.15,kill_grace_seconds=2)
                self.assertIn('SIGKILL',result['signals'])
                self.assertEqual(result['remaining_processes'],[])
                self.assertIsNone(unrelated.poll())
            finally:
                stop_process_group(wrapper,grace_seconds=.05,kill_grace_seconds=2)
                stop_process_group(unrelated,grace_seconds=.1,kill_grace_seconds=2)

    def test_live_leader_terminates_gracefully(self):
        process=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
        result=stop_process_group(process,grace_seconds=2)
        self.assertEqual(result['signals'],['SIGTERM'])
        self.assertEqual(result['remaining_processes'],[])
        self.assertIsNotNone(process.returncode)

    def test_clean_exit_requires_no_signal(self):
        process=subprocess.Popen([sys.executable,'-c','pass'],start_new_session=True)
        process.wait(timeout=3)
        self.assertEqual(stop_process_group(process)['signals'],[])
