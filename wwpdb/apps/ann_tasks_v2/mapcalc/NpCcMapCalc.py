##
# File:  NpCcMapCalc.py
# Date:  16-Jul-2014  J. Westbrook
#
# Update:
#
##
"""
Manage local electon density map calculations around individual non-polymer chemical components --

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


class NpCcMapCalc(SessionWebDownloadUtils):
    """
    Manage local electon density map calculations around individual non-polymer chemical components --

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(NpCcMapCalc, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__mapArgs = None
        self.__cleanup = False
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def setArguments(self, mapArgs):
        self.__mapArgs = mapArgs

    def run(self, entryId, modelInputFile=None, expInputFile=None, updateInput=True, doOmit=False):  # pylint: disable=unused-argument
        """Run map calculations operation -"""
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
            logPath = os.path.join(self.__sessionPath, entryId + "_map-npcc-calc.log")
            outDataPath = os.path.join(self.__sessionPath, "np-cc-maps")
            outIndexPath = os.path.join(self.__sessionPath, "np-cc-maps", "np-cc-maps-index.cif")
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.setDebugMode(flag=True)
            dp.imp(inpPath)
            dp.addInput(name="sf_file_path", value=sfPath)

            if self.__mapArgs is not None:
                dp.addInput(name="map_arguments", value=self.__mapArgs)

            dp.addInput(name="output_data_path", value=outDataPath)
            dp.addInput(name="output_index_path", value=outIndexPath)
            dp.op("annot-make-ligand-maps")
            dp.expLog(logPath)
            self.addDownloadPath(logPath)
            #
            #
            if self.__verbose:
                self.__lfh.write("+NpCcMapCalc.run-  completed for entryId %s file %s\n" % (entryId, inpPath))
            if self.__cleanup:
                dp.cleanup()

            if doOmit:
                dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=True, log=self.__lfh)
                dp.setDebugMode(flag=True)
                #
                logPath = os.path.join(self.__sessionPath, entryId + "_map-omit-npcc-calc.log")
                outDataPath = os.path.join(self.__sessionPath, "np-cc-omit-maps")
                outIndexPath = os.path.join(self.__sessionPath, "np-cc-omit-maps", "np-cc-omit-maps-index.cif")
                dp.imp(inpPath)
                dp.addInput(name="sf_file_path", value=sfPath)

                if self.__mapArgs is not None:
                    dp.addInput(name="map_arguments", value=self.__mapArgs)

                dp.addInput(name="omit_map", value=True)
                dp.addInput(name="output_data_path", value=outDataPath)
                dp.addInput(name="output_index_path", value=outIndexPath)
                dp.op("annot-make-ligand-maps")
                dp.expLog(logPath)
                self.addDownloadPath(logPath)
                if self.__verbose:
                    self.__lfh.write("+NpCcMapCalc.run-  completed for entryId %s file %s\n" % (entryId, inpPath))
                if self.__cleanup:
                    dp.cleanup()

            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+NpCcMapCalc.run-  failed with exception for entryId %s file %s\n" % (entryId, inpPath))

            traceback.print_exc(file=self.__lfh)
            return False
