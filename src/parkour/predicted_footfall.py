"""Real-time predicted footfall for the follow video: where each foot is heading right now.

The policy is a plain MLP with no explicit footstep output, so the "plan" it exposes (`env.plan`) is the fixed per-surface
pair target from the geometric planner. To show the *live* intention, each swing foot is extrapolated ballistically from its
current position/velocity onto the plane of its pair's current target surface and clamped to that surface's usable region;
a stance foot is shown at its contact point. Display only — never used for reward, acceptance or training.
"""
import torch

G = torch.tensor([0., 0., -9.81])


def _tab(env, table, k):
    mix = getattr(env, 'mix', None)
    return table[k] if mix is None else table[env._foot_env_index, k]


def predicted_footfall(env, index=0):
    """→ positions_w [4,3], normals_w [4,3], mode [4] (0 none, 1 stance, 2 flight-extrapolated), target_surface [4]."""
    i = index
    dev = env.device
    feet = env.robot.data.body_pos_w[i, env.foot_ids]                      # [4,3] world
    vel = env.robot.data.body_lin_vel_w[i, env.foot_ids]
    stance = env.contact_on[i].bool()
    names = list(getattr(env, 'foot_names', ['FL', 'FR', 'RL', 'RR']))
    pair = torch.tensor([0 if n.upper().startswith('F') else 1 for n in names], device=dev)   # 0 front, 1 rear
    target = env.progress.target[i][pair]                                    # [4] surface index per foot
    if getattr(env, 'mix', None) is not None:
        env._foot_env_index = torch.full_like(target, i)
    center = _tab(env, env.surface_centers, target) + env.scene.env_origins[i]   # [4,3]
    normal = _tab(env, env.surface_normals, target)
    rot = _tab(env, env.surface_rotations, target)                          # [4,3,3] local→world
    halves = _tab(env, env.surface_halves, target)                          # [4,2]
    g = G.to(dev)
    # n·(p + v t + ½ g t² − c) = 0
    a = .5 * (normal * g).sum(1)
    b = (normal * vel).sum(1)
    c0 = (normal * (feet - center)).sum(1)
    disc = b * b - 4 * a * c0
    ok = disc >= 0
    root = torch.sqrt(disc.clamp_min(0))
    t1 = (-b - root) / (2 * a.clamp(max=-1e-6))
    t2 = (-b + root) / (2 * a.clamp(max=-1e-6))
    t = torch.where(t1 >= 0, t1, t2)
    t = torch.where(ok & (t >= 0), t, torch.zeros_like(t)).clamp(max=1.5)
    landing = feet + vel * t[:, None] + .5 * g * (t * t)[:, None]
    # clamp into the usable rectangle of the target surface (local frame)
    local = torch.einsum('fji,fj->fi', rot, landing - center)              # R^T (x − c)
    local[:, 0] = local[:, 0].clamp(-halves[:, 0], halves[:, 0])
    local[:, 1] = local[:, 1].clamp(-halves[:, 1], halves[:, 1])
    local[:, 2] = 0.
    clamped = center + torch.einsum('fij,fj->fi', rot, local)
    mode = torch.where(stance, torch.ones_like(target), torch.full_like(target, 2))
    mode = torch.where(ok | stance, mode, torch.zeros_like(target))
    pos = torch.where(stance[:, None], feet, clamped)
    return pos, normal, mode, target
