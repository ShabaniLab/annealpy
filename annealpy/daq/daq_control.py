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
import os
import json
from typing import Optional

from atom.api import (Atom, Bool, Callable, Dict, Float, FloatRange, List, Str,
                      Typed)

try:
    import nidaqmx
except ImportError:
    print('NIDAQmx does not seem to be installed. Running in simulation mode.')
    nidaqmx = None


class AnnealerDaq(Atom):
    """Annealer controller through a NI-DAQ 6008.

    The annealer control relies on the use of seven channels:
    - one input channel is used to read the temperature measured by a
      thermocouple
    - one pair of input/output channels are used to control the current output
      of the power source driving the heater
    - one input is used to monitor the actual current output of the source
    - one pair of input/output channels are used to control the voltage output
      of the power source driving the heater
    - one input is used to monitor the actual voltage output of the source

    """
    #: Id of the NI-DAQ used to control the annealer.
    device_id = Str('Dev1')

    #: Id of the channels used to control the heater current regulator.
    #: The first channel is used to read the value using single end
    #: measurement, the second to set it, the third to moinitor the actual
    #: output.
    #: The user is responsible for setting up the proper jumper.
    heater_curr_id = List(Str(), ['ai1', 'ao1', 'ai5'])

    #: Id of the channels used to control the heater voltage regulator.
    #: The first channel is used to read the value using single end
    #: measurement, the second to set it, the third to moinitor the actual
    #: output.
    #: The user is responsible for setting up the proper jumper.
    heater_volt_id = List(Str(), ['ai0', 'ao0', 'ai4'])

    #: Id of the channel used to read the temperature. This measurement is done
    #: using a differential channel (So in the default case ai2 is the positive
    #: side and ai6 is the negative one, refer to the daq documentation for
    #: more details).
    temperature_id = Str('ai2')

    #: State of the heater regulator. Changing this value directly affects the
    #: hardware.
    heater_curr_state = FloatRange(low=0.0, high=1.0)

    #: Maximal value that can be used by the regulator.
    heater_curr_max_value = FloatRange(low=0.0, high=5.0, value=2.6)

    #: Minimal value that can be used by the regulator.
    heater_curr_min_value = FloatRange(low=0.0, high=5.0)

    #: State of the heater regulator. Changing this value directly affects the
    #: hardware.
    heater_volt_state = FloatRange(low=0.0, high=1.0)

    #: Maximal value that can be used by the regulator.
    heater_volt_max_value = FloatRange(low=0.0, high=5.0, value=1.5)

    #: Minimal value that can be used by the regulator.
    heater_volt_min_value = FloatRange(low=0.0, high=5.0)

    #: Minimal voltage expected to be measured by the temperature sensor
    temperature_min_volt = FloatRange(low=-5, high=5.0)

    #: Maximal voltage expected to be measured by the temperature sensor
    temperature_max_volt = FloatRange(low=-5, high=5.0)

    def __init__(self, config: dict) -> None:
        for attr in ('device_id',
                     'heater_curr_id',
                     'heater_volt_id',
                     'temperature_id',
                     'heater_curr_max_value',
                     'heater_curr_min_value',
                     'heater_volt_max_value',
                     'heater_volt_min_value',
                     'temperature_min_volt',
                     'temperature_max_volt'):
            if attr in config:
                setattr(self, attr, config[attr])

        if "temperature_conversion" in config:
            self._create_converter(config['temperature_conversion'])
        else:
            raise ValueError("No temperature conversion specified in the DAQ "
                             f"config file. Content is {config}")

    def initialize(self) -> None:
        if nidaqmx is None:
            return
        # Validate that the device we will use exist.
        devices = nidaqmx.system.System.local().devices
        if self.device_id not in devices.device_names:
            raise ValueError(f'The specified device {self.device_id} does not'
                             f' exist. Existing devices are {list(devices)}')

        # Create one task per channel we need to control.
        for task_id, ch_id in [('heater_curr', 'heater_curr_id'),
                               ('heater_volt', 'heater_volt_id'),
                               ('temperature', 'temperature_id')]:

            if task_id == 'temperature':
                full_id = self.device_id + '/' + getattr(self, ch_id)
                task = nidaqmx.Task()
                self._tasks[task_id] = task
                mode = nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL
                task.ai_channels.add_ai_voltage_chan(
                    full_id, terminal_config=mode,
                    min_val=self.temperature_min_volt,
                    max_val=self.temperature_max_volt)
            else:
                tasks = (nidaqmx.Task(), nidaqmx.Task(), nidaqmx.Task())
                self._tasks[task_id] = tasks

                # Input channel to monitor the set value
                full_id = self.device_id + '/' + getattr(self, ch_id)[0]
                mode = nidaqmx.constants.TerminalConfiguration.RSE
                tasks[0].ai_channels.add_ai_voltage_chan(full_id,
                                                         terminal_config=mode)

                # Output channel
                full_id = self.device_id + '/' + getattr(self, ch_id)[1]
                tasks[1].ao_channels.add_ao_voltage_chan(full_id,
                                                         min_val=0,
                                                         max_val=5)

                # Input channel to monitor the actual value
                full_id = self.device_id + '/' + getattr(self, ch_id)[2]
                mode = nidaqmx.constants.TerminalConfiguration.RSE
                tasks[2].ai_channels.add_ai_voltage_chan(full_id,
                                                         terminal_config=mode)

    def finalize(self) -> None:
        for t in self._tasks.values():
            if isinstance(t, (tuple, list)):
                for st in t:
                    st.close()
            else:
                t.close()

    def read_heater_voltage(self) -> float:
        """Read the heater current output (may differ from the set target).

        """
        if not nidaqmx:
            return 0

        if 'temperature' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'reading the heater voltage by calling `initialize`')
            raise RuntimeError(msg)

        value = self._tasks['heater_volt'][2].read()

        return self._convert_heater_volt(value)

    def read_heater_current(self) -> float:
        """Read the heater current output (may differ from the set target).

        """
        if not nidaqmx:
            return 0

        if 'temperature' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'reading the heater current by calling `initialize`')
            raise RuntimeError(msg)

        value = self._tasks['heater_curr'][2].read()

        return self._convert_heater_current(value)

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

        temperature = self._convert_temp(temp_volt)

        return temperature

    # --- Private API ---------------------------------------------------------

    #: NiDAQ tasks used to control the physical DAQ
    _tasks = Dict(Str())

    #: Temperature conversion function.
    _convert_temp = Callable()

    def _convert_heater_current(self, value: float) -> float:
        """Convert the DAQ value into a fraction of the allowed range.

        """
        span = self.heater_curr_max_value - self.heater_curr_min_value
        return round((value - self.heater_curr_min_value) / span, 2)

    def _convert_heater_volt(self, value: float) -> float:
        """Convert the DAQ value into a fraction of the allowed range.

        """
        span = self.heater_volt_max_value - self.heater_volt_min_value
        return round((value - self.heater_volt_min_value) / span, 2)

    def _default_heater_curr_state(self) -> float:
        """Get the value from the DAQ on first read.

        """
        if not nidaqmx:
            return 0.0

        if 'heater_curr' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'reading the heater regulator stqte by calling `initialize`'
                   )
            raise RuntimeError(msg)

        value = self._tasks['heater_curr'][0].read()
        return self._convert_heater_current(value)


    def _default_heater_volt_state(self) -> float:
        """Get the value from the DAQ on first read.

        """
        if not nidaqmx:
            return 0.0

        if 'heater_volt' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'reading the heater regulator stqte by calling `initialize`'
                   )
            raise RuntimeError(msg)

        value = self._tasks['heater_volt'][0].read()
        return round(((value - self.heater_volt_min_value) /
                     (self.heater_volt_max_value - self.heater_volt_min_value)),
                     2)

    def _post_validate_heater_curr_state(self,
                                         old: Optional[float],
                                         new: float):
        """Try to update the DAQ when a valid value is passed.

        """
        if not nidaqmx:
            return new

        if 'heater_curr' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'writing the heater regulator state by calling `initialize`'
                   )
            raise RuntimeError(msg)

        value = (new*(self.heater_curr_max_value - self.heater_curr_min_value) +
                 self.heater_curr_min_value)
        self._tasks['heater_curr'][1].write(value)
        return new

    def _post_validate_heater_volt_state(self,
                                         old: Optional[float],
                                         new: float):
        """Try to update the DAQ when a valid value is passed.

        """
        if not nidaqmx:
            return new

        if 'heater_volt' not in self._tasks:
            msg = ('The connection to the DAQ must be established prior to '
                   'writing the heater regulator state by calling `initialize`'
                   )
            raise RuntimeError(msg)

        value = (new*(self.heater_volt_max_value - self.heater_volt_min_value) +
                 self.heater_volt_min_value)
        self._tasks['heater_volt'][1].write(value)
        return new

    def _create_converter(self, temp_conv_config: dict) -> None:
        """Create a temperature conversion function based on the configuration.

        Parameters
        ----------
        temp_conv_config : dict
            Configuration for the conversion function. Expected keys are:
            - Vref: voltage of the reference part of the thermocouple
            - type: Thermocouple type which should refer to a file in the
                    thermocouples folder. Should be omitted if a custom
                    thermocouple is used.
            - thermocouple: a complete thermocouple description (refers to
                            thermocouples/README for a detailed description)

        """
        if "type" in temp_conv_config:
            dirname = os.path.dirname(__file__)
            path = os.path.join(dirname,
                                'thermocouples',
                                temp_conv_config['type'] + '.json')
            if not os.path.isfile(path):
                raise ValueError('Specified thermocouple file does not exist.'
                                 f'Full path: {path}')
            with open(path) as f:
                temp_conv_config['thermocouple'] = json.load(f)

        c_def = ['def converter(voltage: float) -> float:',
                 f'    x = voltage*1e3 - {temp_conv_config["Vref"]}']

        therm = temp_conv_config['thermocouple']

        def poly_conversion(coeffs):
            i = 0
            value = '0 '
            while True:
                key = f'C{i}'
                if key not in coeffs:
                    break
                value += f'+ {coeffs[key]}*x**{i}'
                i += 1
            return value

        # No validity range:
        if 'C0' in therm:
            c_def.append('    return ' + poly_conversion(therm))

        # We have multiple range
        else:
            for key in therm:
                low, high = key.split(',')
                c_def.append(f'    if x > {low} and x < {high}:')
                c_def.append(f'        return {poly_conversion(therm[key])}')
            c_def.extend(('    else:',
                          '        ' +
                          'raise ValueError(f"No matching range for {x}")'
                          )
                         )

        glob = {}
        exec('\n'.join(c_def), glob)
        self._convert_temp = glob['converter']
