##
# File:  EmMapCheck.py
# Date:  1-Jun-2023  Zukang Feng
#
# Update:
#
##
"""
Check consistencies between em_map category vs. map files in archival directory

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import os.path
import os
import inspect
import logging

from mmcif.io.IoAdapterCore import IoAdapterCore
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils
from wwpdb.io.locator.PathInfo import PathInfo

logger = logging.getLogger()


class EmMapCheck(SessionWebDownloadUtils):
    """
    Encapsulates checking consistencies between em_map category vs. map files in archival directory

    Operations are performed in the current session context defined in the input
    reqObj().

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(EmMapCheck, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
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

    def run(self, entryId, modelInputFile):
        """Run the format-level check on the input PDBx/mmCIF data file -"""
        logger.debug("About to perform emd-xml check")
        try:
            self.clearFileList()
            #
            self.__reportPath = os.path.join(self.__exportPath, entryId + "_em-map-check-report_P1.txt.V1")
            if os.access(self.__reportPath, os.R_OK):
                os.remove(self.__reportPath)
            #
            checkTask = EmMapCheckTask(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
            checkTask.run(entryId, modelInputFile, self.__reportPath)
            #
            if not os.access(self.__reportPath, os.R_OK):
                return
            #
            self.__reportFileSize = self.__getSize(self.__reportPath)
            if self.__reportFileSize > 0:
                self.addDownloadPath(self.__reportPath)
            #
            if self.__verbose:
                self.__lfh.write(
                    "+%s.%s em_map check completed for entryId %s file %s report %s size %d\n"
                    % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, modelInputFile, self.__reportPath, self.__reportFileSize)
                )
            #
        except Exception as e:
            if self.__verbose:
                logger.error("em_map check failed for entryId %s file %s error: %s", entryId, modelInputFile, str(e))
            #
            logger.exception("Failed to check XML file production")
        #

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
        #


class EmMapCheckTask(object):
    """ """

    def __init__(self, siteId=None, sessionPath=None, verbose=False, log=sys.stderr):
        """ """
        self.__siteId = siteId
        self.__sessionPath = sessionPath
        self.__verbose = verbose
        self.__lfh = log

    def run(self, entryId, modelInputFile, reportPath):
        """ """
        # Test if em_admin present in model
        ioObj = IoAdapterCore(verbose=self.__verbose, log=self.__lfh)
        dIn = ioObj.readFile(inputFilePath=modelInputFile, selectList=["em_admin", "em_map"])
        if not dIn or len(dIn) == 0:
            return
        #
        cObj = dIn[0].getObj("em_admin")
        if not cObj:
            # No em_admin
            return
        else:
            has_deposition_date = False
            valueList = self.__getValueList(cObj)
            for valueD in valueList:
                if ("deposition_date" in valueD) and valueD["deposition_date"]:
                    has_deposition_date = True
                #
            #
            if not has_deposition_date:
                return
            #
        #
        recordedMapList = []
        emMapObj = dIn[0].getObj("em_map")
        if emMapObj:
            valueList = self.__getValueList(emMapObj)
            for valueD in valueList:
                if ("file" in valueD) and valueD["file"]:
                    recordedMapList.append(valueD["file"])
                #
            #
        #
        pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        #
        archivalMapList = []
        for mapType in (
            "em-3d-classification-additional-volume",
            "em-additional-volume",
            "em-alignment-mask-volume",
            "em-focus-refinement-additional-volume",
            "em-focused-refinement-mask-volume",
            "em-fsc-half-mask-volume",
            "em-fsc-map-model-mask-volume",
            "em-half-volume",
            "em-mask-volume",
            "em-raw-volume",
            "em-segmentation-volume",
            "em-volume",
        ):
            partNum = 1
            while True:
                archiveFilePath = pI.getFilePath(
                    dataSetId=entryId, wfInstanceId=None, contentType=mapType, formatType="map", fileSource="archive", versionId="latest", partNumber=str(partNum)
                )
                if (not archiveFilePath) or (not os.access(archiveFilePath, os.F_OK)):
                    break
                #
                (_dir, fileName) = os.path.split(archiveFilePath)
                archivalMapList.append(fileName)
                partNum += 1
            #
        #
        (_dir, modelFileName) = os.path.split(modelInputFile)
        #
        archivePath = pI.getArchivePath(dataSetId=entryId)
        oth = open(reportPath, "w")
        for mapFileName in recordedMapList:
            if os.access(os.path.join(archivePath, mapFileName), os.F_OK):
                continue
            #
            oth.write("Map file '%s' defined in 'em_map' category of model file '%s' can not be found in archive directory.\n" % (mapFileName, modelFileName))
        #
        for mapFileName in archivalMapList:
            if mapFileName in recordedMapList:
                continue
            #
            oth.write("Map file '%s' is not included in 'em_map' category of model file '%s'.\n" % (mapFileName, modelFileName))
        #
        oth.close()

    def __getValueList(self, catObj):
        """ """
        valueList = []
        attribList = catObj.getAttributeList()
        rowList = catObj.getRowList()
        for rowD in rowList:
            tD = {}
            for idxIt, itName in enumerate(attribList):
                if rowD[idxIt] != "?" and rowD[idxIt] != ".":
                    tD[itName] = rowD[idxIt]
            #
            if tD:
                valueList.append(tD)
            #
        #
        return valueList
