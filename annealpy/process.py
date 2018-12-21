# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Annealpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the MIT license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------

# This can use a multiprocessing.Process subclass handling the DAQ (all steps
# must go through it which means it can take care of piping the relevant infos
# back to the app for plotting).