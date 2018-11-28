import unittest

from traceinfo import calculate_resistance, calculate_length

class Point(object):
    def __init__(self, **args):
        self.x = args['x'] or 0
        self.y = args['y'] or 0
    def y(self, yy):
        self.y = yy
        return self.y
    def x(self, xx):
        self.x = xx
        return self.x
    
    

testcases_resistance = (
    (Point(x=0, y=0), Point(x=10, y=0), 1e-3, 35e-6, 1.72e-8, 0.00491429),
)

testcases_length = (
    (Point(x=0, y=0), Point(x=10e+5, y=0), 1),
)

class TestTraceInfo(unittest.TestCase):
    def test_calculate_resistance(self):
        for start, end, width, thick, rho, expected in testcases_resistance:
            self.assertEqual(calculate_resistance(start, end, width, rho), expected)


    def test_calculate_length(self):
        for start, end, expected in testcases_length:
            self.assertEqual(calculate_length(start, end), expected)
if __name__ == '__main__':
    unittest.main()
