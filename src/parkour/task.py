"""T0: four nearby, world-fixed foothold targets on a support surface.

Import only after AppLauncher. This is an oracle-state prerequisite, not parkour.
"""
from __future__ import annotations

import copy
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv, DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensor, ContactSensorCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_apply_inverse
from isaaclab_assets import UNITREE_A1_CFG


@configclass
class FootholdCfg(DirectRLEnvCfg):
    decimation = 4
    episode_length_s = 4.0
    action_space = 12
    observation_space = 61
    state_space = 0
    is_finite_horizon = False
    action_scale = 0.35
    target_offset_m = 0.06
    success_radius_m = 0.035
    success_dwell_s = 0.2
    surface_height_m = 0.0
    support_contract = None
    support_assignment = None
    sim = sim_utils.SimulationCfg(dt=0.005, render_interval=4)
    scene = InteractiveSceneCfg(num_envs=256, env_spacing=2.5, replicate_physics=True)
    robot = UNITREE_A1_CFG.replace(prim_path="/World/envs/env_.*/Robot")
    contact_sensor = ContactSensorCfg(
        prim_path="/World/envs/env_.*/Robot/.*", update_period=0.005, history_length=4,
    )
    terrain = TerrainImporterCfg(prim_path="/World/Ground", terrain_type="plane", collision_group=-1)


