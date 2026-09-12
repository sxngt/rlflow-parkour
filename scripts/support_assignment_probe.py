"""Eight-robot physical support and cross-environment isolation probe, no learning."""
import argparse
import json
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from parkour.runtime import begin_run, finish_run, launch_app, atomic_json, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    config['num_envs'] = 8
    config['research_tags'] = ['phase:P2', 'step:p2-38-support-mixture', 'purpose:physical-probe']
    meta = begin_run(args.out, config, 'probe')
    try:
        launch_app(False)
        import torch
        from parkour.learning import make_env
        from parkour.support_inspection import inspect_support_assignment
        env = make_env(config)
        atomic_json(args.out / 'support-inspection.json', inspect_support_assignment(env))
        env.reset()
        traces = []

        def advance(phase, count):
            for i in range(count):
                env.robot.set_joint_position_target(env.robot.data.default_joint_pos)
                env.scene.write_data_to_sim()
                env.sim.step(render=False)
                env.scene.update(env.physics_dt)
                traces.append(dict(phase=phase, step=i + 1,
                    root_world_m=env.robot.data.root_pos_w.tolist(),
                    foot_force_z_N=env.contacts.data.net_forces_w[:, env.contact_ids, 2].tolist()))

        advance('own_support', 300)
        own = env.robot.data.root_pos_w[:, 2] - env.scene.env_origins[:, 2]
        forces = env.contacts.data.net_forces_w[:, env.contact_ids, 2]
        supported = bool(((own > .2) & (own < .4)).all() and (forces > 5).all())
        own_heights = own.tolist()
        # Robot 0 now overlaps robot 4 in XY, but keeps its original collision group.
        # Robot 4 is the positive control proving its local support is physically active.
        state = env.robot.data.root_state_w[4:5].clone()
        state[:, 2] += .10
        state[:, 7:] = 0
        ids = torch.tensor([0], device=env.device)
        env.robot.write_root_pose_to_sim(state[:, :7], env_ids=ids)
        env.robot.write_root_velocity_to_sim(state[:, 7:], env_ids=ids)
        advance('foreign_environment_drop', 240)
        final = env.robot.data.root_pos_w[:, 2] - env.scene.env_origins[4, 2]
        isolated = float(final[0]) < -.1 and .2 < float(final[4]) < .4
        result = dict(own_support_passed=supported, own_root_heights_m=own_heights,
                      foreign_drop_root_z_m=float(final[0]), positive_control_root_z_m=float(final[4]),
                      isolation_passed=isolated, passed=supported and isolated,
                      physics_dt_s=env.physics_dt, traces=traces,
                      scope='physical eight-environment stance and one cross-group overlap/drop; not exhaustive collision isolation proof')
        atomic_json(args.out / 'probe.json', result)
        assert supported and isolated, {k: v for k, v in result.items() if k != 'traces'}
        meta['artifacts'] = {name: sha256(args.out / name) for name in ('probe.json', 'support-inspection.json')}
        env.close()
        finish_run(args.out, meta)
    except BaseException as error:
        traceback.print_exc()
        finish_run(args.out, meta, error)


if __name__ == '__main__':
    main()
