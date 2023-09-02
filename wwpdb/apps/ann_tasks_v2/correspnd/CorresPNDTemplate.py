##
# File:  CorresPNDTemplate.py
# Date:  07-Oct-2013
# Update:
##
"""
Generating correspondence to depositor template.

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

from wwpdb.apps.ann_tasks_v2.correspnd.ValidateXml import ValidateXml
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class CorresPNDTemplate(object):
    """
    The CorresPNDTemplate class generates correspondence to depositor template.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """ """
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__EmMapOnly = False
        self.__EmMapwithModel = False
        self.__EmFsc143CutOff = False
        self.__corresInfo = {}
        self.__ligandInfo = []
        self.__letterTemplateMap = {}
        self.__valueMap = {}
        self.__questionList = []
        self.__all_items = []
        self.__corres_items = []
        self.__token_question_mapping = {}
        self.__additional_text_mapping = {}
        self.__javascript_text_mapping = ""
        #
        self.__setup()

    def __setup(self):
        """ """
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__TemplateFile = os.path.join(str(self.__reqObj.getValue("TemplatePath")), "templates", "correspondence_templt.cif")
        self.__LigandTemplateFile = os.path.join(str(self.__reqObj.getValue("TemplatePath")), "templates", "correspondence_ligand_templt.html")
        self.__ContentTemplateFile = os.path.join(str(self.__reqObj.getValue("TemplatePath")), "templates", "correspondence_content_templt.html")
        self.__ContentTemplateFileMapOnly = os.path.join(str(self.__reqObj.getValue("TemplatePath")), "templates", "correspondence_content_em_map_only_templt.html")
        self.__entryFile = self.__reqObj.getValue("entryfilename")

    def get(self):
        """Get correspondence template"""
        try:
            error, resultfile = self.__runGetCorresInfo()
            if error:
                return error
            #
            self.__getCorrespondenceTempltInfo()
            self.__getCorresInfo(resultfile)
            self.__getValidateInfo()
            if self.__EmMapwithModel or self.__EmFsc143CutOff:
                self.__getValidateInfoCif()
            #
            return self.__doRender()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return "Generating correspondence template failed"
        #

    def __runGetCorresInfo(self):
        """ """
        try:
            resultfile = os.path.join(self.__sessionPath, "corres_1.cif")
            logfilename = os.path.join(self.__sessionPath, "corres_1.log")
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(os.path.join(self.__sessionPath, self.__entryFile))
            dp.op("annot-get-corres-info")
            dp.exp(resultfile)
            dp.expLog(logfilename)
            dp.cleanup()
            #
            f = open(logfilename, "r")
            data = f.read()
            f.close()
            #
            error = ""
            if len(data) > 0 and data.find("Finished!") == -1:
                error = "<pre>\n" + data + "\n</pre>\n"
            #
            return error, "corres_1.cif"
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            error = "error:" + traceback.format_exc()
            return error, ""

    def __getCorrespondenceTempltInfo(self):
        """ """
        cifObj = mmCIFUtil(filePath=self.__TemplateFile)
        #
        tlist = cifObj.GetValue("letter_template")
        for tdir in tlist:
            self.__letterTemplateMap[tdir["type"]] = tdir["text"]
        #
        vlist = cifObj.GetValue("value_mapping")
        for vdir in vlist:
            self.__valueMap[vdir["token"]] = vdir["text"]
        #
        self.__questionList = cifObj.GetValue("rcsb_question_category")
        #
        vlist = cifObj.GetValue("token_question_mapping")
        for vdir in vlist:
            self.__all_items.append(vdir["token"])
            self.__corresInfo[vdir["token"]] = ""
            if "from_corres_info" in vdir and vdir["from_corres_info"] == "y":
                self.__corres_items.append(vdir["token"])
            #
            if "question" in vdir and vdir["question"]:
                self.__token_question_mapping[vdir["token"]] = vdir["question"]
            #
            if "additional_text" in vdir and vdir["additional_text"] == "y":
                self.__additional_text_mapping[vdir["token"]] = "y"
        #

    def __getCorresInfo(self, resultfile):
        """ """
        inputFile = os.path.join(self.__sessionPath, resultfile)
        cifObj = mmCIFUtil(filePath=inputFile)
        for item in self.__corres_items:
            self.__corresInfo[item] = cifObj.GetSingleValue("correspondence_information", item)
        #
        self.__corresInfo["values"] = self.__getMissingAndInsistentValues(cifObj)
        self.__ligandInfo = cifObj.GetValue("ligand_information")
        #
        self.__EmFsc143CutOff = cifObj.GetSingleValue("correspondence_information", "fsc_143_cut_off") == "yes"
        if ("emdbid" in self.__corresInfo) and self.__corresInfo["emdbid"] and ("pdbid" in self.__corresInfo) and self.__corresInfo["pdbid"]:
            self.__EmMapwithModel = True
        #

    def __getMissingAndInsistentValues(self, cifObj):
        """ """
        text = self.__getConcatText(cifObj, "missing_value_items")
        txt = self.__getComparisonText(cifObj)
        if txt:
            if text:
                text += "\n\n"
            #
            text += txt
        #
        return text

    def __getConcatText(self, cifObj, category):
        """ """
        dlist = cifObj.GetValue(category)
        if not dlist:
            return ""
        #
        text = ""
        for dldir in dlist:
            if not dldir["name"] in self.__valueMap:
                continue
            #
            if text:
                text += "\n\n"
            #
            text += self.__valueMap[dldir["name"]]
        #
        return text

    def __getComparisonText(self, cifObj):
        """ """
        dlist = cifObj.GetValue("comparison_info")
        if not dlist:
            return ""
        #
        text = ""
        for dldir in dlist:
            if not dldir["label"] in self.__valueMap:
                continue
            #
            if text:
                text += "\n\n"
            #
            text += self.__valueMap[dldir["label"]] % dldir
        #
        return text

    def __getValidateInfo(self):
        """ """
        depid = self.__reqObj.getValue("entryid")
        xmlPath = os.path.join(self.__sessionPath, depid + "_val-data_P1.xml")
        if not os.access(xmlPath, os.F_OK):
            return
        #
        try:
            vobj = ValidateXml(FileName=xmlPath, verbose=self.__verbose, log=self.__lfh)
            self.__corresInfo["calculated_completeness"] = vobj.getCalculatedCompleteness()
            if self.__corresInfo["reported_completeness"] and self.__corresInfo["calculated_completeness"]:
                c1 = float(self.__corresInfo["reported_completeness"])
                c2 = float(self.__corresInfo["calculated_completeness"])
                cmin = c1
                if c2 < cmin:
                    cmin = c2
                #
                if (abs(c1 - c2) / cmin) > 0.1:
                    self.__corresInfo["completeness_warning"] = "yes"
                #
            #
            for item in ("r_free_diff", "r_work_diff"):
                r_list = vobj.getOutlier(item)
                if r_list:
                    self.__corresInfo[item] = "yes"
                #
            #
            if vobj.getNotFoundResidueInStructureCsList():
                self.__corresInfo["cs_sequence_mismatch"] = "yes"
            #
            if vobj.getCsReferencingOffsetFlag():
                self.__corresInfo["cs_referencing"] = "yes"
            #
            if vobj.getCsOutliers():
                self.__corresInfo["cs_statistics"] = "yes"
            #
            # self.__getPolymerBondOutlier(vobj)
            # self.__getPolymerAngleOutlier(vobj)
            # self.__getPolymerTorsionOutlier(vobj)
            # self.__getNonPolymerBondOutlier(vobj)
            # self.__getNonPolymerAngleOutlier(vobj)
            # self.__getNonPolymerTorsionOutlier(vobj)
            self.__getPolymerRsrzOutlier(vobj)
            # self.__getNonPolymerRsrzOutlier(vobj)
        except:  # noqa: E722 pylint: disable=bare-except
            self.__lfh.write("Read %s failed.\n" % xmlPath)
        #

    def __getValidateInfoCif(self):
        """ """
        depid = self.__reqObj.getValue("entryid")
        cifPath = os.path.join(self.__sessionPath, depid + "_val-data_P1.cif")
        if not os.access(cifPath, os.F_OK):
            return
        #
        try:
            cifObj = mmCIFUtil(filePath=cifPath)
            if self.__EmMapwithModel:
                atom_inclusion_all_atoms = cifObj.GetSingleValue("pdbx_vrpt_summary_em", "atom_inclusion_all_atoms")
                atom_inclusion_backbone = cifObj.GetSingleValue("pdbx_vrpt_summary_em", "atom_inclusion_backbone")
                if atom_inclusion_all_atoms and atom_inclusion_backbone:
                    try:
                        self.__corresInfo["atom_inclusion_all_atoms"] = "%.2f" % (float(atom_inclusion_all_atoms) * 100)
                        self.__corresInfo["atom_inclusion_backbone"] = "%.2f" % (float(atom_inclusion_backbone) * 100)
                    except:  # noqa: E722 pylint: disable=bare-except
                        self.__lfh.write(
                            "_pdbx_vrpt_summary_em.atom_inclusion_all_atoms=%r _pdbx_vrpt_summary_em.atom_inclusion_backbone=%r\n"
                            % (atom_inclusion_all_atoms, atom_inclusion_backbone)
                        )
                    #
                #
            #
            if self.__EmFsc143CutOff:
                author_fsc_cutoff = cifObj.GetSingleValue("pdbx_vrpt_summary_em", "author_provided_fsc_resolution_by_cutoff_pt_143")
                EMDB_resolution = cifObj.GetSingleValue("pdbx_vrpt_summary_em", "EMDB_resolution")
                if author_fsc_cutoff and EMDB_resolution:
                    try:
                        lower_bound = 0.9 * float(author_fsc_cutoff)
                        upper_bound = 1.1 * float(author_fsc_cutoff)
                        resolution = float(EMDB_resolution)
                        if (resolution < lower_bound) or (resolution > upper_bound):
                            self.__corresInfo["fsc_curve"] = "yes"
                        #
                    except:  # noqa: E722 pylint: disable=bare-except
                        self.__lfh.write(
                            "_pdbx_vrpt_summary_em.author_provided_fsc_resolution_by_cutoff_pt_143=%r _pdbx_vrpt_summary_em.EMDB_resolution=%r\n"
                            % (author_fsc_cutoff, EMDB_resolution)
                        )
                    #
                #
            #
        except:  # noqa: E722 pylint: disable=bare-except
            self.__lfh.write("Read %s failed.\n" % cifPath)
        #

    # def __getPolymerBondOutlier(self, vobj):
    #     """ """
    #     list = vobj.getOutlier("bond-outlier")
    #     if not list:
    #         return
    #     #
    #     if len(list) > 1:
    #         self.__corresInfo["polymer_geometry"] = "Bond length outliers:\n"
    #     else:
    #         self.__corresInfo["polymer_geometry"] = "Bond length outlier:\n"
    #     #
    #     self.__corresInfo["polymer_geometry"] += "Molecule  Chain ID  Res Num  Res Name        Atoms        Z     Observed (A)   Ideal (A)"
    #     format = "  %5s     %4s      %4s   %6s     %10s    %7s    %8s       %s"
    #     for dir in list:
    #         if self.__corresInfo["polymer_geometry"]:
    #             self.__corresInfo["polymer_geometry"] += "\n"
    #         #
    #         vlist = []
    #         for item in ("ent", "chain", "resnum", "resname", "atoms", "z", "obs", "mean"):
    #             if item == "atoms":
    #                 vlist.append(dir["atom0"] + "-" + dir["atom1"])
    #             else:
    #                 vlist.append(dir[item])
    #             #
    #         #
    #         self.__corresInfo["polymer_geometry"] += format % tuple(vlist)
    #     #

    # def __getPolymerAngleOutlier(self, vobj):
    #     """ """
    #     list = vobj.getOutlier("angle-outlier")
    #     if not list:
    #         return
    #     #
    #     if self.__corresInfo["polymer_geometry"]:
    #         self.__corresInfo["polymer_geometry"] += "\n\n"
    #     #
    #     if len(list) > 1:
    #         self.__corresInfo["polymer_geometry"] += "Angle value outliers:\n"
    #     else:
    #         self.__corresInfo["polymer_geometry"] += "Angle value outlier:\n"
    #     #
    #     self.__corresInfo["polymer_geometry"] += "Molecule  Chain ID  Res Num  Res Name        Atoms        Z     Observed (A)   Ideal (A)"
    #     format = "  %5s     %4s      %4s   %6s  %15s  %7s    %8s      %s"
    #     for dir in list:
    #         if self.__corresInfo["polymer_geometry"]:
    #             self.__corresInfo["polymer_geometry"] += "\n"
    #         #
    #         vlist = []
    #         for item in ("ent", "chain", "resnum", "resname", "atoms", "z", "obs", "mean"):
    #             if item == "atoms":
    #                 vlist.append(dir["atom0"] + "-" + dir["atom1"] + "-" + dir["atom2"])
    #             else:
    #                 vlist.append(dir[item])
    #             #
    #         #
    #         self.__corresInfo["polymer_geometry"] += format % tuple(vlist)
    #     #

    # def __getPolymerTorsionOutlier(self, vobj):
    #     """ """
    #     list = vobj.getOutlier("torsion-outlier")
    #     if not list:
    #         return
    #     #
    #     if len(list) > 1:
    #         self.__corresInfo["torsion"] = "Ramachandran outliers:\n"
    #     else:
    #         self.__corresInfo["torsion"] = "Ramachandran outlier:\n"
    #     #
    #     self.__corresInfo["torsion"] += "Molecule  Chain ID  Res Num  Res Name        Phi        Psi"
    #     format = "  %5s     %4s      %4s   %6s     %8s   %8s"
    #     for dir in list:
    #         if self.__corresInfo["torsion"]:
    #             self.__corresInfo["torsion"] += "\n"
    #         #
    #         vlist = []
    #         for item in ("ent", "chain", "resnum", "resname", "phi", "psi"):
    #             vlist.append(dir[item])
    #         #
    #         self.__corresInfo["torsion"] += format % tuple(vlist)
    #     #

    # def __getNonPolymerBondOutlier(self, vobj):
    #     """ """
    #     list = vobj.getOutlier("mog-bond-outlier")
    #     if not list:
    #         return
    #     #
    #     if len(list) > 1:
    #         self.__corresInfo["ligand_geometry"] = "Bond length outliers:\n"
    #     else:
    #         self.__corresInfo["ligand_geometry"] = "Bond length outlier:\n"
    #     #
    #     self.__corresInfo["ligand_geometry"] += "Molecule  Chain ID  Res Num  Res Name        Atoms        Z     Observed (A)   Ideal (A)"
    #     format = "  %5s     %4s      %4s   %6s     %10s    %7s    %8s       %s"
    #     for dir in list:
    #         if self.__corresInfo["ligand_geometry"]:
    #             self.__corresInfo["ligand_geometry"] += "\n"
    #         #
    #         vlist = []
    #         for item in ("ent", "chain", "resnum", "resname", "atoms", "Zscore", "obsval", "mean"):
    #             vlist.append(dir[item])
    #         #
    #         self.__corresInfo["ligand_geometry"] += format % tuple(vlist)
    #     #

    # def __getNonPolymerAngleOutlier(self, vobj):
    #     """ """
    #     list = vobj.getOutlier("mog-angle-outlier")
    #     if not list:
    #         return
    #     #
    #     if self.__corresInfo["ligand_geometry"]:
    #         self.__corresInfo["ligand_geometry"] += "\n\n"
    #     #
    #     if len(list) > 1:
    #         self.__corresInfo["ligand_geometry"] += "Angle value outliers:\n"
    #     else:
    #         self.__corresInfo["ligand_geometry"] += "Angle value outlier:\n"
    #     #
    #     self.__corresInfo["ligand_geometry"] += "Molecule  Chain ID  Res Num  Res Name        Atoms        Z     Observed (A)   Ideal (A)"
    #     format = "  %5s     %4s      %4s   %6s  %15s  %7s    %8s      %s"
    #     for dir in list:
    #         if self.__corresInfo["ligand_geometry"]:
    #             self.__corresInfo["ligand_geometry"] += "\n"
    #         #
    #         vlist = []
    #         for item in ("ent", "chain", "resnum", "resname", "atoms", "Zscore", "obsval", "mean"):
    #             vlist.append(dir[item])
    #         #
    #         self.__corresInfo["ligand_geometry"] += format % tuple(vlist)
    #     #

    # def __getNonPolymerTorsionOutlier(self, vobj):
    #     """ """
    #     list = vobj.getOutlier("mog-torsion-outlier")
    #     if not list:
    #         return
    #     #

    def __getPolymerRsrzOutlier(self, vobj):
        """ """
        plist = vobj.getOutlier("polymer-rsrz-outlier")
        if not plist:
            return
        #
        if len(plist) > 1:
            self.__corresInfo["z_score"] = "RSRZ outliers:\n"
        else:
            self.__corresInfo["z_score"] = "RSRZ outlier:\n"
        #
        self.__corresInfo["z_score"] += "Molecule  Chain ID  Res Num  Res Name    RSRZ"
        fmt = "  %5s     %4s      %4s   %6s    %6s"
        llist = []
        for pdir in plist:
            vlist = []
            for item in ("ent", "chain", "resnum", "resname", "rsrz"):
                vlist.append(pdir[item])
            #
            llist.append(vlist)
        #
        if len(plist) > 1:
            llist.sort(key=lambda e: float(e[4]), reverse=True)
        #
        for vlist in llist:
            self.__corresInfo["z_score"] += "\n" + fmt % tuple(vlist)
        #

    # def __getNonPolymerRsrzOutlier(self, vobj):
    #     """ """
    #     list = vobj.getOutlier("ligand-rsrz-outlier")
    #     if not list:
    #         return
    #     #
    #     if self.__corresInfo["z_score"]:
    #         self.__corresInfo["z_score"] += "\n\n"
    #     #
    #     self.__corresInfo["z_score"] += "Molecule  Chain ID  Res Num  Res Name    LLDF"
    #     format = "  %5s     %4s      %4s   %6s    %6s"
    #     for dir in list:
    #         self.__corresInfo["z_score"] += "\n"
    #         #
    #         vlist = []
    #         for item in ("ent", "chain", "resnum", "resname", "ligRSRZ"):
    #             vlist.append(dir[item])
    #         #
    #         self.__corresInfo["z_score"] += format % tuple(vlist)
    #     #

    def __doRender(self):
        """ """
        selectD = {}
        selectD["Sequence"] = "yes"
        selectD["Biological Assembly"] = "yes"
        additionalD = {}
        for item in self.__all_items:
            if (item not in self.__token_question_mapping) or (not self.__corresInfo[item]):
                continue
            #
            selectD[self.__token_question_mapping[item]] = "yes"
            if item in self.__additional_text_mapping and self.__additional_text_mapping[item] == "y":
                additionalD[self.__token_question_mapping[item]] = "yes"
            #
        #
        checked_count = 0
        major_text, checked_count = self.__getMajorMinorText(checked_count, selectD, additionalD, "y")
        minor_text, checked_count = self.__getMajorMinorText(checked_count, selectD, additionalD, "n")
        #
        myD = {}
        myD["letter_header"] = self.__getHeader()

        enc = self.__getEncourage()
        myD["letter_encourage"] = "\n\n" + enc if enc else ""

        myD["major"] = self.__letterTemplateMap["major"]
        myD["major_release"] = self.__letterTemplateMap["major_release"]
        myD["major_minor_addition"] = self.__letterTemplateMap["major_minor_addition"]
        myD["minor"] = self.__letterTemplateMap["minor"]
        myD["minor_release"] = self.__getRelaseInfo()
        myD["letter_footer"] = self.__letterTemplateMap["signature"]
        myD["slection_text"] = self.__getSlectionText(selectD, additionalD)
        myD["text_map"] = self.__javascript_text_mapping
        if self.__EmMapOnly:
            # For map only deposition, encouragement is in the header already.
            myD["full_text"] = myD["letter_header"]
        elif major_text != "":
            myD["full_text"] = (
                myD["letter_header"]
                + myD["letter_encourage"]
                + "\n\n"
                + myD["major"]
                + "\n\n"
                + major_text
                + "\n\n"
                + myD["major_minor_addition"]
                + "\n\n"
                + minor_text
                + "\n\n"
                + myD["major_release"]
                + "\n\n"
                + myD["letter_footer"]
            )
        else:
            myD["full_text"] = (
                myD["letter_header"] + myD["letter_encourage"] + "\n\n" + myD["minor"] + "\n\n" + minor_text + "\n\n" + myD["minor_release"] + "\n\n" + myD["letter_footer"]
            )
        flist = myD["full_text"].split("\n")
        myD["rows"] = str(len(flist))
        #
        # write out default letter
        depid = self.__reqObj.getValue("entryid")
        filename = os.path.join(self.__sessionPath, depid + "_correspondence-to-depositor_P1.txt")
        f = open(filename, "w")
        f.write(myD["full_text"] + "\n")
        f.close()
        #
        if self.__EmMapOnly:
            return self.__processTemplate(self.__ContentTemplateFileMapOnly, myD)
        else:
            return self.__processTemplate(self.__ContentTemplateFile, myD)

    def __getMajorMinorText(self, checked_count, selectD, additionalD, flag):
        text = ""
        for qdir in self.__questionList:
            if qdir["major_flag"] != flag:
                continue
            #
            if qdir["question"] == "Ligand Identity":
                if not self.__ligandInfo:
                    continue
                #
                checked_count += 1
                text += "\n" + str(checked_count) + ". " + qdir["question"] + "\n" + self.__getLigandText(qdir["text"]) + "\n"
            else:
                if not qdir["question"] in selectD:
                    continue
                #
                context = ""
                if "text" in qdir:
                    context = qdir["text"] % self.__corresInfo
                #
                if (qdir["question"] in additionalD) and ("additional_text" in qdir) and qdir["additional_text"]:
                    context += "\n\n" + qdir["additional_text"]
                #
                checked_count += 1
                text += "\n" + str(checked_count) + ". "
                if not qdir["question"].startswith("Free text question"):
                    text += qdir["question"] + "\n\n"
                #
                text += context + "\n\n"
            #
        #
        return text, checked_count

    def __getSlectionText(self, selectD, additionalD):
        text = '<input type="hidden" id="number_question" name="number_question" value="' + str(len(self.__questionList)) + '" />\n'
        #
        count = 0
        for qdir in self.__questionList:
            option = ""
            style = "display: none;"
            if qdir["question"] == "Ligand Identity":
                ligandlist = "[]"
                ligand_context = ""
                table_context = ""
                ligand_text = ""
                text_id = "text_" + str(count)
                if self.__ligandInfo:
                    option = "checked"
                    style = "display: inline;"
                    ligandlist = self.__getLigandList()
                    ligand_context = self.__getLigandContext()
                    table_context = self.__getTableContext(str(count))
                    ligand_text = self.__getLigandText(qdir["text"])
                #
                js_class = "check_box_div"
                text += self.__getCheckBox(str(count), js_class, option, qdir)
                #
                myD = {}
                myD["style"] = style
                myD["ligandlist"] = ligandlist
                myD["template_context"] = qdir["text"]
                myD["ligand_context"] = ligand_context
                myD["table_context"] = table_context
                myD["ligand_text"] = ligand_text
                myD["name"] = text_id
                text += self.__processTemplate(self.__LigandTemplateFile, myD)
            else:
                if qdir["question"] in selectD:
                    option = "checked"
                    style = "display: inline;"
                #
                js_class = "check_box"
                text += self.__getCheckBox(str(count), js_class, option, qdir)
                context = ""
                if "text" in qdir:
                    context = qdir["text"] % self.__corresInfo
                #
                if ("additional_text" in qdir) and qdir["additional_text"]:
                    if ("text_index" in qdir) and qdir["text_index"]:
                        if self.__javascript_text_mapping:
                            self.__javascript_text_mapping += ","
                        self.__javascript_text_mapping += '"' + qdir["text_index"] + '_text":"' + context.replace("\n", "$line_break$") + '",'
                        self.__javascript_text_mapping += '"' + qdir["text_index"] + '_additional_text":"' + qdir["additional_text"].replace("\n", "$line_break$") + '"'
                    #
                    if qdir["question"] in additionalD:
                        context += "\n\n" + qdir["additional_text"]
                    #
                #
                text += self.__getTextArea(str(count), context, style + " font-family: Courier, Serif;")
            #
            count += 1
        #
        return text

    def __getLigandList(self):
        text = ""
        for ldir in self.__ligandInfo:
            if text:
                text += ", "
            #
            text += '"' + ldir["id"] + '"'
        #
        return "[ " + text + " ]"

    def __getLigandContext(self):
        text = ""
        for ldir in self.__ligandInfo:
            text += '<p id="ligand_' + ldir["id"] + '" style="display: none;">\n'
            text += "ID:      " + ldir["id"]
            if "original_id" in ldir:
                text += "    Original ID:  " + ldir["original_id"]
            #
            text += "\n" + ldir["ligand_info"] + "\n"
            text += "</p>\n"
        #
        return text

    def __getHeader(self):
        myD = {}
        for item in ("pdbid", "entryid", "emdbid", "title", "title_em", "author", "author_em", "status_em"):
            myD[item] = self.__corresInfo[item]
        #
        if ("emdbid" in myD) and myD["emdbid"]:
            if ("pdbid" in myD) and myD["pdbid"]:
                return self.__letterTemplateMap["header_pdb_em"] % myD
            else:
                self.__EmMapOnly = True
                return self.__letterTemplateMap["letter_em_only"] % myD
        else:
            return self.__letterTemplateMap["header"] % myD

    def __getEncourage(self):
        myD = {}
        for item in ("pdbid", "emdbid", "nmr_entry", "status_em"):
            myD[item] = self.__corresInfo.get(item, "")

        if len(myD["nmr_entry"]) > 0:
            print("NMR ENTRY - no encouragement")
            return None

        if myD["emdbid"]:
            if myD["status_em"]:
                # map only or map + model
                return self.__letterTemplateMap["encourage_em"]
            else:
                # EM model only
                return None

        # Not EM and not NMR -- Xray
        return self.__letterTemplateMap["encourage_xray"]

    def __getRelaseInfo(self):
        text = ""
        author_release_status_code = self.__corresInfo["author_release_status_code"]
        #
        if author_release_status_code == "HOLD":
            text += self.__letterTemplateMap["release_hold"] % self.__corresInfo
        elif author_release_status_code == "HPUB":
            text += self.__letterTemplateMap["release_hpub"]
        elif author_release_status_code == "REL":
            text += self.__letterTemplateMap["release_rel"]
        else:
            text += self.__letterTemplateMap["release_unknown"]
        #
        text += "\n\n"
        sequence_code = self.__corresInfo["author_release_sequence_code"]
        if sequence_code == "RELEASE NOW":
            text += self.__letterTemplateMap["pre_release_yes"]
        else:
            text += self.__letterTemplateMap["pre_release_no"]
        #
        return text

    def __getTableContext(self, count):
        text = ""
        for ldir in self.__ligandInfo:
            label = "ID: " + ldir["id"]
            if "original_id" in ldir:
                label += " &nbsp; &nbsp; ( Original ID: " + ldir["original_id"] + " )"
            #
            text += "<tr>\n"
            text += '<td style="text-align:left;border-style:none;width:200px"> ' + label + " </td>\n"
            text += (
                '<td style="text-align:center;border-style:none;width:120px"> '
                + '<input class="add_context" id="add_'
                + count
                + "_"
                + ldir["id"]
                + '" type="button" value ="Add" /> </td>\n'
            )
            text += (
                '<td style="text-align:center;border-style:none;width:120px"> '
                + '<input class="remove_context" id="remove_'
                + count
                + "_"
                + ldir["id"]
                + '" type="button" value ="Remove" /> </td>\n'
            )
            text += "</tr>\n"
        #
        return text

    def __getLigandText(self, template_context):
        text = "\n" + template_context + "\n\n"
        first = True
        for ldir in self.__ligandInfo:
            if not first:
                text += "\n"
            #
            text += "ID:      " + ldir["id"]
            if "original_id" in ldir:
                text += "    Original ID:  " + ldir["original_id"]
            #
            text += "\n" + ldir["ligand_info"] + "\n"
            first = False
        #
        return text

    def __getCheckBox(self, cid, js_class, option, qdir):
        """ """
        value = qdir["question"]
        flag = qdir["major_flag"]
        text = "<tr>\n"
        name = "question_" + cid
        text += (
            '<td style="text-align:left; border-style:none"><input type="checkbox" class="'
            + js_class
            + '" id="'
            + name
            + '" name="'
            + name
            + '" value="'
            + value
            + '" '
            + option
            + " /> "
            + value
            + " </td> \n"
        )
        #
        if (
            ("additional_text" in qdir)
            and qdir["additional_text"]
            and ("text_index" in qdir)
            and qdir["text_index"]
            and ("add_remove_button" in qdir)
            and qdir["add_remove_button"]
        ):
            text += (
                '<td style="text-align:left; border-style:none"><input type="button" value="Add '
                + qdir["add_remove_button"]
                + "\" onclick=\"update_text_area('add', '"
                + qdir["text_index"]
                + "', 'text_"
                + cid
                + "');\"/> </td> \n"
            )
            text += (
                '<td style="text-align:left; border-style:none"><input type="button" value="Remove '
                + qdir["add_remove_button"]
                + "\" onclick=\"update_text_area('remove', '"
                + qdir["text_index"]
                + "', 'text_"
                + cid
                + "');\"/> </td> \n"
            )
        else:
            text += '<td style="text-align:left; border-style:none"> &nbsp; </td>\n' + '<td style="text-align:left; border-style:none"> &nbsp; </td>\n'
        #
        major_option = ""
        if flag == "y":
            major_option = "checked"
        #
        name = "majorflag_" + cid
        text += '<td style="text-align:left; border-style:none"><input type="checkbox" id="' + name + '" name="' + name + '" value="y" ' + major_option + " /> Major issue </td> \n"
        text += "</tr>\n"
        return text

    def __getTextArea(self, tid, value, style):
        """ """
        vlist = value.split("\n")
        irow = len(vlist) + 3
        name = "text_" + tid
        text = '<tr><td style="text-align:left; border-style:none" colspan="4">'
        text += '<textarea style="' + style + '" id="' + name + '" name="' + name + '" cols="120" rows="' + str(irow) + '" wrap>\n' + value + "</textarea>\n </td></tr> \n"
        text += '<tr><td style="text-align:left; border-style:none" colspan="4">&nbsp;</td></tr>\n'
        return text

    def __processTemplate(self, fn, parameterDict=None):
        """ """
        if parameterDict is None:
            parameterDict = {}
        ifh = open(fn, "r")
        sIn = ifh.read()
        ifh.close()
        return sIn % parameterDict
