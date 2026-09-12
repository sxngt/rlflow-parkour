"""Per-environment maneuver boundaries; never touches simulator state.

Resolve after the hop's success gates, commit after its metrics snapshot, and
reset only on a real episode reset. A first-hop success is not course success.
"""
from dataclasses import dataclass

import torch


@dataclass
class ChainDecision:
    advance: torch.Tensor
    success: torch.Tensor
    failure: torch.Tensor
    timeout: torch.Tensor


class ChainedProgress:
    def __init__(self, count, device, hops=2, hop_steps=200, target_hops=None):
        if type(hops) is not int or hops < 1 or type(hop_steps) is not int or hop_steps < 1:
            raise ValueError('Positive integer hop count and step budget required')
        self.hops, self.hop_steps = hops, hop_steps
        if target_hops is None:
            self.target_hops = torch.full((count,), hops, dtype=torch.long, device=device)
        else:
            if (not isinstance(target_hops, torch.Tensor) or target_hops.shape != (count,)
                    or target_hops.dtype != torch.long
                    or bool(((target_hops < 1) | (target_hops > hops)).any())):
                raise ValueError('Per-environment hop counts must be int64 in [1, hops]')
            self.target_hops = target_hops.to(device=device).clone()
        self.completed = torch.zeros(count, dtype=torch.long, device=device)
        self.start_step = torch.zeros_like(self.completed)
        self.launch_origin = torch.zeros(count, 2, device=device)
        self.finished = torch.zeros(count, dtype=torch.bool, device=device)
        self.pending = torch.zeros_like(self.finished)

    def reset(self, ids, origin):
        self.completed[ids] = 0
        self.start_step[ids] = 0
        self.launch_origin[ids] = origin
        self.finished[ids] = False
        self.pending[ids] = False

    def local_steps(self, episode_steps):
        return episode_steps - self.start_step

    def resolve(self, hop_success, failure, episode_steps):
        if bool(self.pending.any()):
            raise RuntimeError('Commit pending maneuver transitions before the next resolve')
        active = ~self.finished
        failed = active & failure
        passed = active & hop_success & ~failed
        success = passed & (self.completed == self.target_hops - 1)
        global_limit = episode_steps >= self.target_hops * self.hop_steps
        advance = passed & ~success & ~global_limit
        timeout = active & ~failed & ~success & ~advance & (
            (self.local_steps(episode_steps) >= self.hop_steps) | global_limit)
        self.completed += (advance | success).long()
        self.finished |= failed | success | timeout
        self.pending.copy_(advance)
        return ChainDecision(advance.clone(), success, failed, timeout)

    def commit(self, episode_steps, root_xy):
        """Latch next launch origin and local clock, with asynchronous masks."""
        if root_xy.shape != self.launch_origin.shape or episode_steps.shape != self.start_step.shape:
            raise ValueError('Expected per-environment steps and root XY')
        ids = self.pending.nonzero(as_tuple=False).flatten()
        self.start_step[ids] = episode_steps[ids]
        self.launch_origin[ids] = root_xy[ids]
        self.pending.zero_()
        return ids
