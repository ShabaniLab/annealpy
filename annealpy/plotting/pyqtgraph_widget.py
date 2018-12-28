# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Annealpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""A pyqtgraph widget embedded in an enaml widget.

"""
import pyqtgraph as pg
from atom.api import Typed, Dict, Value
from enaml.core.api import d_
from enaml.layout.api import hbox, vbox, spacer
from enaml.widgets.api import RawWidget

from ..app_state import ApplicationState


class DualAxisPyqtGraphWidget(RawWidget):
    """PyqtGraph widget plotting the three monitored quantities.

    """
    #: Reference to the application state.
    app_state = d_(Typed(ApplicationState))

    def create_widget(self, parent):
        """Create the pyqtgraph widget.

        """
        widget = pg.PlotWidget()
        left_plot = widget.plotItem
        left_plot.setLabels(left='Temperature (C)')
        self._left_plot = left_plot

        # create a new ViewBox, link the right axis to its coordinate system
        right_plot = pg.ViewBox()
        left_plot.showAxis('right')
        left_plot.scene().addItem(right_plot)
        left_plot.getAxis('right').linkToView(right_plot)
        right_plot.setXLink(left_plot)
        left_plot.getAxis('right').setLabel('Heater state', color='#0000ff')
        right_plot.setYRange(0, 1)

        return widget

    def add_plot(self, id):
        """Add a plot to the proper axis.

        """
        time = None
        if id != 'temperature' and 'temperature' in self._curves:
            temp = self.app_state.temperature
            time = temp.time[temp.current_index - 1]

        time, data = getattr(self.app_state, id).get_data(time)

        curve = pg.PlotCurveItem(namepen=pg.mkPen(color='#025b94', width=1))
        curve.setData(x=time, y=data)
        self._curves[id] = curve

        plot = self._left_plot if id == 'temperature' else self._right_plot
        plot.addItem(curve)

    def remove_plot(self, id):
        """Remove a plot.

        """
        if id not in self._curves:
            return

        curve = self._curves[id]
        plot = self._left_plot if id == 'temperature' else self._right_plot
        plot.removeItem(curve)

    # --- Private API ---------------------------------------------------------

    _curves = Dict()

    _left_plot = Value()

    _right_plot = Value()

    def _post_setattr_app_state(self, old, new):
        """Start observing the plot_update event when the app_state is set.

        """
        new.observe('plot_update', self._update_plots)

    def _update_plots(self, change):
        """Update the data of the plots.

        """
        time = None

        if 'temperature' in self._curves:
            time, data = self.app_state.temperature.get_data()
            self._curves['temperature'].setData(x=time, y=data)

        if 'heater_switch' in self._curves:
            time, data = self.app_state.heater_switch.get_data(time[-1])
            self._curves['heater_switch'].setData(x=time, y=data)

        if 'heater_regulation' in self._curves:
            time, data = self.app_state.heater_regulation.get_data()
            self._curves['heater_regulation'].setData(x=time, y=data)



