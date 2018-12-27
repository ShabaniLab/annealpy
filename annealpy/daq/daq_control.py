# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Annealpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Wrapper around NiDAQmx to control the annealer.

"""
from typing import Optional

import nidaqmx
from atom.api import Atom, Bool, Dict, Float, Str, Typed


class AnnealerDaq(Atom):
    """Annealer controller through a NI-DAQ 6003.

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

    #: Value in V used to represent the on state of the heater switch.
    heater_switch_on_value = Float(5.0)

    #: Value in V used to represent the on state of the heater switch.
    heater_switch_off_value = Float(0)

    #: State of the heater regulator. Changing this value directly affects the
    #: hardware.
    heater_reg_state = Float(min=0, max=1)

    #: Maximal value that can be used by the regulator.
    heater_reg_max_value = Float(min=-10, max=10)

    #: Minimal value that can be used by the regulator.
    heater_reg_min_value = Float(min=-10, max=10)

    def __init__(self, config: dict) -> None:
        for attr in ('device_id', 'heater_switch_id',
                     'heater_reg_id', 'temperature_id'):
            if attr in config:
                setattr(self, attr, config[attr])

    def initialize(self) -> None:
        # Validate that the device we will use exist.
        devices = nidaqmx.system.System.local().devices
        if self.device_id not in devices:
            raise ValueError(f'The specified device {self.device_id} does not'
                             f' exist. Existing devices are {devices}')

        # Create one task per channel we need to control.
        for task_id, ch_id in [('heater_switch', 'heater_switch_id'),
                               ('heater_reg', 'heater_reg_id'),
                               ('temperature', 'temperature_id')]:
            task = nidaqmx.Task()
            self._tasks[task_id] = task
            if task_id == 'temperature':
                task.add_ai_voltage_chan(self.device_id + '/' + ch_id)
            else:
                task.add_ao_voltage_chan(self.device_id + '/' + ch_id)

    def finalize(self) -> None:
        for t in self._tasks:
            t.close()

    def read_temperature(self) -> float:
        """Read the temperature measured by the DAQ.

        """
        if 'temperature' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'reading the temperature by calling `initialize`')
            raise RuntimeError(msg)

        temp_volt = self._tasks['temperature'].read()

        # XXX do conversion
        temperature = temp_volt

        return temperature

    # --- Private API ---------------------------------------------------------

    #: NiDAQ tasks used to control the physical DAQ
    _tasks = Dict(Str(), Typed(nidaqmx.Task))

    def _default_heater_switch_state(self) -> bool:
        """Get the value from the DAQ on first read.

        """
        if 'heater_switch' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'reading the heater switch state by calling `initialize`')
            raise RuntimeError(msg)

        value = self._tasks['heater_switch'].read()
        return abs(value - self.heater_switch_on_value) < 1e-3

    def _post_validate_heater_switch_state(self,
                                           old: Optional[bool],
                                           new: bool) -> bool:
        """Try to update the DAQ when a valid value is passed.

        """
        if 'heater_switch' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'writing the heater switch state by calling `initialize`')
            raise RuntimeError(msg)

        if new:
            self._tasks['heater_switch'].write(self.heater_switch_on_value)
        else:
            self._tasks['heater_switch'].write(self.heater_switch_off_value)
        return new

    def _default_heater_reg_state(self) -> float:
        """Get the value from the DAQ on first read.

        """
        if 'heater_reg' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'reading the heater regulator stqte by calling `initialize`'
                   )
            raise RuntimeError(msg)

        value = self._tasks['heater_reg'].read()
        return ((value - self.heater_reg_min_value) /
                (self.heater_reg_max_value - self.heater_reg_min_value))

    def _post_validate_heater_reg_state(self,
                                        old: Optional[float],
                                        new: float):
        """Try to update the DAQ when a valid value is passed.

        """
        if 'heater_reg' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'writing the heater regulator state by calling `initialize`'
                   )
            raise RuntimeError(msg)

        value = (new*(self.heater_reg_max_value - self.heater_reg_min_value) +
                 self.heater_reg_min_value)
        self._tasks['heater_switch'].write(value)
        return new
