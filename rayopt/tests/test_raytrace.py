# -*- coding: utf8 -*-
#
#   pyrayopt - raytracing for optical imaging systems
#   Copyright (C) 2013 Robert Jordens <jordens@phys.ethz.ch>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, print_function,
        unicode_literals, division)

import os
import unittest

from scipy import constants as ct
import numpy as np
from numpy import testing as nptest


from rayopt import system_from_yaml, ParaxialTrace, GeometricTrace
from rayopt import system_to_yaml


class DemotripCase(unittest.TestCase):
    def setUp(self):
        self.s = system_from_yaml("""
description: 'oslo cooke triplet example 50mm f/4 20deg'
object: {angle: .364}
stop: 5
elements:
- {material: air}
- {roc: 21.25, distance: 5.0, material: SK16, radius: 6.5}
- {roc: -158.65, distance: 2.0, material: air, radius: 6.5}
- {roc: -20.25, distance: 6.0, material: F4, radius: 5.0}
- {roc: 19.3, distance: 1.0, material: air, radius: 5.0}
- {material: basic/air, radius: 4.75}
- {roc: 141.25, distance: 6.0, material: SK16, radius: 6.5}
- {roc: -17.285, distance: 2.0, material: air, radius: 6.5}
- {distance: 42.95, radius: 0.364}
""")
        print(system_to_yaml(self.s))

    def test_from_text(self):
        self.assertFalse(self.s.object.finite)
        for i, el in enumerate(self.s):
            if i not in (0,):
                self.assertGreater(el.radius, 0)
            if i not in (0, self.s.stop):
                self.assertGreater(el.distance, 0)
            if i not in (0, self.s.stop, len(self.s)-1):
                self.assertGreater(abs(el.curvature), 0)
            if i not in (len(self.s)-1, ):
                self.assertIsNot(el.material, None)

    def test_system(self):
        s = self.s
        self.assertGreater(len(str(s).splitlines()), 10)
        self.assertIs(s.aperture, s[s.stop])
        #self.assertEqual(len(self.s), 9)

    def test_reverse(self):
        s = self.s
        s.reverse()
        s.reverse()
        self.test_from_text()
        self.test_system()

    def test_rescale(self):
        l = [el.distance for el in self.s]
        self.s.rescale(123)
        nptest.assert_allclose([el.distance/123 for el in self.s], l)
        self.s.rescale()
        nptest.assert_allclose([el.distance for el in self.s], l)

    def test_funcs(self):
        self.s.fix_sizes()
        list(self.s.surfaces_cut(axis=1, points=11))
        self.s.paraxial_matrices(self.s.wavelengths[0], start=1, stop=None)
        self.s.paraxial_matrix(self.s.wavelengths[0], start=1, stop=None)
        self.s.track
        self.s.origins
        self.s.mirrored
        self.s.align(np.ones_like(self.s.track))

    def test_paraxial(self):
        p = ParaxialTrace(self.s)
        print(unicode(p).encode("ascii", errors="replace"))
        unicode(p)

    def traces(self):
        p = ParaxialTrace(self.s)
        g = GeometricTrace(self.s)
        return p, g
    
    def test_aim(self):
        p, g = self.traces()
        z = p.pupil_distance[0] + p.z[1]
        a = np.arctan2(p.pupil_height[0], z)
        print(z, a)
        z, a = g.aim_pupil(1., z, a)
        print(z, a)

    def test_aim_point(self):
        p, g = self.traces()
        g.rays_paraxial_clipping(p)
        g.rays_paraxial_point(p)
        g.rays_paraxial_line(p)

    def test_aim_point(self):
        p, g = self.traces()
        i = self.s.stop
        r = np.array([el.radius for el in self.s[1:-1]])

        g.rays_paraxial_clipping(p)
        if not self.s.object.finite:
            nptest.assert_allclose(g.u[0, :, :], g.u[0,
                (0,)*g.u.shape[1], :])
        nptest.assert_allclose(g.y[i, 0, 1], 0, atol=1e-7)
        nptest.assert_allclose(min(g.y[1:-1, 1, 1] + r), 0, atol=1e-7)
        nptest.assert_allclose(max(g.y[1:-1, 2, 1] - r), 0, atol=1e-7)

        g.rays_paraxial_point(p, 1., distribution="cross", nrays=5)
        if not self.s.object.finite:
            nptest.assert_allclose(g.u[0, :, :], g.u[0,
                (0,)*g.u.shape[1], :])
        nptest.assert_allclose(g.y[i, :3, 1]/self.s[i].radius,
                [-1, 0, 1], atol=1e-2)
        nptest.assert_allclose(g.y[i, :, 0]/self.s[i].radius,
                [0, 0, 0, -1, 0, 1], atol=1e-3)
        print(g.y[i, :, :2]/self.s[i].radius)
        g.rays_paraxial_line(p)


