# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Annealpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the MIT license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Wrapper around NiDAQmx to control the annealer.

"""
import json
import os

import nidaqmx
from atom.api import Atom, Bool, Float, ReadOnly, Str, Typed


class AnnealerDac(Atom):
    """Annealer controller through a NI-DAQ.

    The annealer control relies on the use of three channels:
    - one input channel is used to read the temperature measured by a
      thermocouple
    - two output channels are used to control the heater:
      - one actuates a swicth.
      - the other actuates a current regulator.

    The switch is meant to be used for fast temperature ramping, while the
    regulator is meant to be used for slow ramps or when a stable temperature
    is required over extended periods of time.

    """
    #: Id of the NI-DAQ used to control the annealer.
    device_id = Str('Dev0')

    #: Id of the channel used to control the heater switch.
    heater_switch_id = Str('ao0')

    #: Id of the channel used to control the heater current regulator.
    heater_reg_id = Str('ao1')

    #: Id of the channel used to read the temperature.
    temperature_id = Str('ai0')

    #: State of the heater switch. Changing this value directly affects the
    #: hardware.
    heater_switch_state = Bool()

    #: State of the heater regulator. Changing this value directly affects the
    #: hardware.
    heater_reg_state = Float(min=0, max=1)

    def __init__(self, config):
        pass

    def initialize(self):
        pass

    def finalize(self):
        pass

    def read_temperature(self):
        pass

    # --- Private API ---------------------------------------------------------

    #: NiDAQ task used to control the physical DAQ
    _task = Typed(nidaqmx.Task)

    def _default_heater_switch_state(self):
        """Get the value from the DAQ on first read.

        """
        pass

    def _post_validate_heater_switch_state(self, old, new):
        """Try to update the DAQ when a valid value is passed.

        """
        pass

    def _default_heater_reg_state(self):
        """Get the value from the DAQ on first read.

        """
        pass

    def _post_validate_heater_reg_state(self, old, new):
        """Try to update the DAQ when a valid value is passed.

        """
        pass
