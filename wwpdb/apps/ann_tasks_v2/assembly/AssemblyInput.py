##
# File:  AssemblyInput.py
# Date:  29-Mar-2013  J. Westbrook
#
# Update:
#  30-Oct-2013  jdw revise form construction to include prior values.
#  13-Dec-2013  jdw add rows to input form on load.
#  12-Mar-2014  jdw update table dialog style
#  19-Feb-2105  jdw add edit support for _struct_biol.details.
#  02-Feb-2017  ep  add support for display author provided assembly and evidence
#  04-Oct-2017  zf  add __getPdbxStructAssemblyGenDepositorInfo(), makeEntityInfoTable(), makeSymopInfoTable() & __getSymmetryCellValue()
##
"""
Calculation, selection and depiction of coordinate assemblies.

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

from wwpdb.apps.ann_tasks_v2.io.PdbxIoUtils import ModelFileIo, PdbxFileIo
from wwpdb.apps.ann_tasks_v2.assembly.AssemblySelect import AssemblySelect
from mmcif.io.IoAdapterCore import IoAdapterCore
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class AssemblyInput(object):

    """
    AssemblyInput class encapsulates the data input operations for user supplied assemblies.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__debug = False
        self.__setup()

    def __setup(self):
        self.__placeHolderValue = "click-to-edit"
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        self.__formDefList = [
            ("assem_id", "a_id_", self.__placeHolderValue),
            ("provenance", "a_prov_", self.__placeHolderValue),
            ("buried_area", "a_ba_", self.__placeHolderValue),
            ("surface_area", "a_sa_", self.__placeHolderValue),
            ("free_energy", "a_fe_", self.__placeHolderValue),
            ("oligomeric_count", "a_oc_", self.__placeHolderValue),
        ]

    def getAssemblyFormDef(self):
        return self.__formDefList

    # def __fetchMolecularDetails(self, entryFileName=None):
    #     """Return a dictionary containing the auth_asym_ids for each polymer entity."""
    #     fN = os.path.join(self.__sessionPath, entryFileName)
    #     c0 = PdbxFileIo(ioObj=IoAdapterCore(), verbose=self.__verbose, log=self.__lfh).getContainer(fN)
    #     sdf = ModelFileIo(dataContainer=c0, verbose=self.__verbose, log=self.__lfh)
    #     ed, bList = sdf.getPolymerEntityChainDict()
    #     if self.__debug:
    #         for eId, iList in ed.items():
    #             self.__lfh.write("+AssemblyInput.__fetchMolecularDetails() entity %s  instance list = %r\n" % (eId, iList))

    #     return ed

    def __fetchAssemblyDepositorDetails(self, entryFileName=None):
        """Return a list of dictionaries containing depositor provided details about molecular assemblies."""
        assemL = []
        assemRcsbL = []
        assemGen = []
        assemOper = []
        assemEvidence = []
        assemClassification = []
        branchInstList = []
        ed = {}
        #
        if self.__verbose:
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDepositorDetails() entryFileName %r\n" % entryFileName)
        #
        if entryFileName is None or len(entryFileName) < 1:
            return assemL, assemRcsbL, ed, assemGen, assemOper, assemEvidence, assemClassification, branchInstList

        fN = os.path.join(self.__sessionPath, entryFileName)
        if fN is not None and not os.access(fN, os.R_OK):
            return assemL, assemRcsbL, ed, assemGen, assemOper, assemEvidence, assemClassification, branchInstList
        #
        c0 = PdbxFileIo(ioObj=IoAdapterCore(), verbose=self.__verbose, log=self.__lfh).getContainer(fN)
        sdf = ModelFileIo(dataContainer=c0, verbose=self.__verbose, log=self.__lfh)

        assemL = sdf.getDepositorAssemblyDetails()
        assemRcsbL = sdf.getDepositorAssemblyDetailsRcsb()
        # assemGen = sdf.getDepositorAssemblyGen()
        assemGen = self.__getPdbxStructAssemblyGenDepositorInfo(sdf, c0)
        assemOper = sdf.getDepositorStructOperList()
        assemEvidence = sdf.getDepositorAssemblyEvidence()
        assemClassification = sdf.getDepositorAssemblyClassification()
        ed, branchInstList = sdf.getPolymerEntityChainDict()

        if self.__verbose:
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDepositorDetails()        %r\n" % assemL)
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDepositorDetails() legacy %r\n" % assemRcsbL)
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDepositorDetails() gen %r\n" % assemGen)
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDepositorDetails() oper %r\n" % assemOper)
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDepositorDetails() evidence %r\n" % assemEvidence)
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDepositorDetails() classification %r\n" % assemClassification)
            if self.__debug:
                for eId, iList in ed.items():
                    self.__lfh.write("+AssemblyInput.__fetchMolecularDetails() entity %s  instance list = %r\n" % (eId, iList))

        return assemL, assemRcsbL, ed, assemGen, assemOper, assemEvidence, assemClassification, branchInstList

    def __getPdbxStructAssemblyGenDepositorInfo(self, modelFile, container):
        assemGen = modelFile.getDepositorAssemblyGen()
        if len(assemGen) == 0:
            return assemGen
        #
        polychainIDList = []
        polyEntityList = modelFile.getPolymerEntityList()
        if len(polyEntityList) > 0:
            for eId in polyEntityList:
                polychainIDList.extend(modelFile.getPdbChainIdList(eId))
            #
        #
        if len(polychainIDList) == 0:
            return assemGen
        #
        chnAsymIdMap = {}
        allAsymIdList = []
        try:
            for category in ("pdbx_poly_seq_scheme", "pdbx_branch_scheme", "pdbx_nonpoly_scheme"):
                if not container.exists(category):
                    if category == "pdbx_poly_seq_scheme":
                        break
                    #
                    continue
                #
                attributeList = ["asym_id", "pdb_strand_id"]
                if category == "pdbx_branch_scheme":
                    attributeList = ["asym_id", "pdb_asym_id"]
                #
                catObj = container.getObj(category)
                colNames = list(catObj.getAttributeList())
                nRows = catObj.getRowCount()
                for iRow in range(0, nRows):
                    rD = {}
                    row = catObj.getRow(iRow)
                    for col in attributeList:
                        col_out = col
                        if col == "pdb_asym_id":
                            col_out = "pdb_strand_id"
                        #
                        if col in colNames:
                            val = str(row[colNames.index(col)])
                            if val is None:
                                val = ""
                            elif (val == ".") or (val == "?"):
                                val = ""
                            #
                            rD[col_out] = val
                        else:
                            rD[col_out] = ""
                        #
                    #
                    if ("pdb_strand_id" not in rD) or (not rD["pdb_strand_id"]) or ("asym_id" not in rD) or (not rD["asym_id"]):
                        continue
                    #
                    if rD["pdb_strand_id"] in chnAsymIdMap:
                        if rD["asym_id"] not in chnAsymIdMap[rD["pdb_strand_id"]]:
                            chnAsymIdMap[rD["pdb_strand_id"]].append(rD["asym_id"])
                            allAsymIdList.append(rD["asym_id"])
                        #
                    else:
                        chnAsymIdMap[rD["pdb_strand_id"]] = [rD["asym_id"]]
                        allAsymIdList.append(rD["asym_id"])
                    #
                #
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #
        for myD in assemGen:
            if ("chain_id_list" not in myD) or (not myD["chain_id_list"]):
                continue
            #
            newAsymList = []
            newList = []
            oldList = myD["chain_id_list"].split(",")
            for chain_id in oldList:
                cid = chain_id.strip()
                if cid in polychainIDList:
                    newList.append(cid)
                    if cid in chnAsymIdMap:
                        newAsymList.extend(chnAsymIdMap[cid])
                    #
                #
            #
            myD["chain_id_list"] = ",".join(newList)
            if chnAsymIdMap:
                sortAsymList = []
                for asym in newAsymList:
                    if asym not in allAsymIdList:
                        continue
                    #
                    sortAsymList.append([asym, allAsymIdList.index(asym)])
                #
                sortAsymList.sort(key=lambda data: data[1])
                newAsymList = []
                for tList in sortAsymList:
                    newAsymList.append(tList[0])
                #
                myD["asym_id_list"] = ",".join(newAsymList)
            #
        #
        return assemGen

    def __fetchAssemblyDetails(self, entryFilePath=None):
        """Return a list of dictionaries containing the current assembly details."""
        c0 = PdbxFileIo(ioObj=IoAdapterCore(), verbose=self.__verbose, log=self.__lfh).getContainer(entryFilePath)
        sdf = ModelFileIo(dataContainer=c0, verbose=self.__verbose, log=self.__lfh)

        assemL, assemGenL, assemOpL = sdf.getAssemblyDetails()

        if self.__verbose:
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDetails()  assemL     %r\n" % assemL)
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDetails()  assemGenL  %r\n" % assemGenL)
            self.__lfh.write("+AssemblyInput.__fetchAssemblyDetails()  assemOpL   %r\n" % assemOpL)
        return assemL, assemGenL, assemOpL

    def makeAssemblyDetailsTable(self, entryFilePath=None):
        return self.__fetchAssemblyDetails(entryFilePath=entryFilePath)

    def makeEntityInfoTable(self, entryId="1ABC", entryFileName=None):
        """Return entity ids, names & related PDB chain ids"""
        not_found_msg = "<br />\nNo polymer entity information found."
        #
        if entryFileName is None or len(entryFileName) < 1:
            return not_found_msg
        #
        fN = os.path.join(self.__sessionPath, entryFileName)
        if not os.access(fN, os.R_OK):
            return not_found_msg
        #
        c0 = PdbxFileIo(ioObj=IoAdapterCore(), verbose=self.__verbose, log=self.__lfh).getContainer(fN)
        sdf = ModelFileIo(dataContainer=c0, verbose=self.__verbose, log=self.__lfh)
        polyEntityList = sdf.getPolymerEntityList()
        if len(polyEntityList) > 0:
            oL = []
            oL.append('<table class="table table-bordered table-striped">')
            oL.append("<tr>")
            for label in ("Entity Id", "Entity Name", "Related PDB Chain(s)"):
                oL.append("<th>%s</th>" % label)
            #
            oL.append("</tr>")
            for eId in polyEntityList:
                oL.append("<tr>")
                oL.append("<td>%s</td>" % eId)
                oL.append("<td>%s</td>" % sdf.getEntityDescription(eId))
                oL.append("<td>%s</td>" % ",".join(sdf.getPdbChainIdList(eId)))
                oL.append("</tr>")
            #
            oL.append("</table>")
            #
            branchChainIdList = sdf.getBranchChainIdList()
            if branchChainIdList:
                branchInfoPath = os.path.join(self.__sessionPath, entryId + "-branch-info.cif")
                if not os.access(branchInfoPath, os.R_OK):
                    try:
                        dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
                        dp.imp(fN)
                        dp.op("get-branch-polymer-info")
                        dp.exp(branchInfoPath)
                        dp.cleanup()
                    except:  # noqa: E722 pylint: disable=bare-except
                        traceback.print_exc(file=self.__lfh)
                    #
                #
            #
            return "\n".join(oL)
        else:
            return not_found_msg
        #

    def makeSymopInfoTable(self, entryId="1ABC", entryFileName=None):
        """Return symmetry operation information"""
        not_found_msg = "<br />\nNo symmetry operation information found."
        #
        if entryFileName is None or len(entryFileName) < 1:
            return not_found_msg
        #
        fN = os.path.join(self.__sessionPath, entryFileName)
        if not os.access(fN, os.R_OK):
            return not_found_msg
        #
        c0 = PdbxFileIo(ioObj=IoAdapterCore(), verbose=self.__verbose, log=self.__lfh).getContainer(fN)
        if (not c0.exists("cell")) or (not c0.exists("symmetry")):
            return not_found_msg
        #
        myList = ("space_group_name_H-M", "length_a", "length_b", "length_c", "angle_alpha", "angle_beta", "angle_gamma")
        myD = {}
        #
        sTable = c0.getObj("symmetry")
        myD = self.__getSymmetryCellValue(sTable, myList, myD)
        #
        cTable = c0.getObj("cell")
        myD = self.__getSymmetryCellValue(cTable, myList, myD)
        if ("space_group_name_H-M" not in myD) or (not myD["space_group_name_H-M"]):
            return not_found_msg
        #
        myLabel = {"space_group_name_H-M": "Space Group", "length_a": "a", "length_b": "b", "length_c": "c", "angle_alpha": "alpha", "angle_beta": "beta", "angle_gamma": "gamma"}
        #
        oL = []
        oL.append('<table class="table table-bordered table-striped">')
        oL.append("<tr>")
        for item in myList:
            oL.append("<th>%s</th>" % myLabel[item])
        #
        oL.append("</tr>")
        oL.append("<tr>")
        for item in myList:
            val = ""
            if item in myD:
                val = myD[item]
            #
            oL.append("<td>%s</td>" % val)
        #
        oL.append("</tr>")
        oL.append("</table>")
        #
        space_group = myD["space_group_name_H-M"].replace(" ", "_")
        for ext in ("-symop-info.txt", "-symop-info.log", "-symop-info.clog"):
            fTmp = os.path.join(self.__sessionPath, entryId + ext)
            if os.access(fTmp, os.R_OK):
                os.remove(fTmp)
            #
        #
        symopFile = os.path.join(self.__sessionPath, entryId + "-symop-info.txt")
        #
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.addInput(name="space_group", value=space_group)
            dp.op("annot-get-symmetry-operator")
            dp.exp(symopFile)
            dp.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #
        if os.access(symopFile, os.R_OK):
            ifh = open(symopFile, "r")
            data = ifh.read()
            ifh.close()
            #
            symList = []
            for line in data.split("\n"):
                if not line:
                    continue
                #
                tList = line.split(" ")
                if len(tList) == 2:
                    symList.append(tList)
                #
            #
            if symList:
                oL.append('<br /><table class="table table-bordered table-striped">')
                oL.append("<tr>")
                for label in ("SymOp", "Symmetry Operator"):
                    oL.append("<th>%s</th>" % label)
                #
                oL.append("</tr>")
                for tList in symList:
                    oL.append("<tr>")
                    oL.append("<td>%s</td>" % tList[0])
                    oL.append("<td>%s</td>" % tList[1])
                    oL.append("</tr>")
                #
                oL.append("</table>")
        #
        return "\n".join(oL)

    def __getSymmetryCellValue(self, Table, myList, myD):
        colNames = list(Table.getAttributeList())
        row = Table.getRow(0)
        for col in myList:
            if col in colNames:
                val = str(row[colNames.index(col)])
                if val is None:
                    val = ""
                elif (val == ".") or (val == "?"):
                    val = ""
                #
                myD[col] = val
            #
        #
        return myD

    def makeDepositorAssemblyDetailsTable(self, entryId="1ABC", entryFileName=None):
        """Return HTML markup with the contents of depositor provided assembly details --"""
        oL = []
        sbAttList = [
            ("id", "ID"),
            ("details", "Details"),
            ("rcsb_description", "Description"),
            ("method_details", "Method details"),
            ("pdbx_aggregation_state", "Aggregation state"),
            ("pdbx_assembly_method", "Assembly method"),
            ("pdbx_formula_weight", "Formula weight"),
            ("pdbx_formula_weight_method", "Formula weight method"),
        ]

        aS = AssemblySelect(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        _tfD, extraD = aS.getAssemblyFormDetails(entryId)
        if self.__verbose:
            self.__lfh.write("+AssemblyInput.makeDepositorAssemblyDetailsTable() updated description saved in extraD %r\n" % extraD.items())
        assemL, assemRcsbL, eD, assemGen, _assemOper, assemEvidence, assemClassification, _branchInstList = self.__fetchAssemblyDepositorDetails(entryFileName=entryFileName)

        #
        if (extraD is not None) and (len(extraD) > 0):
            if (assemRcsbL is not None) and (len(assemRcsbL) > 0):
                for rowD in assemRcsbL:
                    if rowD["id"] == extraD["id"]:
                        rowD["details"] = extraD["details"]
            else:
                assemRcsbL = []
                rowD = {}
                for tup in sbAttList:
                    rowD[tup[0]] = ""
                for k, v in extraD.items():
                    rowD[k] = v
                assemRcsbL.append(rowD)

        # if len(assemL) == 0 or len(eD) == 0:
        #    return '\n'.join(oL)
        #
        instanceIdList = []
        for _eId, instL in eD.items():
            for inst in instL:
                instanceIdList.append(inst)
            #
        #
        sorted(instanceIdList)
        iC = ""
        iS = ""
        if len(instanceIdList) > 0:
            iC = "Instance List (%d):" % len(instanceIdList)
            iS = str("<br />".join([",".join(v) for v in self.__chunker(instanceIdList, 35)])).replace('"', "")
        #

        # pdbx_struct_assembly_auth_evidence
        attList = [("id", "ID"), ("assembly_id", "Assembly"), ("experimental_support", "Exp. Support"), ("details", "Details")]
        self.__displayTable(oL, assemEvidence, "pdbx_struct_assembly_auth_evidence", entryId, "", "", attList)

        # pdbx_struct_assembly_auth_classification
        attList = [("assembly_id", "Assembly ID"), ("reason_for_interest", "Reason of Interest")]
        self.__displayTable(oL, assemClassification, "pdbx_struct_assembly_auth_classification", entryId, "", "", attList)

        # pdbx_struct_assembly_depositor_info
        attList = [
            ("id", "ID"),
            ("details", "Details"),
            ("method_details", "Method details"),
            ("oligomeric_count", "Olig. Count"),
            ("oligomeric_details", "Olig. Details"),
            ("matrix_flag", "Matrices provided"),
            ("upload_file_name", "Upload file name"),
        ]
        self.__displayTable(oL, assemL, "pdbx_struct_assembly_depositor_info", entryId, iC, iS, attList)

        # pdbx_struct_assembly_gen_depositor_info
        attList = [
            ("id", "ID"),
            ("assembly_id", "Assembly"),
            ("chain_id_list", "Chain ids"),
            ("all_chains", "All Chains?"),
            ("asym_id_list", "Asym ids"),
            ("oper_expression", "Operators"),
            ("full_matrices", "Matrices"),
            ("at_unit_matrix", "Unit matrix?"),
            ("helical_rotation", "Hel. rot."),
            ("helical_rise", "Hel. rise."),
        ]
        self.__displayTable(oL, assemGen, "pdbx_struct_assembly_gen_depositor_info", entryId, "", "", attList)
        # pdbx_struct_oper_list_depositor_info
        attList = [
            ("id", "ID"),
            ("name", "Name"),
            ("symmetry_operation", "Op"),
            ("type", "Type"),
            ("matrix[1][1]", "[1][1]"),
            ("matrix[1][2]", "[1][2]"),
            ("matrix[1][3]", "[1][3]"),
            ("matrix[2][1]", "[2][1]"),
            ("matrix[2][2]", "[2][2]"),
            ("matrix[2][3]", "[2][3]"),
            ("matrix[3][1]", "[3][1]"),
            ("matrix[3][2]", "[3][2]"),
            ("matrix[3][3]", "[3][3]"),
            ("vector[1]", "T1"),
            ("vector[2]", "T2"),
            ("vector[3]", "T3"),
        ]
        # DAOTHER-2389 do not display pdbx_struct_oper_list_depositor_info
        # self.__displayTable(oL, assemOper,
        #                    'pdbx_struct_oper_list_depositor_info',
        #                    entryId, '', '', attList)

        # struct_biol table
        # self.__displayTable(oL, assemRcsbL, 'struct_biol',
        #                    entryId, '', '', sbAttList)

        if self.__verbose:
            self.__lfh.write("+AssemblyInput.makeDepositorAssemblyDetailsTable() returned markup %s\n" % "\n".join(oL))

        return "\n".join(oL)

    def __displayTable(self, oL, tableData, tableName, entryId, iC, iS, attrList):
        """Internal display table"""
        top_table_template = """
        <div id="assembly-depositor-info">
          <h4>Depositor provided assembly description (original) from category %s for %s</h4>
          <div class="row">
          <div class="col-md-2">%s</div>  <div class="col-md-8">%s</div>
          </div>
          <table class="table table-bordered table-striped">
        """
        #
        bottom_table_template = """
            </table>
        </div>
        """

        if len(tableData) > 0:
            oL.append(top_table_template % (tableName, entryId, iC, iS))
            oL.append("<tr>")
            for ky, label in attrList:
                oL.append("<th>%s</th>" % label)
            oL.append("</tr>")
            for rowD in tableData:
                oL.append("<tr>")
                for ky, label in attrList:
                    oL.append("<td>%s</td>" % rowD[ky])
            oL.append("</tr>")
            oL.append(bottom_table_template)

    def makeAssemblyEditForm(self, entryId="1ABC", entryFileName=None):
        """
        <div class="ief" data-ief-edittype="select"
         data-ief-selectvalues="[{"value":"1","label":"Presentation Label","selected":true},{"value":"2","label":"Label 2","selected":false}]">
        """
        top_form_template = """
        <div id="sectassembly">
        <h3>Assembly Data Entry Form for Data Set %s</h3>

        <form name="formassembly" id="formassembly" action="/service/ann_tasks_v2/assemblysaveform" method="post" class="assembly_ajaxform form-inline">
        <span><input type="submit" name="submit" value="Submit edits" class="btn btn-primary"  /> </span>
           <br />
            <input type="hidden" name="sessionid" value="%s" />
            <table class="table table-striped width100">
                <tr><td style="width:20%%" >Update depositor provided assembly details</td><td> %s </td></tr>
            </table>
            <br />
            %s
            <table id="assembly_input_table" class="table table-bordered table-striped width100">
            <tr>
               <th class="width10">Assembly<br /> Id</th>
               <th class="width10">Provenance</th>
               <th class="width10">Buried<br /> Area</th>
               <th class="width10">Surface<br /> Area</th>
               <th class="width10">Free<br /> Energy</th>
               <th class="width10">Oligomeric<br />Count</th>
               <th class="width30">Operations<br />
                  <input id="formassembly_select_all" value="Select All" type="button" onClick="select_entry('formassembly', 'formassembly_select_all');" />
                  &nbsp; &nbsp; &nbsp; &nbsp;
                  <input id="formassembly_set_monomer" value="All Monomers" type="button" onClick="set_all_monomers('formassembly', 'formassembly_set_monomer', '%s');" />
               </th>
             </tr>
        """
        #
        bottom_form_template = """
            </table>
        <br  />
        <input type="submit" name="submit" value="Submit edits" class="btn btn-primary"  />
        <input type="button" id="add_row_button" name="add_row_button" value="Add rows" class="btn btn-primary fltrgt" />
        <br />
        <span id="assembly-form-status" class="width50 fltright"></span>
        <br class="clearfloat" />
        </form>
        </div>
        """
        #
        aS = AssemblySelect(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        fD, extraD = aS.getAssemblyFormDetails(entryId)
        if self.__verbose:
            self.__lfh.write("AssemblyInput.makeAssemblyEditForm() prior form content %r extra %r\n" % (fD.items(), extraD.items()))

        # eD = self.__fetchMolecularDetails(entryFileName=entryFileName)
        _assemL, assemRcsbL, eD, _assemGen, _assemOper, _assemEvidence, _assemClassification, _branchInstList = self.__fetchAssemblyDepositorDetails(entryFileName=entryFileName)
        #
        #
        tS = ""
        if (len(extraD) > 0) and (len(extraD["details"]) > 0):
            tS = extraD["details"]
        elif len(assemRcsbL) > 0:
            rowD = assemRcsbL[0]
            if "id" in rowD and "details" in rowD:
                tS = rowD["details"]
            #
        #
        tHtml = "<textarea style='width:100%%; height:100%%;' rows='4' name='details_1'>%s</textarea>" % tS
        #
        branch2LinearMap = {}
        linear2BranchMap = {}
        linearInstList = []
        linearbranchmap = ""
        branchInfoPath = os.path.join(self.__sessionPath, entryId + "-branch-info.cif")
        if os.access(branchInfoPath, os.R_OK):
            cifObj = mmCIFUtil(filePath=branchInfoPath)
            status = cifObj.GetSingleValue("summary", "status")
            if status == "yes":
                infoList = cifObj.GetValue("branch_polymer_info")
                for infoD in infoList:
                    if (
                        ("branch_polymer_chain_id" not in infoD)
                        or (not infoD["branch_polymer_chain_id"])
                        or ("linear_polymer_chain_id" not in infoD)
                        or (not infoD["linear_polymer_chain_id"])
                        or ("type" not in infoD)
                        or (not infoD["type"])
                    ):
                        continue
                    #
                    if infoD["linear_polymer_chain_id"] not in linearInstList:
                        linearInstList.append(infoD["linear_polymer_chain_id"])
                    #
                    branch2LinearMap[infoD["branch_polymer_chain_id"]] = infoD["linear_polymer_chain_id"]
                    if infoD["linear_polymer_chain_id"] in linear2BranchMap:
                        linear2BranchMap[infoD["linear_polymer_chain_id"]].append((infoD["branch_polymer_chain_id"], infoD["type"]))
                    else:
                        linear2BranchMap[infoD["linear_polymer_chain_id"]] = [(infoD["branch_polymer_chain_id"], infoD["type"])]
                    #
                #
            #
            for key, valist in linear2BranchMap.items():
                if linearbranchmap != "":
                    linearbranchmap += ";"
                #
                branchIdList = []
                for branchTup in valist:
                    branchIdList.append(branchTup[0])
                #
                linearbranchmap += key + ":" + ",".join(branchIdList)
            #
        #
        branchInfoText = ""
        for inst in linearInstList:
            if inst not in linear2BranchMap:
                continue
            #
            branchInfoText += "<tr><td>Polymer chain '" + inst + "' is associated with branch polymer(s): "
            first = True
            for branchTup in linear2BranchMap[inst]:
                if not first:
                    branchInfoText += ", "
                #
                branchInfoText += branchTup[0]
                if branchTup[1] == "linked":
                    branchInfoText += " (linked)"
                #
                first = False
            #
            branchInfoText += "</td></tr>\n"
        #
        branchInfoTabletext = ""
        if branchInfoText:
            branchInfoTabletext = '<table class="table table-borderless width100">\n' + branchInfoText + "</table><br />"
        #
        instanceIdList = []
        allInstanceIdList = []
        for _eId, instL in eD.items():
            for inst in instL:
                allInstanceIdList.append(inst)
                if inst in branch2LinearMap:
                    continue
                #
                instanceIdList.append(inst)
            #
        #
        instanceIdList.sort()
        #
        provenanceList = ["author_defined_assembly", "software_defined_assembly", "author_and_software_defined_assembly"]

        defautSymOp = "1_555"
        checkInstTemplate = ' %s <input id="a_%d_inst_%s" name="a_%d_inst_%s" type="checkbox" checked="checked"></input> OP <span  id="a_%d_symop_%s"  class="ief">%s</span> '
        chainInstTemplate = ' %s <input id="a_%d_inst_%s" name="a_%d_inst_%s" type="checkbox"></input> OP <span  id="a_%d_symop_%s"  class="ief">%s</span> '
        #
        allMonomerList = []
        for assemId in range(0, len(instanceIdList)):
            instId = "a_%d_inst_%s" % ((assemId + 1), instanceIdList[assemId])
            allMonomerList.append(instId)
            if instanceIdList[assemId] in linear2BranchMap:
                for branchTup in linear2BranchMap[instanceIdList[assemId]]:
                    instId = "a_%d_inst_%s" % ((assemId + 1), branchTup[0])
                    allMonomerList.append(instId)
                #
            #
        #
        oL = []
        oL.append(top_form_template % (entryId, self.__sessionId, tHtml, branchInfoTabletext, ",".join(allMonomerList)))
        defaultValue = self.__placeHolderValue
        nRows = 0
        numAssem = len(fD) + 21
        if numAssem < len(instanceIdList) + 1:
            numAssem = len(instanceIdList) + 1
        #
        for assemId in range(1, numAssem):
            if assemId in fD:
                # JDW insert real values here ---
                d = fD[assemId]
                jsonTxt = self.__setSelectText(optionList=provenanceList, selectedValue=d["provenance"])
                oL.append("<tr>")
                oL.append('<td><input type="hidden"  name="a_id_%d" value="%d" />%d</td>' % (assemId, assemId, assemId))
                oL.append('<td><span  id="a_prov_%d" class="ief" data-ief-edittype="select" data-ief-selectvalues=\'%s\'>%s</span>' % (assemId, jsonTxt, d["provenance"]))
                for fTup in self.__formDefList[2:]:
                    ky = fTup[1] + str(assemId)
                    if d[fTup[0]] == "?":
                        oL.append('<td><span  id="%s"   class="ief greyedout">%s</span></td>' % (ky, defaultValue))
                    else:
                        oL.append('<td><span  id="%s"   class="ief">%s</span></td>' % (ky, d[fTup[0]]))
                    #
                #
                inD = {}
                for op in d["op_list"]:
                    inD[op[0]] = op
                #
                oL.append('<td class="textleft">')
                for instanceId in instanceIdList:
                    if instanceId in inD:
                        oL.append(
                            ' %s <input id="a_%d_inst_%s" name="a_%d_inst_%s" type="checkbox" checked="checked"></input>' % (instanceId, assemId, instanceId, assemId, instanceId)
                        )
                        oL.append(' OP <span  id="a_%d_symop_%s"  class="ief">%s</span> <br/>' % (assemId, instanceId, inD[instanceId][1]))
                    else:
                        oL.append(' %s <input id="a_%d_inst_%s" name="a_%d_inst_%s" type="checkbox"></input>' % (instanceId, assemId, instanceId, assemId, instanceId))
                        oL.append(' OP <span  id="a_%d_symop_%s"  class="ief">%s</span> <br/>' % (assemId, instanceId, defautSymOp))
                    #
                    if instanceId in linear2BranchMap:
                        includeBranchList = []
                        for branchTup in linear2BranchMap[instanceId]:
                            instId = branchTup[0]
                            if instId in inD:
                                includeBranchList.append(checkInstTemplate % (instId, assemId, instId, assemId, instId, assemId, instId, inD[instId][1]))
                            else:
                                includeBranchList.append(chainInstTemplate % (instId, assemId, instId, assemId, instId, assemId, instId, defautSymOp))
                            #
                        #
                        if includeBranchList:
                            includeBranchList[0] = "( " + includeBranchList[0]
                            includeBranchList[-1] = includeBranchList[-1] + " )"
                            for branchText in includeBranchList:
                                oL.append(branchText + " <br/>")
                            #
                        #
                    #
                #
                oL.append("</td>")
                oL.append("</tr>")
            else:
                # JDW add remaining values ---
                jsonTxt = self.__setSelectText(optionList=provenanceList, selectedValue=defaultValue)
                oL.append("<tr>")
                oL.append('<td><input type="hidden"  name="a_id_%d" value="%d" />%d</td>' % (assemId, assemId, assemId))
                oL.append('<td><span  id="a_prov_%d" class="ief" data-ief-edittype="select" data-ief-selectvalues=\'%s\'>%s</span>' % (assemId, jsonTxt, "author_defined_assembly"))
                oL.append('<td><span  id="a_ba_%d"   class="ief greyedout">%s</span></td>' % (assemId, defaultValue))
                oL.append('<td><span  id="a_sa_%d"   class="ief greyedout">%s</span></td>' % (assemId, defaultValue))
                oL.append('<td><span  id="a_fe_%d"   class="ief greyedout">%s</span></td>' % (assemId, defaultValue))
                oL.append('<td><span  id="a_oc_%d"   class="ief greyedout">%s</span></td>' % (assemId, defaultValue))
                #
                oL.append('<td class="textleft">')
                for instanceId in instanceIdList:
                    oL.append(' %s <input id="a_%d_inst_%s" name="a_%d_inst_%s" type="checkbox"></input>' % (instanceId, assemId, instanceId, assemId, instanceId))
                    oL.append(' OP <span  id="a_%d_symop_%s"  class="ief">%s</span> <br/>' % (assemId, instanceId, defautSymOp))
                    #
                    if instanceId in linear2BranchMap:
                        includeBranchList = []
                        for branchTup in linear2BranchMap[instanceId]:
                            instId = branchTup[0]
                            includeBranchList.append(chainInstTemplate % (instId, assemId, instId, assemId, instId, assemId, instId, defautSymOp))
                        #
                        if includeBranchList:
                            includeBranchList[0] = "( " + includeBranchList[0]
                            includeBranchList[-1] = includeBranchList[-1] + " )"
                            for branchText in includeBranchList:
                                oL.append(branchText + " <br/>")
                            #
                        #
                    #
                #
                oL.append("</td>")
                oL.append("</tr>")
            nRows += 1
        oL.append('<input type="hidden" id="formlength" name="formlength" value="%d" />' % nRows)
        oL.append('<input type="hidden" name="instanceidlist" value="%s" />' % ",".join(allInstanceIdList))
        oL.append('<input type="hidden" id="polyinstanceidlist" value="%s" />' % ",".join(instanceIdList))
        oL.append('<input type="hidden" id="linearbranchmap" value="%s" />' % linearbranchmap)
        oL.append("</table>")
        oL.append(bottom_form_template)
        return "\n".join(oL)
        #

    def assemblyInputFormReader(self):
        """ """
        tS = self.__reqObj.getValue("instanceidlist")
        instanceIdList = str(tS).split(",")
        formLength = int(str(self.__reqObj.getValue("formlength")))
        #
        eD = {}
        tVal = self.__reqObj.getValue("details_1")
        if (tVal is not None) and (len(tVal) > 0):
            eD["id"] = "1"
            eD["details"] = tVal
        #
        fD = {}
        for assemId in range(1, formLength + 1):
            d = {}
            for k, prefix, placeHolderValue in self.__formDefList:
                tok = "%s%d" % (prefix, assemId)
                tVal = self.__reqObj.getValue(tok)
                if tVal != placeHolderValue:
                    d[k] = tVal
                else:
                    d[k] = "?"

            opList = []
            for instanceId in instanceIdList:
                instTok = "a_%d_inst_%s" % (assemId, instanceId)
                symTok = "a_%d_symop_%s" % (assemId, instanceId)
                if self.__reqObj.getValue(instTok) == "on":
                    opList.append((instanceId, self.__reqObj.getValue(symTok)))
            d["op_list"] = opList
            if len(opList) > 0:
                fD[assemId] = d

        if self.__verbose:
            self.__lfh.write("+AssemblyInput.assemblyInputFormReader() form contents:  %r extra %r\n" % (fD.items(), eD.items()))

        return fD, eD

    def __setSelectText(self, optionList, selectedValue="author_defined_assembly"):
        oL = []
        pSelectList = ["false" for p in optionList]
        if selectedValue is not None and len(selectedValue) > 1:
            optionListU = [p.upper() for p in optionList]
            selectedValueU = selectedValue.upper()
            try:
                idx = optionListU.index(selectedValueU)
                pSelectList[idx] = "true"
            except ValueError:
                idx = -1
        tL = []
        for pt, psel in zip(optionList, pSelectList):
            tL.append('{"value":"%s","label":"%s","selected":%s}' % (pt, pt, psel))
        oL.append("[")
        oL.append(",".join(tL))
        oL.append("]")

        return "".join(oL)

    def __chunker(self, lst, n):
        """Divide the input list into a list of lists of size n"""
        return [lst[i : i + n] for i in range(0, len(lst), n)]
