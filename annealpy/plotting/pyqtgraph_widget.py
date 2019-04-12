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


MEASURED_Q = ('temperature',
              'measured_heater_voltage',
              'measured_heater_current')

NON_MEASURED_Q = ('heater_voltage_target', 'heater_current_target')


class PyqtGraphWidget(RawWidget):
    """PyqtGraph widget plotting the three monitored quantities.

    """
    #: Reference to the application state.
    app_state = d_(Typed(ApplicationState))

    #: Colors to use for the plots.
    colors = d_(Dict())

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
        if id not in MEASURED_Q:
            temp = self.app_state.temperature
            time = temp.times[temp.current_index - 1]

        left_label = ('Temperature (C)'
                      if id == 'temperature' else
                      'Heater state %')
        self._plot.setLabels(bottom='Time (s)', left=left_label)

        time, data = getattr(self.app_state, id).get_data(time)

        legend_name = id.capitalize().replace('_', " ")
        curve = pg.PlotCurveItem(name=legend_name,
                                 pen=pg.mkPen(color=self.colors[id], width=1))
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

    def _observe_colors(self, change):
        """Update the plots colors.

        """
        for c_id, c_obj in self._curves.items():
            c_obj.setPen(color=self.colors[c_id], width=1)

    def _update_plots(self, change):
        """Update the data of the plots.

        """
        if self.app_state.temperature.current_index == 0:
            return
        time = [None]

        for nid in MEASURED_Q:
            if nid in self._curves:
                time, data = getattr(self.app_state, nid).get_data()
                self._curves[nid].setData(x=time, y=data)

        for nid in NON_MEASURED_Q:
            if nid in self._curves:
                time, data = getattr(self.app_state, nid).get_data(time[-1])
                self._curves[nid].setData(x=time, y=data)
