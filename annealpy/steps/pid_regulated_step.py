# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018-2019 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Constant temperature step relying on a pid.

"""
import time

from atom.api import Float

from .base_step import BaseStep
from .pid import PID


class PIDRegulatedStep(BaseStep):
    """Constant temperature step handled by a PID regulator.

    """
    #: Target temperature in Celsius
    target_temperature = Float().tag(pref=True)

    #: P parameter of the PID in Celsiusˆ-1
    parameter_p = Float().tag(pref=True)

    #: I parameter of the PID in Celsiusˆ-1sˆ-1
    parameter_i = Float().tag(pref=True)

    #: D parameter of the PID s.Celsius
    parameter_d = Float().tag(pref=True)

    #: Total duration of the step in s, including any initial settling time.
    duration = Float().tag(pref=True)

    #: Time interval at which to update the PID answer in s.
    interval = Float(.1).tag(pref=True)

    def run(self, actuator):
        """Use a PID to regulate the temperature.

        """
        start = time.time()
        stop = start + self.duration

        pid = PID(target=self.target_temperature,
                  parameter_p=self.parameter_p,
                  parameter_i=self.parameter_i,
                  parameter_d=self.parameter_d)

        while True:

            current_time = time.time()
            if stop - current_time < 0 or actuator.stop_event.is_set():
                break

            actuator.read_heater_voltage()
            actuator.read_heater_current()
            temp = actuator.read_temperature()
            feedback = pid.compute_new_output(current_time, temp)
            actuator.heater_curr_state = max(0.0, min(feedback, 1.0))

            time.sleep(min(self.interval, stop - current_time))
