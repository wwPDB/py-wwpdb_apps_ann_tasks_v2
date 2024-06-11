"""
Runs the operation to detect CCDs missing PCM annotation

"""
import sys
import os.path
import os
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class CheckCCDAnnotation(SessionWebDownloadUtils):
    """
    The CheckCCDAnnotation class encapsulates the calculation of geometrical features of nucleic acid polymers.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(CheckCCDAnnotation, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
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
        """Check CCDs missing PCM annotation and update the model file."""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath1 = os.path.join(self.__sessionPath, entryId + "-na-anal.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
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
            if updateInput:
                dp.exp(inpPath)
            if self.__verbose:
                self.__lfh.write("+CheckCCDAnnotation.run-  completed for entryId %s file %s\n" % (entryId, inpPath))

            dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
