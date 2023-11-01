##
# File:  StatusUpdate.py
# Date:  11-July-2013
#
# Updates:
#   2-Jan-2014 jdw change to STATUS_CODE
#  18-Jan-2015 jdw integrate status history tracking
#   2-Mar-2016 jdw add annotator initials to the wfemload() method...
#  12-Feb-2018 ep  Rewrite get() operation as getV2 that returns dictionary
##
"""
Methods to manage model PDBx database release and progress status updates

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import time
import traceback
import copy

from mmcif.io.IoAdapterCore import IoAdapterCore
from wwpdb.utils.db.DbLoadingApi import DbLoadingApi
from wwpdb.utils.wf.dbapi.WfDbApi import WfDbApi

#
from mmcif.api.DataCategory import DataCategory

import logging

logger = logging.getLogger()


class StatusUpdate(object):

    """Update release status items."""

    def __init__(self, reqObj, IoAdapter=IoAdapterCore(), verbose=False, log=sys.stderr):
        """
        :param `verbose`:  boolean flag to activate verbose logging.
        :param `log`:      stream for logging.

        """
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        #
        self.__reqObj = reqObj
        self.__io = IoAdapter
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #
        self.__savedStatusD = {}
        #
        # Temporary placeholder for annotator initials to assign - process_site - defaults
        # Also used for list of processing sites
        #
        self.__annInitials = {
            "PDBJ": ["MC", "KM", "JPN", "JS", "PDBJ", "RI", "USJS", "USMC", "USRI", "USYK", "YK"],
            "PDBE": ["DA", "EBI", "SS", "MJC", "AM", "AC", "GS", "GVG", "JB"],
            "RCSB": ["LEAD", "BD", "BH", "BN", "CS", "EP", "GG", "IP", "JW", "JY", "LD", "LT", "MRS", "MZ", "SG", "SKB"],
            "PDBC": ["PDBC"],
        }
        #

    def dbLoad(self, pdbxFilePath):
        try:
            dbLd = DbLoadingApi(log=self.__lfh, verbose=self.__verbose)
            return dbLd.doLoadStatus(pdbxFilePath, self.__sessionPath)
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.__dbload() dbload failed for %s\n" % pdbxFilePath)
                traceback.print_exc(file=self.__lfh)
            return False

    def wfRollBack(self, idCode):
        try:
            c = WfDbApi(self.__lfh, self.__verbose)
            constDict = {}
            constDict["DEP_SET_ID"] = idCode
            c.saveObject(self.__savedStatusD, "update", constDict)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.__wfRollBack() %s status database update rollback failed.\n" % idCode)
                traceback.print_exc(file=self.__lfh)
            return False

    def wfLoad(
        self,
        idCode,
        statusCode=None,
        annotatorInitials=None,
        initialDepositionDate=None,
        authRelCode=None,
        postRelStatusCode=None,
        postRelRecvdCoord=None,
        postRelRecvdCoordDate=None,
    ):
        """
        c=WfDbApi(self.__lfh, self.__verbose)
        rd = c.getObject('D_1100200206')
        constDict={}
        if(c.exist(rd)):
        rd['STATUS_CODE_EMDB'] ='PROC'
        rd['DEP_AUTHOR_RELEASE_STATUS_CODE_EMDB'] ='HOLD'
        constDict['DEP_SET_ID']='D_1100200206'
        c.saveObject(rd, 'update',constDict)
        """
        try:
            c = WfDbApi(self.__lfh, self.__verbose)
            if self.__debug:
                self.__lfh.write("+StatusUpdate.__wfload() fetch current status for %s\n" % idCode)
            rd = c.getObject(idCode)
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.__wfload() fetch current status for %s\n" % idCode)
                for k, v in rd.items():
                    self.__lfh.write("+StatusUpdate.__wfload() %r  %r\n" % (k, v))

            self.__savedStatusD = copy.deepcopy(rd)
            if statusCode is not None:
                rd["STATUS_CODE"] = statusCode

            if postRelStatusCode is not None:
                if len(postRelStatusCode) > 0:
                    rd["POST_REL_STATUS"] = postRelStatusCode
                else:
                    rd["POST_REL_STATUS"] = None

            if annotatorInitials is not None and len(annotatorInitials) > 1:
                rd["ANNOTATOR_INITIALS"] = annotatorInitials

            if "TITLE" in rd and (len(rd["TITLE"]) > 0):
                maxlen = 370
                rd["TITLE"] = str(rd["TITLE"]).replace("'", "''")
                if len(rd["TITLE"]) > maxlen:
                    rd["TITLE"] = rd["TITLE"][0:maxlen]
            if "AUTHOR_LIST" in rd and (len(rd["AUTHOR_LIST"]) > 0):
                rd["AUTHOR_LIST"] = str(rd["AUTHOR_LIST"]).replace("'", "''")

            if (initialDepositionDate is not None) and (len(initialDepositionDate) > 4):
                rd["INITIAL_DEPOSITION_DATE"] = initialDepositionDate

            if (authRelCode is not None) and (len(authRelCode) > 2):
                rd["AUTHOR_RELEASE_STATUS_CODE"] = authRelCode

            if postRelRecvdCoord is not None:
                if postRelRecvdCoord != "":
                    rd["POST_REL_RECVD_COORD"] = postRelRecvdCoord
                else:
                    rd["POST_REL_RECVD_COORD"] = None

            if postRelRecvdCoordDate is not None:
                if postRelRecvdCoordDate != "":
                    rd["POST_REL_RECVD_COORD_DATE"] = postRelRecvdCoordDate
                else:
                    rd["POST_REL_RECVD_COORD_DATE"] = None

            constDict = {}
            constDict["DEP_SET_ID"] = idCode
            if self.__debug:
                self.__lfh.write("+StatusUpdate.__wfload() updating current status for %s\n" % idCode)
                for k, v in rd.items():
                    self.__lfh.write("+StatusUpdate.__wfload() %r  %r\n" % (k, v))
            c.saveObject(rd, "update", constDict)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.__wfload() wfload failed  %s\n" % idCode)
                traceback.print_exc(file=self.__lfh)
            return False

    def wfEmLoad(self, idCode, statusCode=None, title=None, authRelCode=None, annotatorInitials=None):
        """
        c=WfDbApi(self.__lfh, self.__verbose)
        rd = c.getObject('D_1100200206')
        constDict={}
        if(c.exist(rd)):
        rd['STATUS_CODE_EMDB'] ='PROC'
        rd['DEP_AUTHOR_RELEASE_STATUS_CODE_EMDB'] ='HOLD'
        constDict['DEP_SET_ID']='D_1100200206'
        c.saveObject(rd, 'update',constDict)


        """
        try:
            c = WfDbApi(self.__lfh, self.__verbose)
            rd = c.getObject(idCode)
            self.__savedStatusD = copy.deepcopy(rd)

            if statusCode is not None and len(statusCode) > 0:
                rd["STATUS_CODE_EMDB"] = statusCode

            if "TITLE_EMDB" in rd and rd["TITLE_EMDB"] is not None and (len(rd["TITLE_EMDB"]) > 0):
                rd["TITLE"] = str(rd["TITLE"]).replace("'", "''")

            if "AUTHOR_LIST_EMDB" in rd and rd["AUTHOR_LIST_EMDB"] is not None and (len(rd["AUTHOR_LIST_EMDB"]) > 0):
                rd["AUTHOR_LIST_EMDB"] = str(rd["AUTHOR_LIST_EMDB"]).replace("'", "''")

            if (authRelCode is not None) and (len(authRelCode) > 2):
                rd["DEP_AUTHOR_RELEASE_STATUS_CODE_EMDB"] = authRelCode

            if (title is not None) and (len(title) > 2):
                rd["TITLE_EMDB"] = title

            if annotatorInitials is not None and len(annotatorInitials) > 1:
                rd["ANNOTATOR_INITIALS"] = annotatorInitials

            constDict = {}
            constDict["DEP_SET_ID"] = idCode
            c.saveObject(rd, "update", constDict)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.__wfEmload() wfEmload failed  %s\n" % idCode)
                traceback.print_exc(file=self.__lfh)
            return False

    # This interface is still used by wwpdb.utils.letters.AutoOnHold
    def setEmStatusDetails(self, inpFilePath, outFilePath, statusD, processSite=None, annotatorInitials=None, approvalType=None):
        self.__lfh.write(
            "\n+StatusUpdate.setEmStatusDetails() statuD %s, processSite %s, annotatorInitials %s, approvalType %s \n" % (statusD, processSite, annotatorInitials, approvalType)
        )

        try:
            cList = self.__io.readFile(inpFilePath)
            container = cList[0]

            ok = self.__setEmStatusDetails(container, statusD=statusD, processSite=processSite, annotatorInitials=annotatorInitials, approvalType=approvalType)
            if ok:
                return self.__io.writeFile(outFilePath, cList)

        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.setEmStatusDetails() failed file %s outPath %s\n" % (inpFilePath, outFilePath))
                traceback.print_exc(file=self.__lfh)

        return False

    def __setEmStatusDetails(self, cObj, statusD, processSite=None, annotatorInitials=None, approvalType=None):
        """Set selected status items in the em_admin data category represented as attributes in
        input dictionary --  Input dictionary assumed to have artificial "em_" key prefixes ---
                             keys starting em_depui are handled in em_depui category
        """
        #
        attributeNameList = [
            "entry_id",
            "current_status",
            "deposition_date",
            "deposition_site",
            "obsoleted_date",
            "details",
            "last_update",
            "map_release_date",
            "map_hold_date",
            "header_release_date",
            "replace_existing_entry_flag",
            "title"
            # Do not add process_site here.  Handled internally below
        ]

        depuiAttributeNameList = ["depositor_hold_instructions"]

        try:
            dcObj = cObj.getObj("pdbx_database_status")
            if dcObj is not None:
                #    _pdbx_database_status.pdbx_annotator
                #    _pdbx_database_status.process_site
                #
                # if self.__debug:
                #    self.__lfh.write("+StatusUpdate.setEmStatusDetails() after read before update writefile \n")
                #    dcObj.dumpIt(fh=self.__lfh)
                if (processSite is not None) and (processSite in self.__annInitials.keys()):
                    if dcObj.getAttributeIndex("process_site") < 0:
                        dcObj.appendAttribute("process_site")
                    dcObj.setValue(processSite, attributeName="process_site", rowIndex=0)

                if annotatorInitials is not None and (len(annotatorInitials) > 1):
                    if dcObj.getAttributeIndex("pdbx_annotator") < 0:
                        dcObj.appendAttribute("pdbx_annotator")
                    dcObj.setValue(annotatorInitials, attributeName="pdbx_annotator", rowIndex=0)

                if dcObj.hasAttribute("rcsb_annotator"):
                    dcObj.removeAttribute("rcsb_annotator")
                if dcObj.getAttributeIndex("author_approval_type") < 0:
                    dcObj.appendAttribute("author_approval_type")

                if approvalType is not None:
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

            dcObj = cObj.getObj("em_admin")
            if dcObj is None:
                newCat = DataCategory("em_admin")
                for attributeName in attributeNameList:
                    newCat.appendAttribute(attributeName)
                if cObj is not None:
                    cObj.append(newCat)
                dcObj = cObj.getObj("em_admin")
            else:
                # handle incomplete categories --
                for ky in attributeNameList:
                    if not dcObj.hasAttribute(ky):
                        dcObj.appendAttribute(ky)
            #
            kys = dcObj.getAttributeList()
            if self.__debug:
                self.__lfh.write("+StatusUpdate.setEmStatusDetails() kys %r\n" % kys)
                self.__lfh.write("+StatusUpdate.setEmStatusDetails() statusD %r\n" % statusD.items())

            for emKy in statusD.keys():
                if emKy.startswith("em_") and not emKy.startswith("em_depui_"):
                    ky = emKy[3:]
                else:
                    continue
                if ky in kys:
                    dcObj.setValue(statusD[emKy], attributeName=ky, rowIndex=0)

            # em_admin.process_site
            if processSite is not None:
                if dcObj.getAttributeIndex("process_site") < 0:
                    dcObj.appendAttribute("process_site")
                dcObj.setValue(processSite, attributeName="process_site", rowIndex=0)

            dcObj = cObj.getObj("em_depui")
            if dcObj is None:
                newCat = DataCategory("em_depui")
                for attributeName in depuiAttributeNameList:
                    newCat.appendAttribute(attributeName)
                if cObj is not None:
                    cObj.append(newCat)
                dcObj = cObj.getObj("em_depui")
            else:
                # handle incomplete categories --
                for ky in depuiAttributeNameList:
                    if not dcObj.hasAttribute(ky):
                        dcObj.appendAttribute(ky)
            #
            kys = dcObj.getAttributeList()
            if self.__debug:
                self.__lfh.write("+StatusUpdate.setEmStatusDetails() em_depui kys %r\n" % kys)
                self.__lfh.write("+StatusUpdate.setEmStatusDetails() statusD %r\n" % statusD.items())

            for emKy in statusD.keys():
                if emKy.startswith("em_depui_"):
                    ky = emKy[9:]
                else:
                    continue
                if ky in kys:
                    dcObj.setValue(statusD[emKy], attributeName=ky, rowIndex=0)

            #
            if self.__debug:
                self.__lfh.write("+StatusUpdate.setEmStatusDetails() before writefile \n")
                dcObj.dumpIt(fh=self.__lfh)
            return True

        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+PdbxEntryInfoIo.setEmStatusDetails() failed\n")
            if self.__debug:
                traceback.print_exc(file=self.__lfh)
        return False

    def set(
        self,
        inpFilePath,
        outFilePath,
        statusCode,
        approvalType,
        annotatorInitials,
        authReleaseCode=None,
        holdCoordinatesDate=None,
        expMethods=None,
        processSite=None,
        postRelStatusCode=None,
    ):
        """Set selected status items in the input model file"""

        #
        self.__lfh.write(
            "\n+StatusUpdate.set() statusCode %s approvalType %s initials %s authRelCode %s holdDate %s expMethod %r postRelStatusCode %s\n"
            % (statusCode, approvalType, annotatorInitials, authReleaseCode, holdCoordinatesDate, expMethods, postRelStatusCode)
        )

        try:
            cList = self.__io.readFile(inpFilePath)
            container = cList[0]

            ok = self.__set(
                container,
                statusCode=statusCode,
                approvalType=approvalType,
                annotatorInitials=annotatorInitials,
                authReleaseCode=authReleaseCode,
                holdCoordinatesDate=holdCoordinatesDate,
                expMethods=expMethods,
                processSite=processSite,
                postRelStatusCode=postRelStatusCode,
            )
            if ok:
                return self.__io.writeFile(outFilePath, cList)

        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.__set() failed file %s statusCode %s approvalType %s outPath %s\n" % (inpFilePath, statusCode, approvalType, outFilePath))
                traceback.print_exc(file=self.__lfh)

        return False

    def __set(
        self, container, statusCode, approvalType, annotatorInitials, authReleaseCode=None, holdCoordinatesDate=None, expMethods=None, processSite=None, postRelStatusCode=None
    ):
        """Set selected status items in the input model file

        _pdbx_database_status.status_code                  (HPUB,REL,PROC,...)
        _pdbx_database_status.recvd_author_approval         Y/N
        _pdbx_database_status.author_approval_type          implicit/explicit/unassigned
        _pdbx_database_status.date_author_approval          yyyy-mm-dd current
        _pdbx_database_status.pdbx_annotator                XX

        """

        self.__lfh.write(
            "\n+StatusUpdate.__set() statusCode %s approvalType %s initials %s authRelCode %s holdDate %s expMethod %r postRelStatusCode %s\n"
            % (statusCode, approvalType, annotatorInitials, authReleaseCode, holdCoordinatesDate, expMethods, postRelStatusCode)
        )

        try:
            dcObj = container.getObj("pdbx_database_status")
            if dcObj is not None:
                #
                if self.__debug:
                    self.__lfh.write("+StatusUpdate.__set() after read before update writefile \n")
                    dcObj.dumpIt(fh=self.__lfh)
                #
                if (processSite is not None) and (processSite in self.__annInitials.keys()):
                    if dcObj.getAttributeIndex("process_site") < 0:
                        dcObj.appendAttribute("process_site")
                    dcObj.setValue(processSite, attributeName="process_site", rowIndex=0)
                #
                if statusCode and len(statusCode) > 1:
                    if dcObj.getAttributeIndex("status_code") < 0:
                        dcObj.appendAttribute("status_code")
                    dcObj.setValue(statusCode, attributeName="status_code", rowIndex=0)

                #
                if postRelStatusCode and len(postRelStatusCode) > 1:
                    if dcObj.getAttributeIndex("pos_rel_status") < 0:
                        dcObj.appendAttribute("post_rel_status")
                    dcObj.setValue(postRelStatusCode, attributeName="post_rel_status", rowIndex=0)

                if expMethods is not None and self.__inMethod("X-RAY", expMethods):
                    if dcObj.getAttributeIndex("status_code_sf") < 0:
                        dcObj.appendAttribute("status_code_sf")
                    dcObj.setValue(statusCode, attributeName="status_code_sf", rowIndex=0)

                if expMethods is not None and statusCode is not None and self.__inMethod("NMR", expMethods):
                    have_cs_data = dcObj.getValueOrDefault(attributeName="recvd_chemical_shifts", rowIndex=0, defaultValue="").upper()
                    if have_cs_data == "Y":
                        if dcObj.getAttributeIndex("status_code_cs") < 0:
                            dcObj.appendAttribute("status_code_cs")
                        dcObj.setValue(statusCode, attributeName="status_code_cs", rowIndex=0)

                    have_mr_data = dcObj.getValueOrDefault(attributeName="recvd_nmr_constraints", rowIndex=0, defaultValue="").upper()
                    if have_mr_data == "Y":
                        if dcObj.getAttributeIndex("status_code_mr") < 0:
                            dcObj.appendAttribute("status_code_mr")
                        dcObj.setValue(statusCode, attributeName="status_code_mr", rowIndex=0)

                    # For nmr-data - only set if recvd
                    have_nmr_data = dcObj.getValueOrDefault(attributeName="recvd_nmr_data", rowIndex=0, defaultValue="").upper()
                    if have_nmr_data == "Y":
                        dcObj.setValue(statusCode, attributeName="status_code_nmr_data", rowIndex=0)

                if dcObj.getAttributeIndex("author_approval_type") < 0:
                    dcObj.appendAttribute("author_approval_type")

                if approvalType is not None:
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

                # If statusCode is REL when you come here, means that postRel entry - do not change approval date
                if approvalType in ["implicit", "explicit"] and statusCode != "REL":
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

                #
                if authReleaseCode is not None and (len(authReleaseCode) > 1):
                    if dcObj.getAttributeIndex("author_release_status_code") < 0:
                        dcObj.appendAttribute("author_release_status_code")
                    dcObj.setValue(authReleaseCode, attributeName="author_release_status_code", rowIndex=0)

                # if (holdCoordinatesDate is not None and (len(holdCoordinatesDate) > 1)):
                if holdCoordinatesDate is not None:
                    if dcObj.getAttributeIndex("date_hold_coordinates") < 0:
                        dcObj.appendAttribute("date_hold_coordinates")
                    dcObj.setValue(holdCoordinatesDate, attributeName="date_hold_coordinates", rowIndex=0)

                    if expMethods is not None and self.__inMethod("X-RAY", expMethods):
                        if dcObj.getAttributeIndex("date_hold_struct_fact") < 0:
                            dcObj.appendAttribute("date_hold_struct_fact")
                        dcObj.setValue(holdCoordinatesDate, attributeName="date_hold_struct_fact", rowIndex=0)

                    if expMethods is not None and self.__inMethod("NMR", expMethods):
                        if dcObj.getAttributeIndex("date_hold_nmr_constraints") < 0:
                            dcObj.appendAttribute("date_hold_nmr_constraints")
                        dcObj.setValue(holdCoordinatesDate, attributeName="date_hold_nmr_constraints", rowIndex=0)

                        if dcObj.getAttributeIndex("date_hold_chemical_shifts") < 0:
                            dcObj.appendAttribute("date_hold_chemical_shifts")
                        dcObj.setValue(holdCoordinatesDate, attributeName="date_hold_chemical_shifts", rowIndex=0)
                #
                #
                if self.__debug:
                    self.__lfh.write("+StatusUpdate.__set() before writefile \n")
                    dcObj.dumpIt(fh=self.__lfh)
                return True
            else:
                return False
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.__set() failed statusCode %s approvalType %s\n" % (statusCode, approvalType))
                traceback.print_exc(file=self.__lfh)
            return False

    def __inMethod(self, tag, methodString):
        if str(methodString).upper().find(tag) != -1:
            return True
        return False

    def _isEmptyValue(self, val):
        if (val is None) or (len(val) == 0) or (val in [".", "?"]):
            return True
        else:
            return False

    def _firstOrDefault(self, valList, default=""):
        if len(valList) > 0 and not self._isEmptyValue(valList[0]):
            return valList[0]
        else:
            return default

    def getV2(self, inpFilePath):
        """Return selected status items from the input model files."""
        #
        logger.debug("Starting %s", inpFilePath)

        ret = {}

        initList = [
            "pdb_id",
            "emdb_id",
            "statusCode",
            "authReleaseCode",
            "initialDepositionDate",
            "holdCoordinatesDate",
            "coordinatesDate",
            "annotatorInitials",
            "titleSupp",
            "reqAccTypes",
        ]

        for i in initList:
            ret[i] = ""

        try:
            cList = self.__io.readFile(inpFilePath, selectList=["database_2", "pdbx_database_status", "pdbx_depui_entry_details"])
            container = cList[0]
            catObj = container.getObj("database_2")
            vals = catObj.selectValuesWhere("database_code", "PDB", "database_id")
            ret["pdb_id"] = self._firstOrDefault(vals, default="")
            vals = catObj.selectValuesWhere("database_code", "EMDB", "database_id")
            ret["emdb_id"] = self._firstOrDefault(vals, default="")

            #
            dcObj = container.getObj("pdbx_database_status")
            if dcObj is not None:
                ret["statusCode"] = dcObj.getValueOrDefault(attributeName="status_code", rowIndex=0, defaultValue="")
                ret["authReleaseCode"] = dcObj.getValueOrDefault(attributeName="author_release_status_code", rowIndex=0, defaultValue="")
                ret["initialDepositionDate"] = dcObj.getValueOrDefault(attributeName="recvd_initial_deposition_date", rowIndex=0, defaultValue="")
                ret["holdCoordinatesDate"] = dcObj.getValueOrDefault(attributeName="date_hold_coordinates", rowIndex=0, defaultValue="")
                ret["coordinatesDate"] = dcObj.getValueOrDefault(attributeName="date_coordinates", rowIndex=0, defaultValue="")
                ret["annotatorInitials"] = dcObj.getFirstValueOrDefault(attributeNameList=["pdbx_annotator", "rcsb_annotator"], rowIndex=0, defaultValue="")
                ret["titleSupp"] = dcObj.getValueOrDefault(attributeName="title_suppression", rowIndex=0, defaultValue="")
                ret["postRelStatus"] = dcObj.getValueOrDefault(attributeName="post_rel_status", rowIndex=0, defaultValue="")
            dcObj = container.getObj("pdbx_depui_entry_details")
            if dcObj is not None:
                ret["reqAccTypes"] = dcObj.getValueOrDefault(attributeName="requested_accession_types", rowIndex=0, defaultValue="")
                logger.debug("requested_accession_Types %r", ret["reqAccTypes"])

        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                logger.error("Failed file %s", inpFilePath)
            if self.__debug:
                logger.exception("In retrieving data from model")

        logger.debug("Finishing")
        return ret

    def assignProcessSite(self, annotatorInitials):
        for processSite, aList in self.__annInitials.items():
            if annotatorInitials.upper() in aList:
                return processSite
        return None

    def setProcessSite(self, inpFilePath, outFilePath, processSite=None):
        """Set processing site in the input model file"""
        #
        self.__lfh.write("\n+StatusUpdate.setProcessSite()  start setting processSite %s\n" % (processSite))
        try:
            cList = self.__io.readFile(inpFilePath)
            container = cList[0]
            dcObj = container.getObj("pdbx_database_status")
            if dcObj is not None:
                if self.__debug:
                    self.__lfh.write("+StatusUpdate.__setProcessSite() after read before update writefile \n")
                    dcObj.dumpIt(fh=self.__lfh)
                #
                if (processSite is not None) and (processSite in self.__annInitials.keys()):
                    if dcObj.getAttributeIndex("process_site") < 0:
                        dcObj.appendAttribute("process_site")
                    dcObj.setValue(processSite, attributeName="process_site", rowIndex=0)
                #

                if self.__debug:
                    self.__lfh.write("+StatusUpdate.__setProcessSite() before writefile \n")
                    dcObj.dumpIt(fh=self.__lfh)
                return self.__io.writeFile(outFilePath, cList)
            else:
                return False
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.__setProcessSite() failed for input file %s output file %s\n" % (inpFilePath, outFilePath))
                traceback.print_exc(file=self.__lfh)
            return False

    def setBoth(
        self,
        inpFilePath,
        outFilePath,
        reqAccTypes,
        statusCode,
        statusD,
        approvalType,
        annotatorInitials,
        authReleaseCode=None,
        holdCoordinatesDate=None,
        expMethods=None,
        processSite=None,
        postRelStatusCode=None,
    ):
        """Set both PDB and EM statuses in model file based on requested accession types.  statusD containts the EM update"""

        #
        self.__lfh.write(
            "\n+StatusUpdate.setBoth() reqtypes %s statusCode %s approvalType %s initials %s authRelCode %s holdDate %s expMethod %r postRelStatusCode %s statusD %s\n"
            % (reqAccTypes, statusCode, approvalType, annotatorInitials, authReleaseCode, holdCoordinatesDate, expMethods, postRelStatusCode, statusD)
        )

        hasPdb = False
        hasEM = False
        if len(reqAccTypes) < 2 or "PDB" in reqAccTypes:
            hasPdb = True
        if "EMDB" in reqAccTypes:
            hasEM = True

        try:
            cList = self.__io.readFile(inpFilePath)
            container = cList[0]

            ok = True
            if hasPdb:
                ok = self.__set(
                    container,
                    statusCode=statusCode,
                    approvalType=approvalType,
                    annotatorInitials=annotatorInitials,
                    authReleaseCode=authReleaseCode,
                    holdCoordinatesDate=holdCoordinatesDate,
                    expMethods=expMethods,
                    processSite=processSite,
                    postRelStatusCode=postRelStatusCode,
                )
                self.__lfh.write("\n+StatusUpdate.setBoth() __set returns %s\n" % ok)

            if ok and hasEM:
                ok = self.__setEmStatusDetails(container, statusD=statusD, processSite=processSite, annotatorInitials=annotatorInitials, approvalType=approvalType)
                self.__lfh.write("\n+StatusUpdate.setBoth() __setEmStatusDetails returns %s\n" % ok)

            if ok:
                self.__lfh.write("\n+StatusUpdate.setBoth() about to write file %s\n" % outFilePath)
                return self.__io.writeFile(outFilePath, cList)

        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+StatusUpdate.__set() failed file %s statusCode %s approvalType %s outPath %s\n" % (inpFilePath, statusCode, approvalType, outFilePath))
                traceback.print_exc(file=self.__lfh)

        return False


if __name__ == "__main__":
    pass
