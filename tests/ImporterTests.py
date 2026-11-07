##
# File: ImportTests.py
# Date:  06-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for ann_tasks_v2"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import unittest

if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from commonsetup import TESTOUTPUT
else:
    from .commonsetup import TESTOUTPUT


from wwpdb.utils.session.WebRequest import InputRequest

from wwpdb.apps.ann_tasks_v2.em3d.EmAutoFix import EmAutoFix
from wwpdb.apps.ann_tasks_v2.webapp.AnnTasksWebApp import AnnTasksWebApp
from wwpdb.apps.ann_tasks_v2.webapp.CommonTasksWebAppWorker import CommonTasksWebAppWorker


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.__reqObj = InputRequest(paramDict={})

    def testInstantiate(self):
        """Tests simple instantiation"""
        # Needs a reqobj
        _ctw = CommonTasksWebAppWorker(self.__reqObj)
        _atw = AnnTasksWebApp(self.__reqObj)
        _emaut = EmAutoFix(os.path.join(TESTOUTPUT, "sess"))
