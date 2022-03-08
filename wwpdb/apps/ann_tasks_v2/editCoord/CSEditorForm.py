##
# File:  CSEditorForm.py
# Date:  04-Agu-2015
# Update:
##
"""
Manage the generating chemical shift editor form

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class CSEditorForm(object):
    """
    The CSEditorForm class generates chemical shift editor form.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__entryId = self.__reqObj.getValue("entryid")
        self.__entryFile = self.__reqObj.getValue("entrycsfilename")
        #
        pickleFile = os.path.join(self.__sessionPath, self.__entryId + "_cs_pickle.db")
        if os.access(pickleFile, os.F_OK):
            os.remove(pickleFile)
        #

    def get(self):
        """Get chemical shift editor form"""
        myD = {}
        #
        coordFile = os.path.join(self.__sessionPath, self.__entryFile)
        if not os.access(coordFile, os.F_OK):
            myD["htmlcontent"] = "No chemical shift file uploaded"
            return myD
        #
        self.__runScript()
        #
        myD["htmlcontent"] = self.__getHtmlcontent()
        return myD

    def __runScript(self):
        """ """
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(os.path.join(self.__sessionPath, self.__entryFile))
            dp.op("annot-depict-chemical-shift")
            dp.exp(os.path.join(self.__sessionPath, self.__entryId + "_cs_html.txt"))
            dp.expLog(os.path.join(self.__sessionPath, self.__entryId + "_cs_summary.log"))
            dp.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #

    def __getHtmlcontent(self):
        content = "No result found!"
        filename = os.path.join(self.__sessionPath, self.__entryId + "_cs_html.txt")
        if os.access(filename, os.F_OK):
            f = open(filename, "r")
            content = f.read()
            f.close()
        #
        return content
