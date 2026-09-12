"""Bounded cleanup for a worker launched with start_new_session=True (Linux)."""
import os
from pathlib import Path
import signal
import time


def live_group_members(group_id):
    members = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            fields = (directory/'stat').read_text().rsplit(')', 1)[1].split()
            # state, ppid, pgrp, session. Zombies own no executable resources.
            if fields[0] != 'Z' and int(fields[2]) == group_id and int(fields[3]) == group_id:
                members.append(int(directory.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return sorted(members)


def stop_process_group(proc, grace_seconds=10, kill_grace_seconds=5):
    """Wait for the owned session's whole group, not just its shell leader."""
    group = proc.pid
    if group == os.getpgrp():
        raise ValueError('Refusing to signal supervisor process group')
    signals = []
    def send(sig):
        if live_group_members(group):
            try:
                os.killpg(group, sig)
                signals.append(sig.name)
            except ProcessLookupError:
                pass
    def wait_until(deadline):
        while True:
            proc.poll()  # Reap the direct child if it exited before descendants.
            remaining = live_group_members(group)
            if not remaining or time.monotonic() >= deadline:
                return remaining
            time.sleep(.05)
    send(signal.SIGTERM)
    remaining = wait_until(time.monotonic()+grace_seconds)
    if remaining:
        send(signal.SIGKILL)
        remaining = wait_until(time.monotonic()+kill_grace_seconds)
    proc.poll()
    return {'process_group': group, 'signals': signals, 'remaining_processes': remaining}
