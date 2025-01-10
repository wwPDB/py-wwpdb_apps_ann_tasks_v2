##
# File:  EmAutoFix.py
# Date:  17-Jun-2019  E Peisach
#
# Update:
##
"""
Auto runs mapfix on maps specified in em_map category

"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"

import sys
import os.path
import os
import json
import logging
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from mmcif.io.IoAdapterCore import IoAdapterCore
from wwpdb.io.locator.PathInfo import PathInfo

logger = logging.getLogger()


class EmAutoFix(object):
    def __init__(self, sessionPath, siteId=None, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__siteId = siteId
        self.__sessionPath = sessionPath
        self.__cleanup = True
        self.__pI = PathInfo(sessionPath=sessionPath, verbose=self.__verbose, log=self.__lfh)
        self.__mD = {"primary map": "em-volume", "mask": "em-mask-volume", "additional map": "em-additional-volume", "half map": "em-half-volume", "map header": "em-volume-header"}

    @staticmethod
    def __getEmdDbCode(blockobj):
        """Return the database code for EMDB.  Returns None is
        EMDB id not present.
        """
        try:
            catObj = blockobj.getObj("database_2")
            vals = catObj.selectValuesWhere("database_code", "EMDB", "database_id")
            if len(vals):
                return vals[0]
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        return None

    def __mapfix(self, depsetid, emdbid, volin, volout, voxel):
        resultPath = os.path.join(self.__sessionPath, depsetid + "_mapfix-header-report_P1.json")
        logPath = os.path.join(self.__sessionPath, depsetid + "_mapfix-report_P1.txt")
        for filePath in (resultPath, logPath):
            if os.access(filePath, os.R_OK):
                os.remove(filePath)
            #
        #
        dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        dp.setDebugMode(flag=True)
        dp.addInput(name="input_map_file_path", value=volin, type="file")
        dp.addInput(name="output_map_file_path", value=volout, type="file")
        dp.addInput(name="label", value=emdbid)
        dp.addInput(name="voxel", value=voxel)
        dp.op("annot-update-map-header-in-place")
        dp.expLog(logPath)
        dp.exp(resultPath)

        if self.__cleanup:
            dp.cleanup()
        #
        return resultPath

    def autoFixMapLabels(self, datasetid, modelin, modelout, vollocation="archive"):
        """For a given deposition id, takes em_map category from latest model file at modellocation, and if EMDB id
        is not in the em_map labels, will run mapfix to update.

        Assumptions - which hold true in June 2019
        o Model file is authoritative for voxel spacing
        o If depositor uploads new model file, the label in em_map will revert to the D_xxxxx version.
        o File type is always 'map'

        Returns True is model & volumes updated
        Returns False if not adjustment made to model file
        """

        logger.info("Checking for map updates to %r", modelin)

        # Parse model file
        ioobj = IoAdapterCore()
        c0 = ioobj.readFile(inputFilePath=modelin)

        block0 = c0[0]

        # Is there an em_map category?

        # block0.printIt()
        emdbid = self.__getEmdDbCode(block0)
        if not emdbid:
            logger.info("No emdb id")
            return False

        tobj = block0.getObj("em_map")
        if not tobj:
            logger.info("No em_map category - done")
            return False

        updated = False
        for row in range(tobj.getRowCount()):
            label = tobj.getValue("label", row)
            map_type = tobj.getValue("type", row)
            partition = tobj.getValue("partition", row)
            pixel_x = tobj.getValue("pixel_spacing_x", row)
            pixel_y = tobj.getValue("pixel_spacing_y", row)
            pixel_z = tobj.getValue("pixel_spacing_z", row)

            if emdbid in label:
                continue

            logger.info("Updating %r part %r label %r", map_type, partition, label)
            ctxtype = self.__mD.get(map_type, None)
            if not ctxtype:
                logger.error("Unknown map type %s", map_type)
                continue

            volin = self.__pI.getFilePath(dataSetId=datasetid, contentType=ctxtype, formatType="map", fileSource=vollocation, partNumber=partition, versionId="latest")
            volout = self.__pI.getFilePath(dataSetId=datasetid, contentType=ctxtype, formatType="map", fileSource=vollocation, partNumber=partition, versionId="next")
            logger.debug("Updating %s to %s", volin, volout)
            ####
            rep = self.__mapfix(datasetid, emdbid, volin, volout, "{} {} {}".format(pixel_x, pixel_y, pixel_z))
            if not os.path.exists(volout):
                logger.error("Output path %s does not exist", volout)
                continue
            # Get label from report
            with open(rep, "r") as fin:
                mrep = json.load(fin)
                labelnew = mrep["output_header_long"]["label"]
                tobj.setValue(value=labelnew, attributeName="label", rowIndex=row)
                # Update filename in em_map
                newname = self.__pI.getFileName(dataSetId=datasetid, contentType=ctxtype, formatType="map", fileSource=vollocation, partNumber=partition, versionId="latest")
                tobj.setValue(value=newname, attributeName="file", rowIndex=row)

            updated = True

        if updated:
            logger.info("Model file updated")

            # Write model
            ret = ioobj.writeFile(outputFilePath=modelout, containerList=c0)
            logger.info("Writing file returns %s %s", ret, modelout)
            return True

        return False


if __name__ == "__main__":
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    pI = PathInfo(sessionPath="/tmp")

    dep = "D_800037"
    modellocation = "archive"
    modin = pI.getModelPdbxFilePath(dataSetId=dep, fileSource=modellocation)
    modout = pI.getModelPdbxFilePath(dataSetId=dep, fileSource=modellocation, versionId="next")
    ema = EmAutoFix(sessionPath="/tmp")
    ema.autoFixMapLabels(datasetid=dep, modelin=modin, modelout=modout)
