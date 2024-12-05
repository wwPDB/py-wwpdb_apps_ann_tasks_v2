##
# File:  CSEditorUpdate.py
# Date:  04-Aug-2015
# Update:
##
"""
Update chemical shift cif file

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

import sys
import os.path
import os
import traceback

from mmcif.io.PdbxWriter import PdbxWriter
from mmcif.api.PdbxContainers import DataContainer
from mmcif.api.DataCategory import DataCategory
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class CSEditorUpdate(object):
    """
    The CSEditorUpdate class updates chemical shift cif file.

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

    def run(self):
        """Run update"""
        cmap = {}
        #
        pickleFile = os.path.join(self.__sessionPath, self.__entryId + "_cs_pickle.db")
        if os.access(pickleFile, os.F_OK):
            fb = open(pickleFile, "rb")
            cmap = pickle.load(fb)
            fb.close()
        #
        ddir = self.__reqObj.getDictionary()
        for key, value in ddir.items():
            if key.startswith("RangeNum") or key.startswith("RangeCID"):
                if value and value[0]:
                    cmap[key] = value[0]
                #
            #
        #
        if not cmap:
            return "No option selected."
        #
        self.__writeSelectInfo(cmap)
        text = self.__runUpdateScript()
        if text:
            return text
        #
        return "OK"

    def __writeSelectInfo(self, cmap):
        category = DataCategory("update_info")
        category.appendAttribute("key")
        category.appendAttribute("value")
        row = 0
        for key, v in cmap.items():
            category.setValue(key, "key", row)
            category.setValue(v, "value", row)
            row += 1
        #
        container = DataContainer("XXXX")
        container.append(category)
        #
        myDataList = []
        myDataList.append(container)
        #
        filename = os.path.join(self.__sessionPath, self.__entryId + "_cs_select.cif")
        f = open(filename, "w")
        pdbxW = PdbxWriter(f)
        pdbxW.write(myDataList)
        f.close()

    def __runUpdateScript(self):
        """ """
        try:
            logPath = os.path.join(self.__sessionPath, self.__entryId + "_cs_update.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(os.path.join(self.__sessionPath, self.__entryFile))
            dp.addInput(name="assign", value=os.path.join(self.__sessionPath, self.__entryId + "_cs_select.cif"))
            dp.op("annot-edit-chemical-shift")
            dp.exp(os.path.join(self.__sessionPath, self.__entryFile))
            dp.expLog(logPath)
            dp.cleanup()
            #
            return self.__readLogFile("_cs_update.log", "Update failed!")
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            error = "error:" + traceback.format_exc()
            return error
        #

    def __readLogFile(self, extension, default_message):
        filename = os.path.join(self.__sessionPath, self.__entryId + extension)
        if os.access(filename, os.F_OK):
            f = open(filename, "r")
            content = f.read()
            f.close()
            #
            if content.find("Finished!") == -1:
                return default_message + "\n\n" + content
            #
            error = ""
            clist = content.split("\n")
            for line in clist:
                if not line:
                    continue
                #
                if line == "Finished!":
                    continue
                #
                error += line + "\n"
            #
            return error
        else:
            return default_message
        #
