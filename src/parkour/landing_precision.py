"""Symmetric dense precision aggregation; original pre-landing reward preserved."""
import torch


def precision_reward(errors, landed, mode='mean'):
    if mode not in ('mean', 'worst_after_landing_v1'):
        raise ValueError('Unknown landing precision aggregation')
    scores = torch.exp(-(errors / .06).square())
    mean = scores.mean(dim=1) - 1
    if mode == 'mean':
        return mean
    return torch.where(landed, scores.amin(dim=1) - 1, mean)
