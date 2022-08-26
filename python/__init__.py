#
# Copyright 2008,2009 Free Software Foundation, Inc.
#
# This application is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This application is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# The presence of this file turns this directory into a Python package

'''
This is the GNU Radio STAMINA module. Place your Python package
description here (python/__init__.py).
'''
from __future__ import unicode_literals

# GNU Radio 3.8 is compatible with both Python 2 and 3,
# which raise different exceptions if a module is not found.
try:
    module_not_found_error = ModuleNotFoundError
except NameError:
    module_not_found_error = ImportError

# import swig generated symbols into the stamina namespace
try:
    # this might fail if the module is python-only
    from .stamina_swig import *
except module_not_found_error:
    pass

# import any pure python here
from .beam_mapper import beam_mapper
from .beam_sweep import beam_sweep
from .rss_calc import rss_calc
from .kpi_agg import kpi_agg

from .beam_selector import beam_selector
from .manual_beam import manual_beam
from .rate_measure import rate_measure



#
