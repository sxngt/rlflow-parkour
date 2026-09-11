"""T0S v2: calibrated stance, then four genuine lift/place events on flat ground."""
from __future__ import annotations
import math
import torch
from isaaclab.utils import configclass
from parkour.task import FootholdCfg, FootholdEnv
from parkour.sequence import contact_events


@configclass
class SequentialCfg(FootholdCfg):
    observation_space = 69
    episode_length_s = 12.0
    action_scale = 0.5
    sequence = {}


class SequentialEnv(FootholdEnv):
    def __init__(self, cfg, render_mode=None):
        super().__init__(cfg, render_mode)
        self.seq = cfg.sequence
        self.order = torch.tensor([self.foot_names.index(name) for name in self.seq['foot_order']], device=self.device)
        self.episode_order = self.order.expand(self.num_envs, -1).clone()
        self.stage = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self.phase = torch.zeros_like(self.stage)
        self.lift_count = torch.zeros_like(self.stage)
        self.grounded_seen = torch.zeros_like(self.stage, dtype=torch.bool)
        self.lift_event = torch.zeros_like(self.grounded_seen)
        self.place_event = torch.zeros_like(self.grounded_seen)
        self.landing_goals = torch.zeros_like(self.targets)
        self.indices = torch.arange(self.num_envs, device=self.device)
        self._calibrate()

    def _calibrate(self):
        if self.cfg.support_contract:
            import copy
            reference = self.cfg.support_contract
            if self.foot_names != reference['foot_names']:
                raise ValueError('Reference calibration foot order differs from asset')
            self.calibration = copy.deepcopy(reference['calibration'])
            self.calibrated_root = torch.tensor(self.calibration['root_state'], device=self.device)
            self.calibrated_joint_pos = torch.tensor(self.calibration['joint_positions'], device=self.device)
            self.nominal_xy = torch.tensor(self.calibration['foot_xy_m'], device=self.device)
            self.calibration['application'] = 'frozen flat reference; no terrain-specific recalibration'
            return
        # Run actual default-position PD to static equilibrium before creating
        # targets. Calibration steps are setup cost, never counted as PPO samples.
        root = self.robot.data.default_root_state.clone()
        root[:, :3] += self.scene.env_origins
        self.robot.write_root_pose_to_sim(root[:, :7])
        self.robot.write_root_velocity_to_sim(root[:, 7:])
        self.robot.write_joint_state_to_sim(self.robot.data.default_joint_pos, self.robot.data.default_joint_vel)
        self.robot.reset()
        for _ in range(300):
            self.robot.set_joint_position_target(self.robot.data.default_joint_pos)
            self.scene.write_data_to_sim()
            self.sim.step(render=False)
            self.scene.update(self.physics_dt)
        self.calibrated_root = self.robot.data.root_state_w[0].clone()
        self.calibrated_root[:3] -= self.scene.env_origins[0]
        self.calibrated_root[7:] = 0
        self.calibrated_joint_pos = self.robot.data.joint_pos[0].clone()
        self.nominal_xy = (self.robot.data.body_pos_w[0, self.foot_ids, :2] - self.scene.env_origins[0, :2]).clone()
        forces = self.contacts.data.net_forces_w[0, self.contact_ids, 2]
        if not bool((forces > 5).all()) or not (0.2 < float(self.calibrated_root[2]) < 0.4):
            raise RuntimeError('Stance calibration did not reach supported equilibrium')
        self.calibration = {'physics_steps': 300, 'root_state': self.calibrated_root.tolist(),
                            'joint_positions': self.calibrated_joint_pos.tolist(),
                            'foot_xy_m': self.nominal_xy.tolist(), 'foot_normal_force_N': forces.tolist()}

    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        super()._reset_idx(env_ids)
        for value in (self.stage, self.phase, self.lift_count, self.grounded_seen, self.lift_event, self.place_event):
            value[env_ids] = 0
        root = self.calibrated_root.expand(len(env_ids), -1).clone()
        root[:, :3] += self.scene.env_origins[env_ids]
        self.robot.write_root_pose_to_sim(root[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(root[:, 7:], env_ids)
        joints = self.calibrated_joint_pos.expand(len(env_ids), -1).clone()
        self.robot.write_joint_state_to_sim(joints, torch.zeros_like(joints), env_ids=env_ids)
        self.episode_order[env_ids] = self.order
        if self.seq.get('randomize_first_foot',False):
            starts=torch.randint(4,(len(env_ids),),generator=self.generator,device=self.device)
            self.episode_order[env_ids]=self.order[(starts[:,None]+torch.arange(4,device=self.device))%4]
        low, high = self.seq['forward_step_range_m']
        offsets = torch.rand(len(env_ids), 4, 2, generator=self.generator, device=self.device)
        offsets[:, :, 0] = low + (high-low) * offsets[:, :, 0]
        offsets[:, :, 1] = (offsets[:, :, 1]*2-1) * self.seq['lateral_step_m']
        self.set_sequence_offsets(offsets, env_ids)

    def set_sequence_offsets(self, offsets, env_ids=None, episode_orders=None):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        if episode_orders is not None:
            self.episode_order[env_ids] = episode_orders
        self.targets[env_ids, :, :2] = self.scene.env_origins[env_ids, None, :2] + self.nominal_xy
        self.targets[env_ids, :, 2] = self.scene.env_origins[env_ids, None, 2] + 0.02
        self.landing_goals[env_ids] = self.targets[env_ids]
        self.landing_goals[env_ids, :, :2] += offsets
        first=self.episode_order[env_ids,0]
        self.targets[env_ids, first] = self.landing_goals[env_ids, first]

    def active_feet(self):
        return self.episode_order[self.indices,self.stage.clamp_max(self.seq.get("sequence_length",4)-1)]

    def _get_observations(self):
        basic = super()._get_observations()['policy']
        active = self.active_feet()
        return {'policy': torch.cat((basic, torch.nn.functional.one_hot(active, 4),
                torch.nn.functional.one_hot(self.phase, 2), self.stage[:, None]/4,
                (self.episode_length_buf[:, None]*self.step_dt/self.seq['settle_seconds']).clamp_max(1)), dim=1)}

    def _get_dones(self):
        forces = self.contacts.data.net_forces_w[:, self.contact_ids, 2]
        self.contact_on = torch.where(self.contact_on, forces > 2.0, forces > 5.0)
        active = self.active_feet()
        foot_z = self.robot.data.body_pos_w[self.indices, torch.tensor(self.foot_ids, device=self.device)[active], 2]
        surface = self.scene.env_origins[:, 2]
        contact = self.contact_on[self.indices, active]
        support = self.contact_on.sum(dim=1) - contact.long()
        settled = self.episode_length_buf*self.step_dt >= self.seq['settle_seconds']
        self.grounded_seen, self.lift_count, self.hold_steps, self.lift_event, self.place_event = contact_events(
            self.phase, self.grounded_seen, self.lift_count, self.hold_steps, contact,
            foot_z-surface-0.02, self._errors()[self.indices, active], (foot_z-surface-0.02).abs(),
            support, settled, self.cfg.success_radius_m, self.seq['min_lift_clearance_m'],
            self.seq['lift_confirm_steps'], math.ceil(self.cfg.success_dwell_s/self.step_dt),
            min_support=self.seq.get('min_support_feet',2))
        base_contact = self.contacts.data.net_forces_w_history[:, :, self.base_ids].norm(dim=-1).amax(dim=(1, 2)) > 5
        height = self.robot.data.root_pos_w[:, 2] - surface
        out = (self.robot.data.root_pos_w[:, :2] - self.scene.env_origins[:, :2]).norm(dim=-1) > 0.6
        self.failure = base_contact | (height < 0.13) | (self.robot.data.projected_gravity_b[:, 2] > -0.5) | out
        self.place_event &= ~self.failure
        self.lift_event &= ~self.failure
        self.success = (self.stage == 3) & self.place_event
        terminated = self.success | self.failure
        return terminated, (self.episode_length_buf >= self.max_episode_length) & ~terminated

    def _get_rewards(self):
        active = self.active_feet()
        desired = self.targets.clone()
        desired[self.indices, active, 2] += (self.phase == 0)*self.seq['lift_target_height_m']
        errors3d = (self.robot.data.body_pos_w[:, self.foot_ids] - desired).norm(dim=-1)
        active_error = errors3d[self.indices, active]
        support_error = (errors3d.sum(dim=1)-active_error)/3
        precision = torch.exp(-(active_error/0.05).square())
        dense = (precision-1 - (support_error/0.06).square().clamp_max(1)
                 - self.robot.data.projected_gravity_b[:, :2].square().sum(dim=1)
                 - 0.02*self.robot.data.root_ang_vel_b.square().sum(dim=1)
                 - 0.002*(self.actions-self.previous_actions).square().sum(dim=1)
                 - 0.00002*self.robot.data.applied_torque.square().sum(dim=1))
        reward = dense*self.step_dt + self.lift_event.float() + 3*self.place_event.float() + 5*self.success.float() - 30*self.failure.float()
        planar = self._errors().mean(dim=1)
        self.error_sum += planar
        self.sample_count += 1
        self.reward_sum += reward
        self.extras['terminal_metrics'] = {
            'success': self.success.clone(), 'failure': self.failure.clone(), 'timeout': self.reset_time_outs.clone(),
            'length': self.episode_length_buf.clone(), 'mean_error_m': self.error_sum/self.sample_count.clamp_min(1),
            'final_error_m': planar.clone(), 'return': self.reward_sum.clone(),
            'completed_contacts': (self.stage+self.place_event.long()).clone(),
        }
        lift = self.lift_event & ~self.reset_buf
        self.phase[lift] = 1
        self.hold_steps[lift] = 0
        advance = self.place_event & ~self.reset_buf
        ids = advance.nonzero().flatten()
        self.stage[ids] += 1
        self.phase[ids] = 0
        self.grounded_seen[ids] = False
        self.lift_count[ids] = 0
        self.hold_steps[ids] = 0
        next_feet = self.episode_order[ids,self.stage[ids]]
        self.targets[ids, next_feet] = self.landing_goals[ids, next_feet]
        return reward
