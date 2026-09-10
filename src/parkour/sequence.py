"""Tensor-only contact phase rules, independently testable without Isaac Sim."""
import torch


def contact_events(phase, grounded_seen, lift_count, hold_count, contact,
                   clearance, error_xy, height_error, support_count, settled,
                   radius, min_clearance, lift_steps, hold_steps):
    grounded_seen = grounded_seen | contact
    lift_valid = (phase == 0) & grounded_seen & ~contact & (clearance >= min_clearance) & (support_count >= 2) & settled
    lift_count = torch.where(lift_valid, lift_count + 1, 0)
    place_valid = (phase == 1) & contact & (error_xy <= radius) & (height_error <= 0.025) & (support_count >= 2) & settled
    hold_count = torch.where(place_valid, hold_count + 1, 0)
    return grounded_seen, lift_count, hold_count, lift_count >= lift_steps, hold_count >= hold_steps
