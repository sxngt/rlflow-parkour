import unittest,struct
from parkour.shared_contact_inspection import position_tolerance

class RayPrecisionTest(unittest.TestCase):
    def test_float32_world_rounding_is_bounded_without_accepting_mm_errors(self):
        origin=[590.123456,-570.123456,.35];expected=[590.12,-570.1,.25]
        quantized=[struct.unpack('f',struct.pack('f',x))[0] for x in expected]
        error=sum((a-b)**2 for a,b in zip(quantized,expected))**.5
        bound=position_tolerance(origin,expected)
        self.assertLess(error,bound);self.assertLess(bound,.00025)
        self.assertLess(position_tolerance([1,1,.3],[1,1,.2]),.000051)
        with self.assertRaises(ValueError):position_tolerance([1e6,0,0],[1e6,0,0])
