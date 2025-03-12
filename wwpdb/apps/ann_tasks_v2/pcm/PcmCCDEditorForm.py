"""
Manage the generating of PCM missing annotation table.

"""

import os
import csv
import sys
import logging
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.io.locator.PathInfo import PathInfo


class PcmCCDEditorForm(object):
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
        self.__entryFile = None
        #
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        self.__csvFile = self.__pI.getFileName(self.__entryId, contentType="pcm-missing-data", formatType="csv", versionId="none", partNumber="1")
        self.__csvPath = os.path.join(self.__sessionPath, self.__csvFile)
        #
        self.__tableTemplate = '<table id="table_%s" class="table table-condensed table-bordered table-striped">\n'
        self.__tdTagTemplate = '<td style="border-style:none">%s</td>\n'
        self.__editableTemplate = '<b class="%s" id="%s" style="display:inline">%s</b>'
        logging.info("Processing entry %s", self.__entryId)

    def setLogHandle(self, log=sys.stderr):
        """Reset the stream for logging output."""
        try:
            self.__lfh = log
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def run(self):
        """Generate JSON format data"""
        logging.info("Processing entry %s", self.__entryId)

        if not self.__identifier:
            return False
        #
        if self.__identifier == self.__entryId:
            self.__runPcmCcdCheck()

        if os.access(self.__csvPath, os.F_OK):
            return True
        #
        return False

    def __runPcmCcdCheck(self):
        """Run PCM script to check missing annotation"""
        self.__entryFile = self.__reqObj.getValue("entryfilename")
        inpPdbxPath = os.path.join(self.__sessionPath, self.__entryFile)
        if not os.access(inpPdbxPath, os.F_OK):
            logging.error("Missing entry file %s", inpPdbxPath)
            return
        #
        logging.info("Processing entry file %s", self.__entryFile)
        #
        if os.access(self.__csvPath, os.F_OK):
            os.remove(self.__csvPath)
        #
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPdbxPath)
            dp.op("annot-pcm-check-ccd-ann")
            dp.expList(dstPathList=[inpPdbxPath, self.__csvPath])
            dp.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #

    def getCCDForm(self):
        """Get CCD missing annotation form"""
        myD = {}
        myD["statuscode"] = "failed"
        myD["statustext"] = "Invalid ajax call"
        if not self.__identifier:
            return myD
        #
        if self.__identifier == self.__entryId:
            return self.__buildCCDFormHtml()
        #
        return myD

    def __buildCCDFormHtml(self):
        # depending on the output of the binary
        # check if it matches this entry id

        if not os.access(self.__csvPath, os.F_OK):
            myD = {}
            myD["statuscode"] = "failed"
            myD["statustext"] = "Failed to build form for %s. Couldn't find output csv file" % self.__entryId
            return myD

        with open(self.__csvPath, 'r') as fp:
            content = "PTM annotation is successfully updated. No missing pcm data found."
            if content in fp.read():
                myD = {}
                myD["statuscode"] = "ok"
                myD["htmlcontent"] = content
                return myD

        htmlcontent = self.__tableTemplate % self.__identifier
        htmlcontent += (
            "<tr>\n<th>Comp Id</th>\n<th>Link Id</th>\n<th>Modified Residue Id</th>\n<th>Type</th>\n<th>Category</th>\n<th>Position</th>\n<th>Polypeptide Position</th>\n<th>Comp Id Linking Atom</th>\n<th>Modified Residue Id Linking Atom</th>\n<th>First Instance Model Db Code</th>\n<th>ChemRefUI Link</th>\n</tr>\n"  # noqa: E501
        )
        #
        columns = {
            "Comp_id": {"editable": False},
            "Link_id": {"editable": False},
            "Modified_residue_id": {"editable": False},
            "Type": {"editable": False},
            "Category": {"editable": False},
            "Position": {"editable": False},
            "Polypeptide_position": {"editable": False},
            "Comp_id_linking_atom": {"editable": False},
            "Modified_residue_id_linking_atom": {"editable": False},
            "First_instance_model_db_code": {"editable": False},
        }

        with open(self.__csvPath, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                comp_id = row['Comp_id']

                for c in columns:
                    if columns[c]['editable']:
                        ed_id = f"{comp_id}_{c}"
                        ed_text = self.__editableTemplate % ("editable_text", ed_id, row[c])
                        htmlcontent += self.__tdTagTemplate % ed_text
                    else:
                        htmlcontent += self.__tdTagTemplate % row[c]

                # add last column with link
                chem_ref_link = "/chem_ref_data_ui/chemref_editor_bs.html?searchTarget=%s" % comp_id
                htmlcontent += self.__tdTagTemplate % f'<a href="{chem_ref_link}" target="_blank">{comp_id}</a>'
                htmlcontent += "</tr>\n"
        #
        htmlcontent += "</table>\n"
        #
        myD = {}
        myD["statuscode"] = "ok"
        myD["htmlcontent"] = htmlcontent
        return myD
