##
# File:  DccCalc.py
# Date:  15-Aug-2013  J. Westbrook
#
# Update:
# 28-Feb -2014  Add base class
#
##
"""
Manage DCC electon density calculation from model coordinates and structure factors.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class DccCalc(SessionWebDownloadUtils):
    """
    The DccCalc class launches electon density calculation and creates a report of residue rspace values and diagnostics.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(DccCalc, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__dccArgs = None
        self.__cleanup = False
        self.__exportPath = None
        self.__reportPath = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__exportPath = self.__sessionPath

    def getReportPath(self):
        return self.__reportPath

    def setExportPath(self, exportPath):
        self.__exportPath = exportPath

    def setArguments(self, dccArgs):
        self.__dccArgs = dccArgs

    def run(self, entryId, modelInputPath=None, expInputPath=None, updateInput=True):  # pylint: disable=unused-argument
        """Run the dcc calculation -"""
        try:
            if self.__verbose:
                self.__lfh.write("\n+DccCalc.run  starting for entryId %s model %s sf %s\n" % (entryId, modelInputPath, expInputPath))
            if modelInputPath is None:
                modelFileName = entryId + "_model_P1.cif"
                inpPath = os.path.join(self.__sessionPath, modelFileName)
            else:
                inpPath = modelInputPath

            if expInputPath is None:
                expFileName = entryId + "_sf_P1.cif"
                sfPath = os.path.join(self.__sessionPath, expFileName)
            else:
                sfPath = expInputPath

            #
            logPath = os.path.join(self.__exportPath, entryId + "_dcc-calc.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            self.__reportPath = os.path.join(self.__exportPath, entryId + "_dcc-report_P1.cif.V1")
            if os.access(self.__reportPath, os.R_OK):
                os.remove(self.__reportPath)
            #
            if not os.access(sfPath, os.R_OK):
                if self.__verbose:
                    self.__lfh.write("+DccCalc.run  failed for entryId %s file %s\n" % (entryId, inpPath))
                ofh = open(logPath, "w")
                ofh.write("+DccCalc.run calculation failed no structure factor file for entry %s\n" % entryId)
                ofh.close()
                self.addDownloadPath(logPath)
                return False
            #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            dp.addInput(name="sf_file_path", value=sfPath)
            if self.__dccArgs is not None:
                dp.addInput(name="dcc_arguments", value=self.__dccArgs)
            dp.op("annot-dcc-report")
            dp.expLog(logPath)

            dp.exp(self.__reportPath)

            self.addDownloadPath(self.__reportPath)
            self.addDownloadPath(logPath)
            #
            if self.__verbose:
                self.__lfh.write("+DccCalc.run  completed for entryId %s file %s\n" % (entryId, inpPath))

            if self.__cleanup:
                dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+DccCalc.run-  failed with exception for entryId %s file %s\n" % (entryId, inpPath))

            traceback.print_exc(file=self.__lfh)
            return False
