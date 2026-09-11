"""Frozen-policy sampling with an RNG isolated from simulator resets."""
import torch


def sample_action(policy, observations, generator):
    policy.update_distribution(observations)
    mean, std = policy.action_mean, policy.action_std
    if not torch.isfinite(std).all() or not (std > 0).all():
        raise ValueError('Policy standard deviation must be finite and positive')
    noise = torch.randn(mean.shape, dtype=mean.dtype, device=mean.device, generator=generator)
    return mean + std * noise
