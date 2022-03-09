##
# File:  NmrModelUtils.py
# Date:  18-Sep-2014  J. Westbrook
#
# Update:
##
"""
Various NMR model update tasks. --

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


class NmrModelUtils(SessionWebDownloadUtils):
    """
    NmrModelUtils class encapsulates updates of NMR model files.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(NmrModelUtils, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__repModelNumber = None
        self.__status = "none"
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #

    def setRepresentativeModelNumber(self, modelNum):
        self.__repModelNumber = modelNum

    def getLastStatus(self):
        return self.__status

    def __checkStatus(self, logFilePath):
        #       status='ok'
        status = "error"
        if os.access(logFilePath, os.R_OK):
            ifh = open(logFilePath, "r")
            for line in ifh:
                #               if str(line).upper().startswith("++WARN"):
                #                   return 'warn'
                if str(line).startswith("Finished!"):
                    status = "ok"
            ifh.close()
        else:
            return "error"

        return status

    def run(self, entryId, inpFile, updateInput=True):
        """Run the selection of representative model update -"""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath1 = os.path.join(self.__sessionPath, entryId + "-nmr-rep-model-update.log")
            if os.access(logPath1, os.R_OK):
                os.remove(logPath1)
            #
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            if os.access(retPath, os.R_OK):
                os.remove(retPath)
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            if self.__repModelNumber is not None:
                dp.addInput(name="model_number", value=self.__repModelNumber)
            dp.op("annot-reorder-models")
            dp.expLog(logPath1)
            dp.exp(retPath)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath1)
            self.__status = self.__checkStatus(logPath1)
            if self.__verbose:
                self.__lfh.write("+NmrModelUtils.run-  completed with status %s for entryId %s file %s\n" % (self.__status, entryId, inpPath))
            #
            if updateInput and (self.__status == "ok"):
                dp.exp(inpPath)
            #
            # dp.cleanup()
            if self.__status == "ok":
                return True
            else:
                return False
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
