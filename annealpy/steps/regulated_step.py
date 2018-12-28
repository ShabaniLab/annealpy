# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Annealpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Constant temperature step relying on a pid.

"""
from atom.api import Float, Float

from .base_step import BaseStep
from .pid import PID


class PIDRegulatedStep(BaseStep):
    """Constant temperature step handled by a PID regulator.

    """
    #:
    target_temperature = Float().tag(pref=True)

    #:
    parameter_p = Float().tag(pref=True)

    #:
    parameter_i = Float().tag(pref=True)

    #:
    parameter_d = Float().tag(pref=True)

    def run(self, actuator):
        """
        """
        pass

