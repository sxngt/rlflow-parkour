"""Mutually exclusive continuous-range and uniform discrete jump goals."""
import math


def target_ranges(jump):
    choices = jump.get('train_forward_choices_m')
    if choices is not None:
        if 'train_forward_range_m' in jump or jump.get('distance_curriculum') is not None:
            raise ValueError('Discrete jump goals cannot be combined with a range or curriculum')
        if not choices or len(set(choices)) != len(choices) or not all(math.isfinite(x) and x >= 0 for x in choices):
            raise ValueError('Discrete goals must be distinct finite nonnegative distances')
        return [[d, d] for d in choices]
    interval = jump['train_forward_range_m']
    if len(interval) != 2 or not all(math.isfinite(x) for x in interval) or interval[0] < 0 or interval[0] > interval[1]:
        raise ValueError('Invalid continuous goal range')
    return [interval]


def sample_distances(jump, count, device, generator):
    import torch
    target_ranges(jump)
    if 'train_forward_choices_m' in jump:
        choices = torch.tensor(jump['train_forward_choices_m'], device=device)
        indices = torch.randint(len(choices), (count,), device=device, generator=generator)
        return choices[indices]
    low, high = jump['train_forward_range_m']
    return low + (high-low)*torch.rand(count, device=device, generator=generator)
