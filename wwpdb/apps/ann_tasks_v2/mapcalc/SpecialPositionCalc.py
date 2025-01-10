##
# File:  SpecialPositionCalc.py
# Date:  18-Oct-2013  J. Westbrook
#
# Update:
# 28-Feb -2014  Add base class
#
##
"""
Run DCC/Tool calculation of special symmetry positions -

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
from mmcif.io.IoAdapterCore import IoAdapterCore


class SpecialPositionCalc(SessionWebDownloadUtils):
    """
    The SpecialPositionCalc class launches DCC/Tool to calculate special symmetry positions.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(SpecialPositionCalc, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        # self.__dccArgs = None
        self.__reportPath = None
        self.__reportFileSize = 0
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__cleanup = True

    def setArguments(self, dccArgs):  # pylint: disable=unused-argument
        # self.__dccArgs = dccArgs
        pass

    def getReportSize(self):
        return self.__reportFileSize

    def getReportPath(self):
        return self.__reportPath

    def run(self, entryId, modelInputFile=None):
        """Calculate the special positions."""
        try:
            inpPath = None
            if modelInputFile is None:
                modelFileName = entryId + "_model_P1.cif"
                inpPath = os.path.join(self.__sessionPath, modelFileName)
            else:
                inpPath = os.path.join(self.__sessionPath, modelInputFile)
            #
            logPath = os.path.join(self.__sessionPath, entryId + "_special-position-calc.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            self.__reportPath = os.path.join(self.__sessionPath, entryId + "_special-position-report_P1.txt.V1")
            if os.access(self.__reportPath, os.R_OK):
                os.remove(self.__reportPath)
            #
            # We should not run special position check for NMR, EM.  Program detects no unit cell and complains
            # Program used to crash - which is why error being reported.
            try:
                ioobj = IoAdapterCore()
                c0 = ioobj.readFile(inputFilePath=modelInputFile, selectList=["exptl"])
                if c0:
                    b0 = c0[0]
                    catObj = b0.getObj("exptl")
                    if catObj:
                        methods = catObj.getAttributeValueList("method")
                        runProcess = False
                        for m in methods:
                            if m.upper() in ["X-RAY DIFFRACTION", "NEUTRON DIFFRACTION", "POWDER DIFFRACTION", "ELECTRON CRYSTALLOGRAPHY"]:
                                runProcess = True
                                break

                        if not runProcess:
                            return True
            except:  # noqa: E722 pylint: disable=bare-except
                pass

            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            # if (self.__dccArgs is not None):
            #    dp.addInput(name="dcc_arguments",value=self.__dccArgs)
            dp.op("annot-dcc-special-position")
            dp.expLog(logPath)
            self.__reportFileSize = dp.expSize()
            if self.__reportFileSize > 0:
                dp.exp(self.__reportPath)
                self.addDownloadPath(self.__reportPath)
            #
            self.addDownloadPath(logPath)
            if self.__verbose:
                self.__lfh.write(
                    "+%s.%s special position check completed for entryId %s file %s report size %d\n"
                    % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath, self.__reportFileSize)
                )

            if self.__cleanup:
                dp.cleanup()
            #
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+SpecialPositionCalc.run-  failed with exception for entryId %s file %s\n" % (entryId, inpPath))

            traceback.print_exc(file=self.__lfh)
            return False
