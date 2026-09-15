"""Live four-step footfall plan for the follow video, drawn ON the surfaces.

The policy (MLP) has no explicit footstep output, so the overlay estimates where the feet will land:
  horizon 1 (next surface of each pair): body motion extrapolated to that surface, plus the nominal stance offset of each
  foot, snapped onto the surface plane and clamped to its usable region; smoothed over frames so the dots do not jitter.
  horizons 2–4: the planner's pair targets on the following surfaces (what the policy is trained to track).
Points always lie on a surface (never in the air). Display only — never used for reward, acceptance or training.
"""
import math
import torch


class FootfallPlanner:
    def __init__(self, env, index=0, horizon=4, smoothing=.25):
        self.env, self.i, self.h, self.alpha = env, index, horizon, smoothing
        self.prev = None          # smoothed horizon-1 points [4,3]
        self.prev_target = None   # [2] pair targets when prev was computed

    def _tab(self, table, idx):
        env = self.env
        if getattr(env, 'mix', None) is None:
            return table[idx]
        return table[torch.full_like(idx, self.i), idx]

    def _plane_z(self, xy, center, normal):
        nz = normal[:, 2].clamp_min(.2)
        return center[:, 2] - (normal[:, 0] * (xy[:, 0] - center[:, 0]) + normal[:, 1] * (xy[:, 1] - center[:, 1])) / nz

    def _clamp(self, pts, center, rot, halves):
        local = torch.einsum('fji,fj->fi', rot, pts - center)
        local[:, 0] = local[:, 0].clamp(-halves[:, 0], halves[:, 0])
        local[:, 1] = local[:, 1].clamp(-halves[:, 1], halves[:, 1])
        local[:, 2] = 0.
        return center + torch.einsum('fij,fj->fi', rot, local)

    def step(self):
        """→ positions_w [H,4,3], normals_w [H,4,3], valid [H,4] (foot order = env.foot_ids), target surfaces [2]."""
        env, i, dev = self.env, self.i, self.env.device
        origin = env.scene.env_origins[i]
        names = list(getattr(env, 'foot_names', ['FL', 'FR', 'RL', 'RR']))
        pair = torch.tensor([0 if n.upper().startswith('F') else 1 for n in names], device=dev)   # 0 front, 1 rear
        n_surf = env.progress.target_count
        target = env.progress.target[i]                                       # [2]
        root = env.robot.data.root_state_w[i]
        w, x, y, z = root[3:7]
        yaw = math.atan2(float(2 * (w * z + x * y)), float(1 - 2 * (y * y + z * z)))
        rot2 = torch.tensor([[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]], device=dev)
        nominal = env.nominal_xy.to(dev)                                       # [4,2] body-frame stance offsets
        outs, norms, valids = [], [], []
        for k in range(self.h):
            s = (target + k).clamp_max(n_surf - 1)                             # [2] per pair
            valid_pair = (target + k) < n_surf
            s_foot = s[pair]                                                   # [4]
            center = self._tab(env.surface_centers, s_foot) + origin
            normal = self._tab(env.surface_normals, s_foot)
            rot = self._tab(env.surface_rotations, s_foot)
            halves = self._tab(env.surface_halves, s_foot)
            if k == 0:
                # 몸통 운동 외삽: 목표 표면까지의 도달 시간 t 동안 현재 수평 속도로 이동한 몸통 위치 + 발별 nominal stance 오프셋
                v = root[7:10]
                pc = self._tab(env.surface_centers, s) + origin                # [2,3] pair target centers
                d = pc[:, :2] - root[None, :2]
                dist = d.norm(dim=1)
                along = (v[None, :2] * d).sum(1) / dist.clamp_min(1e-3)
                t = (dist / along.clamp_min(.4)).clamp(0., 1.5)                # [2]
                body_xy = root[None, :2] + v[None, :2] * t[:, None]            # [2,2]
                foot_xy = body_xy[pair] + (rot2 @ nominal.T).T                 # [4,2]
                pts = torch.cat([foot_xy, self._plane_z(foot_xy, center, normal)[:, None]], dim=1)
                pts = self._clamp(pts, center, rot, halves)
                if self.prev is not None and self.prev_target is not None and bool((self.prev_target == target).all()):
                    pts = self.alpha * pts + (1 - self.alpha) * self.prev
                    pts = self._clamp(pts, center, rot, halves)
                self.prev, self.prev_target = pts.clone(), target.clone()
            else:
                # 계획기의 페어 목표(왼/오): plan [2,S,2,3] (mix: [E,2,S,2,3]); 발 순서에 맞춰 왼/오 배정
                plan = getattr(env, 'candidate_plan', env.plan)
                if plan.ndim == 5:
                    plan = plan[i]
                side = torch.tensor([0 if n.upper()[1:2] == 'L' else 1 for n in names], device=dev)
                pts = plan[pair, s_foot, side] + origin
                pts = self._clamp(pts, center, rot, halves)
            outs.append(pts); norms.append(normal); valids.append(valid_pair[pair])
        return torch.stack(outs), torch.stack(norms), torch.stack(valids), target
