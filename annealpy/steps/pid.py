# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""PID regulation implementation.

This is heavily inspired from:

    https://github.com/ivmech/ivPID/blob/master/PID.py

"""
from atom.api import Atom, Float


class PID(Atom):
    """PID implementation.

    """
    #: Target value
    target = Float()

    #: P parameter of the PID
    parameter_p = Float()

    #: I parameter of the PID
    parameter_i = Float()

    #: Windup guard avoiding that the integral term causes issues after an
    #: update of the target value
    windup_guard = Float(20)

    #: D parameter of the PID
    parameter_d = Float()

    def compute_new_output(self, time, value):
        """Compute the new value of the output based on the measurement.

        """
        error = self.target - value

        # This the first ever call I and D terms are meaningless.
        if not self._last_time:
            self._last_time = time
            self._last_error = error
            return self.parameter_p*error

        delta_time = time - self._last_time
        delta_error = error - self._last_error

        self._error_int += error * delta_time

        if (self._error_int < -self.windup_guard):
            self._error_int = -self.windup_guard
        elif (self._error_int > self.windup_guard):
            self._error_int = self.windup_guard

        d_term = 0.0
        if delta_time > 0:
            d_term = delta_error / delta_time

        # Remember last time and last error for next calculation
        self._last_time = time
        self._last_error = error

        return (self.parameter_p*error + self.parameter_i*self._error_int +
                self.parameter_d * self.d_term)

    def reset(self):
        """Reset the PID history.

        """
        del self._error_int

    # --- Private API ---------------------------------------------------------

    #: Last time at which we update the value in s
    _last_time = Float()

    #: Last measured difference to the target.
    _last_error = Float()

    #: Integral of the error.
    _error_int = Float()
