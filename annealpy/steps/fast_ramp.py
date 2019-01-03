# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fast ramps relying on the maximum outoput power of the heater.

"""
from atom.api import Float, Tuple

from .base_step import BaseStep


class FastRamp(BaseStep):
    """Perform a fast ramp by using the maximum output power.

    """
    #:
    target_temperature = Float().tag(pref=True)

    #:
    output_reduction_threshold = Float().tag(pref=True)

    #:
    target_accuracy = Float().tag(pref=True)

    #:
    pid_parameters = Tuple(Float()).tag(pref=True)

    def run(self, actuator):
        """
        """
        pass
