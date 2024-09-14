##
# File:  UpdateCloseContact.py
# Date:  29-Sep-2020  Zukang Feng
#
# Update:
#  06-Sep-2024   zf   export the PTM/PCM "pcm-missing-data" csv file
##
"""
Manage utility to correct close contact problems

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

from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class UpdateCloseContact(SessionWebDownloadUtils):
    """
    UpdateCloseContact class encapsulates correcting close contact problems.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(UpdateCloseContact, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
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
            pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
            csvFile = pI.getFileName(entryId, contentType="pcm-missing-data", formatType="csv", versionId="none", partNumber="1")
            csvPath = os.path.join(self.__sessionPath, csvFile)
            #
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath = os.path.join(self.__sessionPath, entryId + "-update-close-contact.log")
            dataPath = os.path.join(self.__sessionPath, entryId + "-close-contact.txt")
            for filePath in (csvPath, dataPath, logPath):
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
            dp.op("annot-convert-close-contact-to-link")
            dp.expLog(dstPath=logPath, appendMode=False)
            if os.access(logPath, os.R_OK):
                self.addDownloadPath(logPath)
                if self.__checkStatus(logPath) == "ok":
                    dp.expList(dstPathList=[inpPath, csvPath])
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
