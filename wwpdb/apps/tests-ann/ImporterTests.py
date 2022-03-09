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

import unittest
import os
import sys

if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa:  F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=relative-beyond-top-level


from wwpdb.apps.ann_tasks_v2.webapp.CommonTasksWebAppWorker import CommonTasksWebAppWorker
from wwpdb.apps.ann_tasks_v2.webapp.AnnTasksWebApp import AnnTasksWebApp  # noqa: F401 pylint: disable=unused-import
from wwpdb.apps.ann_tasks_v2.em3d.EmAutoFix import EmAutoFix  # noqa: F401 pylint: disable=unused-import
from wwpdb.utils.session.WebRequest import InputRequest


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.__reqObj = InputRequest(paramDict={})

    def testInstantiate(self):
        """Tests simple instantiation"""
        # Needs a reqobj
        _ctw = CommonTasksWebAppWorker(self.__reqObj)  # noqa: F841
        _atw = AnnTasksWebApp(self.__reqObj)  # noqa: F841
        _emaut = EmAutoFix(os.path.join(TESTOUTPUT, "sess"))  # noqa: F841
