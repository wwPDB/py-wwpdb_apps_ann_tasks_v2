##
# File:  PdbxReportDepictBootstrap.py
# Date:  11-Jul-2013  Jdw
#
# Updates:
#
##
"""
Create tabular HTML reports from chemical reference definitions.

This version uses Bootstrap CSS framework constructs.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import random
from wwpdb.apps.ann_tasks_v2.depict.PdbxDepictBootstrapBase import PdbxDepictBootstrapBase


class PdbxReportDepictBootstrap(PdbxDepictBootstrapBase):
    """Create tabular HTML reports from PDBx data files.

    This version uses Bootstrap CSS framework constructs.

    """

    def __init__(self, styleObject=None, includePath=None, verbose=False, log=sys.stderr):
        """
        :param `styleObject`:  object containing report data and formatting details.
        :param `includePath`:  path to web application html include files.
        :param `verbose`:      boolean flag to activate verbose logging.
        :param `log`:          stream for logging.

        """
        super(PdbxReportDepictBootstrap, self).__init__(includePath=includePath, verbose=verbose, log=log)
        self.__lfh = log
        self.__debug = False
        #
        self.__st = styleObject
        #
        self.__requestHost = None
        #
        self.__setup()

    def __setup(self):
        """Category list --

        [(categoryName, categoryAbbrev, displayStyle (row-wise,column-wise)], ... ]
        """
        #
        if self.__st.getStyleId() in ["PDBX_T1"]:
            self.__reportCategories = [("citation", "citation", "row-wise"), ("citation_author", "citation_author", "row-wise")]
        elif self.__st.getStyleId() in ["PDBX_T2"]:
            self.__reportCategories = [("citation", "citation", "row-wise"), ("citation_author", "citation_author", "row-wise")]
        elif self.__st.getStyleId() in ["PDBX_REPORT_V1"]:
            self.__reportCategories = [
                ("pdbx_data_processing_status", "Data Processing Skip Tasks", "row-wise"),
                ("exptl", "Experimental", "row-wise"),
                ("pdbx_related_exp_data_set", "Related Exp Data", "row-wise"),
                ("pdbx_database_status", "PDB Status", "row-wise"),
                ("em_admin", "EM admin", "row-wise"),
                ("em_experiment", "EM experiment", "row-wise"),
                ("database_PDB_caveat", "Caveat", "row-wise"),
                ("entity", "Entity description", "row-wise"),
                ("entity_poly", "Polymers", "row-wise"),
                ("pdbx_entity_branch_list", "Carbohydrate polymers", "row-wise"),
                ("entity_src_gen", "Engineered Source", "row-wise"),
                ("entity_src_nat", "Natural Source", "row-wise"),
                ("pdbx_entity_src_syn", "Synthetic Source", "row-wise"),
                ("em_entity_assembly", "EM entity assembly", "row-wise"),
                ("em_entity_assembly_naturalsource", "EM Natural Source", "row-wise"),
                ("em_entity_assembly_recombinant", "EM recombinant Source", "row-wise"),
                ("struct_ref", "Sequence reference", "row-wise"),
                ("struct_ref_seq", "Sequence alignment details", "row-wise"),
                ("pdbx_struct_ref_seq_depositor_info", "Depositors cross reference", "row-wise"),
                ("struct_ref_seq_dif", "Sequence discrepancies", "row-wise"),
                ("pdbx_entity_nonpoly", "Non-polymers", "row-wise"),
                ("pdbx_entity_instance_feature", "Ligand of Interest", "row-wise"),
                ("pdbx_chem_comp_depositor_info", "Depositor ligand info", "row-wise"),
                ("struct_keywords", "Keywords", "row-wise"),
                ("pdbx_struct_assembly", "Assembly Details", "row-wise"),
                ("pdbx_struct_assembly_gen", "Assembly Gen Details", "row-wise"),
                ("pdbx_struct_oper_list", "Assembly Oper List Details", "row-wise"),
                ("pdbx_struct_assembly_depositor_info", "Author Assembly Details", "row-wise"),
                ("pdbx_struct_assembly_auth_evidence", "Author Assembly Evidence", "row-wise"),
                # ('pdbx_depui_status_flags', 'DepUI Flags', 'row-wise'),
                ("pdbx_SG_project", "Structural genomics", "row-wise"),
                ("pdbx_database_related", "Related entries", "row-wise"),
                ("pdbx_contact_author", "Contact authors", "row-wise"),
                # ('citation','Primary citation','column-wise'),
                ("pdbx_validate_close_contact", "Close contacts", "row-wise"),
                ("pdbx_validate_symm_contact", "Close symmetry contacts", "row-wise"),
                ("struct_conn", "Links", "row-wise"),
                # ('symmetry', 'Symmetry', 'row-wise'),
                # ('cell', 'Cell constants', 'row-wise'),
                # ('exptl_crystal_grow', 'Crystallization details', 'row-wise'),
                # ('diffrn_source','Data collection (source details)','row-wise'),
                # ('diffrn_detector','Data collection (detector details)','row-wise'),
                # ('reflns', 'Reflection statistics','row-wise'),
                # ('reflns_shell','Reflection shell statistics','row-wise'),
                # ('refine','Refinement','column-wise'),
                # ('refine_ls_restr','Refinement restraints','row-wise'),
                # ('refine_ls_shell','Refinement shell statistics','row-wise'),
                # ('software','Software','row-wise'),
                # ('pdbx_binding_assay','Binding Assay','row-wise')
            ]

        elif self.__st.getStyleId() in ["PDBX_DCC_REPORT_V1"]:
            self.__reportCategories = [
                ("pdbx_density", "DCC Errors", "column-wise"),
                # ('pdbx_rscc_mapman_overall','Density correlation summary','column-wise'),
                # ('pdbx_dcc_software','Software used by DCC','row-wise'),
                ("pdbx_dcc_sf", "Counting statistics of SF file", "row-wise"),
                ("pdbx_density_corr", "Density correlation", "row-wise"),
                # ('pdbx_rscc_mapman', 'Real-space density statistics by residue','row-wise')
            ]
        elif self.__st.getStyleId() in ["PDBX_GEOMETRY_REPORT_V1"]:
            self.__reportCategories = [
                ("pdbx_validate_close_contact", "Close contacts", "row-wise"),
                ("pdbx_validate_symm_contact", "Close symmetry contacts", "row-wise"),
                ("pdbx_validate_rmsd_bond", "Bond distance RMSD", "row-wise"),
                ("pdbx_validate_rmsd_angle", "Bond angle RMSD", "row-wise"),
                ("pdbx_validate_torsion", "Torsion outliers", "row-wise"),
                ("pdbx_validate_peptide_omega", "Omega bond", "row-wise"),
                ("pdbx_validate_main_chain_plane", "Main chain planarity", "row-wise"),
                ("pdbx_validate_polymer_linkage", "Polymer linkages", "row-wise"),
                ("pdbx_validate_chiral", "Chirality exceptions", "row-wise"),
            ]

    def render(self, eD, style="tabs", leadingHtmlL=None, trailingHtmlL=None):
        """ """
        if style in ["tabs"]:
            return self.__doRenderTabs(eD)
        elif style in ["accordion", "multiaccordion"]:
            return self.__doRenderAccordion(eD)
        elif style in ["page-multiaccordion", "page-accordion"]:
            return self.__doRenderPage(eD, leadingHtmlL, trailingHtmlL)
        else:
            return []

    def __doRenderPage(self, eD, leadingHtmlL, trailingHtmlL):
        """
        <div id="review-admin-dialog">
            <div id="review-report-container">
                <div id="review-inline-idops-report"  class="report-content"></div>
            </div>
        </div> <!-- end review admin dialog -->
        """
        oL = []
        oL.extend(self.appPageTop())

        oL.append('<div class="page-header">')
        oL.append("<h3>Data Review Report</h3>")
        oL.append("</div>")
        if leadingHtmlL is not None and len(leadingHtmlL) > 0:
            oL.extend(leadingHtmlL)
        oL.append('<div id="review-admin-dialog">')
        oL.append('<div id="review-report-container">')
        oL.append('<div id="review-inline-idops-report"  class="report-content">')
        oL.extend(self.__doRenderAccordion(eD))
        oL.append("</div>")
        oL.append("</div>")
        oL.append("</div>")
        if trailingHtmlL is not None and len(trailingHtmlL) > 0:
            oL.extend(trailingHtmlL)

        oL.extend(self.appPageBottom())
        return oL

    def __doRenderTabs(self, eD):
        """Render a tabbed table set.

        Bootstrap markup template  --

        <div class="tabbable"> <!-- Only required for left/right tabs -->
            <ul class="nav nav-tabs">
               <li class="active"><a href="#tab1" data-toggle="tab">Section 1</a></li>
               <li><a href="#tab2" data-toggle="tab">Section 2</a></li>
            </ul>

            <div class="tab-content">
               <div class="tab-pane active" id="tab1">
                   <p>I'm in Section 1.</p>
               </div>
                <div class="tab-pane" id="tab2">
                             <p>Howdy, I'm in Section 2.</p>
                </div>
             </div>
        </div>

        """
        idPrefix = "tab" + str(random.randint(0, 100000))
        catList = self.__reportCategories
        #
        if self.__debug:
            for ii, tup in enumerate(catList):
                self.__lfh.write("PdbxReportDepict (doRenderTabs) ii %d  tup %r\n" % (ii, tup))
            for ii, (x, y, z) in enumerate(catList):
                self.__lfh.write("PdbxReportDepict (doRenderTabs) ii %d  values  %s %s %s\n" % (ii, x, y, z))
        #
        oL = []

        #
        # need for URL construction --
        self.__requestHost = eD["requestHost"]
        cD = eD["dataDict"]
        idCode = eD["idCode"]
        #
        #
        # Write the tabs --
        #
        oL.append('<div class="tabbable">')
        oL.append('<ul class="nav nav-tabs">')
        oL.append('<li><a  class="active" href="#%s-tabs-id" data-toggle="tab">%s</a></li>' % (idPrefix, idCode))

        for ii, (catName, catNameAbbrev, catStyle) in enumerate(catList):
            # For only popuated categories
            if catName in cD and (len(cD[catName]) > 0):
                oL.append('<li><a href="#%s-tabs-%d" data-toggle="tab">%s</a></li>' % (idPrefix, ii, catNameAbbrev))
        oL.append("</ul>")
        #
        # Write the tables --
        #
        oL.append('<div  class="tab-content"> ')
        #
        oL.append('<div class="tab-pane active"  id="%s-tabs-id"></div>' % (idPrefix))

        for ii, (catName, catNameAbbrev, catStyle) in enumerate(catList):
            # For only popuated categories
            if catName in cD and (len(cD[catName]) > 0):
                oL.append('<div class="tab-pane"  id="%s-tabs-%d">' % (idPrefix, ii))
                oL.append('<table class="table table-striped table-bordered table-condensed" id="%s-%s">' % (idPrefix, catName))
                if catStyle == "column-wise":
                    self.__renderTableColumnWise(catName, cD[catName][0], oL)
                else:
                    self.__renderTableRowWise(catName, cD[catName], oL)

                oL.append("</table>")

                oL.append("</div>")
        oL.append('</div>  <!-- end "tab-content" -->')
        oL.append("</div>  <!-- end tabbable -->")
        #
        return oL

    def __doRenderAccordion(self, eD):
        """
        Bootstrap accordion template  --

        <div class="accordion" id="accordion2">
            <div class="accordion-group">
               <div class="accordion-heading">
                 <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapseOne">  Collapsible Group Item #1  </a>
               </div>
               <div id="collapseOne" class="accordion-body collapse in">
                   <div class="accordion-inner">
                         Anim pariatur cliche...
                   </div>
               </div>
             </div>

             <div class="accordion-group">
                 <div class="accordion-heading">
                     <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapseTwo"> Collapsible Group Item #2 </a>
                 </div>
                  <div id="collapseTwo" class="accordion-body collapse">
                     <div class="accordion-inner">
                           Anim pariatur cliche...
                     </div>
                  </div>
             </div>
        </div>

        """
        #

        #
        idPrefix = "acc" + str(random.randint(0, 100000))
        oL = []
        catList = self.__reportCategories
        self.__requestHost = eD["requestHost"]
        cD = eD["dataDict"]
        #
        idTop = idPrefix + "-top"

        #
        # Write the tables --
        #
        surroundOp = True
        #
        oL.append('<div class="accordion" id="%s">' % idTop)
        if surroundOp:
            idCode = eD["idCode"] if eD["idCode"] is not None else eD["blockId"]
            idSectionTop = idCode + "-" + idPrefix
            active = "in"
            oL.append('<div class="accordion-group">')
            oL.append('<div class="accordion-heading">')
            oL.append('<a class="accordion-toggle pull-right" data-toggle="collapse" href="#%s">Show/hide report for %s</a>' % (idSectionTop, idCode))
            oL.append("<br />")
            oL.append("</div>")
            oL.append('<div id="%s" class="accordion-body collapse %s">' % (idSectionTop, active))
            oL.append('<div  class="accordion-inner">')

        #
        isMulti = True
        isFirst = True
        for ii, (catName, catNameAbbrev, catStyle) in enumerate(catList):
            # For only popuated categories
            if catName in cD and (len(cD[catName]) > 0):
                active = "in" if isFirst else ""
                idSection = idPrefix + "-sec-" + str(ii)
                oL.append('<div class="accordion-group">')
                oL.append('<div class="accordion-heading">')
                if isMulti:
                    oL.append('<a class="accordion-toggle" data-toggle="collapse" href="#%s"> <h4>%s</h4></a>' % (idSection, catNameAbbrev))
                else:
                    oL.append('<a class="accordion-toggle" data-toggle="collapse" data-parent="#%s" href="#%s"><h4>%s</h4></a>' % (idTop, idSection, catNameAbbrev))
                oL.append("</div>")
                oL.append('<div id="%s" class="accordion-body collapse %s">' % (idSection, active))
                oL.append('<div  class="accordion-inner">')
                #
                oL.append('<table class="table table-striped table-bordered table-condensed">')
                if catStyle == "column-wise":
                    self.__renderTableColumnWise(catName, cD[catName][0], oL)
                else:
                    self.__renderTableRowWise(catName, cD[catName], oL)
                oL.append("</table>")
                #
                oL.append("</div>")
                oL.append("</div>")
                #
                oL.append("</div> <!-- end of accordion group -->")

        if surroundOp:
            oL.append("</div>")
            oL.append("</div>")
            oL.append("</div>")

        oL.append("</div> <!-- end of accordion -->")
        #
        return oL

    def __renderTableColumnWise(self, catName, rD, oL):
        """Render table with unit cardinality.  Columns for the single row are listed vertically
        to the left of column values.
        """

        #
        iCol = 0
        self.__markupRow(catName, rD)
        #
        for itemName, itemDefault in self.__st.getItemNameAndDefaultList(catName):
            if itemName in rD:
                itemValue = rD[itemName]
            else:
                itemValue = itemDefault

            itemValue = "<br />".join(itemValue.split("\n"))

            oL.append("<tr>")
            oL.append("<td>%s</td>" % self.__attributePart(itemName))

            oL.append("<td>%s</td>" % (itemValue))
            oL.append("</tr>")
            iCol += 1

    def __renderTableRowWise(self, catName, rL, oL):
        """Render a multirow table."""
        # Column labels --
        oL.append("<tr>")
        for itemName in self.__st.getItemNameList(catName):
            oL.append("<th>%s</th>" % self.__attributePart(itemName))
        oL.append("</tr>")
        #
        # Column data ---
        #
        iRow = 0
        for row in rL:
            self.__markupRow(catName, row)
            self.__renderRow(catName, row, iRow, oL, insertDefault=False, insertCode="", opNum=0)
            iRow += 1
        #
        #

    def __renderRow(self, catName, row, iRow, oL, insertDefault=False, insertCode="", opNum=0):  # pylint: disable=unused-argument
        """Render a row in a multirow table."""
        oL.append("<tr>")
        #
        for itemName, itemDefault in self.__st.getItemNameAndDefaultList(catName):
            if insertDefault:
                itemValue = itemDefault
            elif itemName in row:
                itemValue = row[itemName]
            else:
                itemValue = itemDefault
            itemValue = "<br />".join(itemValue.split("\n"))

            oL.append("<td>%s</td>" % (itemValue))
        oL.append("</tr>")
        #

    def __markupRow(self, catName, rD):
        """Markup a row (row dictionary) in the input category."""
        if catName == "pdbx_reference_molecule_list":
            itemName = "_pdbx_reference_molecule_list.prd_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) > 5 and itemValue.startswith("PRD_"):
                    rD[itemName] = '<a target="_blank" href="http://%s/service/chemref/bird/report?prdId=%s&format=%s">%s</a>' % (self.__requestHost, itemValue, "html", itemValue)

        if catName == "pdbx_reference_molecule_synonyms":
            itemName = "_pdbx_reference_molecule_synonyms.prd_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) > 5 and itemValue.startswith("PRD_"):
                    rD[itemName] = '<a target="_blank" href="http://%s/service/chemref/bird/report?prdId=%s&format=%s">%s</a>' % (self.__requestHost, itemValue, "html", itemValue)

            itemName = "_pdbx_reference_molecule_synonyms.chem_comp_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">%s</a>' % (
                        itemValue,
                        itemValue,
                    )

        if catName == "pdbx_reference_molecule_features":
            itemName = "_pdbx_reference_molecule_features.prd_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) > 5 and itemValue.startswith("PRD_"):
                    rD[itemName] = '<a target="_blank" href="http://%s/service/chemref/bird/report?prdId=%s&format=%s">%s</a>' % (self.__requestHost, itemValue, "html", itemValue)

            itemName = "_pdbx_reference_molecule_features.chem_comp_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">%s</a>' % (
                        itemValue,
                        itemValue,
                    )

        if catName == "pdbx_reference_molecule_details":
            itemName1 = "_pdbx_reference_molecule_details.source"
            itemName2 = "_pdbx_reference_molecule_details.source_id"
            if itemName1 in rD:
                srcType = str(rD[itemName1]).upper()
                srcValue = rD[itemName2]
                if srcType == "DOI" and len(srcValue) > 2:
                    rD[itemName2] = '<a target="_blank" href="http://dx.doi.org/%s">%s</a>' % (srcValue, srcValue)
                if srcType == "PUBMED" and len(srcValue) > 2:
                    rD[itemName2] = '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/sites/entrez?cmd=search&db=pubmed&term=%s">%s</a>' % (srcValue, srcValue)
                if srcType == "DRUGBANK" and len(srcValue) > 2:
                    rD[itemName2] = '<a target="_blank" href="http://www.drugbank.ca/cgi-bin/getCard.cgi?CARD=%s">%s</a>' % (srcValue, srcValue)
                if srcType == "PUBCHEM" and len(srcValue) > 2:
                    rD[itemName2] = '<a target="_blank" href="http://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid=%s">%s</a>' % (srcValue, srcValue)

                if srcType == "URL" and len(srcValue) > 2:
                    rD[itemName2] = '<a target="_blank" href="%s">%s</a>' % (srcValue, srcValue)

                if srcType == "PMCID" and len(srcValue) > 2:
                    rD[itemName2] = '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/pmc/?term=%s">%s</a>' % (srcValue, srcValue)

                if srcType == "PMC" and len(srcValue) > 2:
                    rD[itemName2] = '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/pmc/?term=%s">%s</a>' % (srcValue, srcValue)

                if srcType == "UNIPROT" and len(srcValue) > 2:
                    rD[itemName2] = '<a target="_blank" href="http://www.uniprot.org/uniprot/%s">%s</a>' % (srcValue, srcValue)

        if catName == "citation":
            itemName = "_citation.pdbx_database_id_DOI"
            if itemName in rD and len(rD[itemName]) > 1:
                itemValue = rD[itemName]
                rD[itemName] = '<a target="_blank" href="http://dx.doi.org/%s">%s</a>' % (itemValue, itemValue)
            itemName = "_citation.pdbx_database_id_PubMed"
            if itemName in rD and len(rD[itemName]) > 1:
                itemValue = rD[itemName]
                rD[itemName] = '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/sites/entrez?cmd=search&db=pubmed&term=%s">%s</a>' % (itemValue, itemValue)

        if catName == "pdbx_reference_molecule":
            itemName = "_pdbx_reference_molecule.representative_PDB_id_code"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) > 3:
                    rD[itemName] = '<a target="_blank" href="http://www.rcsb.org/pdb/explore/explore.do?structureId=%s">%s</a>' % (itemValue, itemValue)

            itemName = "_pdbx_reference_molecule.chem_comp_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">%s</a>' % (
                        itemValue,
                        itemValue,
                    )

        if catName == "pdbx_reference_entity_nonpoly":
            itemName = "_pdbx_reference_entity_nonpoly.chem_comp_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">%s</a>' % (
                        itemValue,
                        itemValue,
                    )

        if catName == "pdbx_reference_entity_poly_seq":
            itemName = "_pdbx_reference_entity_poly_seq.mon_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">%s</a>' % (
                        itemValue,
                        itemValue,
                    )

            itemName = "_pdbx_reference_entity_poly_seq.parent_mon_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">%s</a>' % (
                        itemValue,
                        itemValue,
                    )

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1 :]
