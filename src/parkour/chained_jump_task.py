"""Frozen-policy, stabilize-then-jump evaluation on a common flat deck.

Only final episode termination invokes Isaac's reset. Intermediate success
changes command/bookkeeping after the terminal-metric snapshot, before obs.
"""
import torch

from parkour.chained_progress import ChainedProgress
from parkour.directed_jump_task import DirectedJumpEnv


class ChainedDirectedJumpEnv(DirectedJumpEnv):
    def __init__(self, cfg, render_mode=None, hops=2):
        if hops not in (1, 2):
            raise ValueError('P2-32 supports one-hop control or two-hop evaluation')
        super().__init__(cfg, render_mode)
        self.chain = ChainedProgress(self.num_envs, self.device, hops=hops,
                                     hop_steps=round(4. / self.step_dt))
        self.chain.reset(self.robot._ALL_INDICES, self.calibrated_root[:2])
        self.hop_events = []
        self.transition_events = []

    def maneuver_time_s(self):
        if not hasattr(self, 'chain'):
            return super().maneuver_time_s()
        return self.chain.local_steps(self.episode_length_buf) * self.step_dt

    def launch_reference_xy(self):
        return self.chain.launch_origin if hasattr(self, 'chain') else super().launch_reference_xy()

    def _reset_idx(self, env_ids):
        super()._reset_idx(env_ids)
        if hasattr(self, 'chain'):
            if env_ids is None:
                env_ids = self.robot._ALL_INDICES
            self.chain.reset(env_ids, self.calibrated_root[:2])

    def _get_dones(self):
        super()._get_dones()
        self.hop_success = self.success.clone()
        self.segment_before = self.chain.completed.clone()
        self.chain_decision = self.chain.resolve(self.hop_success, self.failure, self.episode_length_buf)
        # Keep self.success as hop success until the inherited reward snapshot.
        d = self.chain_decision
        return d.success | d.failure, d.timeout

    def _preserved_state(self):
        return {
            'root': self.robot.data.root_state_w.clone(),
            'joint_pos': self.robot.data.joint_pos.clone(),
            'joint_vel': self.robot.data.joint_vel.clone(),
            'actions': self.actions.clone(),
            'previous_actions': self.previous_actions.clone(),
            'contact_on': self.contact_on.clone(),
            'contact_history': self.contacts.data.net_forces_w_history.clone(),
            'episode_steps': self.episode_length_buf.clone(),
            'origins': self.scene.env_origins.clone(),
        }

    def _advance_maneuver(self):
        before = self._preserved_state()
        root_xy = self.robot.data.root_pos_w[:, :2] - self.scene.env_origins[:, :2]
        ids = self.chain.commit(self.episode_length_buf, root_xy)
        # Deliberately no _reset_idx, robot.reset, scene.update or state writes.
        for value in (self.flight_seen, self.landed, self.touched, self.apex,
                      self.air_time, self.flight_event, self.new_touch,
                      self.apex_progress, self.apex_progress_delta,
                      self.first_touch_bonus, self.stabilized,
                      self.precise_stabilized, self.hold_steps, self.phase,
                      self.stage, self.success, self.failure):
            value[ids] = 0
        self.first_touch.reset(ids)
        self.travel.reset(ids)
        self.travel_reward.reset(ids)
        offsets = torch.zeros(len(ids), 4, 2, device=self.device)
        offsets[:, :, 0] = .15 * (self.chain.completed[ids, None] + 1)
        self.set_sequence_offsets(offsets, ids)
        # Absolute world targets advance to 30 cm; per-hop flight demand is 15 cm.
        self.goal_distance[ids] = .15
        after = self._preserved_state()
        unchanged = {key: torch.equal(value, after[key]) for key, value in before.items()}
        if not all(unchanged.values()):
            raise RuntimeError(f'Maneuver transition changed preserved state: {unchanged}')
        for index in ids.tolist():
            if hasattr(self, 'evaluation_done') and bool(self.evaluation_done[index]):
                continue
            self.transition_events.append({
                'env_index': index, 'episode_step': int(self.episode_length_buf[index]),
                'segment': int(self.chain.completed[index]),
                'launch_origin_xy_m': self.chain.launch_origin[index].tolist(),
                'target_xy_m': (self.targets[index, :, :2] - self.scene.env_origins[index, :2]).tolist(),
                'preserved_tensors_exact': unchanged,
            })

    def _get_rewards(self):
        reward = super()._get_rewards()
        metrics = self.extras['terminal_metrics']
        d = self.chain_decision
        ended = d.advance | d.success | d.failure | d.timeout
        for index in ended.nonzero(as_tuple=False).flatten().tolist():
            if hasattr(self, 'evaluation_done') and bool(self.evaluation_done[index]):
                continue
            self.hop_events.append({
                'env_index': index, 'segment': int(self.segment_before[index]),
                'episode_step': int(self.episode_length_buf[index]),
                'local_steps': int(self.chain.local_steps(self.episode_length_buf)[index]),
                'metrics': {key: value[index].item() for key, value in metrics.items()},
            })
        self.success = d.success.clone()
        metrics.update(success=d.success.clone(), failure=d.failure.clone(), timeout=d.timeout.clone(),
                       completed_hops=self.chain.completed.clone(), segment=self.segment_before.clone(),
                       hop_success=self.hop_success.clone())
        if bool(d.advance.any()):
            self._advance_maneuver()
        return reward
