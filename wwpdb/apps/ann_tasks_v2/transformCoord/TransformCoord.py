##
# File:  TransformCoord.py
# Date:  15-Aug-2013  J. Westbrook
#
# Update:
#  25-Jan-2014  jdw add some error control for missing input files and results
# 28-Feb -2014  Add base class
##
"""
Manage calculation of secondary structure.

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
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.io.file.DataFile import DataFile
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class TransformCoord(SessionWebDownloadUtils):
    """
    TransformCoord class encapsulates calculation of symmetry and matrix transformations

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(TransformCoord, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__transFilePath = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #

    def setTransformFile(self, transFileName):
        tPath = os.path.join(self.__sessionPath, transFileName)
        if os.access(tPath, os.F_OK):
            self.__transFilePath = tPath
            if self.__verbose:
                self.__lfh.write("+TransformCoord.setTransformFile file path %s\n" % self.__transFilePath)
        else:
            if self.__verbose:
                self.__lfh.write("+TransformCoord.setTransformFile ERROR read failed for file %s\n" % tPath)

    def run(self, entryId, inpFile, fileType="symop", updateInput=True):
        """Run the coordinate transform calculation on the input model file."""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath1 = os.path.join(self.__sessionPath, entryId + "-trans-coord.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            if self.__transFilePath is not None:
                dp.addInput(name="transform_file_path", value=self.__transFilePath)
            if fileType == "symop":
                dp.op("annot-move-xyz-by-symop")
            elif fileType == "matrix":
                dp.op("annot-move-xyz-by-matrix")
            else:
                dp.op("annot-move-xyz-by-symop")
            dp.expLog(logPath1)
            dp.exp(retPath)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath1)
            #
            status = False
            f1 = DataFile(retPath)
            if f1.srcFileExists() and f1.srcFileSize() > 0:
                status = True
                if updateInput:
                    dp.exp(inpPath)
                if self.__verbose:
                    self.__lfh.write("+TransformCoord.run-  completed for entryId %s file %s\n" % (entryId, inpPath))
            elif not f1.srcFileExists():
                status = False
            else:
                status = False

            dp.cleanup()
            return status
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+TransformCoord.run-  failed for entryId %s file %s\n" % (entryId, inpPath))
                traceback.print_exc(file=self.__lfh)
            return False
