##
# File:  TerminalAtoms.py
# Date:  12-Dec-2013  J. Westbrook
#
# Update:
# 28-Feb -2014  Add base class
##
"""
Manage utility to remove or rename  terminal OXT atoms.

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


class TerminalAtoms(SessionWebDownloadUtils):
    """
    TerminalAtoms class encapsulates removing or renaming  terminal OXT atoms.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(TerminalAtoms, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__status = "none"
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def getLastStatus(self):
        return self.__status

    def __checkStatus(self, logFilePath):
        status = "ok"
        if os.access(logFilePath, os.R_OK):
            ifh = open(logFilePath, "r")
            for line in ifh:
                if str(line).upper().startswith("++ERROR"):
                    return "error"
                if str(line).upper().startswith("++WARN"):
                    return "warn"
            ifh.close()
        else:
            return "error"

        return status

    def run(self, entryId, inpFile, updateInput=True, updateOption="delete"):
        """Run the calculation - updateOption = delete|rename"""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath1 = os.path.join(self.__sessionPath, entryId + "-terminal-atoms.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            dp.addInput(name="option", value=updateOption)

            dp.op("annot-update-terminal-atoms")
            dp.expLog(logPath1)
            dp.exp(retPath)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath1)
            if updateInput:
                dp.exp(inpPath)

            #
            self.__status = self.__checkStatus(logPath1)
            if self.__verbose:
                self.__lfh.write("+TerminalAtoms.run-  completed with status %s for entryId %s file %s\n" % (self.__status, entryId, inpPath))

            dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
