##
# File:  ValidateXml.py
# Date:  14-Aug-2014
# Updates:
##
"""
Parse validation XML report

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2014 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

from xml.dom import minidom
import sys
import traceback


class ValidateXml(object):
    """Class responsible for parsing validation XML report"""

    def __init__(self, FileName=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        # self.__verbose = verbose
        # self.__lfh = log
        self.__xmlFile = FileName
        self.__doc = minidom.parse(self.__xmlFile)
        #
        self.clashMap = {}
        self.clashOutliers = []
        self.__outlierMap = {}
        self.__outlierResult = {}
        self.__calculated_completeness = ""
        self.__number_of_errors_while_mapping = 0
        self.__number_of_warnings_while_mapping = 0
        self.__not_found_in_structure_cs_list = []
        self.__not_found_residue_in_structure_cs_list = []
        self.__cs_outlier_list = []
        self.__cs_referencing_offset_list = []
        self.__has_cs_referencing_offset_flag = False
        #
        self.__getOutlierDefinition()
        self.__parse()

    def getOutlier(self, Type):
        """ """
        if Type in self.__outlierResult:
            return self.__outlierResult[Type]
        #
        return []

    def getClashOutliers(self):
        """ """
        return self.clashOutliers

    def getCalculatedCompleteness(self):
        """ """
        return self.__calculated_completeness

    def getCsMappingErrorNumber(self):
        """ """
        return self.__number_of_errors_while_mapping

    def getCsMappingWarningNumber(self):
        """ """
        return self.__number_of_warnings_while_mapping

    def getNotFoundInStructureCsList(self):
        """ """
        return self.__not_found_in_structure_cs_list

    def getNotFoundResidueInStructureCsList(self):
        """ """
        return self.__not_found_residue_in_structure_cs_list

    def getCsOutliers(self):
        """ """
        return self.__cs_outlier_list

    def getCsReferencingOffsetFlag(self):
        """ """
        return self.__has_cs_referencing_offset_flag

    def __getOutlierDefinition(self):
        """ """
        self.__outlierMap["torsion-outlier"] = ["phi", "psi"]
        self.__outlierMap["mog-ring-outlier"] = ["atoms", "mean", "mindiff", "stdev", "numobs"]
        self.__outlierMap["mog-angle-outlier"] = ["atoms", "mean", "mindiff", "stdev", "numobs", "Zscore", "obsval"]
        self.__outlierMap["mog-torsion-outlier"] = ["atoms", "mean", "mindiff", "stdev", "numobs", "obsval"]
        self.__outlierMap["mog-bond-outlier"] = ["atoms", "mean", "mindiff", "stdev", "numobs", "Zscore", "obsval"]
        self.__outlierMap["chiral-outlier"] = ["atom", "problem"]
        self.__outlierMap["plane-outlier"] = ["omega", "improper", "planeRMSD", "type"]
        self.__outlierMap["bond-outlier"] = ["atom0", "atom1", "mean", "stdev", "obs", "z", "link"]
        self.__outlierMap["angle-outlier"] = ["atom0", "atom1", "atom2", "mean", "stdev", "obs", "z", "link"]
        self.__outlierMap["clash"] = ["atom", "cid", "clashmag", "dist"]

    def __parse(self):
        """ """
        self.__processGlobalValues()
        #
        self.__processChemcalShiftList()
        #
        items = ["model", "ent", "chain", "resname", "resnum", "icode"]  # , 'ligand_geometry_outlier', 'ligand_density_outlier' ]
        #
        for node in self.__doc.getElementsByTagName("ModelledSubgroup"):
            if node.nodeType != node.ELEMENT_NODE:
                continue
            #
            residueInfo = {}
            if node.hasAttribute("rama"):
                val = node.getAttribute("rama").strip()
                if val == "OUTLIER":
                    if not residueInfo:
                        residueInfo = self.__getMapInfo(node, items)
                    #
                    tdir = self.__getMapInfo(node, self.__outlierMap["torsion-outlier"])
                    outlier = residueInfo.copy()
                    outlier.update(tdir)
                    if "torsion-outlier" in self.__outlierResult:
                        self.__outlierResult["torsion-outlier"].append(outlier)
                    else:
                        tlist = []
                        tlist.append(outlier)
                        self.__outlierResult["torsion-outlier"] = tlist
                    #
                #
            #
            if node.hasAttribute("rsrz"):
                val = node.getAttribute("rsrz").strip()
                if float(val) > 5:
                    if not residueInfo:
                        residueInfo = self.__getMapInfo(node, items)
                    #
                    outlier = residueInfo.copy()
                    outlier["rsrz"] = val
                    if "polymer-rsrz-outlier" in self.__outlierResult:
                        self.__outlierResult["polymer-rsrz-outlier"].append(outlier)
                    else:
                        tlist = []
                        tlist.append(outlier)
                        self.__outlierResult["polymer-rsrz-outlier"] = tlist
                    #
                #
            #
            if node.hasAttribute("ligRSRZ"):
                val = node.getAttribute("ligRSRZ").strip()
                if float(val) > 5:
                    if not residueInfo:
                        residueInfo = self.__getMapInfo(node, items)
                    #
                    outlier = residueInfo.copy()
                    outlier["ligRSRZ"] = val
                    if "ligand-rsrz-outlier" in self.__outlierResult:
                        self.__outlierResult["ligand-rsrz-outlier"].append(outlier)
                    else:
                        tlist = []
                        tlist.append(outlier)
                        self.__outlierResult["ligand-rsrz-outlier"] = tlist
                    #
                #
            #

            for childnode in node.childNodes:
                if childnode.nodeType != node.ELEMENT_NODE:
                    continue
                #
                if childnode.tagName not in self.__outlierMap:
                    continue
                #
                if not residueInfo:
                    residueInfo = self.__getMapInfo(node, items)
                #
                tdir = self.__getMapInfo(childnode, self.__outlierMap[childnode.tagName])
                # jmb - removed cut off in reporting outliers in standard bond lengths and bond angles. Uses validation XML cut off instead.
                # if childnode.tagName == 'bond-outlier' or childnode.tagName == 'angle-outlier':
                #    if abs(float(tdir['z'])) <= 10:
                #        continue
                #
                # skip bonds between standard residues in reporting, these are better captured
                #   in pdbx_validate_polymer_linkage - the validation is limited to a maxiumum distance of 1.999 Angstroms
                # in the validation report for unusual bonds
                if childnode.tagName == "bond-outlier":
                    if tdir["atom0"] in ("C", "O3'") and tdir["atom1"] in ("N", "P"):
                        continue

                if childnode.tagName == "mog-angle-outlier" or childnode.tagName == "mog-bond-outlier":
                    if abs(float(tdir["Zscore"])) <= 10:
                        continue
                    #
                #
                if childnode.tagName == "clash":
                    atom_dict = {
                        "dist": tdir["dist"],
                        "atom": tdir["atom"],
                        "clashmag": tdir["clashmag"],
                        "chain": node.getAttribute("chain").strip(),
                        "model": node.getAttribute("model").strip(),
                        "altcode": node.getAttribute("altcode").strip(),
                        "resnum": node.getAttribute("resnum").strip(),
                        "resname": node.getAttribute("resname").strip(),
                    }
                    if float(tdir["dist"]) < 2.2:
                        self.clashMap.setdefault(tdir["cid"], []).append(atom_dict)

                outlier = residueInfo.copy()
                outlier.update(tdir)
                if childnode.tagName in self.__outlierResult:
                    self.__outlierResult[childnode.tagName].append(outlier)
                else:
                    tlist = []
                    tlist.append(outlier)
                    self.__outlierResult[childnode.tagName] = tlist
                #
            #
        #

        if self.clashMap:
            for o in self.clashMap:
                # check that there are two clashes
                if len(self.clashMap[o]) > 1:
                    clashitem = {
                        "res1model": self.clashMap[o][0]["model"],
                        "res1num": self.clashMap[o][0]["resnum"],
                        "res1name": self.clashMap[o][0]["resname"],
                        "res1chain": self.clashMap[o][0]["chain"],
                        "res1alt": self.clashMap[o][0]["altcode"],
                        "res1atom": self.clashMap[o][0]["atom"],
                        "res2model": self.clashMap[o][1]["model"],
                        "res2num": self.clashMap[o][1]["resnum"],
                        "res2chain": self.clashMap[o][1]["chain"],
                        "res2alt": self.clashMap[o][1]["altcode"],
                        "res2name": self.clashMap[o][1]["resname"],
                        "res2atom": self.clashMap[o][1]["atom"],
                        "dist": self.clashMap[o][0]["dist"],
                        "clashmag": self.clashMap[o][0]["clashmag"],
                    }
                    #
                    if clashitem["res1atom"][0] != "H" and clashitem["res2atom"][0] != "H":
                        self.clashOutliers.append(clashitem)
                    #
                #
            #
        #

    def __processGlobalValues(self):
        """ """
        global_values = {}
        Entry = self.__doc.getElementsByTagName("Entry")[0]
        for item in ("DCC_Rfree", "PDB-Rfree", "DCC_R", "PDB-R"):
            if Entry.getAttribute(item) and Entry.getAttribute(item) != "NotAvailable":
                global_values[item] = Entry.getAttribute(item)
            #
        #
        if Entry.getAttribute("DataCompleteness") and Entry.getAttribute("DataCompleteness") != "NotAvailable":
            self.__calculated_completeness = Entry.getAttribute("DataCompleteness")
        #
        for global_list in (("r_free_diff", "DCC_Rfree", "PDB-Rfree"), ("r_work_diff", "DCC_R", "PDB-R")):
            if (global_list[1] in global_values) and (global_list[2] in global_values):
                if abs(float(global_values[global_list[1]]) - float(global_values[global_list[2]])) > 0.05:
                    r_map = {}
                    r_map["diff"] = str(abs(float(global_values[global_list[1]]) - float(global_values[global_list[2]])))
                    r_map[global_list[1]] = global_values[global_list[1]]
                    r_map[global_list[2]] = global_values[global_list[2]]
                    self.__outlierResult[global_list[0]] = [r_map]
                #
            #
        #

    def __processChemcalShiftList(self):
        """ chemical_shift_list.attributes = ( 'block_name', 'file_id', 'file_name', 'list_id', 'number_of_errors_while_mapping', 'number_of_mapped_shifts' \
                        'number_of_parsed_shifts', 'number_of_unparsed_shifts', 'number_of_warnings_while_mapping', 'total_number_of_shifts' )

            unmapped_chemical_shift.attributes = ( 'ambiguity', 'atom', 'chain', 'diagnostic', 'error', 'rescode', 'resnum', 'value' )

            chemical_shift_outlier.attributes = ( 'atom', 'chain', 'method', 'prediction', 'rescode', 'resnum', 'value', 'zscore' )

            referencing_offset.attributes = ( 'atom', 'number_of_measurements', 'precision', 'uncertainty', 'value' )
        """
        csList = self.__doc.getElementsByTagName("chemical_shift_list")
        if len(csList) < 1:
            return
        #
        for csNode in csList:
            if csNode.getAttribute("number_of_errors_while_mapping"):
                self.__number_of_errors_while_mapping += int(csNode.getAttribute("number_of_errors_while_mapping"))
            #
            if csNode.getAttribute("number_of_warnings_while_mapping"):
                self.__number_of_warnings_while_mapping += int(csNode.getAttribute("number_of_warnings_while_mapping"))
            #
            unmappedCsList = csNode.getElementsByTagName("unmapped_chemical_shift")
            if len(unmappedCsList) > 0:
                for unmappedNode in unmappedCsList:
                    notMappedCsResidueFlag = False
                    if unmappedNode.getAttribute("diagnostic").startswith("Residue not found in structure."):
                        notMappedCsResidueFlag = True
                    #
                    csData = []
                    for attribute in ("chain", "resnum", "rescode", "atom", "value", "error", "ambiguity"):
                        if unmappedNode.getAttribute(attribute):
                            csData.append(unmappedNode.getAttribute(attribute))
                        else:
                            csData.append("")
                        #
                    #
                    self.__not_found_in_structure_cs_list.append(csData)
                    if notMappedCsResidueFlag:
                        self.__not_found_residue_in_structure_cs_list.append(csData)
                    #
                #
            #
            csOutlierList = csNode.getElementsByTagName("chemical_shift_outlier")
            if len(csOutlierList) > 0:
                for outlierNode in csOutlierList:
                    csData = []
                    for attribute in ("chain", "resnum", "rescode", "atom", "value", "prediction", "zscore"):
                        if outlierNode.getAttribute(attribute):
                            csData.append(outlierNode.getAttribute(attribute))
                        else:
                            csData.append("")
                        #
                    #
                    self.__cs_outlier_list.append(csData)
                #
            #
            offsetList = csNode.getElementsByTagName("referencing_offset")
            if len(offsetList) > 0:
                for offsetNode in offsetList:
                    csData = []
                    for attribute in ("atom", "number_of_measurements", "precision", "uncertainty", "value"):
                        if offsetNode.getAttribute(attribute):
                            csData.append(offsetNode.getAttribute(attribute))
                        else:
                            csData.append("")
                        #
                    #
                    if csData[2] and csData[3] and csData[4]:
                        # precision = float(csData[2])
                        uncertainty = float(csData[3])
                        value = float(csData[4])
                        if abs(value) < uncertainty:
                            continue
                        #
                        self.__has_cs_referencing_offset_flag = True
                    #
                    self.__cs_referencing_offset_list.append(csData)
                #
            #
        #

    def __getMapInfo(self, node, items):
        """ """
        rmap = {}
        for item in items:
            val = ""
            if node.hasAttribute(item):
                val = node.getAttribute(item).strip()
            #
            rmap[item] = val
        #
        return rmap


if __name__ == "__main__":
    try:
        obj = ValidateXml(FileName=sys.argv[1])
        #       list = obj.getOutlier('polymer-rsrz-outlier')
        #       print(list)
        #       list1 = obj.getOutlier('r_free_diff')
        #       print(list1)
        #       list2 = obj.getOutlier('r_work_diff')
        #       print(list2)
        #       print(obj.getClashOutliers())
        print((obj.getCsMappingErrorNumber()))
        print((obj.getCsMappingWarningNumber()))
        print((len(obj.getNotFoundInStructureCsList())))
        print((len(obj.getCsOutliers())))
        print((obj.getCsReferencingOffsetFlag()))
    except:  # noqa: E722 pylint: disable=bare-except
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
