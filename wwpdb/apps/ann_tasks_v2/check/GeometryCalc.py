##
# File:  GeometryCalc.py
# Date:  2-Jan-2014  J. Westbrook
#
# Update:
# 28-Feb -2014  Add base class
#
##
"""
Recalculate geometrical anomalies and store these in the model file.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os
import inspect
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class GeometryCalc(SessionWebDownloadUtils):
    """
    Encapsulates geometry calculation updates.

    Operations are performed in the current session context defined in the input
    reqObj().

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(GeometryCalc, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj

        self.__checkArgs = None

        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__cleanup = True

    def setArguments(self, checkArgs):
        self.__checkArgs = checkArgs

    def run(self, entryId, inpFile, updateInput=True):
        """Run the geometry-level check on the input PDBx/mmCIF data file -"""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath = os.path.join(self.__sessionPath, entryId + "_geometry-calc-report.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            if os.access(retPath, os.R_OK):
                os.remove(retPath)
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            if self.__checkArgs is not None:
                dp.addInput(name="check_arguments", value=self.__checkArgs)

            dp.op("annot-validate-geometry")
            dp.expLog(logPath)
            dp.exp(retPath)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath)
            if updateInput and os.access(retPath, os.R_OK):
                dp.exp(inpPath)
            #
            if self.__verbose:
                self.__lfh.write("+%s.%s geometry calc completed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpFile))

            if self.__cleanup:
                dp.cleanup()
            #
            if os.access(retPath, os.R_OK):
                return True
            else:
                return False
            #
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+%s.%s geometry calc failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpFile))
            traceback.print_exc(file=self.__lfh)
            return False
