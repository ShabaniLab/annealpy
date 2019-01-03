#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    print('Please install or upgrade setuptools or pip to continue')
    sys.exit(1)

sys.path.insert(0, os.path.abspath('.'))
from annealpy.version import __version__


def read(filename):
    with open(filename, 'rb') as f:
        return f.read().decode('utf8')


requirements = ['nidaqmx', 'enaml', 'PyQt5', 'pyqtgraph']


setup(name='annealpy',
      description='Annealer control program used in Shabani Lab',
      version=__version__,
      maintainer='Matthieu Dartiailh',
      maintainer_email='m.dartiailh@gmail.com',
      url='https://github.com/ShabaniLab/annealpy',
      license='BSD-3 License',
      python_requires='>=3.6',
      install_requires=requirements,
      packages=find_packages(),
      platforms="Windows",
      use_2to3=False,
      zip_safe=False,
      entry_points={'gui_scripts': 'annealpy = annealpy.__main__:main'},)
