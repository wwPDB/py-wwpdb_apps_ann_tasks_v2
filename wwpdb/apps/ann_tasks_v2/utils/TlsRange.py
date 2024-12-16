##
# File:  TlsRange.py
# Date:  16-May-2018  Zukang Feng
#
# Update:
##
"""
Manage utility to correct TLS problems

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


class TlsRange(SessionWebDownloadUtils):
    """
    TlsRange class encapsulates correcting TLS problems.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(TlsRange, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
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

    def run(self, entryId, depFileName, inpFile):
        """Run the calculation"""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath = os.path.join(self.__sessionPath, entryId + "-tls-range.log")
            retPath = os.path.join(self.__sessionPath, entryId + "-tls-correction.cif")
            for filePath in (retPath, logPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            #
            dp.imp(inpPath)
            dp.addInput(name="depfile", value=depFileName)
            dp.op("annot-tls-range-correction")
            dp.expLog(dstPath=logPath, appendMode=False)
            dp.exp(retPath)
            #
            self.addDownloadPath(logPath)
            #
            if os.access(retPath, os.R_OK):
                dp.imp(inpPath)
                dp.addInput(name="tlsfile", value=retPath)
                dp.op("annot-merge-tls-range-data")
                dp.expLog(dstPath=logPath)
                #
                self.__status = self.__checkStatus(logPath)
                if self.__status == "ok":
                    dp.exp(inpPath)
                    self.addDownloadPath(inpPath)
                #
            else:
                self.__status = "error"
            #
            if self.__verbose:
                self.__lfh.write("+TlsRange.run-  completed with status %s for entryId %s file %s\n" % (self.__status, entryId, inpPath))
            #
            dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
        #


if __name__ == "__main__":
    from wwpdb.utils.config.ConfigInfo import ConfigInfo
    from wwpdb.utils.session.WebRequest import InputRequest

    #
    siteId = os.getenv("WWPDB_SITE_ID")
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH"))
    myReqObj.setValue("TopPath", cI.get("SITE_WEB_APPS_TOP_PATH"))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("sessionid", "579d030a7d3cbfa1365c88e2da66702fd2f95d7d")
    #
    calc = TlsRange(reqObj=myReqObj, verbose=True, log=sys.stderr)
    calc.run("D_1000223249", "/wwpdb_da/da_top/data_test/archive/D_1000223249/D_1000223249_model-upload_P1.pdb.V3", "D_1000223249_model_P1.cif")
