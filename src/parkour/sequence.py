"""Tensor-only contact phase rules, independently testable without Isaac Sim."""
import torch


def contact_events(phase, grounded_seen, lift_count, hold_count, contact,
                   clearance, error_xy, height_error, support_count, settled,
                   radius, min_clearance, lift_steps, hold_steps, min_support=2):
    grounded_seen = grounded_seen | contact
    lift_valid = (phase == 0) & grounded_seen & ~contact & (clearance >= min_clearance) & (support_count >= min_support) & settled
    lift_count = torch.where(lift_valid, lift_count + 1, 0)
    place_valid = (phase == 1) & contact & (error_xy <= radius) & (height_error <= 0.025) & (support_count >= min_support) & settled
    hold_count = torch.where(place_valid, hold_count + 1, 0)
    return grounded_seen, lift_count, hold_count, lift_count >= lift_steps, hold_count >= hold_steps


def stable_landing(stage, contacts, errors, vz, angular_speed, height_error, radius, spec):
    return ((stage == 4) & contacts.all(dim=1) & (errors <= radius).all(dim=1)
            & (vz.abs() <= spec['final_vz_max_m_s'])
            & (angular_speed <= spec['final_angular_speed_max_rad_s'])
            & (height_error.abs() <= spec['final_height_error_max_m']))
