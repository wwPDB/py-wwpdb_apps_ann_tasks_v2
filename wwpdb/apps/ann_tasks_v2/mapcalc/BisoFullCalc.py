##
# File:  BisoFullCalc.py
# Date:  18-Oct-2013  J. Westbrook
#
# Update:
# 28-Feb -2014  Add base class
#
##
"""
Manage DCC/Tool reassignment of alt ids.

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


class BisoFullCalc(SessionWebDownloadUtils):
    """
    The BisoFullCalc class launches dcc/tool to reassign alt ids ...

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(BisoFullCalc, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__dccArgs = None
        self.__cleanup = True
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def setArguments(self, dccArgs):
        self.__dccArgs = dccArgs

    def run(self, entryId, modelInputFile=None, expInputFile=None, updateInput=True):
        """Run the reassignment operation"""
        try:
            if modelInputFile is None:
                modelFileName = entryId + "_model_P1.cif"
                inpPath = os.path.join(self.__sessionPath, modelFileName)
            else:
                inpPath = os.path.join(self.__sessionPath, modelInputFile)

            if expInputFile is None:
                expFileName = entryId + "_sf_P1.cif"
                sfPath = os.path.join(self.__sessionPath, expFileName)
            else:
                sfPath = os.path.join(self.__sessionPath, expInputFile)
            #
            #
            logPath = os.path.join(self.__sessionPath, entryId + "_biso-full-calc.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            for filePath in (retPath, logPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            dp.addInput(name="sf_file_path", value=sfPath)
            if self.__dccArgs is not None:
                dp.addInput(name="dcc_arguments", value=self.__dccArgs)
            dp.op("annot-dcc-biso-full")
            dp.expLog(logPath)
            dp.exp(retPath)
            dp.expLog(logPath)
            dp.exp(retPath)

            if updateInput and os.access(retPath, os.R_OK):
                dp.exp(inpPath)
            #
            if self.__verbose:
                self.__lfh.write("+BisoFullCalc.run-  completed for entryId %s file %s\n" % (entryId, inpPath))

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
                self.__lfh.write("+BisoFullCalc.run-  failed with exception for entryId %s file %s\n" % (entryId, inpPath))

            traceback.print_exc(file=self.__lfh)
            return False
