##
# File:  Solvent.py
# Date:  30-June-2012  J. Westbrook
#
# Update:
#   4-July-2012 - jdw swap and test method "annot-reposition-solvent"
#  17-Dec -2012 - jdw add option to compute selected derived categories after solvent adjustment.
#  28-Feb -2014 - jdw add base class
##
"""
Manage calculation of symmetry related solvent position in closest proximity to the macromolecule components
of the coordinate entry.

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


class Solvent(SessionWebDownloadUtils):
    """
    The Solvent class encapsulates implementation of "standard PDB algorithm" to shuffle symmetry related
    solvent molecules in closest proximity to the macromolecules in the coordinate set.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(Solvent, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__solventArgs = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def setArguments(self, solventArgs):
        self.__solventArgs = solventArgs

    def run(self, entryId, inpFile, updateInput=True):
        """Run the solvent shuffling algorithm and merge the result with the model input data."""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath1 = os.path.join(self.__sessionPath, entryId + "-solvent-anal.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            if self.__solventArgs is not None:
                dp.addInput(name="solvent_arguments", value=self.__solventArgs)
            #
            # dp.op("annot-reposition-solvent")
            # dp.op("annot-distant-solvent")
            dp.op("annot-reposition-solvent-add-derived")

            dp.expLog(logPath1)
            dp.exp(retPath)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath1)
            if updateInput:
                dp.exp(inpPath)
            if self.__verbose:
                self.__lfh.write("+Solvent.run-  completed for entryId %s file %s\n" % (entryId, inpPath))

            dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False
