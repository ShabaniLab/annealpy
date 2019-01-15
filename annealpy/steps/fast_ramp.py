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
import time

from atom.api import Float, Int

from .base_step import BaseStep
from .pid import PID


class FastRamp(BaseStep):
    """Perform a fast ramp by using the maximum output power.

    """
    #: Target temperature to reach in C.
    target_temperature = Float(200).tag(pref=True)

    #: Allowed deviation from the target temperature when operating in
    #: switching regulation mode.
    allowed_error = Float(5).tag(pref=True)

    #: Duration of the PID settling time.
    duration = Float().tag(pref=True)

    #: Number of on-off cycles before switching to the PID controller
    on_off_cycles = Int().tag(pref=True)

    #: Time interval at which to update the switch answer in s.
    switch_interval = Float(.05).tag(pref=True)

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
        target temperature as fast as possible. Next we do some cyles between
        the lowest and highest allowed values to determine the effective output
        power needed to stay at target. Finally we switch to a PID controller
        to stabilize the temperature.

        """
        pid = PID(target=self.target_temperature,
                  parameter_p=self.parameter_p,
                  parameter_i=self.parameter_i,
                  parameter_d=self.parameter_d)

        # Ramp quickly to the maximum allowed value
        actuator.heater_switch_state = True
        actuator.heater_reg_state = 1.0

        max_temp = self.target_temperature + self.allowed_error
        min_temp = self.target_temperature - self.allowed_error

        tic = None

        while True:
            current_temp = actuator.temperature
            if tic is None and current_temp > min_temp:
                tic = time.time()
            elif current_temp > max_temp:
                break
            time.sleep(self.switch_interval)

        # Ramp down to minimum allowed value
        toc = time.time()
        on_time = toc - tic
        actuator.heater_switch_state = False
        while actuator.temperature > min_temp:
            time.sleep(self.switch_interval)
        tic = time.time()
        off_time = tic - toc

        # Repeat the above as many times as requested
        for i in range(self.on_off_cycles - 1):
            actuator.heater_switch_state = True
            while actuator.temperature < max_temp:
                time.sleep(self.switch_interval)
            toc = time.time()
            on_time += toc - tic

            actuator.heater_switch_state = False
            while actuator.temperature > min_temp:
                time.sleep(self.switch_interval)
            tic = time.time()
            off_time += tic - toc

        # Use the on/off ratio to set the ouput power and start the PID
        self.heater_reg_state = on_time/(on_time + off_time)
        self.heater_switch_state = True

        stop = tic + self.duration
        while True:

            current_time = time.time()
            if stop - current_time < 0 or actuator.stop_event.is_set():
                break

            temp = actuator.read_temperature()
            feedback = pid.compute_new_output(current_time, temp)
            actuator.heater_reg_state = max(0.0, min(feedback, 1.0))

            time.sleep(min(self.pid_interval, stop - current_time))
