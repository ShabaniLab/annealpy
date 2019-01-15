# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by AnnealPy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
import enaml

from .base_step import BaseStep
from .fast_ramp import FastRamp
from .pid_regulated_step import PIDRegulatedStep
from .stop_heating_step import StopHeatingStep

with enaml.imports():
    from .views.pid_regulated_step_view import PIDRegulatedStepView
    from .views.stop_heating_step_view import StopHeatingStepView
    from .views.fast_ramp_view import FastRampView

STEPS = {'StopHeatingStep': StopHeatingStep,
         'PIDRegulatedStep': PIDRegulatedStep,
         'FastRamp': FastRamp}


_STEP_VIEWS = {PIDRegulatedStep: PIDRegulatedStepView,
               StopHeatingStep: StopHeatingStepView,
               FastRamp: FastRampView}


def create_widget(step):
    """Create the widget matching a step.

    """
    return _STEP_VIEWS[type(step)](step=step)
