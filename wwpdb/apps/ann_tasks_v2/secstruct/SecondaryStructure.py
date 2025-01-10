##
# File:  SecondaryStructure.py
# Date:  30-June-2012  J. Westbrook
#
# Update:
#         2-July-2012  jdw add topology file option
#         4-July-2012  jdw no restriction on topology file name.
#         28-Feb -2014 jdw Add base class
##
"""
Manage calculation of secondary structure.

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


class SecondaryStructure(SessionWebDownloadUtils):
    """
    SecondaryStructure class encapsulates calculation of secondary structure.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(SecondaryStructure, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__topFilePath = None
        self.__status = "none"
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__topFilePath = None
        #

    def setTopologyFile(self, topFileName):
        tPath = os.path.join(self.__sessionPath, topFileName)
        if os.access(tPath, os.F_OK):
            self.__topFilePath = tPath

    def getLastStatus(self):
        return self.__status

    def __checkStatus(self, logFilePath):
        status = "ok"
        if os.access(logFilePath, os.R_OK):
            ifh = open(logFilePath, "r")
            for line in ifh:
                if str(line).upper().startswith("++WARN"):
                    return "warn"
            ifh.close()
        else:
            return "error"

        return status

    def run(self, entryId, inpFile, updateInput=True):
        """Run the secondary structure calculation and merge the result with model file."""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath1 = os.path.join(self.__sessionPath, entryId + "-sec-struct-anal.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            for filePath in (retPath, logPath1):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            if self.__topFilePath is not None:
                dp.addInput(name="ss_topology_file_path", value=self.__topFilePath)
            #
            dp.op("annot-secondary-structure")
            dp.expLog(logPath1)
            dp.exp(retPath)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath1)
            if updateInput and os.access(retPath, os.R_OK):
                dp.exp(inpPath)
            #
            self.__status = self.__checkStatus(logPath1)
            if self.__verbose:
                self.__lfh.write("+SecondaryStructure.run-  completed with status %s for entryId %s file %s\n" % (self.__status, entryId, inpPath))
            #
            dp.cleanup()
            if os.access(retPath, os.R_OK):
                return True
            else:
                return False
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
