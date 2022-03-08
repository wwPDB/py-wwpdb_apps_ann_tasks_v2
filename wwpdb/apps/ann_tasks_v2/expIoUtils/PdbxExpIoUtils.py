##
# File:  PdbxExpIoUtils.py
# Date:  30-Feb-2014
#
# Updates:
#
##
"""
Utility methods applying routine edits to PDBx experimental reflection data and supporting
categories  -


"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import os
import sys
import traceback
import tempfile

from mmcif.io.IoAdapterCore import IoAdapterCore
from mmcif.api.PdbxContainers import DataContainer
from mmcif.api.DataCategory import DataCategory


class PdbxExpFileIo(object):
    """Read PDBx data files and package content as PDBx container object or container object list

    Write PDBx data using source PDBx container object list source content.

    Updated selected items and container identifiers following current archiving conventions
    for the experimental reflection file.

    """

    def __init__(self, ioObj=IoAdapterCore(), verbose=True, log=sys.stderr):
        """Input processing can be performed using either native Python or C++ Io libraries
        by choosing the appropriate input adapter.
        """

        self.__ioObj = ioObj
        self.__verbose = verbose
        self.__lfh = log

    def __getOutDir(self, fPath):
        """Attempts to find a writeable place for log file during read"""
        for dp in [os.path.dirname(fPath), ".", tempfile.gettempdir()]:
            if os.access(dp, os.W_OK):
                return dp

    def getContainer(self, fPath, index=0):
        outDirPath = self.__getOutDir(fPath)
        try:
            cList = self.__ioObj.readFile(fPath, outDirPath=outDirPath)
            return cList[index]
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return None

    def getContainerList(self, fPath):
        outDirPath = self.__getOutDir(fPath)
        try:
            cList = self.__ioObj.readFile(fPath, outDirPath=outDirPath)
            return cList
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return []

    def writeContainerList(self, fPath, containerList=None):
        try:
            self.__orderContainers(containerList)
            return self.__ioObj.writeFile(fPath, containerList)
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False

    def __orderContainer(self, container):
        stdList = ["audit", "cell", "diffrn", "diffrn_radiation_wavelength", "diffrn_reflns", "entry", "exptl_crystal", "reflns_scale", "symmetry"]
        tailList = ["refln", "diffrn_refln"]
        #
        dC = DataContainer(name=container.getName())
        #
        nL = container.getObjNameList()
        for cn in stdList:
            if container.exists(name=cn):
                dC.append(container.getObj(name=cn))
                nL.remove(cn)
        # whats left --
        for cn in nL:
            if cn not in tailList:
                dC.append(container.getObj(name=cn))
        for cn in tailList:
            if container.exists(name=cn):
                dC.append(container.getObj(name=cn))
        return dC

    def __orderContainers(self, containerList):
        try:
            for ii in range(len(containerList)):
                containerList[ii] = self.__orderContainer(containerList[ii])
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)

        return False

    def __getUniqueList(self, num):
        letterList = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
        #
        uniqueList = []
        uniqueList.append("")
        found = False
        start = 0
        while True:
            end = len(uniqueList)
            for letterCode in letterList:
                for ii in range(start, end):
                    uniqueList.append(uniqueList[ii] + letterCode)
                    if len(uniqueList) > num:
                        found = True
                        break
                    #
                #
                if found:
                    break
                #
            #
            if found:
                break
            #
            start = end
        #
        return uniqueList

    def updateContainerNames(self, idCode, containerList):
        try:
            suffixList = self.__getUniqueList(len(containerList) + 1)
            for ii, container in enumerate(containerList):
                cName = "r" + str(idCode).lower() + suffixList[ii] + "sf"
                container.setName(cName)
            #
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            #
        #
        return False

    def updateEntryIds(self, idCode, containerList):
        catNameList = [("cell", "entry_id"), ("entry", "id"), ("symmetry", "entry_id")]
        try:
            for _ii, container in enumerate(containerList):
                for catName, attribName in catNameList:
                    catObj = container.getObj(catName)
                    if catObj is not None:
                        nRows = catObj.getRowCount()
                        if nRows == 1:
                            _ok = catObj.setValue(value=idCode, attributeName=attribName, rowIndex=0)  # noqa: F841
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
        return False

    def updateRadiationWavelength(self, muList, container):
        try:
            if self.__verbose:
                self.__lfh.write("+PdbxExpIoUtils.updateRadiationWavelength() updating wavelength setting in container %r updMuList %r\n" % (container.getName(), muList))
            #
            dc = DataCategory("diffrn_radiation_wavelength")
            dc.appendAttribute("id")
            dc.appendAttribute("wavelength")
            # dc.appendAttribute('wt')
            for _ii, (cid, mu, _wt) in enumerate(muList):
                dc.append([cid, mu])
            dc.printIt(fh=self.__lfh)

            catObj = container.getObj("diffrn_radiation_wavelength")
            if catObj is not None:
                self.__lfh.write("+PdbxExpIoUtils.updateRadiationWavelength() replacing wavelength setting in container %r\n" % container.getName())
                catObj.printIt(fh=self.__lfh)

                container.replace(dc)
            else:
                self.__lfh.write("+PdbxExpIoUtils.updateRadiationWavelength() adding wavelength setting in container %r\n" % container.getName())
                container.append(dc)

            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("PdbxExpFileIo.updateRadiationWavelength failing \n")
                traceback.print_exc(file=self.__lfh)
        return False


class PdbxExpIoUtils(object):
    """
    Extract selected items from model or reflection data file -
    """

    def __init__(self, dataContainer=None, verbose=True, log=sys.stderr):
        self.__currentContainer = dataContainer
        self.__verbose = verbose
        self.__lfh = log
        #

    def getContainerName(self):
        return self.__currentContainer.getName()

    def getEntryId(self):
        """Return _entry.id"""
        try:
            catObj = self.__currentContainer.getObj("entry")
            return catObj.getValue("id", 0)
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def getDbCode(self, dbId):
        """Return the database code for the input database id/name"""
        try:
            catObj = self.__currentContainer.getObj("database_2")
            vals = catObj.selectValuesWhere("database_code", dbId, "database_id")
            return self.__firstOrDefault(vals, default="NOID")
        except:  # noqa: E722 pylint: disable=bare-except
            return "NOID"

    def getDiffrnSourceIds(self):
        """Return the list of diffrn id's in diffrn_source category"""
        idList = []
        try:
            catObj = self.__currentContainer.getObj("diffrn_source")
            nRows = catObj.getRowCount()
            for ii in range(0, nRows):
                idList.append(catObj.getValue(attributeName="diffrn_id", rowIndex=ii))
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return idList

    def getDiffrnIds(self):
        """Return the list of diffrn id's in diffrn category"""
        idList = []
        try:
            catObj = self.__currentContainer.getObj("diffrn")
            nRows = catObj.getRowCount()
            for ii in range(0, nRows):
                idList.append(catObj.getValue(attributeName="id", rowIndex=ii))
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return idList

    def getDiffrnSourceWavelengthList(self, diffrnId):
        """Return the database code for the input database id/name"""
        try:
            catObj = self.__currentContainer.getObj("diffrn_source")
            vals = catObj.selectValuesWhere("pdbx_wavelength_list", diffrnId, "diffrn_id")
            return self.__firstOrDefault(vals, default=None)
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def getDiffrnSourceWavelengthListAsList(self, diffrnId):
        """Return the database code for the input database id/name"""
        muList = []
        try:
            catObj = self.__currentContainer.getObj("diffrn_source")
            vals = catObj.selectValuesWhere("pdbx_wavelength_list", diffrnId, "diffrn_id")
            sVal = self.__firstOrDefault(vals, default=None)
            # check for range --
            if sVal.find("-") == -1:
                muList = [(str(ii + 1), str(mu).strip(), "1.0") for ii, mu in enumerate(sVal.split("-"))]
            else:
                muList = [(str(ii + 1), str(mu).strip(), "1.0") for ii, mu in enumerate(sVal.split(","))]
            return muList
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)

        return muList

    def getDiffrnSourceWavelength(self, diffrnId):
        """Return the database code for the input database id/name"""
        try:
            catObj = self.__currentContainer.getObj("diffrn_source")
            vals = catObj.selectValuesWhere("pdbx_wavelength", diffrnId, "diffrn_id")
            return self.__firstOrDefault(vals, default=None)
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def getDiffrnRadiationWavelengthList(self):
        """Return a dictionary of wavelength data from category diffrn_radiation_wavelength"""
        muList = []
        try:
            catObj = self.__currentContainer.getObj("diffrn_radiation_wavelength")
            nRows = catObj.getRowCount()
            for ii in range(0, nRows):
                muId = str(catObj.getValue(attributeName="id", rowIndex=ii))
                mu = catObj.getValue(attributeName="wavelength", rowIndex=ii)
                if self.__isEmptyValue(mu):
                    mu = None
                if catObj.hasAttribute("wt"):
                    wt = catObj.getValueOrDefault(attributeName="wt", rowIndex=ii, defaultValue="1.0")
                else:
                    wt = "1.0"
                muList.append((muId, mu, wt))
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        return muList

    def __isEmptyValue(self, val):
        if (val is None) or (len(val) == 0) or (val in [".", "?"]):
            return True
        else:
            return False

    def __firstOrDefault(self, valList, default=""):
        if len(valList) > 0 and not self.__isEmptyValue(valList[0]):
            return valList[0]
        else:
            return default

    # def __getFirstValueFromList(self, attributeNameList, catObj=None, rowIndex=0):
    #     """Return the value from the first non null attribute found in the input attribute list
    #     from the input category object/rowIndex.
    #     """
    #     try:
    #         for at in attributeNameList:
    #             if catObj.hasAttribute(at):
    #                 val = catObj.getValue(at, rowIndex)
    #                 if not self.__isEmptyValue(val):
    #                     return val
    #         return ""
    #     except:  # noqa: E722 pylint: disable=bare-except
    #         return None


if __name__ == "__main__":
    pass
