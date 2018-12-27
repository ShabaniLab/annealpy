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
from .constant_step import ConstantStep


STEPS = {'FastRamp': FastRamp,
         'ConstantStep': ConstantStep}
