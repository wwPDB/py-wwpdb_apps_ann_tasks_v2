##
# File:  Check.py
# Date:  10-Sep-2012  J. Westbrook
#
# Update:
#  2-July-2012  Add entry point for dictionary level checking.
# 29-Dec -2013  Generalized for sharing and api standardized.
# 28-Feb -2014  add base class
#  1-Feb -2015  include pre-dictionary dialect conversion before V4 dicitonary check
# 29-Nov -2016  Include support for new naming and extended checks (still using old rcsbDpUtilities for now (ep)
##
"""
Dictionary-level PDBx/mmCIF checking

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
import inspect

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class Check(SessionWebDownloadUtils):

    """
    Encapsulates dictioanry-level PDBx/mmCIF checking.

    Operations are performed in the current session context defined in the input
    reqObj().

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(Check, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__debug = False
        self.__reportPath = None
        self.__dictionaryVersion = "V5"
        self.__reportFileSize = 0
        self.__checkArgs = None
        self.__exportPath = None
        self.__firstBlock = False

        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__exportPath = self.__sessionPath
        self.__cleanup = False

    def setDictionaryVersion(self, version):
        if version.upper() in ["V6", "V5", "V4", "DEPOSIT", "ARCHIVE_NEXT", "ARCHIVE_CURRENT"]:
            self.__dictionaryVersion = version.upper()
            return True
        else:
            return False

    def setCheckFirstBlock(self, flag):
        self.__firstBlock = flag

    def setExportPath(self, exportPath):
        """Set the path where output files are copyied."""
        self.__exportPath = exportPath

    def setArguments(self, checkArgs):
        self.__checkArgs = checkArgs

    def __cnv(self, entryId, inpPath):
        try:
            logPath = os.path.join(self.__exportPath, entryId + "_cif2pdbx-pubic.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            pdbxPath = os.path.join(self.__exportPath, entryId + "_model-v4-pubic_P1.cif")
            if os.access(pdbxPath, os.R_OK):
                os.remove(pdbxPath)
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            if self.__debug:
                dp.setDebugMode(flag=True)
            dp.imp(inpPath)
            dp.op("cif2pdbx-public")
            dp.exp(pdbxPath)
            dp.expLog(logPath)
            #
            self.addDownloadPath(logPath)
            self.addDownloadPath(pdbxPath)

            if self.__verbose:
                self.__lfh.write("+%s.%s  creating public cif for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath))

            if self.__cleanup:
                dp.cleanup()

            return pdbxPath
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write(
                    "+%s.%s public cif conversion failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath)
                )
                traceback.print_exc(file=self.__lfh)
        return None

    def __cnvNext(self, entryId, inpPath):
        try:
            logPath = os.path.join(self.__exportPath, entryId + "_cif2pdbx-next.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            pdbxPath = os.path.join(self.__exportPath, entryId + "_model-next_P1.cif")
            if os.access(pdbxPath, os.R_OK):
                os.remove(pdbxPath)
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            if self.__debug:
                dp.setDebugMode(flag=True)
            dp.imp(inpPath)
            dp.addInput(name="destination", value="archive_next")
            dp.op("cif2pdbx-ext")
            dp.exp(pdbxPath)
            dp.expLog(logPath)
            #
            self.addDownloadPath(logPath)
            self.addDownloadPath(pdbxPath)

            if self.__verbose:
                self.__lfh.write("+%s.%s  creating test cif for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath))

            if self.__cleanup:
                dp.cleanup()

            return pdbxPath
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+%s.%s test cif conversion failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath))
                traceback.print_exc(file=self.__lfh)
        return None

    def run(self, entryId, inpPath, updateInput=True):  # pylint: disable=unused-argument
        """Run the dictionary-level check on the input PDBx/mmCIF data file -"""
        try:
            self.clearFileList()

            logPath = os.path.join(self.__exportPath, entryId + "_dict-check-report.log")
            self.__reportPath = os.path.join(self.__exportPath, entryId + "_dict-check-report_P1.txt.V1")
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            if self.__debug:
                dp.setDebugMode(flag=True)
            if self.__checkArgs is not None:
                dp.addInput(name="check_arguments", value=self.__checkArgs)
            if self.__firstBlock:
                dp.addInput("first_block")

            if self.__dictionaryVersion in ["V5", "DEPOSIT"]:
                dp.imp(inpPath)
                dp.op("check-cif")

            elif self.__dictionaryVersion in ["V4", "ARCHIVE_CURRENT"]:
                cnvInpPath = self.__cnv(entryId, inpPath)
                if cnvInpPath is not None:
                    dp.imp(cnvInpPath)
                else:
                    dp.imp(inpPath)
                dp.op("check-cif-v4")
                logPath = os.path.join(self.__exportPath, entryId + "_dict-check-report-r4.log")
                self.__reportPath = os.path.join(self.__exportPath, entryId + "_dict-check-report-r4_P1.txt.V1")

            elif self.__dictionaryVersion in ["ARCHIVE_NEXT"]:
                cnvInpPath = self.__cnvNext(entryId, inpPath)
                if cnvInpPath is not None:
                    dp.imp(cnvInpPath)
                else:
                    dp.imp(inpPath)
                dp.op("check-cif-ext")
                dp.addInput(name="dictionary", value="archive_next")
                logPath = os.path.join(self.__exportPath, entryId + "_dict-check-report-next.log")
                self.__reportPath = os.path.join(self.__exportPath, entryId + "_dict-check-report-next_P1.txt.V1")

            elif self.__dictionaryVersion in ["V6"]:
                dp.imp(inpPath)
                dp.op("check-cif-v6")
            else:
                dp.imp(inpPath)
                dp.op("check-cif")
            #
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            if os.access(self.__reportPath, os.R_OK):
                os.remove(self.__reportPath)
            #
            dp.expLog(logPath)
            #
            self.__reportFileSize = dp.expSize()
            if self.__reportFileSize > 0:
                dp.exp(self.__reportPath)
                self.addDownloadPath(self.__reportPath)
            #
            self.addDownloadPath(logPath)

            if self.__verbose:
                self.__lfh.write(
                    "+%s.%s dictionary check version %s completed for entryId %s file %s report %s size %d\n"
                    % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self.__dictionaryVersion, entryId, inpPath, self.__reportPath, self.__reportFileSize)
                )

            if self.__cleanup:
                dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+%s.%s dictionary check failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath))
            traceback.print_exc(file=self.__lfh)
            return False

    def getReportSize(self):
        return self.__reportFileSize

    def getReportPath(self):
        return self.__reportPath
