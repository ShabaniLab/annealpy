# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base class for the all the steps in a process.

"""
from atom.api import Atom


class BaseStep(Atom):
    """Base class for all steps.

    """

    def run(self, actuator):
        """Perform the process step.

        The actuator allows to control the state of the system and provides
        the following attributes and methods:
        - heater_volt_state: float attribute
        - heater_curr_state: float attribute
        - read_temperature: method taking no argument
        - read_heater_voltage: method taking no argument
        - read_heater_current: method taking no argument
        - stop_event: event object signaling to end prematurely

        """
        raise NotImplementedError()

    def get_preferences_from_members(self):
        """Return a dict with all the value that must be saved.

        Values that need to be saved should be tagged with `pref=True`.

        """
        preferences = dict()
        for name, member in self.members().items():
            if member.metadata and 'pref' in member.metadata:
                preferences[name] = getattr(self, name)

        return preferences
