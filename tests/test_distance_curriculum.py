import copy
import unittest
from parkour.launch_curriculum import distance_for_update, checkpoint_state


class DistanceCurriculumTest(unittest.TestCase):
    def setUp(self):
        self.config = {'task': 'a1_directed_jump_v5', 'jump': {'launch_radius_m': .03,
            'train_forward_range_m': [0., .15], 'distance_curriculum': [
                {'start_update': 0, 'forward_range_m': [0., .05]},
                {'start_update': 400, 'forward_range_m': [0., .1]},
                {'start_update': 800, 'forward_range_m': [0., .15]}]}}

    def test_boundaries_resume_and_immutable_final_range(self):
        original = copy.deepcopy(self.config)
        for step, high in [(0, .05), (399, .05), (400, .1), (799, .1), (800, .15), (1600, .15)]:
            self.assertEqual(distance_for_update(self.config, step), [0., high])
            self.assertEqual(checkpoint_state(self.config, step)['next_rollout_forward_range_m'], [0., high])
        self.assertEqual(original, self.config)

    def test_invalid_schedules(self):
        for stages in [[], [{'start_update': 1, 'forward_range_m': [0., .15]}],
                       [{'start_update': 0, 'forward_range_m': [0., float('nan')]}],
                       [{'start_update': 0, 'forward_range_m': [0., .05]}],
                       [{'start_update': 0, 'forward_range_m': [0., .2]},
                        {'start_update': 10, 'forward_range_m': [0., .15]}]]:
            c = copy.deepcopy(self.config)
            c['jump']['distance_curriculum'] = stages
            with self.assertRaises(ValueError):
                distance_for_update(c, 0)

    def test_no_schedule_preserves_legacy(self):
        self.config['jump'].pop('distance_curriculum')
        self.assertEqual(distance_for_update(self.config, 0), [0., .15])
