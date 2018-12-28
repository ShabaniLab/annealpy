# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Annealpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
from .base_step import BaseStep
from .fast_ramp import FastRamp
from .regulated_step import RegulatedStep


STEPS = {'FastRamp': FastRamp,
         'RegulatedStep': RegulatedStep}

def create_widget(step):
    """Create the widget matching a step.

    """
    pass
