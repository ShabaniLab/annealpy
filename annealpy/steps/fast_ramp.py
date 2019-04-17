# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018-2019 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fast ramps relying on the maximum outoput power of the heater.

"""
import time

from atom.api import Float, Int

from .base_step import BaseStep
from .pid import PID


class FastRamp(BaseStep):
    """Perform a fast ramp by using the maximum output power.

    """
    #: Target temperature to reach in C.
    target_temperature = Float(200).tag(pref=True)

    #: Fraction of the temperature at which to start the PID regulator.
    regulation_threshold = Float(0.9).tag(pref=True)

    #: Time interval in s at which to check the temperature during the initial
    #: ramp.
    ramp_interval = Float(0.05).tag(pref=True)

    #: Duration of the PID settling time.
    duration = Float().tag(pref=True)

    #: P parameter of the PID in Celsiusˆ-1
    parameter_p = Float().tag(pref=True)

    #: I parameter of the PID in Celsiusˆ-1sˆ-1
    parameter_i = Float().tag(pref=True)

    #: D parameter of the PID s.Celsius
    parameter_d = Float().tag(pref=True)

    #: Time interval at which to update the PID answer in s.
    pid_interval = Float(.1).tag(pref=True)

    def run(self, actuator):
        """Execute a fast ramp.

        First we use the maximum output power to reach the vicinity of the
        target temperature as fast as possible. Next we move to a PID
        controller to stabilize the temperature.

        """
        pid = PID(target=self.target_temperature,
                  parameter_p=self.parameter_p,
                  parameter_i=self.parameter_i,
                  parameter_d=self.parameter_d)

        # Ramp quickly to the maximum allowed value
        actuator.heater_volt_state = 1.0
        actuator.heater_curr_state = 1.0

        threshold = self.target_temperature * self.regulation_threshold
        last_temperature = None
        last_time = None
        while True:
            if actuator.stop_event.is_set():
                return
            actuator.read_heater_voltage()
            actuator.read_heater_current()
            current_temperature = actuator.read_temperature()
            if current_temperature > threshold:
                break
            last_temperature = current_temperature
            last_time = time.time()
            time.sleep(self.ramp_interval)

        # Provide the PID with the previously measured values
        if last_time is not None:
            pid.compute_new_output(last_time, last_temperature)

        stop = time.time() + self.duration
        while True:

            current_time = time.time()
            if stop - current_time < 0 or actuator.stop_event.is_set():
                break

            actuator.read_heater_voltage()
            actuator.read_heater_current()
            temp = actuator.read_temperature()
            feedback = pid.compute_new_output(current_time, temp)
            actuator.heater_curr_state = max(0.0, min(feedback, 1.0))

            time.sleep(min(self.pid_interval, stop - current_time))
