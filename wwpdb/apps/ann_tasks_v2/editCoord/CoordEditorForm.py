##
# File:  CoordEditorForm.py
# Date:  09-Oct-2013
# Update:
##
"""
Manage the generating coordinate editor form

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os

from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon, ConfigInfoAppCc


class CoordEditorForm(object):
    """
    The CoordEditorForm class generates coordinate editor form.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        # self.__verbose = verbose
        # self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        self.__cIAppCc = ConfigInfoAppCc(self.__siteId)
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__entryId = self.__reqObj.getValue("entryid")
        self.__entryFile = self.__reqObj.getValue("entryfilename")
        #
        pickleFile = os.path.join(self.__sessionPath, self.__entryId + "_coord_pickle.db")
        if os.access(pickleFile, os.F_OK):
            os.remove(pickleFile)
        #

    def get(self):
        """Get coordinate editor form"""
        myD = {}
        #
        coordFile = os.path.join(self.__sessionPath, self.__entryFile)
        if not os.access(coordFile, os.F_OK):
            myD["htmlcontent"] = "No model coordinate file uploaded"
            return myD
        #
        self.__runScript()
        #
        myD["htmlcontent"] = self.__getHtmlcontent()
        select, chainids = self.__getChainInfo()
        if select:
            myD["select"] = select
        #
        if chainids:
            myD["chainids"] = chainids
        #
        return myD

    def __runScript(self):
        script = os.path.join(self.__sessionPath, self.__entryId + "_script.csh")
        f = open(script, "w")
        f.write("#!/bin/tcsh -f\n")
        f.write("#\n")
        f.write("setenv RCSBROOT   " + self.__cICommon.get_site_annot_tools_path() + "\n")
        f.write("setenv COMP_PATH  " + self.__cIAppCc.get_site_cc_cvs_path() + "\n")
        f.write("setenv BINPATH  ${RCSBROOT}/bin\n")
        f.write("#\n")
        f.write(
            "${BINPATH}/DepictMolecule -input "
            + self.__entryFile
            + " -output "
            + self.__entryId
            + "_html.txt "
            + " -output_2 "
            + self.__entryId
            + "_chainids.txt "
            + " -output_3 "
            + self.__entryId
            + "_index.cif "
            + " -log "
            + self.__entryId
            + "_summary.log\n"
        )
        f.write("#\n")
        f.close()
        cmd = "cd " + self.__sessionPath + "; chmod 755 " + self.__entryId + "_script.csh; " + " ./" + self.__entryId + "_script.csh >& summary_log"
        os.system(cmd)

    def __getHtmlcontent(self):
        content = "No result found!"
        filename = os.path.join(self.__sessionPath, self.__entryId + "_html.txt")
        if os.access(filename, os.F_OK):
            f = open(filename, "r")
            content = f.read()
            f.close()
        #
        return content

    def __getChainInfo(self):
        select = ""
        chainids = ""
        filename = os.path.join(self.__sessionPath, self.__entryId + "_chainids.txt")
        if os.access(filename, os.F_OK):
            f = open(filename, "r")
            chainids = f.read()
            f.close()
            #
            chainids = chainids.strip()
            clist = chainids.split(",")
            for cid in clist:
                if select:
                    select += ","
                #
                select += "'" + cid + "': '" + cid + "'"
            #
        #
        select = "{ " + select + " }"
        return select, chainids
