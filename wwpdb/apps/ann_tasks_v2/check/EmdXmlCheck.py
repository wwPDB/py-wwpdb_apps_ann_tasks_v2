##
# File:  EmdXmlCheck.py
# Date:  20-Oct-2019  E. Peisach
#
# Update:
#
##
"""
EMD XML generation check

"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import os.path
import os
import logging

from wwpdb.apps.ann_tasks_v2.em3d.EmHeaderUtils import EmHeaderUtils
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils
from mmcif.io.IoAdapterCore import IoAdapterCore

logger = logging.getLogger()


class EmdXmlCheck(SessionWebDownloadUtils):
    """
    Encapsulates checking of EMD XML generation

    Operations are performed in the current session context defined in the input
    reqObj().

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(EmdXmlCheck, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__exportPath = None
        self.__checkArgs = None  # pylint: disable=unused-private-member
        self.__reportFileSize = 0
        self.__reportPath = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__exportPath = self.__sessionPath

    def setExportPath(self, exportPath):
        """Set the path where output files are copyied."""
        self.__exportPath = exportPath

    def setArguments(self, checkArgs):
        self.__checkArgs = checkArgs  # pylint: disable=unused-private-member

    # def __logerr(self, errstr):
    #     """Writes to the report log"""
    #     if self.__reportPath:
    #         with open(self.__reportPath, "a") as fout:
    #             fout.write("%s\n" % errstr)
    #         self.__reportFileSize = self.__getSize(self.__reportPath)
    #     else:
    #         logger.error("Trying to log %s but reportPath not set!", errstr)

    def run(self, entryId, modelInputFile):
        """Run the format-level check on the input PDBx/mmCIF data file -"""
        logger.debug("About to perform emd-xml check")
        try:
            self.clearFileList()
            logPath = os.path.join(self.__exportPath, entryId + "_emd-check-report.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            self.__reportPath = os.path.join(self.__exportPath, entryId + "_emd-xml-header-report_P1.txt.V1")
            if os.access(self.__reportPath, os.R_OK):
                os.remove(self.__reportPath)
            #

            # Test if em_admin present in model
            ioObj = IoAdapterCore(verbose=self.__verbose, log=self.__lfh)
            dIn = ioObj.readFile(inputFilePath=modelInputFile, selectList=["em_admin"])
            if not dIn or len(dIn) == 0:
                return True

            cObj = dIn[0].getObj("em_admin")
            if not cObj:
                # No em_admin
                return True

            emh = EmHeaderUtils(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            #
            # Convert model to emd
            # emdModelPath = os.path.join(self.__exportPath, entryId + "_model-emd.cif")
            # if os.access(emdModelPath, os.R_OK):
            #     os.remove(emdModelPath)

            # status = emh.transEmd(modelInputFile, emdModelPath, mode="src-dst", tags=[])
            # if not status:
            #     self.__logerr("Conversion of EM_ to EMD failed")
            #     return False

            # if self.__getSize(emdModelPath):
            #     self.addDownloadPath(emdModelPath)

            # Generate XML
            emdXmlPath = os.path.join(self.__exportPath, entryId + "-emd.xml")
            if os.access(emdXmlPath, os.R_OK):
                os.remove(emdXmlPath)

            status = emh.transHeader(modelInputFile, emdXmlPath, self.__reportPath, validateXml=True)
            logger.debug("Status of translation %s", status)

            if self.__getSize(emdXmlPath):
                self.addDownloadPath(emdXmlPath)

            self.__reportFileSize = self.__getSize(self.__reportPath)

            return True
        except Exception as e:
            if self.__verbose:
                logger.error("emd xml header check failed for entryId %s file %s error: %s", entryId, modelInputFile, str(e))
            logger.exception("Failed to check XML file production")
            return False

    def getReportSize(self):
        return self.__reportFileSize

    def getReportPath(self):
        return self.__reportPath

    def __getSize(self, fn):
        try:
            statInfo = os.stat(fn)
            return statInfo.st_size
        except:  # noqa: E722 pylint: disable=bare-except
            return 0
