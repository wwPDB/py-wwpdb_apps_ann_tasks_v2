##
# File:  NmrChemShiftsUtils.py
# Date:  15-Sep-2014  J. Westbrook
#
# Update:
#  1-Oct-2014  jdw add  runUpdate(self,entryId,csInpFilePath,xyzFilePath,csOutFilePath)
##
"""
Chemical shift format conversion and nomenclature update tools --

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os
import inspect
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils
from wwpdb.utils.dp.PdbxChemShiftReport import PdbxChemShiftReport
from wwpdb.io.locator.PathInfo import PathInfo


class NmrChemShiftsUtils(SessionWebDownloadUtils):
    """
    NmrChemShiftsUtils class encapsulates format conversion and nomenclature update tasks --

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(NmrChemShiftsUtils, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        #
        self.__authFilePathList = []
        self.__authNameList = []
        self.__status = "none"
        self.__warnings = ""
        self.__errors = ""
        self.__cleanUp = True
        self.__sessionPath = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #

    def getLastStatus(self):
        return self.__status

    def setAuthFiles(self, authFilePathList, authNameList=None):
        """Input list of author provided CS file paths and optionally an name associated with each."""
        self.__authFilePathList = authFilePathList
        self.__authNameList = authNameList
        return True

    def runPrep(self, entryId):
        """Prepare a list of author chemical shift files for subsequent checking --

        'nmr-chemical-shifts-upload-report'
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)

            dp.addInput(name="chemical_shifts_file_path_list", value=self.__authFilePathList)
            dp.addInput(name="chemical_shifts_auth_file_name_list", value=self.__authNameList)
            pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
            # Output chemical shift file
            csFilePath = pI.getChemcialShiftsFilePath(entryId, formatType="pdbx", fileSource="session", versionId="none", mileStone=None)
            # outPath=os.path.join(self.__sessionPath, entryId + "_cs_P1.cif")
            logPath = os.path.join(self.__sessionPath, entryId + "-annot-chem-shifts-upload-check.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            chkPath = os.path.join(self.__sessionPath, entryId + "_nmr-chemical-shifts-upload-report_P1.cif")
            dp.addInput(name="chemical_shifts_upload_check_file_path", value=chkPath)

            dp.op("annot-chem-shifts-upload-check")
            dp.expLog(logPath)
            dp.exp(csFilePath)
            #
            wPath = os.path.join(self.__sessionPath, "Warnings-combine.txt")
            ePath = os.path.join(self.__sessionPath, "Errors-combine.txt")
            self.__processReport(chkPath, wPath, ePath)

            self.addDownloadPath(chkPath)
            self.addDownloadPath(logPath)
            self.addDownloadPath(csFilePath)

            if self.__cleanUp:
                dp.cleanup()
            #
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        return False

    def runAtomNameCheck(self, entryId, csInpFilePath, xyzFilePath, csOutFilePath):
        """Run atom name check on the current session chemical shift file.  Note that this file must
        contain the data context created in the preceding preparation step runPrep().

        A report with content type 'nmr-chemical-shifts-atom-name-report' is created and parsed.
        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            #
            dp.imp(csInpFilePath)
            # current session model path -
            dp.addInput(name="coordinate_file_path", value=xyzFilePath)
            #
            logPath = os.path.join(self.__sessionPath, entryId + "-chem-shifts-atom-name-check.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            chkPath = os.path.join(self.__sessionPath, entryId + "_nmr-chemical-shifts-atom-name-report_P1.cif")

            dp.addInput(name="chemical_shifts_coord_check_file_path", value=chkPath)

            dp.op("annot-chem-shifts-atom-name-check")
            dp.expLog(logPath)
            dp.exp(csOutFilePath)
            #
            wPath = os.path.join(self.__sessionPath, "Warnings-atom-name.txt")
            ePath = os.path.join(self.__sessionPath, "Errors-atom-name.txt")
            self.__processReport(chkPath, wPath, ePath)
            #
            self.addDownloadPath(chkPath)
            self.addDownloadPath(logPath)
            self.addDownloadPath(csOutFilePath)
            #
            if self.__cleanUp:
                dp.cleanup()
            #
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        return False

    def runUpdate(self, entryId, csInpFilePath, xyzFilePath, csOutFilePath):
        """Update chemical shift atom naming relative to any changes in the coordinate model.
        This operation acts on chemical shift files that are in PDBx format and have been
        preprocessed with to contain original atom nomenclature details.

        """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            #
            dp.imp(csInpFilePath)
            # current session model path -
            dp.addInput(name="coordinate_file_path", value=xyzFilePath)
            #
            logPath = os.path.join(self.__sessionPath, entryId + "-chem-shifts-update.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            dp.op("annot-chem-shifts-update")
            dp.expLog(logPath)
            dp.exp(csOutFilePath)
            #
            self.addDownloadPath(logPath)
            self.addDownloadPath(csOutFilePath)
            #
            if self.__cleanUp:
                dp.cleanup()
            #
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        return False

    def __processReport(self, chkPath, warningPath=None, errorPath=None):
        try:
            csr = PdbxChemShiftReport(inputPath=chkPath, verbose=self.__verbose, log=self.__lfh)
            #
            self.__status = csr.getStatus()
            self.__lfh.write("Status code: %s\n" % self.__status)

            self.__warnings = csr.getWarnings()
            self.__lfh.write("\n\nWarning count : %d\n %s\n" % (len(self.__warnings), ("\n").join(self.__warnings)))
            if len(self.__warnings) > 0 and warningPath is not None:
                ofh = open(warningPath, "w")
                ofh.write("%s" % ("\n").join(self.__warnings))
                ofh.close()
                self.addDownloadPath(warningPath)
            #
            self.__errors = csr.getErrors()
            self.__lfh.write("\n\nError count : %d\n %s\n" % (len(self.__errors), ("\n").join(self.__errors)))
            if len(self.__errors) > 0 and errorPath is not None:
                ofh = open(errorPath, "w")
                ofh.write("%s" % ("\n").join(self.__errors))
                ofh.close()
                self.addDownloadPath(errorPath)
            #
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
