# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Annealpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD 3-Clause license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Main entry point for the annealpy application.

"""
import enaml
from enaml.qt.qt_application import QtApplication

from .app_state import ApplicationState
with enaml.imports():
    from .main_window import AppWindow


def main():

    app_state = ApplicationState()

    app = QtApplication()
    # Create a view and show it.
    view = AppWindow(state=app_state)
    view.show()

    app.start()


if __name__ == '__main__':
    main()
