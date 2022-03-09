##
# File: PdbxIo.py
# Date: 12-Jul-2013  John Westbrook
#
# Update:
#  1-Jan-2014  jdw add X-ray experimental and geometry formats
#  7-Jul-2014  jdw add class PdbxStatusHistoryIo()
# 16-Jul-2014  jdw add class PdbxLocalMapIndexIo()
#  6-Jan-2015  jdw update content for status history -
# 31-Jul-2015  jdw make __getStatusDetails  add support for deposit_site and process_site
#  2-Aug-2015  jdw make  __getInfoHistory() add support for deposit_site and process_site
#                  all downstreamm references updated --
# 27-Aug-2015  jdw add support for managing em_admin status details -
# 27-Aug-2015  jdw return emdb and bmrb accessions with general entry info
# 31-Aug-2015  jdw prefix attribute keys in get/setEmStatusDetails() with 'em_' to avoid
#                  confict with model status details --
# 21-Feb-2016  jdw add header_release_data to em em status details.
# 12-Feb-2018  ep  Add pdbx_depui_entry_details.requested_accession_types to __getInfoGeneral()
#  7-Jul-2019  ep  Retrieve pdbx_database_status.post_rel_status in __getInfoGeneral()
# 15-Jul-2019  ep  Retrieve pdbx_database_status.post_rel_recvd_coord* to __getInfoGeneral()
#
##
"""
Wrapper for reading PDBx data files including style details.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"

import logging
import sys
import time

from mmcif_utils.style.PdbxEntryInfoCategoryStyle import PdbxEntryInfoCategoryStyle
from mmcif_utils.style.PdbxGeometryReportCategoryStyle import PdbxGeometryReportCategoryStyle
from mmcif_utils.style.PdbxLocalMapIndexCategoryStyle import PdbxLocalMapIndexCategoryStyle
from mmcif_utils.style.PdbxStatusHistoryCategoryStyle import PdbxStatusHistoryCategoryStyle
from mmcif_utils.style.PdbxStyleIoUtil import PdbxStyleIoUtil

# from mmcif_utils.style.PdbxXrayExpReportCategoryStyle import PdbxXrayExpReportCategoryStyle
from wwpdb.apps.ann_tasks_v2.report.styles.DCCReport import PdbxXrayExpReportCategoryStyle

# from mmcif_utils.style.PdbxReportCategoryStyle import PdbxReportCategoryStyle
from wwpdb.apps.ann_tasks_v2.report.styles.ModelReport import PdbxReportCategoryStyle

logger = logging.getLogger()


class PdbxReportIo(PdbxStyleIoUtil):
    """Methods for reading PDBx data files for reporting applications including style details."""

    def __init__(self, verbose=True, log=sys.stderr):
        super(PdbxReportIo, self).__init__(styleObject=PdbxReportCategoryStyle(), verbose=verbose, log=log)

        # self.__verbose = verbose
        # self.__debug = False
        self.__lfh = log
        #
        self.__filePath = None

        self.__idCode = None

    def getCategory(self, catName="entity"):
        return self.getItemDictList(catName)

    def setFilePath(self, filePath, idCode=None):
        """Specify the file path for the target and optionally provide an identifier
        for the data section within the file.
        """
        self.__filePath = filePath
        self.__idCode = idCode
        if self.readFile(self.__filePath):
            if self.__idCode is not None:
                return self.setContainer(containerName=self.__idCode)
            else:
                return self.setContainer(containerIndex=0)
        else:
            return False

    def get(self):
        """
        Check for a valid current data container.

        Returns True for success or False otherwise.
        """
        return self.getCurrentContainerId() is not None

    def complyStyle(self):
        return self.testStyleComplete(self.__lfh)

    def setBlock(self, blockId):
        return self.setContainer(containerName=blockId)

    def newBlock(self, blockId):
        return self.newContainer(containerName=blockId)

    def update(self, catName, attributeName, value, iRow=0):
        return self.updateAttribute(catName, attributeName, value, iRow=iRow)

    def write(self, filePath):
        return self.writeFile(filePath)

    def getDbCode(self, dbId="PDB"):
        """Return the database code for the input database id/name"""
        try:
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("database_2")
            vals = catObj.selectValuesWhere("database_code", dbId, "database_id")
            return self._firstOrDefault(vals, default="")
        except Exception as _e:  # noqa: F841
            return ""

    def getStructTitle(self):
        """Return _struct.title"""
        try:
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("struct")
            return catObj.getValue("title", 0)
        except Exception as _e:  # noqa: F841
            return ""

    def getContourLevelMap(self, mapId="primary map"):
        """Return the contour level for a given map"""
        try:
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("em_map")
            vals = catObj.selectValuesWhere("contour_level", mapId, "type")
            return self._firstOrDefault(vals, default="")
        except Exception as e:
            logging.error(e)
            return ""


class PdbxGeometryReportIo(PdbxStyleIoUtil):
    """Methods for reading PDBx geometry data files for reporting applications including style details."""

    def __init__(self, verbose=True, log=sys.stderr):
        super(PdbxGeometryReportIo, self).__init__(styleObject=PdbxGeometryReportCategoryStyle(), verbose=verbose, log=log)

        # self.__verbose = verbose
        # self.__debug = False
        self.__lfh = log
        #
        self.__filePath = None

        self.__idCode = None

    def getCategory(self, catName="entity"):
        return self.getItemDictList(catName)

    def setFilePath(self, filePath, idCode=None):
        """Specify the file path for the target and optionally provide an identifier
        for the data section within the file.
        """
        self.__filePath = filePath
        self.__idCode = idCode
        if self.readFile(self.__filePath):
            if self.__idCode is not None:
                return self.setContainer(containerName=self.__idCode)
            else:
                return self.setContainer(containerIndex=0)
        else:
            return False

    def get(self):
        """
        Check for a valid current data container.

        Returns True for success or False otherwise.
        """
        return self.getCurrentContainerId() is not None

    def complyStyle(self):
        return self.testStyleComplete(self.__lfh)

    def setBlock(self, blockId):
        return self.setContainer(containerName=blockId)

    def newBlock(self, blockId):
        return self.newContainer(containerName=blockId)

    def update(self, catName, attributeName, value, iRow=0):
        return self.updateAttribute(catName, attributeName, value, iRow=iRow)

    def write(self, filePath):
        return self.writeFile(filePath)


class PdbxXrayExpReportIo(PdbxStyleIoUtil):
    """Methods for reading PDBx exp data files for reporting applications including style details."""

    def __init__(self, verbose=True, log=sys.stderr):
        super(PdbxXrayExpReportIo, self).__init__(styleObject=PdbxXrayExpReportCategoryStyle(), verbose=verbose, log=log)

        # self.__verbose = verbose
        # self.__debug = False
        self.__lfh = log
        #
        self.__filePath = None

        self.__idCode = None

    def getCategory(self, catName="entity"):
        return self.getItemDictList(catName)

    def setFilePath(self, filePath, idCode=None):
        """Specify the file path for the target and optionally provide an identifier
        for the data section within the file.
        """
        self.__filePath = filePath
        self.__idCode = idCode
        if self.readFile(self.__filePath):
            if self.__idCode is not None:
                return self.setContainer(containerName=self.__idCode)
            else:
                return self.setContainer(containerIndex=0)
        else:
            return False

    def get(self):
        """
        Check for a valid current data container.

        Returns True for success or False otherwise.
        """
        return self.getCurrentContainerId() is not None

    def complyStyle(self):
        return self.testStyleComplete(self.__lfh)

    def setBlock(self, blockId):
        return self.setContainer(containerName=blockId)

    def newBlock(self, blockId):
        return self.newContainer(containerName=blockId)

    def update(self, catName, attributeName, value, iRow=0):
        return self.updateAttribute(catName, attributeName, value, iRow=iRow)

    def write(self, filePath):
        return self.writeFile(filePath)


class PdbxStatusHistoryIo(PdbxStyleIoUtil):
    """Methods for reading PDBx data files containing status history details."""

    def __init__(self, verbose=True, log=sys.stderr):
        super(PdbxStatusHistoryIo, self).__init__(styleObject=PdbxStatusHistoryCategoryStyle(), verbose=verbose, log=log)

        # self.__verbose = verbose
        # self.__debug = False
        self.__lfh = log
        #
        self.__filePath = None

        self.__idCode = None

    def getCategory(self, catName="entity"):
        return self.getItemDictList(catName)

    def setFilePath(self, filePath, idCode=None):
        """Specify the file path for the target and optionally provide an identifier
        for the data section within the file.
        """
        self.__filePath = filePath
        self.__idCode = idCode
        if self.readFile(self.__filePath):
            if self.__idCode is not None:
                return self.setContainer(containerName=self.__idCode)
            else:
                return self.setContainer(containerIndex=0)
        else:
            return False

    def get(self):
        """
        Check for a valid current data container.

        Returns True for success or False otherwise.
        """
        return self.getCurrentContainerId() is not None

    def complyStyle(self):
        return self.testStyleComplete(self.__lfh)

    def setBlock(self, blockId):
        return self.setContainer(containerName=blockId)

    def newBlock(self, blockId):
        return self.newContainer(containerName=blockId)

    def update(self, catName, attributeName, value, iRow=0):
        return self.updateAttribute(catName, attributeName, value, iRow=iRow)

    def write(self, filePath):
        return self.writeFile(filePath)


class PdbxEntryInfoIo(PdbxStyleIoUtil):
    """Methods for reading PDBx data files for extracting essential entry citation and status information."""

    def __init__(self, verbose=True, log=sys.stderr):
        self.__stObj = PdbxEntryInfoCategoryStyle()
        super(PdbxEntryInfoIo, self).__init__(styleObject=self.__stObj, verbose=verbose, log=log)

        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        self.__filePath = None

        self.__idCode = None

    def getCategory(self, catName="entity"):
        return self.getItemDictList(catName)

    def setFilePath(self, filePath, idCode=None):
        """Specify the file path for the target and optionally provide an identifier
        for the data section within the file.
        """
        self.__filePath = filePath
        self.__idCode = idCode
        if self.readFile(self.__filePath):
            if self.__idCode is not None:
                return self.setContainer(containerName=self.__idCode)
            else:
                return self.setContainer(containerIndex=0)
        else:
            return False

    def get(self):
        """
        Check for a valid current data container.

        Returns True for success or False otherwise.
        """
        return self.getCurrentContainerId() is not None

    def complyStyle(self):
        return self.testStyleComplete(self.__lfh)

    def setBlock(self, blockId):
        return self.setContainer(containerName=blockId)

    def newBlock(self, blockId):
        return self.newContainer(containerName=blockId)

    def update(self, catName, attributeName, value, iRow=0):
        return self.updateAttribute(catName, attributeName, value, iRow=iRow)

    def write(self, filePath):
        return self.writeFile(filePath)

    def getDbCode(self, dbId="PDB"):
        """Return the database code for the input database id/name"""
        try:
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("database_2")
            vals = catObj.selectValuesWhere("database_code", dbId, "database_id")
            return self._firstOrDefault(vals, default="")
        except Exception as _e:  # noqa: F841
            return ""

    def getStructTitle(self):
        """Return _struct.title"""
        try:
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("struct")
            return catObj.getValue("title", 0)
        except Exception as _e:  # noqa: F841
            return ""

    def getExperimentalMethods(self):
        """Return the list of _exptl.method values"""
        rL = []
        try:
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("exptl")
            nRows = catObj.getRowCount()
            for iRow in range(nRows):
                rL.append(catObj.getValue("method", iRow))
            return rL
        except Exception as _e:  # noqa: F841
            pass
        return rL

    def __getEmStatusDetails(self):
        """
            Capture separate map related status information -

            _em_admin.entry_id
            _em_admin.current_status
            _em_admin.deposition_date
            _em_admin.deposition_site
            _em_admin.obsoleted_date
            _em_admin.details
            _em_admin.last_update
            _em_admin.map_release_date
            _em_admin.map_hold_date
            _em_admin.replace_existing_entry_flag
            _em_admin.title

            kys = ['entry_id',
               'current_status',
               'deposition_date',
               'deposition_site',
               'obsoleted_date'
               'details',
               'last_update',
               'map_release_date',
               'map_hold_date',
               'header_release_date'
               'replace_existing_entry_flag',
               'title']

        Return: dictionary of key value pairs -- where keys have "em_" prefix -

        """
        kys = self.__stObj.getAttributeNameList("em_admin")
        oD = {}
        for ky in kys:
            oD[ky] = ""
        try:
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("em_admin")
            if catObj is not None:
                for ky in kys:
                    emKy = "em_" + ky
                    oD[emKy] = catObj.getValueOrDefault(attributeName=ky, rowIndex=0, defaultValue="")
        except Exception as e:
            if self.__verbose:
                logger.info("+PdbxEntryInfoIo.getEmStatusDetails() failed for file %s", self.__filePath)
            if self.__debug:
                logger.exception("Failing with %s", str(e))

        return oD

    def setEmStatusDetails(self, statusD):
        """Set selected status items in the em_admin data category represented as attributes in
        input dictionary --  Input dictionary assumed to have artificial "em_" key prefixes ---
        """
        #
        try:
            kys = self.__stObj.getAttributeNameList("em_admin")
            cObj = self.getCurrentContainer()
            dcObj = cObj.getObj("em_admin")
            if dcObj is None:
                self.newCategory("em_admin", container=None, overWrite=True)
                dcObj = cObj.getObj("em_admin")
            for emKy in statusD.keys():
                if emKy.startswith("em_"):
                    ky = emKy[3:]
                else:
                    continue
                if ky in kys:
                    if dcObj.getAttributeIndex(ky) < 0:
                        dcObj.appendAttribute(ky)
                    dcObj.setValue(statusD[emKy], attributeName=ky, rowIndex=0)
            return True
        except Exception as e:
            if self.__verbose:
                logger.info("+PdbxEntryInfoIo.setEmStatusDetails() failed for file %s", self.__filePath)
            if self.__debug:
                logger.exception("Failing with %s", str(e))
        return False

    def __getStatusDetails(self):
        """Return selected status items from the pdbx_database_status category"""
        #
        #            dict_key: pdbx_database_status key
        mappings = {
            "status_code": "status_code",
            "auth_release_code": "author_release_status_code",
            "deposit_date": "recvd_initial_deposition_date",
            "hold_coord_date": "date_hold_coordinates",
            "coord_date": "date_coordinates",
            "approval_type": "author_approval_type",
            "annotator_initials": ["pdbx_annotator", "rcsb_annotator"],
            "deposit_site": "deposit_site",
            "process_site": "process_site",
            "post_rel_status_code": "post_rel_status",
            "post_rel_recvd_coord": "post_rel_recvd_coord",
            "post_rel_recvd_coord_date": "post_rel_recvd_coord_date",
        }
        oD = {}
        for ky in mappings:
            oD[ky] = ""
        try:
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("pdbx_database_status")
            if catObj is not None:
                for ky, lookup in mappings.items():
                    if isinstance(lookup, list):
                        oD[ky] = catObj.getFirstValueOrDefault(attributeNameList=lookup, rowIndex=0, defaultValue="")
                    else:
                        oD[ky] = catObj.getValueOrDefault(attributeName=lookup, rowIndex=0, defaultValue="")
            else:
                return oD
        except Exception as e:
            if self.__verbose:
                logger.info("+PdbxEntryInfoIo.getStatusDetails() failed for file %s", self.__filePath)
            if self.__debug:
                logger.exception("Failing with %s", str(e))

        return oD

    def __getRequestedAccessionTypes(self):
        """Return requested accession types from pdbx_depui_entry_details category"""
        #
        try:
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("pdbx_depui_entry_details")
            if catObj is not None:
                return catObj.getValueOrDefault(attributeName="requested_accession_types", rowIndex=0, defaultValue="")
        except Exception as _e:  # noqa: F841
            if self.__verbose:
                logger.info("failed for file %s", self.__filePath)
            if self.__debug:
                logger.exception("In retriving accesssion type")

        return ""

    def setStatusDetails(self, statusCode, approvalType, annotatorInitials):
        """Set selected status items ...

        _pdbx_database_status.status_code                  (HPUB,REL,PROC,...)
        _pdbx_database_status.recvd_author_approval         Y/N
        _pdbx_database_status.author_approval_type          implicit/explicit/unassigned
        _pdbx_database_status.date_author_approval          yyyy-mm-dd current
        _pdbx_database_status.pdbx_annotator                XX

        """
        #
        try:
            cObj = self.getCurrentContainer()
            dcObj = cObj.getObj("pdbx_database_status")
            if dcObj is not None:
                if dcObj.getAttributeIndex("status_code") < 0:
                    dcObj.appendAttribute("status_code")
                dcObj.setValue(statusCode, attributeName="status_code", rowIndex=0)
                if dcObj.getAttributeIndex("author_approval_type") < 0:
                    dcObj.appendAttribute("author_approval_type")

                if approvalType == "unassigned":
                    dcObj.setValue(".", attributeName="author_approval_type", rowIndex=0)
                else:
                    dcObj.setValue(approvalType, attributeName="author_approval_type", rowIndex=0)

                if approvalType in ["implicit", "unassigned"]:
                    recApprov = "N"
                else:
                    recApprov = "Y"

                if dcObj.getAttributeIndex("recvd_author_approval") < 0:
                    dcObj.appendAttribute("recvd_author_approval")
                dcObj.setValue(recApprov, attributeName="recvd_author_approval", rowIndex=0)

                if approvalType in ["implicit", "explicit"]:
                    lt = time.strftime("%Y-%m-%d", time.localtime())
                    if dcObj.getAttributeIndex("date_author_approval") < 0:
                        dcObj.appendAttribute("date_author_approval")
                    dcObj.setValue(str(lt), attributeName="date_author_approval", rowIndex=0)
                #
                if annotatorInitials is not None and (len(annotatorInitials) > 1):
                    if dcObj.getAttributeIndex("pdbx_annotator") < 0:
                        dcObj.appendAttribute("pdbx_annotator")
                    dcObj.setValue(annotatorInitials, attributeName="pdbx_annotator", rowIndex=0)

                if dcObj.hasAttribute("rcsb_annotator"):
                    dcObj.removeAttribute("rcsb_annotator")

                return True
            else:
                return False
        except Exception as e:
            if self.__verbose:
                logger.info("+PdbxEntryInfo.setStatusDetails() failed for status code %s approval type %s initials %s", statusCode, approvalType, annotatorInitials)
            if self.__debug:
                logger.exception("Failing with %s", str(e))
        return False

    def getCurrentStatusDetails(self):
        sD = self.getInfoD(contextType="history")
        return self.__evalCurrentStatus(sD)

    def __evalCurrentStatus(self, sD):
        entryId = sD["entry_id"]
        pdbId = sD["pdb_id"]
        statusCode = sD["status_code"]
        authReleaseCode = sD["auth_release_code"]
        initialDepositionDate = sD["deposit_date"]
        annotatorInitials = sD["annotator_initials"]
        beginProcessingDate = sD["begin_processing_date"]
        authorApprovalDate = sD["author_approval_date"]
        releaseDate = sD["release_date"]
        return entryId, pdbId, statusCode, authReleaseCode, annotatorInitials, initialDepositionDate, beginProcessingDate, authorApprovalDate, releaseDate

    def getInfoD(self, contextType="info"):
        """Convenience method returning a dictionary of data item values for the input "content" area -

           info  = items commonly used to identify an entry with a bit of context.
         history = items describing the processing status history of an entry
        em_admin = items describing status details for emdb map entries

        """
        #
        if contextType == "info":
            return self.__getInfoGeneral()
        elif contextType == "history":
            return self.__getInfoHistory()
        elif contextType == "em_admin":
            return self.__getEmStatusDetails()
        else:
            return self.__getInfoGeneral()

    def __getInfoGeneral(self):
        """Return a dictionary of selected items commonly used to identify an entry with a bit of context."""
        #
        oD = {}
        kys = [
            "blockId",
            "pdb_id",
            "bmrb_id",
            "emdb_id",
            "experimental_methods",
            "struct_title",
            "status_code",
            "auth_release_code",
            "deposit_date",
            "hold_coord_date",
            "coord_date",
            "approval_type",
            "annotator_initials",
            "process_site",
            "deposit_site",
            "reqacctypes",
        ]
        for ky in kys:
            oD[ky] = ""
        try:
            oD["blockId"] = self.getCurrentContainerId()
            oD["struct_title"] = self.getStructTitle()
            oD["pdb_id"] = self.getDbCode(dbId="PDB")
            oD["emdb_id"] = self.getDbCode(dbId="EMDB")
            oD["bmrb_id"] = self.getDbCode(dbId="BMRB")
            mL = self.getExperimentalMethods()
            oD["experimental_methods"] = ",".join(mL)
            sD = self.__getStatusDetails()
            oD.update(sD)
            oD["reqacctypes"] = self.__getRequestedAccessionTypes()

        except Exception as e:
            if self.__verbose:
                logger.info("+PdbxEntryInfoIo.__getInfoGeneral() failed for file %s", self.__filePath)
            if self.__debug:
                logger.exception("Failing with %s", str(e))
        return oD

    def __getInfoHistory(self):
        """Return a dictionary selected status history items from the pdbx_database_status category
        #
        _pdbx_database_status.status_code                        REL
        _pdbx_database_status.author_release_status_code         HPUB
        _pdbx_database_status.status_code_sf                     REL
        _pdbx_database_status.status_code_mr                     .
        _pdbx_database_status.dep_release_code_coordinates       "HOLD FOR PUBLICATION"
        _pdbx_database_status.dep_release_code_sequence          "HOLD FOR RELEASE"
        _pdbx_database_status.dep_release_code_struct_fact       "HOLD FOR PUBLICATION"
        _pdbx_database_status.dep_release_code_nmr_constraints   .
        _pdbx_database_status.entry_id                           D_1000200183
        _pdbx_database_status.date_begin_processing              2014-02-17
        _pdbx_database_status.recvd_coordinates                  Y
        _pdbx_database_status.date_coordinates                   2014-02-05
        _pdbx_database_status.recvd_struct_fact                  Y
        _pdbx_database_status.date_struct_fact                   2014-02-05
        _pdbx_database_status.recvd_nmr_constraints              .
        _pdbx_database_status.date_nmr_constraints               .
        _pdbx_database_status.recvd_author_approval              Y
        _pdbx_database_status.author_approval_type               explicit
        _pdbx_database_status.date_author_approval               2014-04-21
        _pdbx_database_status.recvd_initial_deposition_date      2014-02-05
        _pdbx_database_status.date_of_sf_release                 2014-04-30
        _pdbx_database_status.date_of_mr_release                 .
        _pdbx_database_status.date_of_PDB_release                .
        _pdbx_database_status.date_hold_coordinates              .
        _pdbx_database_status.date_hold_struct_fact              .
        _pdbx_database_status.date_hold_nmr_constraints          .
        _pdbx_database_status.hold_for_publication               .
        _pdbx_database_status.SG_entry                           N
        _pdbx_database_status.pdb_date_of_author_approval        .
        _pdbx_database_status.deposit_site                       RCSB
        _pdbx_database_status.process_site                       RCSB
        _pdbx_database_status.dep_release_code_chemical_shifts   .
        _pdbx_database_status.recvd_chemical_shifts              .
        _pdbx_database_status.date_chemical_shifts               .
        _pdbx_database_status.date_hold_chemical_shifts          .
        _pdbx_database_status.status_code_cs                     .
        _pdbx_database_status.date_of_cs_release                 .
        _pdbx_database_status.date_revised                       .
        _pdbx_database_status.replaced_entry_id                  .
        _pdbx_database_status.revision_id                        .
        _pdbx_database_status.revision_description               .
        _pdbx_database_status.pdbx_annotator                     EP
        _pdbx_database_status.date_of_NDB_release                2014-04-30
        _pdbx_database_status.date_released_to_PDB               .
        _pdbx_database_status.skip_PDB_REMARK_500                .
        _pdbx_database_status.skip_PDB_REMARK                    .
        _pdbx_database_status.title_suppression                  .
        #

        """
        #
        oD = {}
        #
        kys = [
            "pdb_id",
            "entry_id",
            "status_code",
            "auth_release_code",
            "deposit_date",
            "hold_coord_date",
            "coord_date",
            "approval_type",
            "annotator_initials",
            "begin_processing_date",
            "author_approval_date",
            "release_date",
            "process_site",
            "deposit_site",
        ]

        for ky in kys:
            oD[ky] = ""

        try:
            #
            cObj = self.getCurrentContainer()
            catObj = cObj.getObj("pdbx_database_status")
            if catObj is not None:
                entryId = catObj.getValueOrDefault(attributeName="entry_id", rowIndex=0, defaultValue="")
                statusCode = catObj.getValueOrDefault(attributeName="status_code", rowIndex=0, defaultValue="")
                authReleaseCode = catObj.getValueOrDefault(attributeName="author_release_status_code", rowIndex=0, defaultValue="")
                initialDepositionDate = catObj.getValueOrDefault(attributeName="recvd_initial_deposition_date", rowIndex=0, defaultValue="")
                holdCoordinatesDate = catObj.getValueOrDefault(attributeName="date_hold_coordinates", rowIndex=0, defaultValue="")
                coordinatesDate = catObj.getValueOrDefault(attributeName="date_coordinates", rowIndex=0, defaultValue="")
                approvalType = catObj.getValueOrDefault(attributeName="author_approval_type", rowIndex=0, defaultValue="")
                annotatorInitials = catObj.getFirstValueOrDefault(attributeNameList=["pdbx_annotator", "rcsb_annotator"], rowIndex=0, defaultValue="")
                beginProcessingDate = catObj.getValueOrDefault(attributeName="date_begin_processing", rowIndex=0, defaultValue="")
                authorApprovalDate = catObj.getValueOrDefault(attributeName="date_author_approval", rowIndex=0, defaultValue="")
                releaseDate = catObj.getValueOrDefault(attributeName="date_of_NDB_release", rowIndex=0, defaultValue="")
                depositSite = catObj.getValueOrDefault(attributeName="deposit_site", rowIndex=0, defaultValue="")
                processSite = catObj.getValueOrDefault(attributeName="process_site", rowIndex=0, defaultValue="")
                #
                oD["pdb_id"] = self.getDbCode(dbId="PDB")
                #
                oD["entry_id"] = entryId
                oD["status_code"] = statusCode
                oD["auth_release_code"] = authReleaseCode
                oD["deposit_date"] = initialDepositionDate
                oD["hold_coord_date"] = holdCoordinatesDate
                oD["coord_date"] = coordinatesDate
                oD["approval_type"] = approvalType
                oD["annotator_initials"] = annotatorInitials
                oD["begin_processing_date"] = beginProcessingDate
                oD["author_approval_date"] = authorApprovalDate
                oD["release_date"] = releaseDate
                oD["process_site"] = processSite
                oD["deposit_site"] = depositSite
        except Exception as e:
            if self.__verbose:
                logger.info("+PdbxEntryInfoIo.__getInfoHistory() failed for file %s", self.__filePath)
            if self.__debug:
                logger.exception("Failing with %s", str(e))
        return oD


class PdbxLocalMapIndexIo(PdbxStyleIoUtil):
    """Methods for reading PDBx data files containing index details for calculated local electron density maps."""

    def __init__(self, verbose=True, log=sys.stderr):
        super(PdbxLocalMapIndexIo, self).__init__(styleObject=PdbxLocalMapIndexCategoryStyle(), verbose=verbose, log=log)

        # self.__verbose = verbose
        # self.__debug = False
        self.__lfh = log
        #
        self.__filePath = None

    def getCategory(self, catName="dcc_ligand"):
        return self.getAttribDictList(catName)

    def setFilePath(self, filePath):
        """Specify the file path for the target  -- The first data block is used by default --"""
        self.__filePath = filePath
        if self.readFile(self.__filePath):
            return self.setContainer(containerIndex=0)
        else:
            return False

    def get(self):
        """
        Check for a valid current data container.

        Returns True for success or False otherwise.
        """
        return self.getCurrentContainerId() is not None

    def complyStyle(self):
        return self.testStyleComplete(self.__lfh)

    def setBlock(self, blockId):
        return self.setContainer(containerName=blockId)

    def newBlock(self, blockId):
        return self.newContainer(containerName=blockId)

    def update(self, catName, attributeName, value, iRow=0):
        return self.updateAttribute(catName, attributeName, value, iRow=iRow)

    def write(self, filePath):
        return self.writeFile(filePath)
