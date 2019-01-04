# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2019 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Step simply stopping the heater.

"""
import time

from .base_step import BaseStep


class StopHeatingStep(BaseStep):
    """Complete stop of the heating system.

    """

    def run(self, actuator):
        """Use a PID to regulated the temperature.

        """
        actuator.heater_reg_state = 0.0
        actuator.heater_switch_state = False
