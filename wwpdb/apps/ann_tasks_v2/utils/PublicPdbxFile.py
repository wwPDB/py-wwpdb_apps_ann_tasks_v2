##
# File:  PublicPdbxFile.py
# Date:  14-Oct-2013
#
# Update:
# 28-Feb -2014  jdw Add base class
# 4-Jun-2014    jdw Added V4 dictionary argument --
##
"""
Generate public pdbx cif file.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import os.path
import sys
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class PublicPdbxFile(SessionWebDownloadUtils):
    """The PublicPdbxFile class encapsulates conversion internal pdbx cif to public pdbx cif file."""

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(PublicPdbxFile, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #

    def run(self, entryId, inpFile):
        """Run conversion."""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath = os.path.join(self.__sessionPath, entryId + "-public_cif.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-review_P1.cif")
            #
            for filePath in (logPath, retPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            dp.op("annot-cif-to-public-pdbx")
            dp.exp(retPath)
            dp.expLog(logPath)
            dp.cleanup()
            #
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
