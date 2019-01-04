# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Objects used to store information about the current state of the application

"""
import os
import json

import numpy as np
from atom.api import Atom, Enum, Int, Str, Typed, Event, Bool, Float, Dict
from enaml.application import timed_call

from .process import AnnealerProcess


class ChannelStatus(Atom):
    """Status of one the DAQ channel over time.

    We keep track of the measured/set values as a function of time in
    pre-allocated numpy arrays.

    """
    #: Kind of the channel.
    #: Continuous channel can vary in between recorded values.
    #: Stepped channel do not vary in between recorded values and should be
    #: plotted as such.
    kind = Enum('continuous', 'stepped')

    #: Array containing the time elapsed in s since the process started.
    times = Typed(np.ndarray)

    #: Recorded values since the process started. Values are stored in such a
    #: way as to produce plot in agreemnent with their kind.
    values = Typed(np.ndarray)

    #: Current index to use to add new values.
    current_index = Int()

    #: Size of the currently allocated arrays used to detect overflows.
    allocated_size = Int()

    def __init__(self, type, kind, initial_size):
        self.kind = kind
        self.times = np.empty(initial_size)
        self.values = np.empty(initial_size, type)
        self.allocated_size = initial_size
        # self.current_index = min(self.allocated_size - 1, 100)

    def add_first_value(self, value):
        """Add a first value in the records.

        This should be called only if the current_index is 0.

        """
        if self.current_index != 0:
            raise ValueError('add_first_value can only be called if the '
                             f'current_index is 0 not {self.current_index}')

        self.times[0] = 0
        self.values[0] = value
        self.current_index += 1

    def append_value(self, time, value):
        """Append a value to the records.

        This is done in such a way as to respect the kind attribute.

        """
        index = self.current_index
        if self.kind == 'stepped':
            self.times[index:index+2] = time
            self.values[index] = self.values[index-1]
            self.values[index+1] = value
            self.current_index += 2
        else:
            self.times[index] = time
            self.values[index] = value
            self.current_index += 1

        if self.current_index + 1 >= self.allocated_size:
            old_time = self.times
            self.times = np.empty(int(1.5*self.allocated_size))
            self.times[:len(old_time)+1] = old_time
            old_values = self.values
            self.values = np.empty(int(1.5*self.allocated_size),
                                   old_values.dtype)
            self.values[:len(old_values)+1] = old_values

    def get_data(self, time=None):
        """Retrieve data in a way consistent with their kind.

        """
        index = self.current_index

        if time is None or self.kind != 'stepped':
            return (self.times[:index],
                    self.values[:index])

        else:
            self.times[index] = time
            self.values[index] = self.values[index-1]
            return (self.times[:index+1],
                    self.values[:index+1])


class ApplicationState(Atom):
    """Object storing the current state of the application.

    Used to centralize information that needs to be shared between the
    different components.

    """
    #: Path to a user defined DAQ config. By default used the one provided with
    #: the library.
    daq_config_path = Str().tag(pref=True)

    #: Path to the last loaded process.
    process_config_path = Str().tag(pref=True)

    #: Plot refresh interval in s.
    plot_refresh_interval = Float(2).tag(pref=True)

    #: Plot colors.
    plot_colors = Typed(dict, ({'temperature': '#f9f9f9',
                                'heater_switch': '#9bceee',
                                'heater_regulation': '#59c3b1'},)
                        ).tag(pref=True)

    #: Process being edited/run
    process = Typed(AnnealerProcess, ())

    #: Measured temperature over time
    temperature = Typed(ChannelStatus, (np.float, 'continuous', 36000))

    #: Heater switch state over time
    heater_switch = Typed(ChannelStatus, (np.int, 'stepped', 10000))

    #: Measured temperature over time
    heater_regulation = Typed(ChannelStatus, (np.float, 'stepped', 10000))

    #: Event signaling the plot should be updated.
    plot_update = Event()

    def __init__(self):
        super().__init__()
        self.load_app_state()
        if self.process_config_path:
            self.process = AnnealerProcess.load(self.process_config_path)

    def load_app_state(self):
        """Load the application state.

        """
        path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.isfile(path):
            with open(path) as f:
                config = json.load(f)
            for name, member in self.members().items():
                if member.metadata and 'pref' in member.metadata:
                    setattr(self, name, config[name])

        else:
            self.daq_config_path = os.path.join(os.path.dirname(__file__),
                                                'daq', 'daq_config.json')

    def save_app_state(self):
        """Save the application state to a JSON file.

        """
        config = {}
        for name, member in self.members().items():
            if member.metadata and 'pref' in member.metadata:
                config[name] = getattr(self, name)
        path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(path, 'w') as f:
            json.dump(config, f)

    def get_daq_config(self):
        """Load the daq configuration.

        """
        with open(self.daq_config_path) as f:
            return json.load(f)

    def start_plot_timer(self):
        """Start a recurring timer that fire the plot_update event.

        """
        self._stop_timer = False
        self._fire_plot_update(schedule_only=True)

    def stop_plot_timer(self):
        """Stop the recurring timer that fire the plot_update event.

        """
        self._stop_timer = True

    # --- Private API ---------------------------------------------------------

    #: Boolean indicating the timer not to re-schedule itself.
    _stop_timer = Bool()

    def _fire_plot_update(self, schedule_only=False):
        """Fire the plot update event and reschedule a new call.

        """
        if not schedule_only:
            self.plot_update = True
        if not self._stop_timer:
            timed_call(1000*self.plot_refresh_interval, self._fire_plot_update)

    def _post_setattr_daq_config_path(self, old, new):
        """Save the app state when the user specifies a new config.

        """
        self.save_app_state()

    def _post_setattr_process_config_path(self, old, new):
        """Save the app state when the user save/load a process.

        """
        self.save_app_state()

    def _post_setattr_plot_refresh_interval(self, old, new):
        """Save the app state when the user change the plot refresh interval.

        """
        self.save_app_state()
