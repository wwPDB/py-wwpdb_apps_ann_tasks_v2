"""
Manage the generating of PCM missing annotation table.

"""

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

import os
import csv
import sys
import logging
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
import logging

# Set the default logger handler level to INFO
logging.getLogger().setLevel(logging.INFO)


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
        self.__csvPath = os.path.join(self.__sessionPath, self.__entryId + "_ccd_no_pcm_ann.csv")
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

    def setLogHandle(self, log=sys.stderr):
        """Reset the stream for logging output."""
        try:
            self.__lfh = log
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def run(self):
        """Generate JSON format data"""
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
        """Run X program"""
        self.__entryFile = self.__reqObj.getValue("entryfilename")
        entry_file_path = os.path.join(self.__sessionPath, self.__entryFile)

        if not os.access(entry_file_path, os.F_OK):
            logging.error("Missing entry file %s", entry_file_path)
            return
        #
        logging.info("Processing entry file %s", self.__entryFile)

        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(entry_file_path)
            dp.op("annot-pcm-check-ccd-ann")
            dp.exp(dstPath=self.__csvPath)
            dp.expLog(os.path.join(self.__sessionPath, self.__entryId + "_ccd_no_pcm_ann.log"))
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
            myD["statustext"] = "Failed to build form for x"
            return myD

        htmlcontent = self.__tableTemplate % self.__identifier
        htmlcontent += (
            "<tr>\n<th>Comp Id</th>\n<th>Modified Residue Id</th>\n<th>Type</th>\n<th>Category</th>\n<th>Position</th>\n<th>Polypeptide Position</th>\n<th>Comp Id Linking Atom</th>\n<th>Modified Residue Id Linking Atom</th>\n<th>First Instance Model Db Code</th>\n<th>ChemRefUI Link</th>\n</tr>\n"
        )
        #
        columns = {
            "Comp_id": {"editable": False},
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
                htmlcontent += "</tr>\n"        
        #
        htmlcontent += "</table>\n"
        #
        myD = {}
        myD["statuscode"] = "ok"
        myD["htmlcontent"] = htmlcontent
        return myD