##
# File:  Validate.py
# Date:  10-Sep-2012  J. Westbrook
#
# Update:
#  2-July-2012  Add entry point for running validation processing
# 13-Dec-2012   Move to validation report v2
# 24-Jan-2014   Move to validation report alt -
# 28-Feb -2014  Add base class
# 16-Sep-2015   Supporting all exp methods --
# 14-July-2016 jdw add validation_mode="annotate" as an optional argument
# 18-Dec-2016  ep Remove obsolete RunAlt and Run...
# 30-Jun-2020  zk added validation-report-images output
##
"""
Manage invoking validation processing -

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import shutil
import sys
import traceback

from wwpdb.utils.dp.ValidationWrapper import ValidationWrapper
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils
from wwpdb.apps.ann_tasks_v2.utils.NmrRemediationUtils import remediate_cs_file, starToPdbx


class Validate(SessionWebDownloadUtils):
    """
    The Validate class launches the validation processing and recovers reports and logs

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(Validate, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__validateArgs = None
        self.__cleanup = False
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def setArguments(self, validateArgs):
        self.__validateArgs = validateArgs

    def run(self, entryId, modelInputFile=None, expInputFile=None, updateInput=True):
        """Old entry point. Believed not in use..."""
        ret = self.runAll(entryId, modelInputFile=modelInputFile, reflnInputFile=expInputFile, updateInput=updateInput)
        return ret

    def runAll(
        self,
        entryId,
        pdb_id=None,
        modelInputFile=None,
        reflnInputFile=None,
        csInputFile=None,
        volInputFile=None,
        authorFscFile=None,
        restraintInputFile=None,
        updateInput=True,
        annotationContext=False,
        validation_mode="annotate",
    ):  # pylint: disable=unused-argument
        """Run the validation operation for all supported methods"""
        uploadVersionOp = "none"
        try:
            pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
            if modelInputFile is None:
                modelFileName = pI.getFileName(entryId, contentType="model", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
                inpPath = os.path.join(self.__sessionPath, modelFileName)
            else:
                inpPath = os.path.join(self.__sessionPath, modelInputFile)

            if reflnInputFile is None:
                reflnFileName = pI.getFileName(entryId, contentType="structure-factors", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
                sfPath = os.path.join(self.__sessionPath, reflnFileName)
            else:
                sfPath = os.path.join(self.__sessionPath, reflnInputFile)

            nmrdata = False
            if csInputFile is None:
                csFileName = pI.getFileName(entryId, contentType="nmr-data-str", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
                csPath = os.path.join(self.__sessionPath, csFileName)
                nmrdata = True
                if not os.access(csPath, os.R_OK):
                    # Fallback on cs file
                    csFileName = pI.getFileName(entryId, contentType="nmr-chemical-shifts", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
                    csPath = os.path.join(self.__sessionPath, csFileName)
                    nmrdata = False
            else:
                csPath = os.path.join(self.__sessionPath, csInputFile)
            #
            # Redmediate legacy CS files 2022-12-05
            if nmrdata is False and os.access(csPath, os.R_OK):
                tmpfile1 = csPath + ".str"
                tmpfile2 = csPath + ".cif"
                remediate_cs_file(csPath, tmpfile1)
                starToPdbx(tmpfile1, tmpfile2)
                csPath = tmpfile2

            if restraintInputFile is None:
                restraintFileName = pI.getFileName(entryId, contentType="nmr-data-str", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
                resPath = os.path.join(self.__sessionPath, restraintFileName)
            else:
                resPath = os.path.join(self.__sessionPath, restraintInputFile)
            #
            if volInputFile is None or not volInputFile:
                volPath = pI.getEmVolumeFilePath(entryId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None)
            else:
                volPath = os.path.join(pI.getArchivePath(entryId), volInputFile)
            if authorFscFile is None or not authorFscFile:
                authorFscPath = pI.getFileName(entryId, contentType="fsc", formatType="xml", versionId=uploadVersionOp, partNumber="1")
            else:
                authorFscPath = os.path.join(pI.getArchivePath(entryId), authorFscFile)
            #
            # Will not look for restraint file
            #
            fName = pI.getFileName(entryId, contentType="validation-report", formatType="pdf", versionId=uploadVersionOp, partNumber="1")
            resultPdfPath = os.path.join(self.__sessionPath, fName)

            fName = pI.getFileName(entryId, contentType="validation-report-full", formatType="pdf", versionId=uploadVersionOp, partNumber="1")
            resultFullPdfPath = os.path.join(self.__sessionPath, fName)

            fName = pI.getFileName(entryId, contentType="validation-data", formatType="xml", versionId=uploadVersionOp, partNumber="1")
            resultXmlPath = os.path.join(self.__sessionPath, fName)

            fName = pI.getFileName(entryId, contentType="validation-report-slider", formatType="png", versionId=uploadVersionOp, partNumber="1")
            resultPngPath = os.path.join(self.__sessionPath, fName)

            fName = pI.getFileName(entryId, contentType="validation-report-slider", formatType="svg", versionId=uploadVersionOp, partNumber="1")
            resultSvgPath = os.path.join(self.__sessionPath, fName)

            fName = pI.getFileName(entryId, contentType="validation-report-images", formatType="tar", versionId=uploadVersionOp, partNumber="1")
            resultImageTarPath = os.path.join(self.__sessionPath, fName)

            fName = pI.getFileName(entryId, contentType="validation-data", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
            resultCifPath = os.path.join(self.__sessionPath, fName)

            fName = pI.getFileName(entryId, contentType="validation-report-2fo-map-coef", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
            result2FoPath = os.path.join(self.__sessionPath, fName)

            fName = pI.getFileName(entryId, contentType="validation-report-fo-map-coef", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
            resultFoPath = os.path.join(self.__sessionPath, fName)
            #
            logPath = os.path.join(self.__sessionPath, entryId + "_val-report.log")
            #
            dp = ValidationWrapper(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)

            dp.addInput(name="entry_id", value=entryId)

            rundir = os.path.join(self.__sessionPath, "LVW_" + entryId.upper())
            if os.access(rundir, os.F_OK):
                shutil.rmtree(rundir)
            #
            os.makedirs(rundir)
            dp.addInput(name="run_dir", value=rundir)

            if os.access(sfPath, os.R_OK):
                dp.addInput(name="sf_file_path", value=sfPath)

            if os.access(csPath, os.R_OK):
                dp.addInput(name="cs_file_path", value=csPath)

            if os.access(resPath, os.R_OK):
                dp.addInput(name="nmr_restraint_file_path", value=csPath)

            if os.access(volPath, os.R_OK):
                dp.addInput(name="vol_file_path", value=volPath)

            if os.access(authorFscPath, os.R_OK):
                dp.addInput(name="fsc_file_path", value=authorFscPath)

            #
            if annotationContext:
                dp.addInput(name="request_annotation_context", value="yes")
            if validation_mode is not None:
                dp.addInput(name="request_validation_mode", value="annotate")
            #
            if self.__validateArgs is not None:
                dp.addInput(name="validate_arguments", value=self.__validateArgs)
            dp.op("annot-wwpdb-validate-all-sf")
            dp.expLog(logPath)
            dp.expList(dstPathList=[resultPdfPath, resultXmlPath, resultFullPdfPath, resultPngPath, resultSvgPath, resultImageTarPath, resultCifPath, resultFoPath, result2FoPath])

            self.addDownloadPath(resultPdfPath)
            self.addDownloadPath(resultXmlPath)
            self.addDownloadPath(resultFullPdfPath)
            self.addDownloadPath(resultPngPath)
            self.addDownloadPath(resultSvgPath)
            self.addDownloadPath(resultImageTarPath)
            self.addDownloadPath(resultCifPath)
            self.addDownloadPath(resultFoPath)
            self.addDownloadPath(result2FoPath)
            self.addDownloadPath(logPath)
            #
            if self.__verbose:
                self.__lfh.write("+Validate.runAll-  completed for entryId %s file %s\n" % (entryId, inpPath))

            if self.__cleanup:
                dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+Validate.runAll-  failed with exception for entryId %s\n" % entryId)

            traceback.print_exc(file=self.__lfh)
            return False
