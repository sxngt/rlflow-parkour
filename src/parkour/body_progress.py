"""Within-control-step body waypoint progress; no reward from a target switch."""
import torch

def waypoint(targets,stance_offset):
    return targets.mean(dim=1)+stance_offset

def progress_reward(before,after,goal,weight):
    return weight*((before-goal).norm(dim=1)-(after-goal).norm(dim=1))
