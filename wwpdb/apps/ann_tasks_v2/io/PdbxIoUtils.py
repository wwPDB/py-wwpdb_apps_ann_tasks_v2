##
# File:  PdbxIoUtils.py
# Date:  09-NovFeb-2018 - Taken from sequence module and trimmed down
#
# Updates:
#
##
"""
Utility methods for accessing model for assembly info.

Content specific classes operate on PDBx container object input.

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

from mmcif.io.IoAdapterPy import IoAdapterPy

# from mmcif.api.PdbxContainers import *


class PdbxFileIo(object):

    """Read PDBx data files and package content as PDBx container object or container object list
    Write PDBx data using source PDBx container object list source content.

    PDBx container object represents
    """

    def __init__(self, ioObj=IoAdapterPy(), verbose=True, log=sys.stderr):
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
        # outDirPath = self.__getOutDir(fPath)
        try:
            cList = self.__ioObj.readFile(fPath, outDirPath=fPath)
            return cList
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return []

    def writeContainerList(self, fPath, containerList=None):
        try:
            return self.__ioObj.writeFile(fPath, containerList)
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False


class ModelFileIo(object):

    """
    Assemble sample and coordinate sequence details from model coordinate data file.

    """

    def __init__(self, dataContainer=None, verbose=True, log=sys.stderr):
        self.__currentContainer = dataContainer
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__polymerEntityChainDict = {}
        self.__branchChainIdList = []
        self.__chainPolymerEntityDict = {}
        self.__buildPolymerEntityChainDict()

    def getContainerName(self):
        return self.__currentContainer.getName()

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

    def getPolymerEntityList(self):
        """Returns a list of polymer entity id's  of 'type=polymer' or 'type=branched')"""
        try:
            catObj = self.__currentContainer.getObj("entity")
            myList = ["id", "type"]
            retList = self.__getAttributeDictList(catObj=catObj, attributeList=myList)
            #
            eList = []
            for rD in retList:
                if ("id" not in rD) or (not rD["id"]) or ("type" not in rD) or (not rD["type"]):
                    continue
                #
                if (rD["type"] == "polymer") or (rD["type"] == "branched"):
                    eList.append(rD["id"])
                #
            #
            return eList
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+PdbxIoUtils.getPolymerEntityList() WARNING - Likely missing entity data category.\n")
            #
        #
        return []

    def getPdbChainIdList(self, entityId):
        if len(self.__polymerEntityChainDict) == 0:
            self.__buildPolymerEntityChainDict()
        #
        if entityId in self.__polymerEntityChainDict:
            return self.__polymerEntityChainDict[entityId]
        #
        return []

    def getEntityDescription(self, entityId):
        """
        Return a the _entity.pdbx_description or empty string.
        """
        try:
            catObj = self.__currentContainer.getObj("entity")
            if catObj.hasAttribute("pdbx_description"):
                vals = catObj.selectValuesWhere("pdbx_description", entityId, "id")
            else:
                vals = []
            return self.__firstOrDefault(vals, "")
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def getEntityPolyList(self):
        """Returns a list of polymer entity ids"""
        if not self.__currentContainer.exists("entity_poly"):
            return []
        #
        catObj = self.__currentContainer.getObj("entity_poly")
        nRows = catObj.getRowCount()

        eList = []
        for ii in range(0, nRows):
            eId = catObj.getValue("entity_id", ii)
            eList.append(eId)
        return eList

    def getPolymerEntityChainDict(self):
        if len(self.__polymerEntityChainDict) == 0:
            self.__buildPolymerEntityChainDict()
        #
        return self.__polymerEntityChainDict, self.__branchChainIdList

    def getBranchChainIdList(self):
        return self.__branchChainIdList

    def __buildPolymerEntityChainDict(self):
        """Build entity chain mapping information --  Chain details must be provided"""
        self.__polymerEntityChainDict = {}
        self.__branchChainIdList = []
        self.__buildBranchEntityChainDict()
        #
        if not self.__currentContainer.exists("entity_poly"):
            return
        #
        catObj = self.__currentContainer.getObj("entity_poly")
        myList = ["entity_id", "pdbx_strand_id"]
        retList = self.__getAttributeDictList(catObj=catObj, attributeList=myList)
        #
        for rD in retList:
            if ("entity_id" not in rD) or (not rD["entity_id"]) or ("pdbx_strand_id" not in rD) or (not rD["pdbx_strand_id"]):
                continue
            #
            rList = []
            for ch in rD["pdbx_strand_id"].split(","):
                if len(ch) == 0 or ch in [".", "?"]:
                    continue
                rList.append(str(ch).strip())
            #
            if rList:
                self.__polymerEntityChainDict[rD["entity_id"]] = rList
            #
        #
        self.__chainPolymerEntityDict = {}
        for eId, cList in self.__polymerEntityChainDict.items():
            for cId in cList:
                self.__chainPolymerEntityDict[cId] = eId
            #
        #

    def __buildBranchEntityChainDict(self):
        """Build branch entity chain mapping information from pdbx_branch_scheme category"""
        if not self.__currentContainer.exists("pdbx_branch_scheme"):
            return
        #
        catObj = self.__currentContainer.getObj("pdbx_branch_scheme")
        myList = ["entity_id", "pdb_asym_id"]
        retList = self.__getAttributeDictList(catObj=catObj, attributeList=myList)
        #
        for rD in retList:
            if ("entity_id" not in rD) or (not rD["entity_id"]) or ("pdb_asym_id" not in rD) or (not rD["pdb_asym_id"]):
                continue
            #
            if rD["pdb_asym_id"] not in self.__branchChainIdList:
                self.__branchChainIdList.append(rD["pdb_asym_id"])
            #
            if rD["entity_id"] in self.__polymerEntityChainDict:
                if rD["pdb_asym_id"] not in self.__polymerEntityChainDict[rD["entity_id"]]:
                    self.__polymerEntityChainDict[rD["entity_id"]].append(rD["pdb_asym_id"])
                #
            else:
                self.__polymerEntityChainDict[rD["entity_id"]] = [rD["pdb_asym_id"]]
            #
        #

    def getAssemblyDetails(self):
        """
        #
        loop_
        _pdbx_struct_assembly.id
        _pdbx_struct_assembly.details
        _pdbx_struct_assembly.method_details
        _pdbx_struct_assembly.oligomeric_count
        1 author_defined_assembly   ?    3
        2 software_defined_assembly PISA 4
        #
        loop_
        _pdbx_struct_assembly_gen.assembly_id
        _pdbx_struct_assembly_gen.oper_expression
        _pdbx_struct_assembly_gen.asym_id_list
        1 1       A,B,C,D,E,F,G,H,I,J,K
        1 2       A,B,C,D,E,F,G,H,I,J,K
        1 3       A,B,C,D,E,F,G,H,I,J,K
        2 1,4,5,6 A,B,C,D,E,F,G,H,I,J,K
        #
        loop_
        _pdbx_struct_assembly_prop.biol_id
        _pdbx_struct_assembly_prop.type
        _pdbx_struct_assembly_prop.value
        _pdbx_struct_assembly_prop.details
        2 "SSA (A^2)"  58580 ?
        2 "ABSA (A^2)" 31160 ?
        2 MORE         -337  ?
        #
        loop_
        _pdbx_struct_oper_list.id
        _pdbx_struct_oper_list.type
        _pdbx_struct_oper_list.name
        _pdbx_struct_oper_list.matrix[1][1]
        _pdbx_struct_oper_list.matrix[1][2]
        _pdbx_struct_oper_list.matrix[1][3]
        _pdbx_struct_oper_list.vector[1]
        _pdbx_struct_oper_list.matrix[2][1]
        _pdbx_struct_oper_list.matrix[2][2]
        _pdbx_struct_oper_list.matrix[2][3]
        _pdbx_struct_oper_list.vector[2]
        _pdbx_struct_oper_list.matrix[3][1]
        _pdbx_struct_oper_list.matrix[3][2]
        _pdbx_struct_oper_list.matrix[3][3]
        _pdbx_struct_oper_list.vector[3]
        1 "identity operation"         1_555 1.0000000000  0.0000000000 0.0000000000 0.0000000000   0.0000000000 1.0000000000  0.0000000000 0.0000000000  0.0000000000 0.0000000000 1.0000000000  0.0000000000  # noqa: E501
        2 "crystal symmetry operation" 2_566 -1.0000000000 0.0000000000 0.0000000000 0.0000000000   0.0000000000 -1.0000000000 0.0000000000 95.9710000000 0.0000000000 0.0000000000 1.0000000000  137.3490000000  # noqa: E501
        3 "crystal symmetry operation" 2_656 -1.0000000000 0.0000000000 0.0000000000 80.9760000000  0.0000000000 -1.0000000000 0.0000000000 0.0000000000  0.0000000000 0.0000000000 1.0000000000  137.3490000000  # noqa: E501
        4 "crystal symmetry operation" 2_765 -1.0000000000 0.0000000000 0.0000000000 161.9520000000 0.0000000000 -1.0000000000 0.0000000000 95.9710000000 0.0000000000 0.0000000000 1.0000000000  0.0000000000  # noqa: E501
        5 "crystal symmetry operation" 3_757 -1.0000000000 0.0000000000 0.0000000000 161.9520000000 0.0000000000 1.0000000000  0.0000000000 0.0000000000  0.0000000000 0.0000000000 -1.0000000000 274.6980000000  # noqa: E501
        6 "crystal symmetry operation" 4_567 1.0000000000  0.0000000000 0.0000000000 0.0000000000   0.0000000000 -1.0000000000 0.0000000000 95.9710000000 0.0000000000 0.0000000000 -1.0000000000 274.6980000000  # noqa: E501
        #
        """
        assemL = []
        assemGenL = []
        assemOpL = []
        if not self.__currentContainer.exists("pdbx_struct_assembly"):
            return assemL, assemGenL, assemOpL
        #
        catObj = self.__currentContainer.getObj("pdbx_struct_assembly")
        myList = ["id", "details", "method_details", "oligomeric_count"]
        assemL = self.__getAttributeDictList(catObj=catObj, attributeList=myList)
        #
        catObj = self.__currentContainer.getObj("pdbx_struct_assembly_gen")
        myList = ["assembly_id", "oper_expression", "asym_id_list"]
        assemGenL = self.__getAttributeDictList(catObj=catObj, attributeList=myList)

        catObj = self.__currentContainer.getObj("pdbx_struct_oper_list")
        myList = ["id", "type", "name"]
        assemOpL = self.__getAttributeDictList(catObj=catObj, attributeList=myList)

        return assemL, assemGenL, assemOpL

    def __getAttributeDictList(self, catObj, attributeList):
        #
        rList = []
        try:
            colNames = list(catObj.getAttributeList())
            nRows = catObj.getRowCount()
            for iRow in range(0, nRows):
                rD = {}
                row = catObj.getRow(iRow)
                for col in attributeList:
                    if col in colNames:
                        val = str(row[colNames.index(col)])
                        if val is None:
                            val = ""
                        elif (val == ".") or (val == "?"):
                            val = ""
                        rD[col] = val
                    else:
                        rD[col] = ""
                rList.append(rD)
        except:  # noqa: E722 pylint: disable=bare-except
            self.__lfh.write("PdbxIoUtils.__getAttributeDictList - failed ")
            traceback.print_exc(file=self.__lfh)

        return rList

    def __getDepositorDetails(self, tableName, myList):
        """Returns a dictionary of assembly details using a list of attributes"""

        if not self.__currentContainer.exists(tableName):
            return []

        catObj = self.__currentContainer.getObj(tableName)

        return self.__getAttributeDictList(catObj, myList)

    def getDepositorAssemblyDetails(self):
        """Returns a dictionary of assembly details provided at deposition."""
        myList = ["id", "details", "matrix_flag", "method_details", "oligomeric_count", "oligomeric_details", "upload_file_name"]

        return self.__getDepositorDetails("pdbx_struct_assembly_depositor_info", myList)

    def getDepositorAssemblyDetailsRcsb(self):
        """Returns a dictionary of assembly details provided at deposition (for current system)"""
        myList = ["id", "details", "rcsb_description", "method_details", "pdbx_aggregation_state", "pdbx_assembly_method", "pdbx_formula_weight", "pdbx_formula_weight_method"]

        return self.__getDepositorDetails("struct_biol", myList)

    def getDepositorAssemblyGen(self):
        """Returns a dictionary of assembly details provided at deposition (for current system)"""
        myList = ["id", "asym_id_list", "assembly_id", "oper_expression", "full_matrices", "at_unit_matrix", "chain_id_list", "all_chains", "helical_rotation", "helical_rise"]

        return self.__getDepositorDetails("pdbx_struct_assembly_gen_depositor_info", myList)

    def getDepositorStructOperList(self):
        """Returns a dictionary of _pdbx_struct_oper_list_depositor_info."""
        myList = [
            "id",
            "name",
            "symmetry_operation",
            "type",
            "matrix[1][1]",
            "matrix[1][2]",
            "matrix[1][3]",
            "matrix[2][1]",
            "matrix[2][2]",
            "matrix[2][3]",
            "matrix[3][1]",
            "matrix[3][2]",
            "matrix[3][3]",
            "vector[1]",
            "vector[2]",
            "vector[3]",
        ]

        return self.__getDepositorDetails("pdbx_struct_oper_list_depositor_info", myList)

    def getDepositorAssemblyEvidence(self):
        """Returns a dictionary of _pdbx_struct_oper_list_depositor_info."""
        myList = ["id", "assembly_id", "experimental_support", "details"]

        return self.__getDepositorDetails("pdbx_struct_assembly_auth_evidence", myList)

    def getDepositorAssemblyClassification(self):
        """Returns a dictionary of _pdbx_struct_assembly_auth_classification"""
        myList = ["assembly_id", "reason_for_interest"]

        return self.__getDepositorDetails("pdbx_struct_assembly_auth_classification", myList)


if __name__ == "__main__":
    pass
