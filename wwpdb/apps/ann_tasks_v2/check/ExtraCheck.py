##
# File:  ExtraCheck.py
# Date:  15-Aug-213  J. Westbrook
#
# Update:
#
# 29-Dec -2013  Generalized for sharing and api standardized.
# 28-Feb -2014  Add base class
##
"""
Extra  PDBx/mmCIF checking

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import shutil
import sys
import os.path
import os
import inspect
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class ExtraCheck(SessionWebDownloadUtils):
    """
    The Check class encapsulates dictioanry-level PDBx/mmCIF checking

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(ExtraCheck, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__exportPath = None
        self.__checkArgs = None
        self.__cleanup = True
        self.__reportFileSize = 0
        self.__reportPath = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__exportPath = self.__sessionPath

    def setArguments(self, checkArgs):
        self.__checkArgs = checkArgs

    def setExportPath(self, exportPath):
        """Set the path where output files are copyied."""
        self.__exportPath = exportPath

    def run(self, entryId, inpPath, updateInput=True):  # pylint: disable=unused-argument
        """Run the extra checks on the input PDBx/mmCIF data file -"""
        try:
            self.clearFileList()
            logPath = os.path.join(self.__exportPath, entryId + "_misc-check-report.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            self.__reportPath = os.path.join(self.__exportPath, entryId + "_misc-check-report_P1.txt.V1")
            if os.access(self.__reportPath, os.R_OK):
                os.remove(self.__reportPath)
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            if self.__checkArgs is not None:
                dp.addInput(name="check_arguments", value=self.__checkArgs)
            dp.op("annot-extra-checks")
            dp.expLog(logPath)
            #
            self.__reportFileSize = dp.expSize()
            if self.__reportFileSize > 0:
                dp.exp(self.__reportPath)
            else:
                if os.access(logPath, os.R_OK):
                    ifh = open(logPath, "r")
                    data = ifh.read()
                    ifh.close()
                    if not str(data).startswith("Finished!"):
                        shutil.copyfile(logPath, self.__reportPath)
                    #
                else:
                    ofh = open(self.__reportPath, "w")
                    ofh.write("Miscellaneous check failed.\n")
                    ofh.close()
                #
                statinfo = os.stat(self.__reportPath)
                self.__reportFileSize = statinfo.st_size
            #
            if self.__verbose:
                self.__lfh.write(
                    "+%s.%s extra check completed for entryId %s file %s report size %d\n"
                    % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath, self.__reportFileSize)
                )
            self.addDownloadPath(self.__reportPath)
            self.addDownloadPath(logPath)
            if self.__cleanup:
                dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+%s.%s extra check failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath))
            traceback.print_exc(file=self.__lfh)
            return False

    def getReportSize(self):
        return self.__reportFileSize

    def getReportPath(self):
        return self.__reportPath
