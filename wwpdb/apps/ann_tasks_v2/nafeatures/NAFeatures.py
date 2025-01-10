##
# File:  NAFeatures.py
# Date:  30-June-2012  J. Westbrook
#
# Update:
#   4-July-2012 jdw  - tested in webapp
#   28-Feb -2014  Add base class
##
"""
Manage the calculation of geometrical features of nucleic acid polymers.

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


class NAFeatures(SessionWebDownloadUtils):
    """
    The NAFeatures class encapsulates the calculation of geometrical features of nucleic acid polymers.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(NAFeatures, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__naArgs = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def setArguments(self, naArgs):
        self.__naArgs = naArgs

    def run(self, entryId, inpFile, updateInput=True):
        """Run the geometrical feature calculation and merge the result with model file."""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath1 = os.path.join(self.__sessionPath, entryId + "-na-anal.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            for filePath in (retPath, logPath1):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            if self.__naArgs is not None:
                dp.addInput(name="na_arguments", value=self.__naArgs)
            dp.op("annot-base-pair-info")
            dp.expLog(logPath1)
            dp.exp(retPath)
            #
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath1)
            if updateInput and os.access(retPath, os.R_OK):
                dp.exp(inpPath)
            #
            if self.__verbose:
                self.__lfh.write("+NAFeatures.run-  completed for entryId %s file %s\n" % (entryId, inpPath))
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
