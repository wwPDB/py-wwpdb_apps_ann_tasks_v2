##
# File:  SpecialPositionUpdate.py
# Date:  13-Jan-2017  E. Peisach
#
# Update:
#
##
"""
Updates occupancy for waters on special position

"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import os.path
import os
import inspect
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class SpecialPositionUpdate(SessionWebDownloadUtils):
    """
    Encapsulates occupancy fix for solvent on special positions

    Operations are performed in the current session context defined in the input
    reqObj().

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(SpecialPositionUpdate, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        # self.__checkArgs = None
        self.__cleanup = False
        self.__modelUpdated = False
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def setArguments(self, checkArgs):  # pylint: disable=unused-argument
        # self.__checkArgs = checkArgs
        pass

    def modelUpdated(self):
        """Returns True if the model was updated in the last run"""
        return self.__modelUpdated

    def run(self, entryId, inpFile, updateInput=True):
        """Updates the occupancy of special positions in model file"""
        if self.__verbose:
            self.__lfh.write(
                "+%s.%s special position update calc entering for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpFile)
            )

        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath = os.path.join(self.__sessionPath, entryId + "_special-position-update.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)

            dp.op("annot-dcc-fix-special-position")
            dp.expLog(logPath)
            if dp.getResultPathList()[0] != "missing":
                dp.expList(dstPathList=[retPath])
                self.addDownloadPath(retPath)
                self.__modelUpdated = True

            self.addDownloadPath(logPath)
            if updateInput:
                dp.expList(dstPathList=[inpPath])
            #
            if self.__verbose:
                self.__lfh.write(
                    "+%s.%s special position update calc completed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpFile)
                )

            if self.__cleanup:
                dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write(
                    "+%s.%s special position update calc failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpFile)
                )
            traceback.print_exc(file=self.__lfh)
            return False
