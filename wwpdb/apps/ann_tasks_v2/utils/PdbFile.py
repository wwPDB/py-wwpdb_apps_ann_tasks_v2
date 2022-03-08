##
# File:  PdbFile.py
# Date:  13-Oct-2013
#
# Update:
# 28-Feb -2014  jdw Add base class
##
"""
Generate PDB file.

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


class PdbFile(SessionWebDownloadUtils):
    """The PdbFile class encapsulates conversion cif to pdb file."""

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(PdbFile, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__retPath = None

        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #

    def getPdbFilePath(self):
        return self.__retPath

    def run(self, entryId, inpFile):
        """Run conversion."""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath = os.path.join(self.__sessionPath, entryId + "-cif2pdb.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            retPath = os.path.join(self.__sessionPath, entryId + "_model_P1.pdb")
            if os.access(retPath, os.R_OK):
                os.remove(retPath)
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            dp.op("cif2pdb")

            dp.expLog(logPath)
            dp.exp(retPath)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath)
            if self.__verbose:
                self.__lfh.write("+PdbFile.run-  completed for entryId %s file %s\n" % (entryId, inpPath))
            self.__retPath = retPath
            dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False

    def runAlt(self, entryId, inpPath):
        """Run conversion."""
        try:
            logPath = os.path.join(self.__sessionPath, entryId + "-cif2pdb.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            retPath = os.path.join(self.__sessionPath, entryId + "_model_P1.pdb")
            if os.access(retPath, os.R_OK):
                os.remove(retPath)
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            dp.op("cif2pdb")

            dp.expLog(logPath)
            dp.exp(retPath)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath)
            if self.__verbose:
                self.__lfh.write("+PdbFile.run-  completed for entryId %s file %s\n" % (entryId, inpPath))
            self.__retPath = retPath
            dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
