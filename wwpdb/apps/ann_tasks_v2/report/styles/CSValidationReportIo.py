##
# File: CSValidationReportIo.py
#
# Date: 08-Dec-2024  Zukang Feng
#
# Update:
#
##
"""
Wrapper for reading NMR chemical shifts validation information from PDB Validation XML report.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zukang.feng@rcsb.org"
__license__ = "Apache 2.0"

import sys
import traceback

from wwpdb.apps.ann_tasks_v2.correspnd.ValidateXml import ValidateXml
from wwpdb.apps.ann_tasks_v2.report.styles.CSValidationReport import CSValidationReportStyle


class CSValidationReportIo(object):
    """ Methods for reading NMR chemical shifts validation information details.
    """

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__filePath = None
        self.__idCode = None
        #
        self.__st = CSValidationReportStyle()
        #
        self.__dataDict = {}

    def setFilePath(self, filePath, idCode=None):
        """ Specify the file path for the target.
        """
        self.__filePath = filePath
        self.__idCode = idCode
        #
        if self.__verbose:
            self.__lfh.write("+CSValidationReportIo.setFilePath() filePath=%r idCode=%r\n" % (self.__filePath, self.__idCode))
        #
        self.__readFile()

    def getCurrentContainerId(self):
        """
        """
        return self.__idCode

    def getCurrentCategoryNameList(self):
        """
        """
        try:
            catList = []
            #
            categoryList = self.__st.getCategoryList()
            for category in categoryList:
                if (category in self.__dataDict) and self.__dataDict[category]:
                    catList.append(category)
                #
            #
            return catList
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+CSValidationReportIo.__readFile() failing\n")
                traceback.print_exc(file=self.__lfh)
            #
            return []
        #

    def getCategory(self, catName="pdbx_nmr_chemical_shift_validation_statistics"):
        """
        """
        if (catName in self.__dataDict) and self.__dataDict[catName]:
            return self.__dataDict[catName]
        #
        return []

    def __readFile(self):
        """ Read XML Validation Report
        """
        try:
            categoryList = self.__st.getCategoryList()

            xmlObj = ValidateXml(FileName=self.__filePath)
            stsTupl = xmlObj.getChemicalShiftStatistics()
            if stsTupl[0] > 0:
                # First category categoryList[0] = "pdbx_nmr_chemical_shift_validation_statistics"
                itemList = self.__st.getItemNameList(categoryList[0])
                dd = {}
                for idx, item in enumerate(itemList):
                    dd[item] = str(stsTupl[idx])
                #
                self.__dataDict[categoryList[0]] = [dd]
            #
            notFoundList = xmlObj.getNotFoundInStructureCsList()
            if len(notFoundList) > 0:
                # Second category categoryList[1] = "pdbx_nmr_chemical_shift_not_found_list"
                itemList = self.__st.getItemNameList(categoryList[1])
                retList = []
                for dataL in notFoundList:
                    dd = {}
                    for idx, item in enumerate(itemList):
                        dd[item] = dataL[idx]
                    #
                    retList.append(dd)
                #
                self.__dataDict[categoryList[1]] = retList
            #
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+CSValidationReportIo.__readFile() failing\n")
                traceback.print_exc(file=self.__lfh)
            #
        #
