"""Explicit ticket sampling, preserving the original uniform RNG path."""
import torch


def sample_goal_indices(count, goal_count, device, generator, weights=None):
    if weights is None:
        return torch.randint(goal_count, (count,), device=device, generator=generator)
    if goal_count != 4 or weights != [1, 1, 1, 3] or any(type(x) is not int for x in weights):
        raise ValueError('Only the versioned four-goal 1:1:1:3 ticket distribution is supported')
    tickets = torch.randint(6, (count,), device=device, generator=generator)
    return tickets.clamp(max=3)