class FootholdEnv(DirectRLEnv):
    def __init__(self, cfg, render_mode=None):
        super().__init__(cfg, render_mode=render_mode)
        self.foot_ids, self.foot_names = self.robot.find_bodies(".*_foot")
        self.contact_ids, names = self.contacts.find_bodies(".*_foot")
        assert self.foot_names == names and len(names) == 4
        self.base_ids, _ = self.contacts.find_bodies("trunk")
        self.actions = torch.zeros(self.num_envs, 12, device=self.device)
        self.previous_actions = torch.zeros_like(self.actions)
        self.targets = torch.zeros(self.num_envs, 4, 3, device=self.device)
        # Foot XY from actual asset forward kinematics, not an assumed URDF order.
        self.nominal_xy = (self.robot.data.body_pos_w[0, self.foot_ids, :2]
                           - self.robot.data.root_pos_w[0, :2]).clone()
        self.contact_on = torch.zeros(self.num_envs, 4, dtype=torch.bool, device=self.device)
        self.hold_steps = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self.success = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self.failure = torch.zeros_like(self.success)
        self.error_sum = torch.zeros(self.num_envs, device=self.device)
        self.reward_sum = torch.zeros(self.num_envs, device=self.device)
        self.sample_count = torch.zeros(self.num_envs, device=self.device)
        self.generator = torch.Generator(device=self.device).manual_seed(cfg.seed)

    def _setup_scene(self):
        self.robot = Articulation(self.cfg.robot)
        self.scene.articulations["robot"] = self.robot
        self.contacts = ContactSensor(self.cfg.contact_sensor)
        self.scene.sensors["contact"] = self.contacts
        self.cfg.terrain.num_envs = self.cfg.scene.num_envs
        self.cfg.terrain.env_spacing = self.cfg.scene.env_spacing
        self.terrain = self.cfg.terrain.class_type(self.cfg.terrain)
        support = self.cfg.support_contract
        if support and support['mode'] != 'flat':
            # Replace the ground before physics initialization. Moving its parent
            # Xform alone did not move the plane collider in this Isaac version.
            self.scene.stage.RemovePrim(self.cfg.terrain.prim_path)
            ground = sim_utils.GroundPlaneCfg(physics_material=self.cfg.terrain.physics_material)
            ground.func(self.cfg.terrain.prim_path, ground,
                        translation=(0., 0., support['layout']['catch_floor_z_m']))
            for surface in ([] if self.cfg.support_assignment else support['layout']['surfaces']):
                material = self.cfg.terrain.physics_material if support.get('matched_material') else None
                override = support.get('surface_material_overrides', {}).get(surface['id'])
                if override is not None:
                    material = copy.deepcopy(self.cfg.terrain.physics_material)
                    material.static_friction = override['static_friction']
                    material.dynamic_friction = override['dynamic_friction']
                block = sim_utils.CuboidCfg(size=tuple(surface['size_m']),
                    collision_props=sim_utils.CollisionPropertiesCfg(),
                    physics_material=material,
                    visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.3, .4, .5)))
                block.func('/World/envs/env_0/Supports/' + surface['id'], block,
                           translation=tuple(surface['center_m']))
        if self.cfg.surface_height_m > 0:
            height = self.cfg.surface_height_m
            block = sim_utils.CuboidCfg(
                size=(1.2, 1.0, height), collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.3, 0.4, 0.5)),
            )
            block.func("/World/envs/env_0/Support", block, translation=(0., 0., height / 2))
        self.scene.clone_environments(copy_from_source=bool(self.cfg.support_assignment))
        if self.cfg.support_assignment:
            for group in self.cfg.support_assignment['groups']:
                for index in range(group['env_start'], group['env_stop']):
                    for surface in group['layout']['surfaces']:
                        block = sim_utils.CuboidCfg(size=tuple(surface['size_m']),
                            collision_props=sim_utils.CollisionPropertiesCfg(),
                            physics_material=self.cfg.terrain.physics_material,
                            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.3, .4, .5)))
                        block.func(f'/World/envs/env_{index}/Supports/' + surface['id'], block,
                                   translation=tuple(surface['center_m']))
        if self.device == "cpu" or self.cfg.support_assignment:
            self.scene.filter_collisions(global_prim_paths=["/World/Ground"])
        light = sim_utils.DomeLightCfg(intensity=2500.0)
        light.func("/World/Light", light)

    def _pre_physics_step(self, actions):
        self.previous_actions.copy_(self.actions)
        self.actions.copy_(actions.clamp(-1., 1.))

    def _apply_action(self):
        self.robot.set_joint_position_target(self.robot.data.default_joint_pos + self.cfg.action_scale * self.actions)

    def _errors(self):
        return torch.linalg.vector_norm(self.robot.data.body_pos_w[:, self.foot_ids, :2] - self.targets[:, :, :2], dim=-1)

    def _get_observations(self):
        rotation = self.robot.data.root_quat_w[:, None, :].expand(-1, 4, -1)
        targets_b = quat_apply_inverse(rotation.reshape(-1, 4),
            (self.targets - self.robot.data.root_pos_w[:, None, :]).reshape(-1, 3)).reshape(self.num_envs, 12)
        obs = torch.cat((self.robot.data.root_lin_vel_b, self.robot.data.root_ang_vel_b,
                         self.robot.data.projected_gravity_b,
                         self.robot.data.joint_pos - self.robot.data.default_joint_pos,
                         self.robot.data.joint_vel * 0.05, self.actions, targets_b,
                         self.contact_on.float()), dim=-1)
        return {"policy": obs}

    def _get_dones(self):
        force = self.contacts.data.net_forces_w[:, self.contact_ids].norm(dim=-1)
        # Hysteresis: onset >5 N, release <2 N. No foot-contact fabrication.
        self.contact_on = torch.where(self.contact_on, force > 2.0, force > 5.0)
        within = (self._errors() < self.cfg.success_radius_m) & self.contact_on
        settled = self.episode_length_buf * self.step_dt >= 0.5
        valid = within.all(dim=1) & settled
        self.hold_steps = torch.where(valid, self.hold_steps + 1, 0)
        base_contact = self.contacts.data.net_forces_w_history[:, :, self.base_ids].norm(dim=-1).amax(dim=(1, 2)) > 5.0
        height = self.robot.data.root_pos_w[:, 2] - self.scene.env_origins[:, 2] - self.cfg.surface_height_m
        tilt = self.robot.data.projected_gravity_b[:, 2] > -0.5
        out = (self.robot.data.root_pos_w[:, :2] - self.scene.env_origins[:, :2]).norm(dim=-1) > 0.6
        self.failure = base_contact | (height < 0.13) | tilt | out
        self.success = (self.hold_steps * self.step_dt >= self.cfg.success_dwell_s) & ~self.failure
        terminated = self.failure | self.success
        truncated = (self.episode_length_buf >= self.max_episode_length) & ~terminated
        return terminated, truncated

    def _get_rewards(self):
        error = self._errors()
        precision = torch.exp(-(error / 0.06).square())
        root_xy = self.robot.data.root_pos_w[:, :2]
        center_error = (root_xy - self.targets[:, :, :2].mean(dim=1)).square().sum(dim=1)
        height = self.robot.data.root_pos_w[:, 2] - self.scene.env_origins[:, 2] - self.cfg.surface_height_m
        dense = (4.0 * precision.mean(dim=1) + 2.0 * (precision * self.contact_on).mean(dim=1)
                 - 2.0 * self.robot.data.projected_gravity_b[:, :2].square().sum(dim=1)
                 - 10.0 * (height - 0.28).square() - 4.0 * center_error
                 - 0.01 * (self.actions - self.previous_actions).square().sum(dim=1)
                 - 0.0001 * self.robot.data.applied_torque.square().sum(dim=1)
                 - 0.05 * self.robot.data.root_ang_vel_b.square().sum(dim=1))
        reward = dense * self.step_dt + 2.0 * self.success - 2.0 * self.failure
        self.error_sum += error.mean(dim=1)
        self.sample_count += 1
        self.reward_sum += reward
        # Pre-reset data: evaluation must consume this, not the auto-reset state.
        self.extras["terminal_metrics"] = {
            "success": self.success.clone(), "failure": self.failure.clone(),
            "timeout": self.reset_time_outs.clone(), "length": self.episode_length_buf.clone(),
            "mean_error_m": (self.error_sum / self.sample_count.clamp_min(1)).clone(),
            "final_error_m": error.mean(dim=1).clone(), "return": self.reward_sum.clone(),
        }
        return reward

    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        self.robot.reset(env_ids)
        super()._reset_idx(env_ids)
        for value in (self.actions, self.previous_actions, self.contact_on, self.hold_steps,
                      self.success, self.failure, self.error_sum, self.reward_sum, self.sample_count):
            value[env_ids] = 0
        root = self.robot.data.default_root_state[env_ids].clone()
        root[:, :3] += self.scene.env_origins[env_ids]
        root[:, 2] += self.cfg.surface_height_m
        self.robot.write_root_pose_to_sim(root[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(root[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(self.robot.data.default_joint_pos[env_ids],
                                           self.robot.data.default_joint_vel[env_ids], env_ids=env_ids)
        offset = (torch.rand(len(env_ids), 4, 2, generator=self.generator, device=self.device) * 2 - 1) * self.cfg.target_offset_m
        self.targets[env_ids, :, :2] = self.scene.env_origins[env_ids, None, :2] + self.nominal_xy + offset
        self.targets[env_ids, :, 2] = self.scene.env_origins[env_ids, None, 2] + self.cfg.surface_height_m + 0.02
