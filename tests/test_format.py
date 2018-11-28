#!/usr/bin/python

import unittest

from traceinfo import format_number

data = (
    (1, "1.000"),
    (-1, "-1.000"),
    (10, "10.000"),
    (100, "100.000"),
    (-100, "-100.000"),
    (1e3, "1.000k"),
    (1e4, "10.000k"),
    (1e5, "100.000k"),
    (-1e5, "-100.000k"),
    (1e6, "1.000M"),
    (1e-1, "100.000m"),
    (1e-2, "10.000m"),
    (1e-3, "1.000m"),
    (1e-4, "100.000u"),
    (1e-5, "10.000u"),
    (1e-6, "1.000u"),
    )


class TestFormatFunc(unittest.TestCase):
    def test_format(self):
        for inp, out in data:
            print "input of '%s' should be '%s'" %(inp, out)
            self.assertEqual(format_number(inp), out)
