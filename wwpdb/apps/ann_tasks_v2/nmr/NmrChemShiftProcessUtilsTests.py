##
# File:    NmrChemShiftProcessUtilsTests.py
# Author:  Zukang Feng
# Date:    26-Sept-2018
# Version: 0.001
#
##
"""
Tests for model update using map header data  -

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import inspect
import os
import shutil
import sys
import time
import traceback
import unittest

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.session.WebRequest import InputRequest
from wwpdb.apps.ann_tasks_v2.nmr.NmrChemShiftProcessUtils import NmrChemShiftProcessUtils


class NmrChemShiftProcessUtilsTests(unittest.TestCase):
    def setUp(self):
        self.__lfh = sys.stderr
        self.__verbose = True
        self.__entryId = "D_1000102134"
        #
        self.__getSession()
        self.__getFiles()

    def __getSession(self):
        self.__siteId = os.getenv("WWPDB_SITE_ID")
        cI = ConfigInfo(self.__siteId)
        myReqObj = InputRequest({}, verbose=self.__verbose, log=self.__lfh)
        myReqObj.setValue("TopSessionPath", cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH"))
        myReqObj.setValue("TopPath", cI.get("SITE_WEB_APPS_TOP_PATH"))
        myReqObj.setValue("WWPDB_SITE_ID", self.__siteId)
        #
        sObj = myReqObj.newSessionObj()
        self.__sessionPath = sObj.getPath()

    def __getFiles(self):
        pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        #
        archiveModelFile = pI.getFilePath(self.__entryId, contentType="model", formatType="pdbx", fileSource="archive", versionId="latest")
        self.__inputModelFile = pI.getFilePath(self.__entryId, contentType="model", formatType="pdbx", fileSource="session", versionId="next")
        shutil.copyfile(archiveModelFile, self.__inputModelFile)
        #
        archiveCsFile = pI.getFilePath(self.__entryId, contentType="nmr-chemical-shifts", formatType="pdbx", fileSource="archive", versionId="latest")
        self.__inputCsFile = pI.getFilePath(self.__entryId, contentType="nmr-chemical-shifts", formatType="pdbx", fileSource="session", versionId="next")
        shutil.copyfile(archiveCsFile, self.__inputCsFile)
        #
        archiveNefFile = pI.getFilePath(self.__entryId, contentType="nmr-data-str", formatType="pdbx", fileSource="archive", versionId="latest")
        self.__inputNefFile = pI.getFilePath(self.__entryId, contentType="nmr-data-str", formatType="pdbx", fileSource="session", versionId="next")
        shutil.copyfile(archiveNefFile, self.__inputNefFile)
        #
        self.__outputModelFile = pI.getFilePath(self.__entryId, contentType="model", formatType="pdbx", fileSource="session", versionId="next")
        self.__outputCsFile = pI.getFilePath(self.__entryId, contentType="nmr-chemical-shifts", formatType="pdbx", fileSource="session", versionId="next")
        self.__outputNefFile = pI.getFilePath(self.__entryId, contentType="nmr-data-str", formatType="pdbx", fileSource="session", versionId="next")
        self.__outputReportFile = pI.getFilePath(self.__entryId, contentType="nmr-shift-error-report", formatType="json", fileSource="session", versionId="next")
        self.__validationReportFile = pI.getFilePath(self.__entryId, contentType="validation-report", formatType="pdf", fileSource="session", versionId="next")
        self.__validationDataFile = pI.getFilePath(self.__entryId, contentType="validation-data", formatType="xml", fileSource="session", versionId="next")
        self.__fullReportFile = pI.getFilePath(self.__entryId, contentType="validation-report-full", formatType="pdf", fileSource="session", versionId="next")
        self.__sliderPngFile = pI.getFilePath(self.__entryId, contentType="validation-report-slider", formatType="png", fileSource="session", versionId="next")
        self.__sliderSvgFile = pI.getFilePath(self.__entryId, contentType="validation-report-slider", formatType="svg", fileSource="session", versionId="next")
        self.__imageTargFile = pI.getFilePath(self.__entryId, contentType="validation-report-images", formatType="tar", fileSource="session", versionId="next")
        self.__validationCifFile = pI.getFilePath(self.__entryId, contentType="validation-data", formatType="pdbx", fileSource="session", versionId="next")

    def tearDown(self):
        pass

    #   def testUpdateModel(self):
    #       self.__lfh.write("inputModelFile=%s\n" % self.__inputModelFile)
    #       self.__lfh.write("inputCsFile=%s\n" % self.__inputCsFile)
    #       self.__lfh.write("outputModelFile=%s\n" % self.__outputModelFile)
    #       self.__lfh.write("outputCsFile=%s\n" % self.__outputCsFile)

    def testUpdateModel(self):
        """Test case -  model file update with map header data"""
        startTime = time.time()
        self.__lfh.write("\nStarting %s %s at %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        try:
            util = NmrChemShiftProcessUtils(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            util.setWorkingDirPath(dirPath=self.__sessionPath)
            util.setInputModelFileName(fileName=self.__inputModelFile)
            util.setInputCsFileName(fileName=self.__inputCsFile)
            util.setInputNefFileName(fileName=self.__inputNefFile)
            util.setOutputModelFileName(fileName=self.__outputModelFile)
            util.setOutputCsFileName(fileName=self.__outputCsFile)
            util.setOutputNefFileName(fileName=self.__outputNefFile)
            util.setOutputReportFileName(fileName=self.__outputReportFile)
            util.setOutputValidationFileList(
                dstPathList=[
                    self.__validationReportFile,
                    self.__validationDataFile,
                    self.__fullReportFile,
                    self.__sliderPngFile,
                    self.__sliderSvgFile,
                    self.__imageTargFile,
                    self.__validationCifFile,
                ]
            )
            #
            util.run()
            util.runNefProcess()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            self.fail()
        #
        endTime = time.time()
        self.__lfh.write(
            "\nCompleted %s %s at %s (%.2f seconds)\n"
            % (self.__class__.__name__, inspect.currentframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - startTime)
        )


def suiteUpdateModelTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(NmrChemShiftProcessUtilsTests("testUpdateModel"))
    return suiteSelect


if __name__ == "__main__":
    mySuite = suiteUpdateModelTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
