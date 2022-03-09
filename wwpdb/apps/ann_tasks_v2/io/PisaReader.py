##
# File:  PisaReader.py
# Date:  April 14, 2012
#
# Updates:
#         5-July-2012 jdw  add read method and improved exception handling
#                          add method to count assembly sets
#         04-Oct-2017  zf  add __reCalculateCompositions(), __getAsuChainOrder(), __reCalculateComposition()
#                          add __reCalculateCompositionBasedAsuOrder(), __reCalculateCompositionBasedCurOrder()
#
##
"""
DOM parser for PISA assembly data files.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.001"


import os
import os.path
import sys
import traceback
from xml.dom import minidom

from wwpdb.io.misc.FormatOut import FormatOut


class PisaAssemblyReader(object):
    def __init__(self, verbose=True, log=sys.stderr):
        self.__lfh = log
        self.__verbose = verbose
        self.__aD = {}
        self.__gD = {}
        self.__sD = {}
        self.__dom = None

    def getSummaryDict(self):
        return self.__gD

    def getAssemblySetDict(self):
        return self.__sD

    def getAssemblyDict(self):
        return self.__aD

    def getAssemblySetCount(self):
        if "total_asm" in self.__gD and (self.__gD["total_asm"] is not None):
            return int(self.__gD["total_asm"])
        else:
            return 0

    def read(self, filePath):
        #
        try:
            self.__aD = {}
            self.__gD = {}
            self.__sD = {}
            #
            if not os.access(filePath, os.F_OK):
                return False
            self.__dom = minidom.parse(filePath)
            return self.__getData()
        except:  # noqa: E722 pylint: disable=bare-except
            self.__lfh.write("+PisaAssemblyReader(read) read failed for file  %s\n" % filePath)
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False
        #

    def __getData(self):
        nodeList = ["name", "status", "total_asm", "multimeric_state", "all_chains_at_identity"]
        gD = {}
        sD = {}
        for node in nodeList:
            gD[node] = None
        els = self.__dom.getElementsByTagName("pisa_results")
        for el in els:
            for child in el.childNodes:
                if child.nodeType != child.ELEMENT_NODE:
                    continue
                if len(child.childNodes) == 0:
                    continue
                node = str(child.nodeName)
                if node in nodeList:
                    gD[node] = child.childNodes[0].nodeValue
                if node == "asm_set":
                    tD = self.__getAssemblySet(child)
                    tId = int(str(tD["ser_no"]))
                    sD[tId] = tD
                if node == "asu_complex":
                    tD = self.__getAssemblySet(child)
                    tD["ser_no"] = 0
                    sD[0] = tD

        # make assembly dictionary
        aD = {}
        for _k, v in sD.items():
            for assem in v["assembly_list"]:
                uId = str(assem["serial_no"])
                assem["set_ser_no"] = int(v["ser_no"])
                assem["all_chains_at_identity"] = v["all_chains_at_identity"]
                aD[int(uId)] = assem

        self.__gD = gD
        self.__sD = sD
        self.__aD = aD

        self.__reCalculateCompositions()

        return True

    def __getAssemblySet(self, el):
        nodeList = ["ser_no", "all_chains_at_identity"]

        sD = {}
        for node in nodeList:
            sD[node] = None
        sD["assembly_list"] = []
        for child in el.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if len(child.childNodes) == 0:
                continue
            if child.nodeName in nodeList:
                sD[str(child.nodeName)] = child.childNodes[0].nodeValue
            elif child.nodeName == "assembly":
                sD["assembly_list"].append(self.__getAssembly(child))
            else:
                pass

        return sD

    def __getAssembly(self, el):
        nodeList = [
            "serial_no",
            "id",
            "size",
            "mmsize",
            "score",
            "diss_energy",
            "asa",
            "bsa",
            "entropy",
            "diss_area",
            "int_energy",
            "n_uc",
            "n_diss",
            "symNumber",
            "formula",
            "composition",
        ]
        aD = {}
        for node in nodeList:
            aD[node] = None
        aD["molecule_list"] = []

        for child in el.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if len(child.childNodes) == 0:
                continue
            if child.nodeName in nodeList:
                aD[str(child.nodeName)] = child.childNodes[0].nodeValue
            elif child.nodeName == "molecule":
                aD["molecule_list"].append(self.__getMolecule(child))
            else:
                pass

        return aD

    def __getMolecule(self, el):
        nodeList = [
            "chain_id",
            "visual_id",
            "rxx",
            "rxy",
            "rxz",
            "tx",
            "ryx",
            "ryy",
            "ryz",
            "ty",
            "rzx",
            "rzy",
            "rzz",
            "tz",
            "rxx-f",
            "rxy-f",
            "rxz-f",
            "tx-f",
            "ryx-f",
            "ryy-f",
            "ryz-f",
            "ty-f",
            "rzx-f",
            "rzy-f",
            "rzz-f",
            "tz-f",
            "symId",
        ]

        mD = {}
        for node in nodeList:
            mD[node] = None

        for child in el.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if len(child.childNodes) == 0:
                continue
            if child.nodeName in nodeList:
                mD[str(child.nodeName)] = child.childNodes[0].nodeValue
            else:
                pass
        return mD

    def __reCalculateCompositions(self):
        chainOrder = self.__getAsuChainOrder()
        for _k, sD in self.__sD.items():
            for aD in sD["assembly_list"]:
                aD["composition"] = self.__reCalculateComposition(aD["molecule_list"], chainOrder)
                #
            #
        #

    def __getAsuChainOrder(self):
        if 0 not in self.__sD:
            return []
        #
        origChainOrder = []
        for mD in self.__sD[0]["assembly_list"][0]["molecule_list"]:
            chain_id = mD["chain_id"]
            idx = chain_id.find("]")
            if idx != -1:
                chain_id = chain_id[: idx + 1]
            #
            if chain_id not in origChainOrder:
                origChainOrder.append(chain_id)
            #
        #
        sortChainOrder = []
        for chain_id in origChainOrder:
            if chain_id[0] == "[":
                continue
            #
            sortChainOrder.append(chain_id)
        #
        for chain_id in origChainOrder:
            if chain_id[0] != "[":
                continue
            #
            sortChainOrder.append(chain_id)
        #
        return sortChainOrder

    def __reCalculateComposition(self, molList, chainOrder):
        idx = len(chainOrder)
        orderList = []
        chnList = []
        myMap = {}
        for mD in molList:
            chain_id = mD["chain_id"]
            idx = chain_id.find("]")
            if idx != -1:
                chain_id = chain_id[: idx + 1]
            #
            if chain_id in myMap:
                myMap[chain_id] += 1
            else:
                myMap[chain_id] = 1
                chnList.append(chain_id)
                if chain_id in chainOrder:
                    orderList.append([chain_id, chainOrder.index(chain_id)])
                else:
                    orderList.append([chain_id, idx])
                    idx += 1
                #
            #
        #
        if chainOrder:
            return self.__reCalculateCompositionBasedAsuOrder(orderList, myMap)
        else:
            return self.__reCalculateCompositionBasedCurOrder(chnList, myMap)
        #

    def __reCalculateCompositionBasedAsuOrder(self, orderList, myMap):
        orderList.sort(key=lambda data: data[1])
        compList = []
        for tList in orderList:
            if myMap[tList[0]] > 1:
                compList.append(tList[0] + "(" + str(myMap[tList[0]]) + ")")
            else:
                compList.append(tList[0])
            #
        #
        return ",".join(compList)

    def __reCalculateCompositionBasedCurOrder(self, chnList, myMap):
        compList = []
        for chain_id in chnList:
            if chain_id[0] == "[":
                continue
            #
            if myMap[chain_id] > 1:
                compList.append(chain_id + "(" + str(myMap[chain_id]) + ")")
            else:
                compList.append(chain_id)
            #
        #
        for chain_id in chnList:
            if chain_id[0] != "[":
                continue
            #
            if myMap[chain_id] > 1:
                compList.append(chain_id + "(" + str(myMap[chain_id]) + ")")
            else:
                compList.append(chain_id)
            #
        #
        return ",".join(compList)

    def dump(self, fileName):
        out = FormatOut()
        out.autoFormat("PISA assembly summary", self.__gD, 3, 3)
        out.autoFormat("PISA assembly dictionary", self.__aD, 3, 3)
        out.autoFormat("PISA assembly set dictionary", self.__sD, 3, 3)
        out.write(fileName)


if __name__ == "__main__":
    # pR=PisaAssemblyReader(verbose=True)
    # pR.read("./data/pisa-assemblies.xml")
    # pR.dump("pisa-assemblies.dump")
    pass
