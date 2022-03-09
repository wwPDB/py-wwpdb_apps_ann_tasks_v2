##
# File:  Site.py
# Date:  28-June-2012  J. Westbrook
#
# Update:
#  2-July-2012  jdw Add command line argument option
# 28-Feb -2014  jdw Add base class
#
##
"""
Manage calculation of site environment.

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


class Site(SessionWebDownloadUtils):
    """
    The Site class encapsulates calculation of site environment.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(Site, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__siteArgs = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def setArguments(self, siteArgs):
        self.__siteArgs = siteArgs

    def run(self, entryId, inpFile, updateInput=True):
        """Run the site calculation and merge the result with model file."""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath1 = os.path.join(self.__sessionPath, entryId + "_site-anal.log")
            logPath2 = os.path.join(self.__sessionPath, entryId + "_site-merge.log")
            resultPath = os.path.join(self.__sessionPath, entryId + "_site-anal_P1.cif")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            dp.addInput(name="block_id", value=entryId)
            if self.__siteArgs is not None:
                dp.addInput(name="site_arguments", value=self.__siteArgs)
            dp.op("annot-site")
            dp.expLog(logPath1)
            dp.exp(resultPath)
            self.addDownloadPath(resultPath)
            self.addDownloadPath(logPath1)

            # Step 2
            dp.imp(inpPath)
            dp.addInput(name="site_info_file_path", value=resultPath, type="file")
            dp.op("annot-merge-struct-site")
            #
            dp.expLog(logPath2)
            dp.exp(retPath)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath2)
            if updateInput:
                dp.exp(inpPath)
            #
            if self.__verbose:
                self.__lfh.write("+Site.run-  completed for entryId %s file %s\n" % (entryId, inpPath))

            dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
