#!/usr/bin/env python3
"""Read-only flight prerequisite diagnosis at captured control boundaries.

This does not reconstruct all termination conditions or replace online events.
"""
import json
import sys
from pathlib import Path
import numpy as np


def summarize(folder):
    meta = json.loads((folder / 'run.json').read_text())
    evaluation = json.loads((folder / 'evaluation.json').read_text())
    spec = meta['config']['jump']
    z0 = meta['stance_calibration']['root_state'][2]
    with np.load(folder / 'motion-trace.npz') as a:
        # Current task uses 200 Hz physics and 50 Hz control, four history bins.
        dt = float(np.median(np.diff(a['time'])))
        if not np.isclose(dt, .005):
            raise ValueError('This diagnostic requires the recorded 200 Hz contract')
        force = np.linalg.norm(a['force'], axis=-1)
        indices = np.arange(3, len(force), 4)
        air = np.stack([(force[t-3:t+1] < 2).all(axis=(0, 2)) for t in indices])
        active = a['valid'][indices] & (a['time'][indices, None] >= spec['settle_seconds'])
        rise = a['root_z'][indices] - z0
        vz = a['root_vz'][indices]
        height = rise >= spec['flight_min_rise_m']
        speed = vz >= spec['flight_min_vz_m_s']
        masks = {'air_window': air, 'rise': height, 'upward_speed': speed,
                 'air_and_rise': air & height,
                 'air_and_upward_speed': air & speed,
                 'all_prerequisites': air & height & speed}
        counts = {k: int((v & active).any(axis=0).sum()) for k, v in masks.items()}
        all_gate = masks['all_prerequisites'] & active
        first = [int(indices[np.flatnonzero(all_gate[:, i])[0]])
                 if all_gate[:, i].any() else None for i in range(active.shape[1])]
        return {'run': folder.name, 'episodes': evaluation['episodes'],
                'online_valid_flights': evaluation['valid_flights'],
                'episodes_with_prerequisite': counts,
                'first_prerequisite_physics_index': first,
                'max_rise_cm_per_episode': (100*np.where(active, rise, -np.inf).max(axis=0)).tolist(),
                'scope': 'Post-settle control boundaries; raw force norm <2N across four bins. '
                         'Failure, already-seen and launch-region gates are not reconstructed. '
                         'Counts are prerequisites, not certified flight events.'}


if __name__ == '__main__':
    print(json.dumps([summarize(Path(p)) for p in sys.argv[1:]], indent=2))
