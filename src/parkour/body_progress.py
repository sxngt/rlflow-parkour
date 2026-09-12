"""Within-control-step body waypoint progress; no reward from a target switch."""
import torch

def waypoint(targets,stance_offset):
    return targets.mean(dim=1)+stance_offset

def gap_landing_waypoint(targets, stance_offset, front_target, front_accepted,
                         gap_surfaces, surface_centers, origins, root_height):
    """Guide the body onto a pending gap landing; retain midpoint elsewhere.

    The returned reference must be cached before stepping, so changing targets
    without physical displacement never earns progress reward.
    """
    midpoint = waypoint(targets, stance_offset)
    pending = gap_surfaces[front_target] & (front_accepted < front_target)
    landing = surface_centers[front_target] + origins
    landing = landing.clone()
    landing[:, 2] += root_height
    return torch.where(pending[:, None], landing, midpoint)

def progress_reward(before,after,goal,weight):
    return weight*((before-goal).norm(dim=1)-(after-goal).norm(dim=1))
