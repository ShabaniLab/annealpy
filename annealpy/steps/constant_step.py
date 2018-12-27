# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Annealpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Constant temperature step relying on a pid.

"""
from atom.api import Float, Tuple

from .base_step import BaseStep


class ConstantStep(BaseStep):
    """Perform a constant temperature step assuming we start from the target.

    """
    #:
    target_temperature = Float().tag(pref=True)

    #:
    pid_parameters = Tuple(Float()).tag(pref=True)

    def run(self, actuator):
        """
        """
        pass
