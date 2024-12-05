##
# File:  MapCalc.py
# Date:  02-Apr-2013  J. Westbrook
#
# Update:
# 28-Feb -2014  Add base class
#
##
"""
Manage electon density map calculation from model coordinates and structure factors.

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
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class MapCalc(SessionWebDownloadUtils):
    """
    The MapCalc class launches electon density map calculation using input model coordinates and structure factors.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(MapCalc, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__mapArgs = None
        self.__cleanup = True
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def setArguments(self, mapArgs):
        self.__mapArgs = mapArgs

    def run(self, entryId, modelInputFile=None, expInputFile=None, updateInput=True, doOmit=False):  # pylint: disable=unused-argument
        """Run the map calculations"""
        try:
            if modelInputFile is None:
                modelFileName = entryId + "_model_P1.cif"
                inpPath = os.path.join(self.__sessionPath, modelFileName)
            else:
                inpPath = os.path.join(self.__sessionPath, modelInputFile)

            if expInputFile is None:
                expFileName = entryId + "_sf_P1.cif"
                sfPath = os.path.join(self.__sessionPath, expFileName)
            else:
                sfPath = os.path.join(self.__sessionPath, expInputFile)
            #
            #
            logPath = os.path.join(self.__sessionPath, entryId + "_map-calc.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            result2fofcPath = os.path.join(self.__sessionPath, entryId + "_map-2fofc_P1.map")
            resultfofcPath = os.path.join(self.__sessionPath, entryId + "_map-fofc_P1.map")
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            dp.addInput(name="sf_file_path", value=sfPath)
            if self.__mapArgs is not None:
                dp.addInput(name="map_arguments", value=self.__mapArgs)
            dp.op("annot-make-maps")
            dp.expLog(logPath)
            dp.expList(dstPathList=[result2fofcPath, resultfofcPath])

            self.addDownloadPath(result2fofcPath)
            self.addDownloadPath(resultfofcPath)
            self.addDownloadPath(logPath)
            #
            if self.__verbose:
                self.__lfh.write("+MapCalc.run-  map calculation completed for entryId %s file %s\n" % (entryId, inpPath))

            if self.__cleanup:
                dp.cleanup()
            #
            if doOmit:
                logPath = os.path.join(self.__sessionPath, entryId + "_map-omit-calc.log")
                if os.access(logPath, os.R_OK):
                    os.remove(logPath)
                #
                result2fofcPath = os.path.join(self.__sessionPath, entryId + "_map-omit-2fofc_P1.map")
                resultfofcPath = os.path.join(self.__sessionPath, entryId + "_map-omit-fofc_P1.map")
                #
                dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
                dp.imp(inpPath)
                dp.addInput(name="sf_file_path", value=sfPath)
                if self.__mapArgs is not None:
                    dp.addInput(name="map_arguments", value=self.__mapArgs)
                dp.op("annot-make-omit-maps")
                dp.expLog(logPath)
                dp.expList(dstPathList=[result2fofcPath, resultfofcPath])

                self.addDownloadPath(result2fofcPath)
                self.addDownloadPath(resultfofcPath)
                self.addDownloadPath(logPath)
                #
                if self.__verbose:
                    self.__lfh.write("+MapCalc.run-  omit map calculation completed for entryId %s file %s\n" % (entryId, inpPath))

                if self.__cleanup:
                    dp.cleanup()

            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+MapCalc.run-  failed with exception for entryId %s file %s\n" % (entryId, inpPath))

            traceback.print_exc(file=self.__lfh)
            return False
