import copy
import json
from pathlib import Path
import unittest
from parkour.terrain_contract import training_support, validate_surface_materials, assert_same_terrain

ROOT=Path(__file__).resolve().parents[1]
class MaterialContractTest(unittest.TestCase):
    def test_valid_and_inconsistent_schedule(self):
        config=json.loads((ROOT/'configs/p4-02-lowfriction.json').read_text())
        support=training_support(config)
        self.assertEqual(len(support['surface_material_overrides']),8)
        for key,value in [('authored_friction',float('nan')),('start_station',4)]:
            bad=copy.deepcopy(support);bad['friction_variation'][key]=value
            with self.assertRaises(ValueError):validate_surface_materials(bad)
        bad=copy.deepcopy(support);bad['surface_material_overrides'].pop(next(iter(bad['surface_material_overrides'])))
        with self.assertRaises(ValueError):validate_surface_materials(bad)
    def test_changed_material_cannot_resume(self):
        low=json.loads((ROOT/'configs/p4-02-lowfriction.json').read_text())
        control=json.loads((ROOT/'configs/p4-02-control.json').read_text())
        with self.assertRaises(ValueError):assert_same_terrain(low,control)
