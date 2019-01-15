# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Wrapper around NiDAQmx to control the annealer.

"""
from typing import Optional

from atom.api import Atom, Bool, Dict, Float, Str, Typed, FloatRange, List

try:
    import nidaqmx
except ImportError:
    print('NIDAQmx does not seem to be installed. Running in simulation mode.')
    nidaqmx = None


class AnnealerDaq(Atom):
    """Annealer controller through a NI-DAQ 6008.

    The annealer control relies on the use of three channels:
    - one input channel is used to read the temperature measured by a
      thermocouple
    - one output channels are used to control the heater through a current
      regulator.

    """
    #: Id of the NI-DAQ used to control the annealer.
    device_id = Str('Dev1')

    #: Id of the channels used to control the heater current regulator.
    #: The first channel is used to read the value using single end
    #: measurement, the second to set it.
    #: The user is responsible for setting up the proper jumper.
    heater_reg_id = List(Str(), ['ai1', 'ao1'])

    #: Id of the channel used to read the temperature. This measurement is done
    #: using a differential channel (So in the default case ai2 is the positive
    #: side and ai6 is the negative one, refer to the daq documentation for
    #: more details).
    temperature_id = Str('ai2')

    #: State of the heater regulator. Changing this value directly affects the
    #: hardware.
    heater_reg_state = FloatRange(low=0.0, high=1.0)

    #: Maximal value that can be used by the regulator.
    heater_reg_max_value = FloatRange(low=0.0, high=5.0, value=5.0)

    #: Minimal value that can be used by the regulator.
    heater_reg_min_value = FloatRange(low=0.0, high=5.0)

    def __init__(self, config: dict) -> None:
        for attr in ('device_id',
                     'heater_reg_id', 'temperature_id'):
            if attr in config:
                setattr(self, attr, config[attr])

    def initialize(self) -> None:
        if nidaqmx is None:
            return
        # Validate that the device we will use exist.
        devices = nidaqmx.system.System.local().devices
        if self.device_id not in devices.device_names:
            raise ValueError(f'The specified device {self.device_id} does not'
                             f' exist. Existing devices are {list(devices)}')

        # Create one task per channel we need to control.
        for task_id, ch_id in [('heater_reg', 'heater_reg_id'),
                               ('temperature', 'temperature_id')]:

            if task_id == 'temperature':
                full_id = self.device_id + '/' + getattr(self, ch_id)
                task = nidaqmx.Task()
                self._tasks[task_id] = task
                mode = nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL
                task.ai_channels.add_ai_voltage_chan(full_id,
                                                     terminal_config=mode)
            else:
                tasks = (nidaqmx.Task(), nidaqmx.Task())
                self._tasks[task_id] = tasks

                # Input channel
                full_id = self.device_id + '/' + getattr(self, ch_id)[0]
                mode = nidaqmx.constants.TerminalConfiguration.RSE
                tasks[0].ai_channels.add_ai_voltage_chan(full_id,
                                                         terminal_config=mode)

                # Output channel
                full_id = self.device_id + '/' + getattr(self, ch_id)[1]
                tasks[1].ao_channels.add_ao_voltage_chan(full_id,
                                                         min_val=0,
                                                         max_val=5)

    def finalize(self) -> None:
        for t in self._tasks.values():
            if isinstance(t, (tuple, list)):
                for st in t:
                    st.close()
            else:
                t.close()

    def read_temperature(self) -> float:
        """Read the temperature measured by the DAQ.

        """
        if not nidaqmx:
            return 20

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
    _tasks = Dict(Str())

    def _default_heater_reg_state(self) -> float:
        """Get the value from the DAQ on first read.

        """
        if not nidaqmx:
            return 0.0

        if 'heater_reg' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'reading the heater regulator stqte by calling `initialize`'
                   )
            raise RuntimeError(msg)

        value = self._tasks['heater_reg'][0].read()
        return round(((value - self.heater_reg_min_value) /
                     (self.heater_reg_max_value - self.heater_reg_min_value)),
                     2)

    def _post_validate_heater_reg_state(self,
                                        old: Optional[float],
                                        new: float):
        """Try to update the DAQ when a valid value is passed.

        """
        if not nidaqmx:
            return new

        if 'heater_reg' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'writing the heater regulator state by calling `initialize`'
                   )
            raise RuntimeError(msg)

        value = (new*(self.heater_reg_max_value - self.heater_reg_min_value) +
                 self.heater_reg_min_value)
        self._tasks['heater_reg'][1].write(value)
        return new
