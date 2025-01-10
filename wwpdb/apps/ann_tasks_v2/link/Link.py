##
# File:  Link.py
# Date:  30-June-2012  J. Westbrook
#
# Update:
#   2-Aug-2012  jdw   add cis peptide annotation
#  28-Feb-2014        Add base class
#  06-Sep-2024   zf   changed "annot-link-ssbond" to "annot-link-ssbond-with-ptm" operator
#
##
"""
Manage the calculation of covalent linkages and disulfide bonds.

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

from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class Link(SessionWebDownloadUtils):
    """
    The Link class encapsulates the calculation of covalent linkages and disulfide bonds.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(Link, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__linkArgs = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def setArguments(self, linkArgs):
        self.__linkArgs = linkArgs

    def run(self, entryId, inpFile, updateInput=True):
        """Run the covalent linkage and disulfide bond calculation and merge the result with model file.

        added cis-peptide detection to this module --
        """
        try:
            pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
            csvFile = pI.getFileName(entryId, contentType="pcm-missing-data", formatType="csv", versionId="none", partNumber="1")
            csvPath = os.path.join(self.__sessionPath, csvFile)
            #
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath1 = os.path.join(self.__sessionPath, entryId + "-link-anal.log")
            logPath2 = os.path.join(self.__sessionPath, entryId + "-cispeptide-anal.log")
            retPath1 = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            retPath2 = os.path.join(self.__sessionPath, entryId + "_model-updated_P2.cif")
            for filePath in (csvPath, retPath1, retPath2, logPath1, logPath2):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            if self.__linkArgs is not None:
                dp.addInput(name="link_arguments", value=self.__linkArgs)
            dp.op("annot-link-ssbond-with-ptm")
            dp.expLog(logPath1)
            dp.expList(dstPathList=[retPath1, csvPath])
            self.addDownloadPath(retPath1)
            self.addDownloadPath(logPath1)
            #

            dp.imp(retPath1)
            dp.op("annot-cis-peptide")
            dp.expLog(logPath2)
            dp.exp(retPath2)
            self.addDownloadPath(retPath2)
            self.addDownloadPath(logPath2)

            if updateInput:
                dp.exp(inpPath)
            if self.__verbose:
                self.__lfh.write("+Link.run-  completed for entryId %s file %s\n" % (entryId, inpPath))

            dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
