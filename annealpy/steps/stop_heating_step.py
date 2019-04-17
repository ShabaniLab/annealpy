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

from atom.api import Float

from .base_step import BaseStep


class StopHeatingStep(BaseStep):
    """Complete stop of the heating system.

    """
    #: Temperature for which to wait before exiting.
    low_temperature = Float(50.0).tag(pref=True)

    def run(self, actuator):
        """Use a PID to regulated the temperature.

        """
        actuator.heater_curr_state = 0.0
        while actuator.read_temperature() > self.low_temperature:
            if actuator.stop_event.is_set():
                return
            actuator.read_heater_voltage()
            actuator.read_heater_current()
            time.sleep(0.1) 
