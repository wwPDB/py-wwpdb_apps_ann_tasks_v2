##
# File:  CoordEditorForm.py
# Date:  12-Jan-2018
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

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

import json
import os
import shutil
import sys
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class CoordEditorForm(object):
    """
    The CoordEditorForm class generates coordinate editor form.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__entryFile = None
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__entryId = self.__reqObj.getValue("entryid")
        self.__identifier = self.__reqObj.getValue("display_identifier")
        self.__jsonPath = os.path.join(self.__sessionPath, self.__entryId + "_Json")
        self.__entryFile = None
        #
        self.__listItemTemplate = (
            '<li><a id="%s" class="discontrol ui-corner-all" href="#">'
            + '<span class="ui-icon fltlft ui-icon-circle-arrow-e"></span> %s </a>\n'
            + '<div id="display_%s" style="display:none"></div>\n</li>\n'
        )
        #
        self.__tableTemplate = '<table id="table_%s" class="table table-condensed table-bordered table-striped">\n'
        self.__tdTagTemplate = '<td style="border-style:none">%s</td>\n'
        self.__editableTemplate = '<b class="%s" id="%s" style="display:inline">%s</b>'

    def run(self):
        """Generate JSON format data"""
        if not self.__identifier:
            return False
        #
        if self.__identifier == self.__entryId:
            return self.__generateEntryJson()
        #
        splitList = self.__identifier.split("_")
        if len(splitList) == 3 and splitList[0] == "chain":
            return self.__geterateChainJson(splitList[1], splitList[2])
        #
        return False

    def get(self):
        """Get coordinate editor form"""
        myD = {}
        myD["statuscode"] = "failed"
        myD["statustext"] = "Invalid ajax call"
        if not self.__identifier:
            return myD
        #
        if self.__identifier == self.__entryId:
            return self.__topEntryHtml()
        #
        splitList = self.__identifier.split("_")
        if len(splitList) == 3:
            if splitList[0] == "chain":
                return self.__topChainHtml(splitList[1], splitList[2])
            elif (splitList[0] == "Polymer") or (splitList[0] == "Nonpolymer") or (splitList[0] == "Water"):
                return self.__typeChainHtml(splitList[0], splitList[1], splitList[2], self.__identifier)
            #
        elif len(splitList) == 7 and splitList[0] == "res":
            residueID = splitList[2] + " " + splitList[3] + " " + splitList[4] + splitList[5]
            return self.__residueHtml(splitList[1], splitList[2], residueID, "_".join(splitList[1:]))
        #
        return myD

    def setLogHandle(self, log=sys.stderr):
        """Reset the stream for logging output."""
        try:
            self.__lfh = log
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def __generateEntryJson(self):
        """Call C++ DepictMolecule_Json program to generate coordinates data in JSON format"""
        #
        # Remove existing entryId_coord_pickle.db file
        #
        pickleFile = os.path.join(self.__sessionPath, self.__entryId + "_coord_pickle.db")
        if os.access(pickleFile, os.F_OK):
            os.remove(pickleFile)
        #
        # Remove existing entryId_Json directory
        #
        if os.access(self.__jsonPath, os.F_OK):
            shutil.rmtree(self.__jsonPath)
        #
        # Create entryId_Json directory
        #
        os.makedirs(self.__jsonPath)
        #
        self.__runScript()
        if (
            os.access(os.path.join(self.__jsonPath, self.__entryId + ".json"), os.F_OK)
            and os.access(os.path.join(self.__sessionPath, self.__entryId + "_chainids.txt"), os.F_OK)
            and os.access(os.path.join(self.__sessionPath, self.__entryId + "_index.cif"), os.F_OK)
        ):
            return True
        #
        return False

    def __runScript(self):
        """Run DepictMolecule_Json program"""
        fileList = []
        for ext in ("_chainids.txt", "_index.cif", "_summary.log", "_command.log"):
            fileName = self.__entryId + ext
            filePath = os.path.join(self.__sessionPath, fileName)
            if os.access(filePath, os.F_OK):
                os.remove(filePath)
            #
            fileList.append(fileName)
        #
        self.__entryFile = self.__reqObj.getValue("entryfilename")
        if not os.access(os.path.join(self.__sessionPath, self.__entryFile), os.F_OK):
            return
        #
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(os.path.join(self.__sessionPath, self.__entryFile))
            dp.op("annot-depict-molecule-json")
            #
            jsonPath = os.path.join(self.__jsonPath, self.__entryId + ".json")
            textPath = os.path.join(self.__sessionPath, self.__entryId + "_chainids.txt")
            indxPath = os.path.join(self.__sessionPath, self.__entryId + "_index.cif")
            dp.expList(dstPathList=[jsonPath, textPath, indxPath])
            dp.expLog(os.path.join(self.__sessionPath, self.__entryId + "_summary.log"))
            dp.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #

    def __geterateChainJson(self, mol_idx, chainID):
        """Read entryId.json file and re-write chain.json file"""
        entryJsonPath = os.path.join(self.__jsonPath, self.__entryId + ".json")
        if not os.access(entryJsonPath, os.F_OK):
            return False
        #
        try:
            entryJSonObj = self.__readJSonFile(entryJsonPath)
            if (mol_idx in entryJSonObj) and (("PDBChainID_" + chainID) in entryJSonObj[mol_idx]):
                self.__proessChainJSonObj(mol_idx, chainID, entryJSonObj[mol_idx]["PDBChainID_" + chainID])
                return True
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #
        return False

    def __readJSonFile(self, filename):
        """Read json file"""
        with open(filename, "r") as f:
            jsonObj = json.load(f)
        #
        return jsonObj

    # def __writeJSonFile(self, jsonObj, filename):
    #     """Write json file"""
    #     with open(filename, "w") as f:
    #         json.dump(jsonObj, f)
    #     #

    def __proessChainJSonObj(self, mol_idx, chainID, jsonObj):
        """Re-organize chain json object and write to chain.json file"""
        chainObj = {}
        for Type in ("Polymer", "Nonpolymer", "Water"):
            if Type not in jsonObj:
                continue
            #
            entityLabel = ""
            if (Type == "Polymer") and ("entity_id" in jsonObj):
                entityLabel = "Entity ID: " + jsonObj["entity_id"] + ","
            #
            typeDict = {}
            typeDict["Label"] = [entityLabel, jsonObj[Type][0]["Label"][3], jsonObj[Type][-1]["Label"][3], jsonObj[Type][-1]["Label"][2]]
            #
            resList = []
            for residue in jsonObj[Type]:
                idxList = []
                idxList.append(mol_idx)
                idxList.append(residue["Label"][0])
                idxList.append(residue["Label"][1])
                idxList.append(residue["Label"][3])
                if residue["Label"][4] == "?":
                    idxList.append("")
                else:
                    idxList.append(residue["Label"][4])
                #
                idxList.append(residue["Label"][6])
                idx = "_".join(idxList)
                resList.append(idx)
                chainObj[idx] = residue
            #
            typeDict["Residue"] = resList
            chainObj[Type] = typeDict
        #
        if chainObj:
            chainObj["mol_idx"] = mol_idx
            chainPicklePath = os.path.join(self.__jsonPath, mol_idx + "_" + chainID + ".pickle")
            self.__writePickleFile(chainObj, chainPicklePath)
        #

    def __writePickleFile(self, pickleObj, filename):
        """Write pickle file"""
        fb = open(filename, "wb")
        pickle.dump(pickleObj, fb, 2)
        fb.close()

    def __topEntryHtml(self):
        """Get Top Editor form html"""
        filename = os.path.join(self.__sessionPath, self.__entryId + "_chainids.txt")
        if not os.access(filename, os.F_OK):
            return self.__topFailedHtml()
        #
        return self.__topSuccessfulHtml(filename)

    def __topSuccessfulHtml(self, filename):
        """return entry successful html"""
        f = open(filename, "r")
        chainids = f.read()
        f.close()
        #
        chainids = chainids.strip()
        #
        mol_idx = "0"
        select = ""
        htmlcontent = ""
        for chnid in chainids.split(","):
            chain_tag_id = "chain_" + mol_idx + "_" + chnid
            chain_label = "PDB chain ID: " + chnid
            htmlcontent += self.__listItemTemplate % (chain_tag_id, chain_label, chain_tag_id)
            if select:
                select += ","
            #
            select += "'" + chnid + "': '" + chnid + "'"
        #
        myD = {}
        if not htmlcontent:
            myD["statuscode"] = "failed"
            myD["statustext"] = "Invalid ajax call"
        else:
            myD["statuscode"] = "ok"
            myD["htmlcontent"] = "<ul>\n" + htmlcontent + "</ul>\n"
            myD["chainids"] = chainids
            myD["select"] = "{ " + select + " }"
        #
        return myD

    def __topFailedHtml(self):
        """return entry failed html"""
        myD = {}
        myD["statuscode"] = "failed"
        statustext = ""
        coordFile = os.path.join(self.__sessionPath, self.__entryFile)
        if not os.access(coordFile, os.F_OK):
            statustext = "No model coordinate file uploaded"
        #
        if not statustext:
            statustext = self.__readLogFile(os.path.join(self.__sessionPath, self.__entryId + "_summary.log"))
        #
        if not statustext:
            statustext = self.__readLogFile(os.path.join(self.__sessionPath, self.__entryId + "_command.log"))
        #
        if not statustext:
            statustext = "Invalid ajax call"
        #
        myD["statustext"] = statustext
        return myD

    def __readLogFile(self, logFile):
        """Read log file message"""
        if not os.access(logFile, os.F_OK):
            return ""
        #
        f = open(logFile, "r")
        data = f.read()
        f.close()
        #
        logMsg = ""
        for line in data.split("\n"):
            if not line:
                continue
            #
            if line == "Finished!":
                continue
            #
            if logMsg:
                logMsg += "\n"
            #
            logMsg += line
        #
        return logMsg

    def __topChainHtml(self, mol_idx, chainID):
        """Get chain html"""
        pickleObj, ok = self.__readChainPickleFile(mol_idx, chainID)
        if not ok:
            myD = {}
            myD["statuscode"] = "failed"
            myD["statustext"] = "Depict chain " + chainID + " failed"
            return myD
        #
        labelTemplates = "%s ( %s First Number: %s, Last Number: %s, Total %s Residues )"
        labelTemplate = "%s ( %s First Number: %s, Last Number: %s, Total %s Residue )"
        #
        htmlcontent = '<li>Rename PDB chain ID: <input type="text" id="chainId_%s_%s" name="chainId_%s_%s" value="" size="15" /></li>\n' % (mol_idx, chainID, mol_idx, chainID)
        for Type in ("Polymer", "Nonpolymer", "Water"):
            if Type not in pickleObj:
                continue
            #
            if int(pickleObj[Type]["Label"][3]) > 1:
                label = labelTemplates % (Type, pickleObj[Type]["Label"][0], pickleObj[Type]["Label"][1], pickleObj[Type]["Label"][2], pickleObj[Type]["Label"][3])
            else:
                label = labelTemplate % (Type, pickleObj[Type]["Label"][0], pickleObj[Type]["Label"][1], pickleObj[Type]["Label"][2], pickleObj[Type]["Label"][3])
            #
            type_id = Type + "_" + mol_idx + "_" + chainID
            htmlcontent += self.__listItemTemplate % (type_id, label, type_id)
        #
        myD = {}
        myD["statuscode"] = "ok"
        myD["htmlcontent"] = "<ul>\n" + htmlcontent + "</ul>\n"
        return myD

    def __readChainPickleFile(self, mol_idx, chainID):
        """Read chain pickle object"""
        chainPicklePath = os.path.join(self.__jsonPath, mol_idx + "_" + chainID + ".pickle")
        if not os.access(chainPicklePath, os.F_OK):
            return None, False
        #
        try:
            chainPickleObj = self.__readPickleFile(chainPicklePath)
            return chainPickleObj, True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return None, False
        #

    def __readPickleFile(self, filename):
        """Read pickle file"""
        fb = open(filename, "rb")
        pickleObj = pickle.load(fb)
        fb.close()
        return pickleObj

    def __typeChainHtml(self, Type, mol_idx, chainID, Identifier):
        """Get type chain html"""
        pickleObj, ok = self.__readChainPickleFile(mol_idx, chainID)
        if (not ok) or (Type not in pickleObj):
            myD = {}
            myD["statuscode"] = "failed"
            myD["statustext"] = "Depict " + Type + " chain " + chainID + " failed"
            return myD
        #
        labelTemplate = 'Renumbering %s Starting from: <input type="text" id="chainNum_%s" name="chainNum_%s" value="" size="15" />'
        htmlcontent = labelTemplate % (Type, Identifier, Identifier)
        if Type == "Polymer":
            labelPolymerTemplate = (
                "<br/>Renumbering Polymer using Range: For the residue renumbering please make sure the range covers the full length of "
                + "the sequence. You must specify original range in an ordinal number followed by a colon with a new range. Use comma to list multiple ranges. "
                + "<br/>e.g. 1-100:301-401, 101-101:1001-1001, 102-300:2002-2300 for a full length of 300.<br/> "
                + '<input type="text" id="chainRangeNum_%s_%s" name="chainRangeNum_%s_%s" value="" size="60" />\n'
            )
            htmlcontent += labelPolymerTemplate % (mol_idx, chainID, mol_idx, chainID)
        #
        colspan = "6"
        htmlcontent += self.__tableTemplate % Identifier
        htmlcontent += "<tr>\n<th>ChainID</th>\n<th>Name</th>\n"
        if Type == "Polymer":
            colspan = "7"
            htmlcontent += "<th>Ordinal Number</th>\n"
        #
        htmlcontent += "<th>PDB Number</th>\n<th>Ins. Code</th>\n<th>AltLoc</th>\n<th>Coord. Link</th>\n</tr>\n"
        #
        editableClass = {0: "editable_select", 3: "editable_text", 4: "editable_text", 5: "editable_text"}
        editablePrefixId = {0: "resChainId", 3: "resNum", 4: "resIns", 5: "resLoc"}
        posList = (0, 1, 3, 4, 5)
        if Type == "Polymer":
            editableClass = {3: "editable_text", 4: "editable_text", 5: "editable_text"}
            editablePrefixId = {3: "resNum", 4: "resIns", 5: "resLoc"}
            posList = (0, 1, 2, 3, 4, 5)
        #
        residueLinkTemplate = '<a id="%s" class="discontrol" href="#"> Show Coord. </a>'
        residueDisplayTemplate = '<tr><td colspan="%s"><div id="display_%s" style="display:none"></td></tr>\n'
        for resID in pickleObj[Type]["Residue"]:
            if resID not in pickleObj:
                continue
            #
            htmlcontent += "<tr>\n"
            residue = pickleObj[resID]
            trueResID = "_".join(resID.split("_")[0:5])
            for pos in posList:
                if (pos in editablePrefixId) and residue["Label"][pos]:
                    editableID = editablePrefixId[pos] + "_" + trueResID
                    editableText = self.__editableTemplate % (editableClass[pos], editableID, residue["Label"][pos])
                    htmlcontent += self.__tdTagTemplate % editableText
                else:
                    htmlcontent += self.__tdTagTemplate % residue["Label"][pos]
                #
            #
            residueText = ""
            if "Atoms" in residue:
                residueText = residueLinkTemplate % ("res_" + resID)
            #
            htmlcontent += self.__tdTagTemplate % residueText
            htmlcontent += "</tr>\n"
            if residueText:
                htmlcontent += residueDisplayTemplate % (colspan, ("res_" + resID))
            #
        #
        htmlcontent += "</table>\n"
        #
        myD = {}
        myD["statuscode"] = "ok"
        myD["htmlcontent"] = "<ul>\n<li>\n" + htmlcontent + "</li>\n</ul>\n"
        return myD

    def __residueHtml(self, mol_idx, chainID, residueID, Identifier):
        """Get residue html"""
        pickleObj, ok = self.__readChainPickleFile(mol_idx, chainID)
        if (not ok) or (Identifier not in pickleObj) or ("Atoms" not in pickleObj[Identifier]):
            myD = {}
            myD["statuscode"] = "failed"
            myD["statustext"] = "Depict " + " residue '" + residueID + "' failed"
            return myD
        #
        editableClass = {0: "editable_text", 1: "editable_text", 2: "editable_text", 6: "editable_text"}
        editablePrefixId = {0: "atomName", 1: "atomType", 2: "atomLoc", 6: "atomOcc"}
        posList = (0, 1, 2, 3, 4, 5, 6, 7)
        #
        htmlcontent = self.__tableTemplate % Identifier
        htmlcontent += (
            "<tr>\n<th>AtomName</th>\n<th>AtomType</th>\n<th>AltLoc</th>\n<th>X</th>\n<th>Y</th>\n<th>Z</th>\n<th>Occupancy</th>\n"
            + "<th>TempFactor</th>\n<th>Deletion</th>\n</tr>\n"
        )
        #
        trueResID = "_".join(Identifier.split("_")[0:5])
        for atom in pickleObj[Identifier]["Atoms"]:
            atomID = trueResID + "_" + atom[8]
            htmlcontent += "<tr>\n"
            for pos in posList:
                if pos in editablePrefixId:
                    editableID = editablePrefixId[pos] + "_" + atomID
                    editableText = self.__editableTemplate % (editableClass[pos], editableID, atom[pos])
                    htmlcontent += self.__tdTagTemplate % editableText
                else:
                    htmlcontent += self.__tdTagTemplate % atom[pos]
                #
            #
            editableID = "atomDel_" + atomID
            editableText = self.__editableTemplate % ("editable_select_YN", editableID, "N")
            htmlcontent += self.__tdTagTemplate % editableText
            htmlcontent += "</tr>\n"
        #
        htmlcontent += "</table>\n"
        #
        myD = {}
        myD["statuscode"] = "ok"
        myD["htmlcontent"] = htmlcontent
        return myD
