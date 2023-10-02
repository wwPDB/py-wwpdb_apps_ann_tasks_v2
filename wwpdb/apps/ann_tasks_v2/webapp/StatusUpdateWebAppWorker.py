##
# File:  StatusUpdateWebAppWorker.py
# Date:  22-Feb-2014
#
# Updates:
#  11-Mar-2014  jdw   fix reponse type for entry report.
#  21-Aug-2014  jdw   fix status update code constraint --
#  17-Jan-2015  jdw   add status history updates
#  21-Jan-2015  jdw   ignore annotatorId parameter input
#  30-Jan-2015  jdw   add special handling of selected prior status codes -REPL|AUCO
#   6-May-2015  jdw   add option to load da_internal and status databases with current model file data
#                     new method = _statusReloadOp()
#  30-Aug-2015  jdw   add update of em_admin category -- _statusCodeUpdateEmOp()
#  21-Feb-206   jdw   change header release processing
#  29-Nov-2016  ep    add support for checkNext (V5RC checking)
#  13-Jun-2017  ep    When creating public mmCIF file use 'review' milestone - not annotate
#  02-Feb-2018  ep    Return requested accession codes to end user
#  23-May-2018  ep    Check status of generating XML header and provide feedback
#  11-Jun-2018  ep    Return contents of XML header error file for display at UI
##
"""
Status update tasks tool  -

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys
import traceback
import shutil
import logging
import inspect

# import datetime
# from dateutil.relativedelta import relativedelta, WE, FR

#
from wwpdb.apps.ann_tasks_v2.webapp.CommonTasksWebAppWorker import CommonTasksWebAppWorker

# from wwpdb.apps.ann_tasks_v2.report.PdbxReport import PdbxReport
from wwpdb.apps.ann_tasks_v2.utils.SessionDownloadUtils import SessionDownloadUtils
from wwpdb.apps.ann_tasks_v2.status.StatusUpdate import StatusUpdate
from wwpdb.utils.db.StatusHistoryUtils import StatusHistoryUtils
from wwpdb.apps.ann_tasks_v2.utils.MergeXyz import MergeXyz
from wwpdb.apps.ann_tasks_v2.em3d.EmHeaderUtils import EmHeaderUtils

# from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.utils.dp.DataFileAdapter import DataFileAdapter
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.utils.session.WebUploadUtils import WebUploadUtils
from wwpdb.utils.session.WebRequest import ResponseContent

#
from wwpdb.apps.wf_engine.engine.WFEapplications import killAllWF

logger = logging.getLogger(__name__)


class StatusUpdateWebAppWorker(CommonTasksWebAppWorker):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        Worker methods for the status update  module.

        Performs URL -> application mapping for this module.

        All operations can be driven from this interface which can
        supplied with control information from web application request
        or from a testing application.


        """
        super(StatusUpdateWebAppWorker, self).__init__(reqObj=reqObj, verbose=verbose, log=log)

        #
        # Service items include:
        #
        self._appPathD = {
            "/service/environment/dump": "_dumpOp",
            "/service/status_update_tasks_v2/entryinfo": "_entryInfoOp",
            "/service/status_update_tasks_v2/newsession": "_newSessionOp",
            "/service/status_update_tasks_v2/start": "_startOp",
            #
            "/service/status_update_tasks_v2/set_idcode": "_setIdCodeFetchModelOp",
            # Deprecated, to be removed
            "/service/status_update_tasks_v2/status_code_update": "_statusCodeUpdateOp",
            "/service/status_update_tasks_v2/status_reload": "_statusReloadOp",
            "/service/status_update_tasks_v2/inline_fileops": "_statusInlineFileOps",
            # "/service/status_update_tasks_v2/misc_reports": "_idReportOps",
            "/service/status_update_tasks_v2/create_files": "_createFileOps",
            "/service/status_update_tasks_v2/mergexyzcalc": "_mergeXyzCalcAltOp",
            "/service/status_update_tasks_v2/process_site_update": "_statusProcessSiteUpdateOp",
            "/service/status_update_tasks_v2/set_idcode_em": "_setIdCodeFetchEmOp",
            # New service for updating
            "/service/status_update_tasks_v2/other_update": "_statusUpdateOtherOp",
            "/service/status_update_tasks_v2/status_code_update_v2": "_statusCodeUpdateV2Op",
        }

        self.addServices(self._appPathD)
        self.__debug = False
        self.__topPath = self._reqObj.getValue("TopPath")
        self.__templatePath = os.path.join(self.__topPath, "htdocs", "status_update_tasks_v2")
        self._reqObj.setValue("TemplatePath", self.__templatePath)

    def doOp(self):
        """Map operation to path and invoke operation.  Exceptions are caught within this method.

        :returns:

        Operation output is packaged in a ResponseContent() object.

        """
        #
        try:
            inpReqPath = self._reqObj.getRequestPath()
            # first pull off the REST style URLS --
            #
            #
            if inpReqPath.startswith("/service/status_update_tasks/report/d_"):
                rFields = inpReqPath.split("/")
                self._reqObj.setValue("idcode", rFields[4].upper())
                reqPath = "/service/status_update_tasks/report"
            else:
                reqPath = inpReqPath
            #
            if reqPath not in self._appPathD:
                # bail out if operation is unknown -
                rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                rC.setError(errMsg="Unknown operation")
            else:
                mth = getattr(self, self._appPathD[reqPath], None)
                rC = mth()
            return rC
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self._lfh)
            rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            rC.setError(errMsg="Operation failure")
            return rC

    def _dumpOp(self):
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setHtmlList(self._reqObj.dump(format="html"))
        return rC

    def _startOp(self):
        """Entry point to launch UI from WF or URL starting point  --"""
        identifier = self._reqObj.getValue("identifier")
        fileSource = self._reqObj.getValue("filesource")
        skipStatus = self._reqObj.getValue("skipstatus")
        #        annotatorId = self._reqObj.getValue('annotator')
        #
        if self._verbose:
            self._lfh.write(
                "\n+%s.%s starting with identifier %s and filesource %s status flag %r \n"
                % (self.__class__.__name__, inspect.currentframe().f_code.co_name, identifier, fileSource, skipStatus)
            )

        return self.__makeStartOpResponse(identifier, contentType="model", formatType="pdbx")

    def __makeStartOpResponse(self, identifier, contentType, formatType="pdbx"):
        """Worker method for UI launch point -"""
        self._getSession()
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        statusCode = ""
        authRelCode = ""
        annotatorId = ""
        postRelStatusCode = ""
        # Original annotator in request from WFM. Stash so we can use elsewhere
        origAnnotator = self._reqObj.getValueOrDefault("annotator", "")

        if du.fetchId(identifier, contentType, formatType=formatType):
            aTagList.append(du.getAnchorTag())
            fP = du.getDownloadPath()

            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            sUD = sU.getV2(fP)
            pdbId = sUD["pdb_id"]
            emdbId = sUD["emdb_id"]
            annotatorId = sUD["annotatorInitials"]
            statusCode = sUD["statusCode"]
            authRelCode = sUD["authReleaseCode"]
            initialDepositDate = sUD["initialDepositionDate"]
            coordinatesDate = sUD["coordinatesDate"]
            holdCoordinatesDate = sUD["holdCoordinatesDate"]
            reqAccTypes = sUD["reqAccTypes"]
            postRelStatusCode = sUD["postRelStatus"]

            if self._verbose:
                self._lfh.write(
                    "\n+%s.%s starting with identifier %s statusCode %r authRelCode %r annotatorId %r\n"
                    % (self.__class__.__name__, inspect.currentframe().f_code.co_name, identifier, statusCode, authRelCode, annotatorId)
                )

        # Prepare the Startup data items
        myD = {}
        myD["entryid"] = identifier
        myD["sessionid"] = self._sessionId
        myD["annotatorid"] = annotatorId
        myD["startannotator"] = origAnnotator
        myD["statuscode"] = statusCode
        myD["postrelstatuscode"] = postRelStatusCode
        myD["authrelcode"] = authRelCode
        #
        #  Insert these dates into the page as global context values --
        #
        myD["initialdepositdate"] = initialDepositDate
        myD["holdcoordinatesdate"] = holdCoordinatesDate
        myD["coordinatesdate"] = coordinatesDate
        #
        myD["emdbid"] = emdbId
        myD["pdbid"] = pdbId
        # Requested accession codes. Legacy entries do not have this.
        myD["reqacctypes"] = reqAccTypes
        logger.debug("reqacctypes is %r", reqAccTypes)

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("html")
        templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "status_admin.html")
        #        if ((pdbId is not None) and (len(pdbId) > 3)):
        #            templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "status_admin.html")
        #        elif ((emdbId is not None) and (len(emdbId) > 3)):
        #            templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "status_admin_em.html")
        #        else:
        #            templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "status_admin.html")
        webIncludePath = os.path.join(self._reqObj.getValue("TopPath"), "htdocs")
        rC.setHtmlTextFromTemplate(templateFilePath=templateFilePath, webIncludePath=webIncludePath, parameterDict=myD, insertContext=True)
        if self.__debug:
            self._lfh.write("\n+%s.%s dump response\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
            rC.dump()
        return rC

    #
    # ---------------------------------------------------------------------------------------------------
    #                      Status and check report options implementing JSON responses -
    #

    def _setIdCodeFetchModelOp(self):
        """Set the active data set identifier - and fetch the associated model file -"""
        idCode = self._reqObj.getValue("idcode")
        if self._verbose:
            self._lfh.write("+CommonWebAppWorker._setIdCodeFetchModelOp() starting with idCode %s\n" % idCode)

        return self._makeIdFetchResponse(idCode, contentType="model", formatType="pdbx")

    # def _idReportOps(self):
    #     """Operations on data files identified by id and type."""
    #     operation = self._reqObj.getValue("operation")
    #     if self._verbose:
    #         self._lfh.write("+StatusUpdateWebAppWorker._reviewDataInlineIdOps() starting with op %s\n" % operation)

    #     idCodes = self._reqObj.getValue("idcode")
    #     idCodeList = idCodes.split(" ")
    #     contentType = self._reqObj.getValue("contentType")

    #     if self._verbose:
    #         self._lfh.write("+StatusUpdateWebAppWorker._reviewDataInlineIdOps() content %s fetch id(s) %r\n" % (contentType, idCodeList))
    #     #
    #     if operation == "fetch_entry":
    #         return self.__makeIdListFetchResponse(idCodeList, contentType="model", formatType="pdbx")
    #     elif operation == "fetch_sf":
    #         return self.__makeIdListFetchResponse(idCodeList, contentType="structure-factors", formatType="pdbx")
    #     elif operation == "report":
    #         return self.__makeIdListReportResponse(idCodeList, contentType)
    #     elif operation in ["check", "checkv4", "checkNext"]:
    #         return self.__makeIdListCheckResponse(idCodeList, contentType, operation=operation)
    #     else:
    #         pass

    # def __makeIdListReportResponse(self, idCodeList, contentType="model", formatType="pdbx"):
    #     """Prepare response for a report request for the input Id code list."""
    #     self._getSession()

    #     rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
    #     rC.setReturnFormat("json")
    #     #
    #     du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
    #     aTagList = []
    #     htmlList = []
    #     # layout='tabs'
    #     # layout='accordion'
    #     layout = "multiaccordion"
    #     pR = PdbxReport(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
    #     for idCode in idCodeList:
    #         ok = du.fetchId(idCode, contentType, formatType=formatType)
    #         if not ok:
    #             continue
    #         downloadPath = du.getDownloadPath()
    #         aTagList.append(du.getAnchorTag())
    #         htmlList.extend(pR.makeTabularReport(filePath=downloadPath, contentType=contentType, idCode=idCode, layout=layout))

    #     if len(aTagList) > 0:
    #         rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
    #         rC.setHtmlList(htmlList)
    #         rC.setStatus(statusMsg="Reports completed")
    #     else:
    #         rC.setError(errMsg="No corresponding data file(s)")
    #         # do nothing

    #     return rC

    # def __makeIdListCheckResponse(self, idCodeList, contentType, operation="check", formatType="pdbx"):
    #     """Prepare response for a check request for the input Id code list."""
    #     self._getSession()
    #     rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
    #     rC.setReturnFormat("json")
    #     #
    #     du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
    #     aTagList = []
    #     htmlList = []
    #     # fileFormat='cif'
    #     # layout='tabs'
    #     # layout='accordion'
    #     # layout='multiaccordion'

    #     for idCode in idCodeList:
    #         ok = du.fetchId(idCode, contentType, formatType=formatType)
    #         if not ok:
    #             continue

    #         if operation in ["check", "checkv4"]:
    #             filePath = du.getDownloadPath()
    #             if operation in ["checkv4"]:
    #                 logPath = os.path.join(self._sessionPath, idCode + "-check-v4.log")
    #             else:
    #                 logPath = os.path.join(self._sessionPath, idCode + "-check.log")
    #             hasDiags = self.__makeCifCheckReport(filePath, logPath, op=operation)
    #             if hasDiags:
    #                 duL = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
    #                 duL.copyToDownload(logPath)
    #                 aTagList.append(duL.getAnchorTag())
    #                 rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
    #                 rC.setStatus(statusMsg="Check completed")
    #             else:
    #                 rC.setStatus(statusMsg="No diagnostics for %s" % idCode)

    #     if len(aTagList) > 0:
    #         rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
    #         rC.setHtmlList(htmlList)
    #         rC.setStatus(statusMsg="Check report completed")
    #     else:
    #         rC.setError(errMsg="Check completed - no diagnostics")
    #         # do nothing

    #     return rC

    # def __makeCifCheckReport(self, filePath, logPath, op="check"):
    #     """Create CIF dictionary check on the input file and return diagnostics in logPath.

    #     Return True if a report is created (logPath exists and has non-zero size)
    #         or False otherwise
    #     """
    #     if self._verbose:
    #         self._lfh.write("+StatusUpdateWebAppWorker.__makeCifCheckReport() with site %s for file %s\n" % (self._siteId, filePath))
    #     dp = RcsbDpUtility(tmpPath=self._sessionPath, siteId=self._siteId, verbose=self._verbose, log=self._lfh)
    #     dp.imp(filePath)
    #     if op in ["check", "updatewithcheck"]:
    #         dp.op("check-cif")
    #     elif op in ["checkv4"]:
    #         dp.op("check-cif-v4")
    #     else:
    #         # do something -
    #         dp.op("check-cif")

    #     dp.exp(logPath)
    #     if not self.__debug:
    #         dp.cleanup()
    #     #
    #     if os.access(logPath, os.R_OK) and os.stat(logPath).st_size > 0:
    #         return True
    #     else:
    #         return False

    # --------------------------------------------------------------------------------------------------------------------------------
    #                      File production options implementing JSON responses -
    #
    #
    def _createFileOps(self):
        """Operations on data files identified by id and type."""
        self._getSession()
        operation = self._reqObj.getValue("operation")
        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._createFileOps() starting with op %s\n" % operation)

        idCode = self._reqObj.getValue("idcode")
        contentType = "model"
        formatType = "pdbx"
        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._createFileOps() content %s id %s\n" % (contentType, idCode))

        aTagList = []
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            #
            #
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

            if operation == "pdb":
                # To determine if failure to produce PDB file, need to check current status
                currArchivePath = pI.getModelPdbFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None)
                currexist = os.path.exists(currArchivePath)

                pdbArchivePath = pI.getModelPdbFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
                dfa = DataFileAdapter(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                dfa.cif2Pdb(filePath, pdbArchivePath)  # This code returns status - True if succeeds or not.

                # Scenarios:
                #  a) old not present and new present --> good
                #  b) old not present, new not present --> error
                #  c) old present and new present
                #     1) old_name==new_name --> error,
                #     2) old_name != new_name --> ok
                #  d) old present and new not present -> error

                newexist = os.path.exists(pdbArchivePath)

                # (b) + (d) -> new not present error
                convok = False
                if newexist:
                    if not currexist:
                        # (a)
                        convok = True
                    elif pdbArchivePath != currArchivePath:
                        convok = True
                    # else fall through as false

                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._createFileOps() PDB conversion status %s\n" % convok)

                if convok:
                    du.fetchId(idCode, "model", formatType="pdb")
                    aTagList.append(du.getAnchorTag())
                    rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                    rC.setStatus(statusMsg="PDB format file created")
                else:
                    rC.setError(errMsg="PDB format file cannot be produced")
            elif operation == "pdbx":
                pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone="review")
                dfa = DataFileAdapter(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                dfa.cif2Pdbx(filePath, pdbxArchivePath)
                du.fetchId(idCode, "model", formatType="pdbx", mileStone="review")
                aTagList.append(du.getAnchorTag())
                rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                rC.setStatus(statusMsg="PDBx format with public data subset file created")
            elif operation == "assembly":
                archivePath = pI.getDirPath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", contentType="assembly-model", formatType="pdbx")
                dfa = DataFileAdapter(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                indexFilePath = os.path.join(self._sessionPath, "assembly-index.txt")
                dfa.pdbx2Assemblies(idCode, filePath, archivePath, indexFilePath=indexFilePath)
                fCount = 0
                try:
                    ifh = open(indexFilePath, "r")
                    for line in ifh:
                        fCount += 1
                        fp = os.path.join(archivePath, line[:-1])
                        du.copyToDownload(fp)
                        aTagList.append(du.getAnchorTag())
                    ifh.close()
                except:  # noqa: E722 pylint: disable=bare-except
                    pass
                #
                if fCount > 0:
                    rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                    rC.setStatus(statusMsg="Assembly files created")
                else:
                    rC.setStatus(statusMsg="No assembly files created")
            else:
                pass
        else:
            rC.setError(errMsg="File creation failed.")
            # do nothing

        return rC

    # --------------------------------------------------------------------------------------------------------------------------------
    #                      File production options implementing JSON responses -
    #
    #
    def _statusCodeUpdateOp(self):
        """Status code updates on data files identified by id and type."""
        self._getSession(useContext=True)

        idCode = self._reqObj.getValue("idcode")
        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() starting with idCode %s\n" % idCode)
        contentType = "model"
        formatType = "pdbx"
        newHistoryFile = False

        # Values from the input form --
        #
        statusCode = self._reqObj.getValue("status-code")
        postRelStatusCode = self._reqObj.getValue("postrel-status-code")
        approvalType = self._reqObj.getValue("approval-type")
        annotatorInitials = self._reqObj.getValue("annotator-initials")
        authStatusHoldDate = self._reqObj.getValue("auth-status-hold-date")
        authStatusCode = self._reqObj.getValue("auth-status-code")
        processSite = self._reqObj.getValue("process-site")
        #
        #  Values from the current version of the model file --
        #
        orgStatusCode = self._reqObj.getValue("statuscode")
        orgPostRelStatusCode = self._reqObj.getValue("postrelstatuscode")
        orgInitialDepositionDate = self._reqObj.getValue("initialdepositdate")
        # orgHoldCoordinatesDate = self._reqObj.getValue("holdcoordinatesdate")
        # orgCoordinatesDate = self._reqObj.getValue("coordinatesdate")
        # orgAuthRelCode = self._reqObj.getValue("authrelcode")
        expMethods = self._reqObj.getValue("experimental_methods")
        orgPostRelRecvdCoord = self._reqObj.getValue("postrelrecvdcoord")
        orgPostRelRecvdCoordDate = self._reqObj.getValue("postrelrecvdcoorddate")
        #
        # For already released entries, statusCode will be '', but orgStatusCode will = 'REL'
        logger.info("Status code change: statuscode %s -> %s, postrel %s -> %s", orgStatusCode, statusCode, orgPostRelStatusCode, postRelStatusCode)
        #
        try:
            #   Update status history - first create a new history file if required.
            shu = StatusHistoryUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
            if statusCode in ["AUTH", "WAIT"]:
                rL = shu.createHistory([idCode], overWrite=False, statusUpdateAuthWait=statusCode)
            else:
                rL = shu.createHistory([idCode], overWrite=False)
            if len(rL) > 0:
                if self._verbose:
                    newHistoryFile = True
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s new status history file created\n" % idCode)
        except:  # noqa: E722 pylint: disable=bare-except
            if self._verbose:
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history file create failed with exception\n" % idCode)
                traceback.print_exc(file=self._lfh)
        #
        msg = "ok"
        # Test if any conditions are violated
        #

        if (str(statusCode).upper() == "HPUB") and (str(authStatusCode).upper() == "HOLD"):
            # ((str(statusCode).upper() == 'HOLD') and (str(authStatusCode).upper() == 'HPUB')):
            msg = "Processing status code and author release status are inconsistent"

        if (str(orgStatusCode).upper() == "PROC") and (str(statusCode).upper() in ["HPUB", "HOLD"]):
            msg = "Processing status code change from PROC to HPUB or HOLD prohibited"

        if str(orgStatusCode).upper() == "REL":
            if len(orgPostRelStatusCode) == 0:
                msg = "Processing status code change from REL prohibited"
            else:
                # Web form does not set in this case
                statusCode = "REL"

        if str(orgStatusCode).upper() == "OBS":
            msg = "Processing status code change from OBS prohibited"

        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpateOp() id %s check status message is: %s\n" % (idCode, msg))
        #

        aTagList = []
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        if msg != "ok":
            rC.setError(errMsg=msg)
            return rC

        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

            pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
            if self._verbose:
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() model input path %s model archive output path %s\n" % (filePath, pdbxArchivePath))

            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            ok1 = sU.wfLoad(
                idCode,
                statusCode,
                annotatorInitials=annotatorInitials,
                initialDepositionDate=orgInitialDepositionDate,
                authRelCode=authStatusCode,
                postRelStatusCode=postRelStatusCode,
                postRelRecvdCoord=orgPostRelRecvdCoord,
                postRelRecvdCoordDate=orgPostRelRecvdCoordDate,
            )
            if self._verbose:
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() wf load completed %r\n" % ok1)
            if ok1:
                ok2 = sU.set(
                    filePath,
                    filePath,
                    statusCode,
                    approvalType,
                    annotatorInitials,
                    authStatusCode,
                    authStatusHoldDate,
                    expMethods,
                    processSite,
                    postRelStatusCode=postRelStatusCode,
                )
                if ok2:
                    shutil.copyfile(filePath, pdbxArchivePath)

                status1 = killAllWF(idCode, "statMod")
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() killallwf returns %r\n" % status1)

                ok3 = sU.dbLoad(filePath)
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() data file status update completed %r\n" % ok3)
                if ok2 & ok3:
                    du.fetchId(idCode, "model", formatType="pdbx")
                    aTagList.append(du.getAnchorTag())
                    rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                    rC.setStatus(statusMsg="Status updated")
                    rC.set("statuscode", statusCode)
                    #
                    myD = {}
                    myD["statuscode"] = statusCode
                    myD["authrelcode"] = authStatusCode
                    myD["holdcoordinatesdate"] = authStatusHoldDate
                    myD["approval_type"] = approvalType
                    myD["process_site"] = processSite
                    myD["annotator_initials"] = annotatorInitials
                    myD["initialdepositdate"] = orgInitialDepositionDate
                    myD["postrelstatuscode"] = postRelStatusCode

                    for k, v in myD.items():
                        rC.set(k, v)
                    self._saveSessionParameter(pvD=myD)
                    try:
                        okShLoad = False
                        shu = StatusHistoryUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                        okShUpdate = shu.updateEntryStatusHistory(
                            entryIdList=[idCode], statusCode=statusCode, annotatorInitials=annotatorInitials, details="Update by status module", statusCodePrior=orgStatusCode
                        )
                        if self._verbose:
                            self._lfh.write(
                                "+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history file update status %r newHistoryFile %r\n" % (idCode, okShUpdate, newHistoryFile)
                            )
                        if okShUpdate or newHistoryFile:
                            okShLoad = shu.loadEntryStatusHistory(entryIdList=[idCode])
                        if self._verbose:
                            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history database load status %r\n" % (idCode, okShLoad))
                    except:  # noqa: E722 pylint: disable=bare-except
                        if self._verbose:
                            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history update and database load failed with exception\n")
                            traceback.print_exc(file=self._lfh)
                    #
                else:
                    rC.setError(errMsg="Data file status update failed.")
                    if ok1:
                        okRb = sU.wfRollBack(idCode=idCode)
                        if not okRb:
                            rC.setError(errMsg="Data file status update failed and workflow status roll back failed.")
                        else:
                            rC.setError(errMsg="Data file status update failed and workflow status rolled back.")
            else:
                rC.setError(errMsg="WF status database update failed.")
        else:
            rC.setError(errMsg="Status update failed, data file cannot be accessed.")
            # do nothing

        return rC

    #

    def _statusReloadOp(self):
        """Status data reload/updates on data files identified by id."""
        self._getSession(useContext=True)

        idCode = self._reqObj.getValue("idcode")
        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._statusReloadOp() starting with idCode %s\n" % idCode)
        contentType = "model"
        formatType = "pdbx"
        #
        #  Values from the current version of the model file --
        #
        orgStatusCode = self._reqObj.getValue("statuscode")
        orgInitialDepositionDate = self._reqObj.getValue("initialdepositdate")
        # orgHoldCoordinatesDate = self._reqObj.getValue("holdcoordinatesdate")
        # orgCoordinatesDate = self._reqObj.getValue("coordinatesdate")
        orgAuthRelCode = self._reqObj.getValue("authrelcode")
        orgPostRelStatusCode = self._reqObj.getValue("postrelstatuscode")
        # expMethods = self._reqObj.getValue("experimental_methods")
        annotatorInitials = self._reqObj.getValue("annotator_initials")
        orgPostRelRecvdCoord = self._reqObj.getValue("postrelrecvdcoord")
        orgPostRelRecvdCoordDate = self._reqObj.getValue("postrelrecvdcoorddate")
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")

        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()

            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            ok1 = sU.wfLoad(
                idCode,
                orgStatusCode,
                annotatorInitials=annotatorInitials,
                initialDepositionDate=orgInitialDepositionDate,
                authRelCode=orgAuthRelCode,
                postRelStatusCode=orgPostRelStatusCode,
                postRelRecvdCoord=orgPostRelRecvdCoord,
                postRelRecvdCoordDate=orgPostRelRecvdCoordDate,
            )
            if self._verbose:
                self._lfh.write("+StatusUpdateWebAppWorker._statusReloadOp() wf load completed %r\n" % ok1)
            if ok1:
                status1 = killAllWF(idCode, "statMod")
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusReloadOp() killallwf returns %r\n" % status1)

                ok2 = sU.dbLoad(filePath)
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusReloadOp() data file status update completed %r\n" % ok2)
                if ok1 & ok2:
                    rC.setStatus(statusMsg="Status updated using current contents of model file")
                else:
                    rC.setError(errMsg="Data file status update failed.")

            else:
                rC.setError(errMsg="WF status database update failed.")
        else:
            rC.setError(errMsg="Status update failed, data file cannot be accessed.")
            # do nothing

        return rC

    #

    def _mergeXyzCalcAltOp(self):
        """Alternative merge coordinate operation"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcAltOp() starting\n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")

        # get a copy of the current model -
        de = DataExchange(reqObj=self._reqObj, depDataSetId=entryId, fileSource="wf-archive", verbose=self._verbose, log=self._lfh)
        pth = de.copyToSession(contentType="model", formatType="pdbx", version="latest", partitionNumber=1)
        (_dn, fileName) = os.path.split(pth)

        # merge file format
        xyzFileFormat = self._reqObj.getValue("xyzfileformat")
        #
        #
        wuu = WebUploadUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        xyzFileName = wuu.copyToSession(fileTag="xyzfilename")

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        calc = MergeXyz(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if xyzFileName is not None and len(xyzFileName) > 0:
            calc.setReplacementXyzFile(xyzFileName, format=xyzFileFormat)
            self._saveSessionParameter(param="xyzfilename", value=xyzFileName, prefix=entryId)

            ok = calc.run(entryId, fileName)
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcAltOp() status %r\n" % ok)
            if ok:
                #
                # copy the file back --
                #
                pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
                pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=entryId, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
                shutil.copyfile(pth, pdbxArchivePath)
                if self._verbose:
                    self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcAltOp() updating model file in %s\n" % pdbxArchivePath)
                rC.setStatus(statusMsg="Merge completed and model updated.")
            else:
                rC.setError(errMsg="Merge failed.")
        else:
            ok = False
            rC.setError(errMsg="Merge failed.")
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcOp() no merge file provided\n")
        #
        aTagList = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
        #

        return rC

    def _statusProcessSiteUpdateOp(self):
        """Status  - processs site update and reload based on current annotator assignment --  Fixes mis-assigned process site --"""
        self._getSession(useContext=True)

        idCode = self._reqObj.getValue("idcode")
        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._statusProcessSiteUpdateOp() starting with idCode %s\n" % idCode)
        contentType = "model"
        formatType = "pdbx"

        annotatorInitials = self._reqObj.getValue("annotator_initials")
        processSite = self._reqObj.getValue("process_site")
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
            pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
            if self._verbose:
                self._lfh.write("+StatusUpdateWebAppWorker._statusProcessSiteUpdateOp() model input path %s model archive output path %s\n" % (filePath, pdbxArchivePath))
            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            tSite = sU.assignProcessSite(annotatorInitials)
            if tSite != processSite:
                ok1 = sU.setProcessSite(filePath, filePath, tSite)
                if ok1:
                    shutil.copyfile(filePath, pdbxArchivePath)

                    status1 = killAllWF(idCode, "statMod")
                    if self._verbose:
                        self._lfh.write("+StatusUpdateWebAppWorker._statusProcessSiteUpdateOp() killallwf returns %r\n" % status1)

                    ok2 = sU.dbLoad(filePath)
                    if self._verbose:
                        self._lfh.write("+StatusUpdateWebAppWorker._statusProcessSiteUpdateOp() data file status update completed %r\n" % ok2)
                    if ok1 & ok2:
                        rC.setStatus(statusMsg="Process site updated and reloaded")
                    else:
                        rC.setError(errMsg="Process site update and reload failed.")

                else:
                    rC.setError(errMsg="Process site update failed.")
            else:
                rC.setError(errMsg="Process site update and reload not performed, no change required.")
                # do nothing
        else:
            rC.setError(errMsg="Process site update failed, data file cannot be accessed.")

        return rC

    # ---------------------------------------------------------------------------------------------------------
    #                                     EM --  entry points  --
    #
    def _setIdCodeFetchEmOp(self):
        """Set the active data set identifier - and fetch the associated EM data file  -"""
        idCode = self._reqObj.getValue("idcode")
        if self._verbose:
            self._lfh.write("+CommonWebAppWorker._setIdCodeFetchEmOp() starting with idCode %s\n" % idCode)

        return self._makeIdFetchResponse(idCode, contentType="model", formatType="pdbx")

    # def __getHeaderReleaseDate(self):
    #     """
    #     Return the date 'yyyy-mm-dd' of the next release date (Wednesday) subject to the policy cutoff date.

    #     Compute the reference delta - Friday 14:30 GMT to next Wed 00:00 GMT

    #     """
    #     #
    #     #
    #     try:
    #         todayUTC = datetime.datetime.utcnow()
    #         nxtFriR = todayUTC + relativedelta(days=+1, weekday=FR(+1))
    #         nxtWedR = nxtFriR + relativedelta(days=+1, weekday=WE(+1))
    #         off1 = datetime.datetime(nxtWedR.year, nxtWedR.month, nxtWedR.day, 0, 0, 1)
    #         off2 = datetime.datetime(nxtFriR.year, nxtFriR.month, nxtFriR.day, 14, 30, 0)
    #         diffRef = (off1 - off2).total_seconds()
    #         # ------------------------------------
    #         todayUTC = datetime.datetime.utcnow()
    #         nxtWed = todayUTC + relativedelta(days=+1, weekday=WE(+1))
    #         nxtWedS = datetime.datetime(nxtWed.year, nxtWed.month, nxtWed.day, 0, 0, 1)
    #         #
    #         diffTest = (nxtWedS - todayUTC).total_seconds()
    #         #
    #         if diffTest < diffRef:
    #             #
    #             trg = todayUTC + relativedelta(days=+1, weekday=WE(+2))
    #         else:
    #             trg = nxtWed
    #         #
    #         retDate = trg.strftime("%Y-%m-%d")
    #     except:  # noqa: E722 pylint: disable=bare-except
    #         traceback.print_exc(file=self._lfh)
    #         retDate = None

    #     return retDate

    def _statusUpdateOtherOp(self):
        """Update header including site, annotator, auth hold requests and date"""
        self._getSession(useContext=True, overWrite=False)

        idCode = self._reqObj.getValue("idcode")
        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOtherOp() starting with idCode %s\n" % idCode)
        contentType = "model"
        formatType = "pdbx"

        #
        newPdbStatus = self._reqObj.getValue("new-auth-status-code")
        newPdbHoldDate = self._reqObj.getValue("auth-status-hold-date")  # Could be empty
        newEmStatus = self._reqObj.getValue("em_depui_depositor_hold_instructions")
        newEmHoldDate = self._reqObj.getValue("em_map_hold_date")
        newAnnotatorInitials = self._reqObj.getValue("annotator-initials")
        newProcessSite = self._reqObj.getValue("process-site")
        # also sent back
        reqAccTypes = self._reqObj.getValue("reqacctypes")

        # Saved away
        expMethods = self._reqObj.getValue("experimental_methods")

        logger.info("New PDB status :%s: Hold :%s:  EMDB status :%s: hold :%s:", newPdbStatus, newPdbHoldDate, newEmStatus, newEmHoldDate)
        logger.info("New annotator :%s: and site :%s:", newAnnotatorInitials, newProcessSite)
        logger.info("Req is %s", reqAccTypes)

        hasPdb = False
        hasEM = False
        if len(reqAccTypes) < 2 or "PDB" in reqAccTypes:
            hasPdb = True
        if "EMDB" in reqAccTypes:
            hasEM = True

        msg = "ok"
        # If there are any policy decisions here is where they would be with msg changed

        aTagList = []
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")

        # Return policy violation
        if msg != "ok":
            rC.setError(errMsg=msg)
            return rC

        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

            pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
            if self._verbose:
                self._lfh.write("+StatusUpdateWebAppWorker.__statusUpdateOtherOp() model input path %s model archive output path %s\n" % (filePath, pdbxArchivePath))

            # filePath is session directory

            # Setup em status setting
            kyPairListEm = [("em_map_hold_date", "em_map_hold_date"), ("em_depui_depositor_hold_instructions", "em_depui_depositor_hold_instructions")]
            statusD = {}
            for kyPair in kyPairListEm:
                statusD[kyPair[0]] = self._reqObj.getValue(kyPair[0])

            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

            ok1 = False
            ok1a = False
            ok2 = False
            ok3 = False

            if hasPdb:
                ok1 = sU.wfLoad(idCode, annotatorInitials=newAnnotatorInitials, authRelCode=newPdbStatus)
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusUpdateotherOp() wf load completed %r\n" % ok1)
            else:
                ok1 = True

            if hasEM and ok1:
                ok1a = sU.wfEmLoad(idCode, annotatorInitials=newAnnotatorInitials, authRelCode=statusD["em_depui_depositor_hold_instructions"])
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusUpdateotherOp() EM wf load completed %r\n" % ok1a)
            else:
                ok1a = True

            if ok1 and ok1a:
                ok2 = sU.setBoth(
                    filePath,
                    filePath,
                    reqAccTypes,
                    statusCode=None,
                    statusD=statusD,
                    approvalType=None,
                    annotatorInitials=newAnnotatorInitials,
                    authReleaseCode=newPdbStatus,
                    holdCoordinatesDate=newPdbHoldDate,
                    processSite=newProcessSite,
                    expMethods=expMethods,
                )
                self._lfh.write("+StatusUpdateWebAppWorker._statusUpdateOtherOp() set completed %r\n" % ok2)

            if ok1 and ok1a and ok2:
                # Copy to archive
                shutil.copyfile(filePath, pdbxArchivePath)

                ok3 = sU.dbLoad(filePath)
                self._lfh.write("+StatusUpdateWebAppWorker._statusUpdateOtherOp() dbLoad completed %r\n" % ok3)

                if ok3:
                    # Fetch again
                    du.fetchId(idCode, "model", formatType="pdbx")
                    aTagList.append(du.getAnchorTag())
                    rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                    rC.setStatus(statusMsg="Status updated")

                    myD = {}
                    myD["authrelcode"] = newPdbStatus
                    myD["holdcoordinatesdate"] = newPdbHoldDate
                    myD["process_site"] = newProcessSite
                    myD["annotator_initials"] = newAnnotatorInitials
                    myD["em_depui_depositor_hold_instructions"] = newEmStatus
                    myD["em_map_hold_date"] = newEmHoldDate

                    for k, v in myD.items():
                        rC.set(k, v)
                    self._saveSessionParameter(pvD=myD)
                else:
                    rC.setError(errMsg="Update failed.")

            else:
                rC.setError(errMsg="Update failed.")

            status1 = killAllWF(idCode, "statMod")
            if self._verbose:
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() killallwf returns %r\n" % status1)

        else:
            rC.setError(errMsg="Status update failed, data file cannot be accessed.")
            # do nothing

        return rC

    # --------------------------------------------------------------------------------------------------------------------------------
    #                      File production options implementing JSON responses -
    #
    #
    def _statusCodeUpdateV2Op(self):
        """Status code updates on data files identified by id and type. Combined EM and PDB operation"""
        self._getSession(useContext=True)

        idCode = self._reqObj.getValue("idcode")
        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateV2Op() starting with idCode %s\n" % idCode)
        contentType = "model"
        formatType = "pdbx"
        newHistoryFile = False

        # Values from the input form --
        #
        statusCode = self._reqObj.getValue("status-code")
        approvalType = self._reqObj.getValue("approval-type")
        # Only sent in postrel situration
        postRelStatusCode = self._reqObj.getValue("postrel-status-code")

        annotatorInitials = self._reqObj.getValue("cur-annotator-initials")
        # authStatusHoldDate = self._reqObj.getValue('auth-status-hold-date')
        # authStatusCode = self._reqObj.getValue('auth-status-code')
        # processSite = self._reqObj.getValue('process-site')
        #
        #  Values from the current version of the model file --
        #
        orgStatusCode = self._reqObj.getValue("statuscode")
        orgPostRelStatusCode = self._reqObj.getValue("postrelstatuscode")
        orgInitialDepositionDate = self._reqObj.getValue("initialdepositdate")
        # orgHoldCoordinatesDate = self._reqObj.getValue("holdcoordinatesdate")
        # orgCoordinatesDate = self._reqObj.getValue("coordinatesdate")
        orgAuthRelCode = self._reqObj.getValue("authrelcode")
        orgPostRelRecvdCoord = self._reqObj.getValue("postrelrecvdcoord")
        orgPostRelRecvdCoordDate = self._reqObj.getValue("postrelrecvdcoorddate")
        orgEmStatus = self._reqObj.getValue("em_current_status")
        orgEmAuthStatus = self._reqObj.getValue("em_depui_depositor_hold_instructions")
        #
        expMethods = self._reqObj.getValue("experimental_methods")
        #
        reqAccTypes = self._reqObj.getValue("reqacctypes")
        #

        # Em related - note we pull "new" status code
        kyPairListEm = [("em_current_status", "em_new_status")]

        statusD = {}
        emdbId = self._reqObj.getValue("emdb_id")
        for kyPair in kyPairListEm:
            statusD[kyPair[0]] = self._reqObj.getValue(kyPair[1])

        #
        # For already released entries, statusCode will be '', but orgStatusCode will = 'REL'
        logger.info("Status code change: statuscode %s -> %s, postrel %s -> %s", orgStatusCode, statusCode, orgPostRelStatusCode, postRelStatusCode)

        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateV2Op() statusD %r\n" % statusD.items())

        hasPdb = False
        hasEM = False
        if len(reqAccTypes) < 2 or "PDB" in reqAccTypes:
            hasPdb = True
        if "EMDB" in reqAccTypes:
            hasEM = True

        msg = "ok"
        # Test if any conditions are violated
        #

        if hasPdb:
            if (str(statusCode).upper() == "HPUB") and (str(orgAuthRelCode).upper() == "HOLD"):
                # ((str(statusCode).upper() == 'HOLD') and (str(authStatusCode).upper() == 'HPUB')):
                msg = "Processing status code and author release status are inconsistent"

            if (str(orgStatusCode).upper() == "PROC") and (str(statusCode).upper() in ["HPUB", "HOLD"]):
                msg = "Processing status code change from PROC to HPUB or HOLD prohibited"

            if str(orgStatusCode).upper() == "REL":
                if len(orgPostRelStatusCode) == 0:
                    msg = "Processing status code change from REL prohibited"
                else:
                    # Web form does not set in this case
                    statusCode = "REL"

            if str(orgStatusCode).upper() == "OBS":
                msg = "Processing status code change from OBS prohibited"

        if hasEM and msg == "ok":
            # For PostRel PDB - this will be empty
            if statusD["em_current_status"] == "":
                statusD["em_current_status"] = orgEmStatus

            newEmStatus = statusD["em_current_status"]

            if (str(orgEmStatus).upper() == "PROC") and (str(newEmStatus).upper() in ["HPUB", "HOLD"]):
                msg = "EM processing status code change from PROC to HPUB or HOLD prohibited"

            if (str(newEmStatus).upper() == "HPUB") and (str(orgEmAuthStatus).upper() == "HOLD"):
                # ((str(statusCode).upper() == 'HOLD') and (str(authStatusCode).upper() == 'HPUB')):
                msg = "Processing status code and author release status are inconsistent"

        if self._verbose:
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpateOp() id %s check status message is: %s\n" % (idCode, msg))
        #

        aTagList = []
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        if msg != "ok":
            rC.setError(errMsg=msg)
            return rC

        # Update status history
        if hasPdb:
            try:
                #   Update status history - first create a new history file if required.
                shu = StatusHistoryUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
                if statusCode in ["AUTH", "WAIT"]:
                    rL = shu.createHistory([idCode], overWrite=False, statusUpdateAuthWait=statusCode)
                else:
                    rL = shu.createHistory([idCode], overWrite=False)
                if len(rL) > 0:
                    if self._verbose:
                        newHistoryFile = True
                        self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s new status history file created\n" % idCode)
            except:  # noqa: E722 pylint: disable=bare-except
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history file create failed with exception\n" % idCode)
                    traceback.print_exc(file=self._lfh)

        # Ok - cleared for operation

        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

            pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
            if self._verbose:
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() model input path %s model archive output path %s\n" % (filePath, pdbxArchivePath))

            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

            ok1 = True
            if hasPdb:
                ok1 = sU.wfLoad(
                    idCode,
                    statusCode,
                    initialDepositionDate=orgInitialDepositionDate,
                    postRelStatusCode=postRelStatusCode,
                    postRelRecvdCoord=orgPostRelRecvdCoord,
                    postRelRecvdCoordDate=orgPostRelRecvdCoordDate,
                )
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() wf load completed %r\n" % ok1)

            ok1a = True
            if hasEM:
                ok1a = sU.wfEmLoad(idCode, statusCode=statusD["em_current_status"], annotatorInitials=annotatorInitials)
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateEmOp() database status.deposition update completed %r\n" % ok1a)

            ok2 = False
            ok3 = False
            if ok1 and ok1a:
                ok2 = sU.setBoth(
                    filePath, filePath, reqAccTypes, statusCode, statusD, approvalType, annotatorInitials=None, expMethods=expMethods, postRelStatusCode=postRelStatusCode
                )
                if ok2:
                    shutil.copyfile(filePath, pdbxArchivePath)

                # Regardless, kill WF
                status1 = killAllWF(idCode, "statMod")
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() killallwf returns %r\n" % status1)

                ok3 = sU.dbLoad(filePath)
                if self._verbose:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() data file status update completed %r\n" % ok3)
                if ok2 and ok3:
                    du.fetchId(idCode, "model", formatType="pdbx")
                    aTagList.append(du.getAnchorTag())
                    rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                    rC.setStatus(statusMsg="Status updated")
                    rC.set("statuscode", statusCode)
                    #
                    # Update internal context for return to client
                    myD = {}
                    if hasPdb:
                        myD["statuscode"] = statusCode
                    if hasEM:
                        myD["em_current_status"] = statusD["em_current_status"]
                    myD["approval_type"] = approvalType
                    myD["initialdepositdate"] = orgInitialDepositionDate
                    myD["postrelstatuscode"] = postRelStatusCode
                    myD["emdb_id"] = emdbId

                    for k, v in myD.items():
                        rC.set(k, v)
                    self._saveSessionParameter(pvD=myD)
                    try:
                        okShLoad = False
                        shu = StatusHistoryUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                        okShUpdate = shu.updateEntryStatusHistory(
                            entryIdList=[idCode], statusCode=statusCode, annotatorInitials=annotatorInitials, details="Update by status module", statusCodePrior=orgStatusCode
                        )
                        if self._verbose:
                            self._lfh.write(
                                "+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history file update status %r newHistoryFile %r\n" % (idCode, okShUpdate, newHistoryFile)
                            )
                        if okShUpdate or newHistoryFile:
                            okShLoad = shu.loadEntryStatusHistory(entryIdList=[idCode])
                        if self._verbose:
                            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history database load status %r\n" % (idCode, okShLoad))
                    except:  # noqa: E722 pylint: disable=bare-except
                        if self._verbose:
                            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history update and database load failed with exception\n")
                            traceback.print_exc(file=self._lfh)
                    #
                else:
                    rC.setError(errMsg="Data file status update failed.")
                    if ok1 or ok1a:
                        okRb = sU.wfRollBack(idCode=idCode)
                        if not okRb:
                            rC.setError(errMsg="Data file status update failed and workflow status roll back failed.")
                        else:
                            rC.setError(errMsg="Data file status update failed and workflow status rolled back.")
            else:
                rC.setError(errMsg="WF status database update failed.")
                return rC

            # If no errors and EM - check header
            if ok1 and ok1a and ok2 and ok3 and hasEM:
                self._lfh.write("About to do xml header\n")
                emdFilePath = du.getFilePath(idCode, contentType="model-emd", formatType="pdbx", fileSource="session-download", versionId="latest")
                emdbLogPath = os.path.join(self._sessionPath, "cif2emdbxml.log")
                emdbFilePath = du.getFilePath(idCode, contentType="em-volume-header", formatType="xml", fileSource="session", versionId="latest")
                #
                # Clear out existing log file - so we get new errors only - not repeats
                if os.path.exists(emdbLogPath):
                    os.remove(emdbLogPath)
                #
                # Create emd flavored file - no title suppression
                headerFilters = []

                emhu = EmHeaderUtils(siteId=self._siteId, verbose=self._verbose, log=self._lfh)

                mPath = filePath
                emdfile = False
                if hasattr(emhu, "transEmd"):
                    emhu.transEmd(filePath, emdFilePath, tags=headerFilters)
                    mPath = emdFilePath
                    emdfile = True

                #
                # Create XML file
                ok3c = emhu.transHeader(mPath, emdbFilePath, emdbLogPath)
                #
                if emdfile:
                    du.copyToDownload(emdFilePath)
                    aTagList.append(du.getAnchorTag())

                ok5 = False
                if ok3c and os.access(emdbFilePath, os.R_OK):
                    du.copyToDownload(emdbFilePath)
                    aTagList.append(du.getAnchorTag())
                    ok5 = True
                    #
                else:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateEmOp() NO HEADER FILE CREATED %s" % emdbFilePath)
                #
                du.copyToDownload(emdbLogPath)
                aTagList.append(du.getAnchorTag())
                #
                #
                #
                rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ", ".join(aTagList))
                htmlText = self.__getFileTextWithMarkup(emdbLogPath)
                rC.setHtmlText(htmlText)

                if ok5:
                    rC.setStatus(statusMsg="Status updated - header file produced")
                else:
                    rC.setError(errMsg="Status updated - no header file produced")

        else:
            rC.setError(errMsg="Status update failed, data file cannot be accessed.")
            # do nothing

        return rC

    #

    def __getFileTextWithMarkup(self, downloadPath):
        """Internal methods used by _makeCheckReports()"""
        try:
            oL = []
            ifh = open(downloadPath, "r")
            oL.append('<div class="highlight">')
            oL.append("<pre>")
            oL.append(ifh.read())
            oL.append("</pre>")
            oL.append("</div>")
            ifh.close()
            return "\n".join(oL)
        except:  # noqa: E722 pylint: disable=bare-except
            if self._verbose:
                self._lfh.write("+ReviewDataWebApp.__getFileTextWithMarkup() - failed to read  %s\n" % downloadPath)
                traceback.print_exc(file=self._lfh)
        return ""
