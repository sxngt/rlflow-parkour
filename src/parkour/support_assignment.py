"""Pure, strict support placement plan for heterogeneous retention environments."""
import copy

from parkour.chain_training import validate_chain_training
from parkour.terrain_contract import training_support
from parkour.support_geometry import build_support_layout, expected_goal_surface


def support_assignment(config):
    spec = config.get('support_assignment')
    if spec is None:
        return None
    if spec not in ({'schema_version': 1, 'single_mode': mode,
                    'assignment': 'fixed_env_id_chain_first', 'replicate_physics': False}
                   for mode in ('deck', 'continuous')):
        raise ValueError('Unsupported per-environment support assignment')
    validate_chain_training(config)
    if config.get('retention_training') is None:
        raise ValueError('Support assignment requires retention task partition')
    count = config['num_envs']
    if type(count) is not int or count < 2 or count % 2:
        raise ValueError('Support assignment needs an even positive environment count')
    support = training_support(config)
    if support['mode'] != 'deck':
        raise ValueError('Primary chain terrain must be deck')
    groups = []
    for task, start, stop, mode, goals in (
            ('chain', 0, count // 2, 'deck', [.15, .30]),
            ('single', count // 2, count, spec['single_mode'], config['retention_training']['single_goal_choices_m'])):
        layout = build_support_layout(support['foot_names'], support['calibration']['foot_xy_m'], mode=mode)
        candidate = dict(support, mode=mode, layout=layout)
        for i, xy in enumerate(support['calibration']['foot_xy_m']):
            for goal in goals:
                expected_goal_surface(candidate, i, xy, goal)
        groups.append(dict(task=task, env_start=start, env_stop=stop, mode=mode, layout=layout))
    return dict(schema_version=1, num_envs=count, replicate_physics=False, copy_from_source=True,
                collision_filter='explicit_environment_groups_with_global_ground',
                calibration=copy.deepcopy(support['calibration']), matched_material=True, groups=groups)


def assert_same_support_assignment(old, new):
    if old.get('support_assignment') != new.get('support_assignment'):
        raise ValueError('Support assignment changed; create a new fork instead of resuming')
