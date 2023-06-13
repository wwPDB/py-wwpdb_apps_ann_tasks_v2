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
# 25-May -2023  Using PublicPdbxFile class for generating PDBx/mmCIF file (zf)
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
from wwpdb.apps.ann_tasks_v2.utils.PublicPdbxFile import PublicPdbxFile


class Check(PublicPdbxFile):

    """
    Encapsulates dictioanry-level PDBx/mmCIF checking.

    Operations are performed in the current session context defined in the input
    reqObj().

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(Check, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__reportPath = None
        self.__dictionaryVersion = "V5"
        self.__reportFileSize = 0
        self.__checkArgs = None
        self.__firstBlock = False

    def setDictionaryVersion(self, version):
        if version.upper() in ["V6", "V5", "V4", "DEPOSIT", "ARCHIVE_NEXT", "ARCHIVE_CURRENT"]:
            self.__dictionaryVersion = version.upper()
            return True
        else:
            return False

    def setCheckFirstBlock(self, flag):
        self.__firstBlock = flag

    def setArguments(self, checkArgs):
        self.__checkArgs = checkArgs

    def run(self, entryId, inpPath):  # pylint: disable=unused-argument
        """Run the dictionary-level check on the input PDBx/mmCIF data file -"""
        try:
            self.clearFileList()

            logPath = os.path.join(self._exportPath, entryId + "_dict-check-report.log")
            self.__reportPath = os.path.join(self._exportPath, entryId + "_dict-check-report_P1.txt.V1")
            #
            dp = RcsbDpUtility(tmpPath=self._sessionPath, siteId=self._siteId, verbose=self._verbose, log=self._lfh)
            if self._debug:
                dp.setDebugMode(flag=True)
            #
            if self.__checkArgs is not None:
                dp.addInput(name="check_arguments", value=self.__checkArgs)
            #
            if self.__firstBlock:
                dp.addInput("first_block")
            #
            if self.__dictionaryVersion in ["V5", "DEPOSIT"]:
                dp.imp(inpPath)
                dp.op("check-cif")
            elif self.__dictionaryVersion in ["V4", "ARCHIVE_CURRENT"]:
                cnvInpPath = self.run_conversion("cif2pdbx-public", entryId, inpPath)
                if cnvInpPath is not None:
                    dp.imp(cnvInpPath)
                else:
                    dp.imp(inpPath)
                #
                dp.op("check-cif-v4")
                logPath = os.path.join(self._exportPath, entryId + "_dict-check-report-r4.log")
                self.__reportPath = os.path.join(self._exportPath, entryId + "_dict-check-report-r4_P1.txt.V1")
            elif self.__dictionaryVersion in ["ARCHIVE_NEXT"]:
                cnvInpPath = self.run_conversion("cif2pdbx-ext", entryId, inpPath)
                if cnvInpPath is not None:
                    dp.imp(cnvInpPath)
                else:
                    dp.imp(inpPath)
                #
                dp.op("check-cif-ext")
                dp.addInput(name="dictionary", value="archive_next")
                logPath = os.path.join(self._exportPath, entryId + "_dict-check-report-next.log")
                self.__reportPath = os.path.join(self._exportPath, entryId + "_dict-check-report-next_P1.txt.V1")
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
            #
            if self._verbose:
                self._lfh.write(
                    "+%s.%s dictionary check version %s completed for entryId %s file %s report %s size %d\n"
                    % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self.__dictionaryVersion, entryId, inpPath, self.__reportPath, self.__reportFileSize)
                )
            #
            if self._cleanup:
                dp.cleanup()
            #
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self._verbose:
                self._lfh.write("+%s.%s dictionary check failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath))
            #
            traceback.print_exc(file=self._lfh)
            return False
        #

    def getReportSize(self):
        return self.__reportFileSize

    def getReportPath(self):
        return self.__reportPath
