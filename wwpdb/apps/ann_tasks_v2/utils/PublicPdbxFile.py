##
# File:  PublicPdbxFile.py
# Date:  14-Oct-2013
#
# Update:
# 28-Feb -2014  jdw Add base class
# 4-Jun-2014    jdw Added V4 dictionary argument --
# 25-May-2023   zf  Added run_conversion() method to generate different flavor of public PDBx/mmCIF files
##
"""
Generate public pdbx cif file.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import os.path
import sys
import traceback
import inspect

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class PublicPdbxFile(SessionWebDownloadUtils):
    """The PublicPdbxFile class encapsulates conversion internal pdbx cif to public pdbx cif file."""

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(PublicPdbxFile, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self._verbose = verbose
        self._lfh = log
        self.__reqObj = reqObj
        self._debug = False
        self.__setup()
        #
        self.__opMap = {
            "annot-cif-to-public-pdbx": ("_model-review_P1.cif", "-public_cif.log"),
            "cif2pdbx-ext": ("_model-next_P1.cif", "_cif2pdbx-next.log"),
            "cif2pdbx-public": ("_model-v4-pubic_P1.cif", "_cif2pdbx-pubic.log"),
        }
        #

    def __setup(self):
        self._siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self._sessionPath = self.__sObj.getPath()
        self._exportPath = self._sessionPath  # pylint: disable=attribute-defined-outside-init
        self._cleanup = False

    def setExportPath(self, exportPath):
        """Set the path where output files are copyied."""
        self._exportPath = exportPath  # pylint: disable=attribute-defined-outside-init

    def run(self, entryId, inpPath):
        """Create review model file"""
        full_inpPath = os.path.join(self._sessionPath, inpPath)
        if self.run_conversion("annot-cif-to-public-pdbx", entryId, full_inpPath):
            return True
        #
        return False

    def run_conversion(self, op, entryId, inpPath):
        """Run conversion."""
        try:
            if op not in self.__opMap:
                return
            #
            pdbxPath = os.path.join(self._exportPath, entryId + self.__opMap[op][0])
            logPath = os.path.join(self._exportPath, entryId + self.__opMap[op][1])
            #
            for filePath in (pdbxPath, logPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self._sessionPath, siteId=self._siteId, verbose=self._verbose, log=self._lfh)
            if self._debug:
                dp.setDebugMode(flag=True)
            #
            dp.imp(inpPath)
            if op == "cif2pdbx-ext":
                dp.addInput(name="destination", value="archive_next")
            #
            dp.op(op)
            dp.exp(pdbxPath)
            dp.expLog(logPath)
            #
            if op != "annot-cif-to-public-pdbx":
                self.addDownloadPath(pdbxPath)
                self.addDownloadPath(logPath)
            #
            if self._verbose:
                self._lfh.write("+%s.%s  creating public cif for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath))
            #
            if self._cleanup:
                dp.cleanup()
            #
            return pdbxPath
        except:  # noqa: E722 pylint: disable=bare-except
            if self._verbose:
                self._lfh.write("+%s.%s public cif conversion failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath))
            #
            traceback.print_exc(file=self._lfh)
        #
        return None
