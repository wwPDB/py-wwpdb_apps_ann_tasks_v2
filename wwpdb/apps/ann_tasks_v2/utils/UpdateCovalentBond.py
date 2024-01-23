##
# File:  UpdateCovalentBond.py
# Date:  22-Jan-2024  Zukang Feng
#
# Update:
##
"""
Manage utility to correct covalent bond problems

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class UpdateCovalentBond(SessionWebDownloadUtils):
    """
    UpdateCovalentBond class encapsulates correcting covalent bond problems.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(UpdateCovalentBond, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def __checkStatus(self, logFilePath):
        status = "error"
        if os.access(logFilePath, os.R_OK):
            ifh = open(logFilePath, "r")
            for line in ifh:
                if str(line).startswith("Finished!"):
                    status = "ok"
                    break
                #
            #
        #
        return status

    def run(self, entryId, inpFile, closeContactList):
        """Run the calculation"""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath = os.path.join(self.__sessionPath, entryId + "-update-covalent-bond.log")
            dataPath = os.path.join(self.__sessionPath, entryId + "-covalent-bond.txt")
            for filePath in (logPath, dataPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            ofh = open(dataPath, "w")
            for closeContact in closeContactList:
                ofh.write("%s\n" % closeContact)
            #
            ofh.close()
            #
            status = False
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            #
            dp.imp(inpPath)
            dp.addInput(name="datafile", value=dataPath)
            dp.op("annot-remove-covalent-bond")
            dp.expLog(dstPath=logPath, appendMode=False)
            if os.access(logPath, os.R_OK):
                self.addDownloadPath(logPath)
                if self.__checkStatus(logPath) == "ok":
                    dp.exp(inpPath)
                    self.addDownloadPath(inpPath)
                    status = True
                #
            #
            dp.cleanup()
            return status
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
        #
