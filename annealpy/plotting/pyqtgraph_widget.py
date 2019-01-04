# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""A pyqtgraph widget embedded in an enaml widget.

"""
import pyqtgraph as pg
from atom.api import Typed, Dict, Value, List, Enum, set_default
from enaml.core.api import d_
from enaml.layout.api import hbox, vbox, spacer
from enaml.widgets.api import RawWidget

from ..app_state import ApplicationState


COLORS = {'temperature': 'w',
          'heater_switch': 'b',
          'heater_regulation': 'r'}


class DualAxisPyqtGraphWidget(RawWidget):
    """PyqtGraph widget plotting the three monitored quantities.

    """
    #: Reference to the application state.
    app_state = d_(Typed(ApplicationState))

    hug_width = set_default('ignore')
    hug_height = set_default('ignore')

    def create_widget(self, parent):
        """Create the pyqtgraph widget.

        """
        widget = pg.PlotWidget(parent)
        plot = widget.plotItem
        plot.addLegend()
        self._plot = plot

        return widget

    def add_plot(self, id):
        """Add a plot to the proper axis.

        """
        time = None
        if id != 'temperature':
            temp = self.app_state.temperature
            time = temp.times[temp.current_index - 1]

        left_label = ('Temperature (C)'
                      if id == 'temperature' else
                      'Heater state %')
        self._plot.setLabels(bottom='Time (s)', left=left_label)

        time, data = getattr(self.app_state, id).get_data(time)

        legend_name = id.capitalize().replace('_', " ")
        curve = pg.PlotCurveItem(name=legend_name,
                                 pen=pg.mkPen(color=COLORS[id], width=1))
        curve.setData(x=time, y=data)
        self._curves[id] = curve

        self._plot.addItem(curve)

    def remove_plot(self, id):
        """Remove a plot.

        """
        if id not in self._curves:
            return

        curve = self._curves[id]
        self._plot.removeItem(curve)

    # --- Private API ---------------------------------------------------------

    _curves = Dict()

    _plot = Value()

    def _update_plots(self, change):
        """Update the data of the plots.

        """
        if self.app_state.temperature.current_index == 0:
            return
        time = [None]

        if 'temperature' in self._curves:
            time, data = self.app_state.temperature.get_data()
            self._curves['temperature'].setData(x=time, y=data)

        if 'heater_switch' in self._curves:
            time, data = self.app_state.heater_switch.get_data(time[-1])
            print(time, data)
            self._curves['heater_switch'].setData(x=time, y=data)

        if 'heater_regulation' in self._curves:
            time, data = self.app_state.heater_regulation.get_data(time[-1])
            print(time, data)
            self._curves['heater_regulation'].setData(x=time, y=data)
