# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Classes related to the execution of a process.

"""
import json
import time
from multiprocessing import Event, Process, Queue
from threading import Thread

from atom.api import Atom, Enum, List, Typed, Str
from enaml.application import deferred_call

from .daq.daq_control import AnnealerDaq
from .steps import STEPS
from .steps.base_step import BaseStep

# This can use a multiprocessing.Process subclass handling the DAQ (all steps
# must go through it which means it can take care of piping the relevant infos
# back to the app for plotting).


class MonitoringThread(Thread):
    """Thread used to monitor the state (alive/dead) of the actuator.

    """
    def __init__(self, process):

        super().__init__()
        self.process = process
        self.daemon = True

    def run(self):
        """Wait for the process to become active and then wait for its death.

        """
        while True:
            # Wait for the process to start
            if self.process._actuator.is_alive():
                break

            # If a stop is requested and we somehow missed the starting of the
            # process exit. THIS SHOULD NEVER HAPPEN
            elif self.process._actuator.stop_event.is_set():
                return

        deferred_call(setattr, self.process, 'status', 'Running')

        while self.process._actuator.is_alive():
            self.process._actuator.join(2)

        if self.process._actuator.crashed_event.is_set():
            deferred_call(setattr, self.process, 'status', 'Failed')
        elif self.process._actuator.stop_event.is_set():
            deferred_call(setattr, self.process, 'status', 'Stopped')
        else:
            deferred_call(setattr, self.process, 'status', 'Completed')


class PollingThread(Thread):
    """Thread polling the queue filled by the actuator to update the app.

    """
    def __init__(self, app_state, actuator_queue):

        super().__init__()
        self.app_state = app_state
        self._actuator_queue = actuator_queue

    def run(self):

        while True:
            channel, time, value = self._actuator_queue.get()
            if channel is None:
                break
            else:
                ch_status = getattr(self.app_state, channel)
                ch_status.append_value(time, value)

        self.app_state.stop_plot_timer()


class ActuatorSubprocess(Process):
    """Subprocess in charge of executing a process.

    """
    def __init__(self, process_config_path, daq_config, queue,
                 stop_event, crashed_event):

        super().__init__(daemon=True)
        self.process_config_path = process_config_path
        self.daq_config = daq_config
        self.queue = queue
        self.stop_event = stop_event
        self._daq = None
        self.start_time = 0.0
        self.crashed_event = crashed_event

    def run(self):
        """Run the process described in the config.

        """
        try:
            self._daq = AnnealerDaq(self.daq_config)
            self._daq.initialize()

            p = AnnealerProcess.load(self.process_config_path)

            self.start_time = time.time()
            # Initialize the values by forcing a notification in the queue
            self.read_temperature()
            self.read_heater_voltage()
            self.read_heater_current()
            self.heater_curr_state = self.heater_curr_state
            self.heater_volt_state = self.heater_volt_state

            for s in p.steps:
                if self.stop_event.is_set():
                    break
                s.run(self)

        except Exception:
            self.crashed_event.set()
            raise

        finally:
            self._daq.finalize()
            self.queue.put((None, None, None))

    def read_temperature(self):
        """Read the temperature through the daq and post the value.

        """
        temp = self._daq.read_temperature()
        self.queue.put(('temperature', time.time() - self.start_time, temp))
        return temp

    def read_heater_voltage(self):
        """Read the voltage applied to the heater.

        """
        val = self._daq.read_heater_voltage()
        self.queue.put(('measured_heater_voltage',
                        time.time() - self.start_time, val))
        return val

    def read_heater_current(self):
        """Read the current applied to the heater.

        """
        val = self._daq.read_heater_current()
        self.queue.put(('measured_heater_current',
                        time.time() - self.start_time, val))
        return val

    @property
    def heater_volt_state(self):
        """Target voltage for the heater regulation controlled by the DAQ.

        """
        return self._daq.heater_volt_state

    @heater_volt_state.setter
    def heater_volt_state(self, value):
        self._daq.heater_volt_state = value
        self.queue.put(('heater_voltage_target',
                        time.time() - self.start_time,
                        value))

    @property
    def heater_curr_state(self):
        """Target current for the heater regulation controlled by the DAQ.

        """
        return self._daq.heater_curr_state

    @heater_curr_state.setter
    def heater_curr_state(self, value):
        self._daq.heater_curr_state = value
        self.queue.put(('heater_current_target',
                        time.time() - self.start_time,
                        value))


class AnnealerProcess(Atom):
    """An annealing process described by a series of steps.

    """
    #: User specified description of the process.
    description = Str()

    #: Path under which this process is saved.
    path = Str()

    #: Steps describing the annealing process.
    steps = List(BaseStep, [])

    #: Current status of the process.
    status = Enum('Inactive', 'Started', 'Running', 'Completed',
                  'Stopping', 'Stopped', 'Failed')

    def save(self, path=None):
        """Save the process to a json file by serializing the steps.

        """
        path = path or self.path
        config = dict(steps=[], description=self.description)
        for s in self.steps:
            s_config = s.get_preferences_from_members()
            s_config['type'] = s.__class__.__name__
            config['steps'].append(s_config)

        with open(path, 'w') as f:
            json.dump(config, f, indent=4)

        self.path = path

    @classmethod
    def load(cls, path):
        """Load a process stored in a JSON file.

        """
        with open(path) as f:
            config = json.load(f)

        steps = []
        for c in config["steps"]:
            step_cls = STEPS[c.pop('type')]
            steps.append(step_cls(**c))

        return cls(description=config['description'],
                   path=path,
                   steps=steps)

    def add_step(self, index, step):
        """Add a step at a given index in the process.

        If index is None the step is appended instead.

        """
        steps = self.steps[:]
        if index is None or index >= len(self.steps):
            steps.append(step)
        else:
            steps.insert(index, step)
        self.steps = steps

    def move_step(self, old_index, new_index):
        """Move a step between two positions.

        """
        steps = self.steps[:]
        step = steps.pop(old_index)
        steps.insert(new_index, step)

        # Force a UI notification
        self.steps = []
        self.steps = steps

    def remove_step(self, index):
        """Remove a step at a given index.

        """
        steps = self.steps[:]
        del steps[index]
        self.steps = steps

    def start(self, app_state):
        """Start the process execution.

        """
        queue = Queue()
        stop_event = Event()
        crashed_event = Event()

        #: Reset the plots data
        app_state.temperature.current_index = 0
        app_state.measured_heater_voltage.current_index = 0
        app_state.measured_heater_current.current_index = 0
        app_state.heater_voltage_target.current_index = 0
        app_state.heater_current_target.current_index = 0

        self._actuator = ActuatorSubprocess(self.path,
                                            app_state.get_daq_config(),
                                            queue, stop_event,
                                            crashed_event)
        self._monitoring_thread = MonitoringThread(self)
        self._polling_thread = PollingThread(app_state, queue)

        self._actuator.start()
        self.status = 'Started'
        self._monitoring_thread.start()
        self._polling_thread.start()

        app_state.start_plot_timer()

    def stop(self, force=False):
        """Stop the process.

        """
        self.status = 'Stopping'
        if force:
            self._actuator.terminate()
        else:
            self._actuator.stop_event.set()

    # --- Private API ---------------------------------------------------------

    #: Subprocess actuator repsonible for the process execution.
    _actuator = Typed(ActuatorSubprocess)

    #: Thread responsible for updating the app about the state of progress of
    #: the process.
    _polling_thread = Typed(PollingThread)

    #: Thread updating the state of the process by monitoring teh actuator.
    _monitoring_thread = Typed(MonitoringThread)
