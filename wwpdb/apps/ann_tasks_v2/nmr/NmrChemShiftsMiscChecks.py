##
# File:  NmrChemShiftsMiscChecks.py
# Date:  15-Dec-2015  J. Westbrook
#
# Update:
#
"""
Chemical shift miscellaneous checks implemented in the validation pipeline --

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import inspect
import sys
import os.path
import os
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils
from wwpdb.apps.ann_tasks_v2.utils.NmrRemediationUtils import remediate_cs_file, starToPdbx


# UI appears to no longer invoke - commented out - so blindly fixing
class NmrChemShiftsMiscChecks(SessionWebDownloadUtils):
    """
    NmrChemShiftsMiscChecks class encapsulates miscellaneous checks implemented in the validation pipeline --

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(NmrChemShiftsMiscChecks, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose  # pylint: disable=unused-private-member
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #
        self.__cleanUp = True
        #

    def run(self, entryId, csInpFilePath, xyzFilePath):
        """Run the NMR specific checks implemented in the validation pipeline -"""
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=True)
            dp.setDebugMode(flag=True)
            # ----------
            ofpdf = os.path.join(self.__sessionPath, entryId + "-nmr-cs-check-rpt.pdf")
            ofxml = os.path.join(self.__sessionPath, entryId + "-nmr-cs-check-rpt.xml")
            offullpdf = os.path.join(self.__sessionPath, entryId + "-nmr-cs-check-rpt-full.pdf")
            ofpng = os.path.join(self.__sessionPath, entryId + "-nmr-val-slider.png")
            ofsvg = os.path.join(self.__sessionPath, entryId + "-nmr-val-slider.svg")
            logPath = os.path.join(self.__sessionPath, entryId + "-nmr-cs-check-rpt.log")
            # ------------
            dp.addInput(name="request_annotation_context", value="yes")
            # adding explicit selection of steps --
            dp.addInput(name="step_list", value=" coreclust,chemicalshiftanalysis,writexml,writepdf ")
            dp.imp(xyzFilePath)
            # Remediation of legacy files in the system - header of chemical shifts section

            tmpStrFilePath = csInpFilePath + ".str"
            csFilePath = csInpFilePath + ".cif"

            remediate_cs_file(csInpFilePath, tmpStrFilePath)
            starToPdbx(tmpStrFilePath, csFilePath)

            # dp.addInput(name="cs_file_path", value=csInpFilePath)
            dp.addInput(name="cs_file_path", value=csFilePath)

            dp.op("annot-wwpdb-validate-all")
            dp.expLog(logPath)
            dp.expList(dstPathList=[ofpdf, ofxml, offullpdf, ofpng, ofsvg])
            #
            self.addDownloadPath(ofpdf)
            self.addDownloadPath(offullpdf)
            self.addDownloadPath(logPath)
            #
            if self.__cleanUp:
                dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        return False
