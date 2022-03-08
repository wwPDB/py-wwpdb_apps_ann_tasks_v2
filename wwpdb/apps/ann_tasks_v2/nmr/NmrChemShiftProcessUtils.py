##
# File:  NmrChemShiftProcessUtils.py
# Date:  18-Sep-2018  Zukang Feng
#
##
"""
Chemical shift nomenclature checking and update tools --

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import json
import os
import sys
import time
import inspect
import traceback

from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class NmrChemShiftProcessUtils(object):
    """
    NmrChemShiftProcessUtils class encapsulates chemical shift nomenclature checking and update tools

    """

    def __init__(self, siteId="WWPDB_DEPLOY_TEST", verbose=False, log=sys.stderr):
        """ """
        self.__siteId = siteId
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__systemLogMessage = ""
        self.__checkReportFilePath = ""
        #
        self.__workingDirPath = "."
        self.__inModelFilePath = ""
        self.__inCsFilePath = ""
        self.__inNefFilePath = ""
        self.__outModelFilePath = ""
        self.__outCsFilePath = ""
        self.__outNefFilePath = ""
        self.__outReportFilePath = ""
        self.__validationResultPath = []

    def setWorkingDirPath(self, dirPath=""):
        """Set working dir path"""
        self.__workingDirPath = dirPath

    def setIdentifier(self, identifier=""):
        """Set entry identifier and create file names in current workingDirPath"""
        pI = PathInfo(siteId=self.__siteId, sessionPath=self.__workingDirPath, verbose=self.__verbose, log=self.__lfh)
        #
        fileName = pI.getFileName(identifier, contentType="model", formatType="pdbx", versionId="none", partNumber="1")
        filePath = os.path.join(self.__workingDirPath, fileName)
        if os.access(filePath, os.R_OK):
            self.__inModelFilePath = filePath
            self.__outModelFilePath = filePath
        #
        fileName = pI.getFileName(identifier, contentType="nmr-chemical-shifts", formatType="pdbx", versionId="none", partNumber="1")
        filePath = os.path.join(self.__workingDirPath, fileName)
        if os.access(filePath, os.R_OK):
            self.__inCsFilePath = filePath
            self.__outCsFilePath = filePath
        #
        fileName = pI.getFileName(identifier, contentType="nmr-shift-error-report", formatType="json", versionId="none", partNumber="1")
        self.__outReportFilePath = os.path.join(self.__workingDirPath, fileName)
        #
        self.__validationResultPath = []
        for contentFormatType in (
            ("validation-report", "pdf"),
            ("validation-data", "xml"),
            ("validation-report-full", "pdf"),
            ("validation-report-slider", "png"),
            ("validation-report-slider", "svg"),
            ("validation-report-images", "tar"),
            ("validation-data", "pdbx"),
        ):
            fileName = pI.getFileName(identifier, contentType=contentFormatType[0], formatType=contentFormatType[1], versionId="none", partNumber="1")
            self.__validationResultPath.append(os.path.join(self.__workingDirPath, fileName))
        #

    def setInputModelFileName(self, fileName=""):
        """Set input model file name"""
        self.__inModelFilePath = fileName

    def setInputCsFileName(self, fileName=""):
        """Set input chemical shift file name"""
        self.__inCsFilePath = fileName

    def setInputNefFileName(self, fileName=""):
        """Set input nef file name"""
        self.__inNefFilePath = fileName

    def setOutputModelFileName(self, fileName=""):
        """Set output model file name"""
        self.__outModelFilePath = fileName

    def setOutputCsFileName(self, fileName=""):
        """Set output chemical shift file name"""
        self.__outCsFilePath = fileName

    def setOutputNefFileName(self, fileName=""):
        """Set output nef file name"""
        self.__outNefFilePath = fileName

    def setOutputReportFileName(self, fileName=""):
        """Set output chemical shift atom name report file name"""
        self.__outReportFilePath = fileName

    def setOutputValidationFileList(self, dstPathList=None):
        """Set output validation result files list.
        The order should be [validationReportPath, xmlReportPath, validationFullReportPath, pngReportPath, svgReportPath]
        """
        if dstPathList is None:
            dstPathList = []
        self.__validationResultPath = dstPathList

    def run(self):
        """Run all processing steps required by annotator team"""
        self.__moveBestRepresentativeModel()
        self.__updateCsFileAndRunNomenclatureCheck()
        self.__runNmrValidationMiscellaneousCheck()
        self.__outputReportFile()

    def runNefProcess(self):
        """Run ref file checking & updating process"""
        self.__updateNefFileAndRunNomenclatureCheck()

    def __moveBestRepresentativeModel(self):
        """Run the selection of representative model update from _pdbx_nmr_representative.conformer_id"""
        try:
            if not self.__inModelFilePath:
                self.__insertSystemLogMessage("Input model file was not provided.")
                return
            #
            if not os.access(self.__inModelFilePath, os.R_OK):
                self.__insertSystemLogMessage("Model file '" + self.__inModelFilePath + "' does not exist.")
                return
            #
            self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
            #
            dp = RcsbDpUtility(tmpPath=self.__workingDirPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(self.__inModelFilePath)
            dp.op("annot-reorder-models")
            #
            logPath = os.path.join(self.__workingDirPath, "nmr-rep-model-update-" + str(time.strftime("%Y%m%d%H%M%S", time.localtime())) + ".log")
            dp.expLog(logPath)
            ok, logMessage = self.__processLogFile("RcsbDpUtility.op='annot-reorder-models'", logPath)
            if ok:
                dp.exp(self.__outModelFilePath)
            #
            if logMessage:
                self.__insertSystemLogMessage(logMessage)
            #
            dp.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #

    def __updateCsFileAndRunNomenclatureCheck(self):
        """Update chemical shift atom naming relative to any changes in the coordinate model.
        This operation acts on chemical shift files that are in PDBx format and have been
        preprocessed with to contain original atom nomenclature details.
        """
        try:
            if not self.__inCsFilePath:
                self.__insertSystemLogMessage("Input chemical shifts file was not provided.")
                return
            #
            if not os.access(self.__inCsFilePath, os.R_OK):
                self.__insertSystemLogMessage("Chemical shifts file '" + self.__inCsFilePath + "' does not exist.")
                return
            #
            xyzFilePath = ""
            if self.__inModelFilePath and os.access(self.__inModelFilePath, os.R_OK):
                xyzFilePath = self.__inModelFilePath
            else:
                return
            #
            if self.__outModelFilePath and os.access(self.__outModelFilePath, os.R_OK):
                xyzFilePath = self.__outModelFilePath
            #
            self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
            self.__checkReportFilePath = os.path.join(self.__workingDirPath, "chem-shifts-update-checking-" + str(time.strftime("%Y%m%d%H%M%S", time.localtime())) + ".cif")
            #
            dp = RcsbDpUtility(tmpPath=self.__workingDirPath, siteId=self.__siteId, verbose=True)
            #
            dp.imp(self.__inCsFilePath)
            # current session model path -
            dp.addInput(name="coordinate_file_path", value=xyzFilePath)
            dp.op("annot-chem-shifts-update-with-check")
            #
            logPath = os.path.join(self.__workingDirPath, "chem-shifts-update-" + str(time.strftime("%Y%m%d%H%M%S", time.localtime())) + ".log")
            dp.expLog(logPath)
            ok, logMessage = self.__processLogFile("RcsbDpUtility.op='annot-chem-shifts-update'", logPath)
            if ok:
                dp.expList(dstPathList=[self.__outCsFilePath, self.__checkReportFilePath])
            #
            if logMessage:
                self.__insertSystemLogMessage(logMessage)
            #
            dp.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #

    def __updateNefFileAndRunNomenclatureCheck(self):
        """Update chemical shift atom naming relative to any changes in the coordinate model.
        This operation acts on chemical shift files that are in PDBx format and have been
        preprocessed with to contain original atom nomenclature details.
        """
        try:
            if not self.__inNefFilePath:
                self.__insertSystemLogMessage("Input nef file was not provided.")
                return
            #
            if not os.access(self.__inNefFilePath, os.R_OK):
                self.__insertSystemLogMessage("Nef file '" + self.__inNefFilePath + "' does not exist.")
                return
            #
            xyzFilePath = ""
            if self.__inModelFilePath and os.access(self.__inModelFilePath, os.R_OK):
                xyzFilePath = self.__inModelFilePath
            else:
                return
            #
            if self.__outModelFilePath and os.access(self.__outModelFilePath, os.R_OK):
                xyzFilePath = self.__outModelFilePath
            #
            self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
            self.__checkReportFilePath = os.path.join(self.__workingDirPath, "nef-update-checking-" + str(time.strftime("%Y%m%d%H%M%S", time.localtime())) + ".cif")
            #
            dp = RcsbDpUtility(tmpPath=self.__workingDirPath, siteId=self.__siteId, verbose=True)
            #
            dp.imp(self.__inNefFilePath)
            # current session model path -
            dp.addInput(name="coordinate_file_path", value=xyzFilePath)
            dp.op("annot-nef-update-with-check")
            #
            dp.exp(self.__outNefFilePath)
            #
            # Need to know the exact requirements
            #           logPath = os.path.join(self.__workingDirPath, "nef-update-" + str(time.strftime("%Y%m%d%H%M%S", time.localtime())) + ".log")
            #           dp.expLog(logPath)
            #           ok,logMessage = self.__processLogFile("RcsbDpUtility.op='annot-nef-update'", logPath)
            #           if ok:
            #               dp.expList(dstPathList=[self.__outNefFilePath, self.__checkReportFilePath])
            #           #
            #           if logMessage:
            #               self.__insertSystemLogMessage(logMessage)
            #           #
            dp.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #

    def __runNmrValidationMiscellaneousCheck(self):
        """Run NMR miscellaneous checks implemented in the validation pipeline"""
        try:
            xyzFilePath = ""
            if self.__inModelFilePath and os.access(self.__inModelFilePath, os.R_OK):
                xyzFilePath = self.__inModelFilePath
            else:
                return
            #
            csFilePath = ""
            if self.__inCsFilePath and os.access(self.__inCsFilePath, os.R_OK):
                csFilePath = self.__inCsFilePath
            else:
                return
            #
            if self.__outModelFilePath and os.access(self.__outModelFilePath, os.R_OK):
                xyzFilePath = self.__outModelFilePath
            #
            if self.__outCsFilePath and os.access(self.__outCsFilePath, os.R_OK):
                csFilePath = self.__outCsFilePath
            #
            self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
            #
            dp = RcsbDpUtility(tmpPath=self.__workingDirPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.addInput(name="request_annotation_context", value="yes")
            # adding explicit selection of steps --
            dp.addInput(name="step_list", value=" coreclust,chemicalshifts,writexml,writepdf ")
            dp.imp(xyzFilePath)
            dp.addInput(name="cs_file_path", value=csFilePath)
            dp.op("annot-wwpdb-validate-all")
            #
            logPath = os.path.join(self.__workingDirPath, "nmr-cs-check-rpt-" + str(time.strftime("%Y%m%d%H%M%S", time.localtime())) + ".log")
            dp.expLog(logPath)
            dp.expList(dstPathList=self.__validationResultPath)
            #
            # do something with logPath file?
            #
            dp.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #

    def __outputReportFile(self):
        """Write atom nomenclature checking result"""
        if not self.__outReportFilePath:
            return
        #
        jsonObj = {}
        #
        if self.__systemLogMessage:
            jsonObj["system_msg"] = self.__systemLogMessage
        #
        cifObj = mmCIFUtil(filePath=self.__checkReportFilePath)
        for msg_type in (("warning_msg", "pdbx_shift_check_warning_message"), ("error_msg", "pdbx_shift_check_error_message")):
            msg = self.__getMsgFromCifObj(cifObj, msg_type[1])
            if msg:
                jsonObj[msg_type[0]] = msg
            #
        #
        with open(self.__outReportFilePath, "w") as outfile:
            json.dump(jsonObj, outfile)
        #

    def __insertSystemLogMessage(self, msg):
        """Append log message to self.__systemLogMessage"""
        if not msg:
            return
        #
        if self.__systemLogMessage.find(msg) != -1:
            return
        #
        if self.__systemLogMessage:
            self.__systemLogMessage += "\n"
        #
        self.__systemLogMessage += msg

    def __processLogFile(self, program, logFileName):
        """Read error/warning message from log file"""
        fp = open(logFileName, "r")
        data = fp.read()
        fp.close()
        #
        ok = False
        msg = ""
        dataDict = {}
        for line in data.split("\n"):
            if line in dataDict:
                continue
            #
            dataDict[line] = "y"
            #
            if line == "Finished!":
                ok = True
                continue
            #
            if msg:
                msg += "\n"
            #
            msg += line
        #
        if program and msg == "Segmentation fault":
            msg = program + ": " + msg
        #
        return ok, msg

    def __getMsgFromCifObj(self, cifObj, categoryName):
        """Read message text from pdbx_shift_check_warning_message & pdbx_shift_check_error_message categories"""
        dList = cifObj.GetValue(categoryName)
        if not dList:
            return ""
        #
        msg = ""
        for Dict in dList:
            if ("text" in Dict) and Dict["text"]:
                if msg:
                    msg += "\n\n"
                #
                msg += Dict["text"]
            #
        #
        return msg
