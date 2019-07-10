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
import datetime
from dateutil.relativedelta import *
#
from wwpdb.apps.ann_tasks_v2.webapp.CommonTasksWebAppWorker import CommonTasksWebAppWorker
from wwpdb.apps.ann_tasks_v2.report.PdbxReport import PdbxReport
from wwpdb.apps.ann_tasks_v2.utils.SessionDownloadUtils import SessionDownloadUtils
from wwpdb.apps.ann_tasks_v2.status.StatusUpdate import StatusUpdate
from wwpdb.utils.db.StatusHistoryUtils import StatusHistoryUtils
from wwpdb.apps.ann_tasks_v2.utils.MergeXyz import MergeXyz

from wwpdb.apps.ann_tasks_v2.em3d.EmHeaderUtils import EmHeaderUtils

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.utils.dp.DataFileAdapter import DataFileAdapter
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.utils.session.WebUploadUtils import WebUploadUtils
from wwpdb.utils.session.WebRequest import ResponseContent
#
from wwpdb.apps.wf_engine.engine.WFEapplications import killAllWF

import logging
# Create logger
logger = logging.getLogger()
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] [%(module)s.%(funcName)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

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
        self._appPathD = {'/service/environment/dump': '_dumpOp',
                          '/service/status_update_tasks_v2/entryinfo': '_entryInfoOp',
                          '/service/status_update_tasks_v2/newsession': '_newSessionOp',
                          '/service/status_update_tasks_v2/start': '_startOp',
                          #
                          '/service/status_update_tasks_v2/set_idcode': '_setIdCodeFetchModelOp',
                          '/service/status_update_tasks_v2/status_code_update': '_statusCodeUpdateOp',
                          '/service/status_update_tasks_v2/status_reload': '_statusReloadOp',
                          '/service/status_update_tasks_v2/inline_fileops': '_statusInlineFileOps',
                          '/service/status_update_tasks_v2/misc_reports': '_idReportOps',
                          '/service/status_update_tasks_v2/create_files': '_createFileOps',
                          '/service/status_update_tasks_v2/mergexyzcalc': '_mergeXyzCalcAltOp',
                          '/service/status_update_tasks_v2/process_site_update': '_statusProcessSiteUpdateOp',
                          '/service/status_update_tasks_v2/set_idcode_em': '_setIdCodeFetchEmOp',
                          '/service/status_update_tasks_v2/status_code_update_em': '_statusCodeUpdateEmOp',
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
            if inpReqPath.startswith('/service/status_update_tasks/report/d_'):
                rFields = inpReqPath.split('/')
                self._reqObj.setValue('idcode', rFields[4].upper())
                reqPath = "/service/status_update_tasks/report"
            else:
                reqPath = inpReqPath
            #
            if reqPath not in self._appPathD:
                # bail out if operation is unknown -
                rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                rC.setError(errMsg='Unknown operation')
            else:
                mth = getattr(self, self._appPathD[reqPath], None)
                rC = mth()
            return rC
        except:
            traceback.print_exc(file=self._lfh)
            rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            rC.setError(errMsg='Operation failure')
            return rC

    def _dumpOp(self):
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setHtmlList(self._reqObj.dump(format='html'))
        return rC

    def _startOp(self):
        """ Entry point to launch UI from WF or URL starting point  --
        """
        identifier = self._reqObj.getValue('identifier')
        fileSource = self._reqObj.getValue('filesource')
        skipStatus = self._reqObj.getValue('skipstatus')
        #        annotatorId = self._reqObj.getValue('annotator')
        #
        if (self._verbose):
            self._lfh.write("\n+%s.%s starting with identifier %s and filesource %s status flag %r \n" %
                            (self.__class__.__name__, sys._getframe().f_code.co_name, identifier, fileSource, skipStatus))

        return self.__makeStartOpResponse(identifier, contentType='model', formatType='pdbx')

    def __makeStartOpResponse(self, identifier, contentType, formatType='pdbx'):
        """ Worker method for UI launch point -
        """
        self._getSession()
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        statusCode = ''
        authRelCode = ''
        annotatorId = ''
        postRelStatusCode = ''
        if du.fetchId(identifier, contentType, formatType=formatType):
            aTagList.append(du.getAnchorTag())
            fP = du.getDownloadPath()

            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            sUD = sU.getV2(fP)
            pdbId = sUD['pdb_id']
            emdbId = sUD['emdb_id']
            annotatorId = sUD['annotatorInitials']
            statusCode = sUD['statusCode']
            authRelCode = sUD['authReleaseCode']
            initialDepositDate = sUD['initialDepositionDate']
            coordinatesDate = sUD['coordinatesDate']
            holdCoordinatesDate = sUD['holdCoordinatesDate']
            reqAccTypes = sUD['reqAccTypes']
            postRelStatusCode = sUD['postRelStatus']

            if (self._verbose):
                self._lfh.write("\n+%s.%s starting with identifier %s statusCode %r authRelCode %r annotatorId %r\n" %
                                (self.__class__.__name__, sys._getframe().f_code.co_name, identifier, statusCode, authRelCode, annotatorId))

        # Prepare the Startup data items
        myD = {}
        myD['entryid'] = identifier
        myD['sessionid'] = self._sessionId
        myD['annotatorid'] = annotatorId
        myD['statuscode'] = statusCode
        myD['postrelstatuscode'] = postRelStatusCode
        myD['authrelcode'] = authRelCode
        #
        #  Insert these dates into the page as global context values --
        #
        myD['initialdepositdate'] = initialDepositDate
        myD['holdcoordinatesdate'] = holdCoordinatesDate
        myD['coordinatesdate'] = coordinatesDate
        #
        myD['emdbid'] = emdbId
        myD['pdbid'] = pdbId
        # Requested accession codes. Legacy entries do not have this.
        myD['reqacctypes'] = reqAccTypes 
        logger.debug('reqacctypes is %r' % reqAccTypes)

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('html')
        if ((pdbId is not None) and (len(pdbId) > 3)):
            templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "status_admin.html")
        elif ((emdbId is not None) and (len(emdbId) > 3)):
            templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "status_admin_em.html")
        else:
            templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "status_admin.html")
        webIncludePath = os.path.join(self._reqObj.getValue("TopPath"), "htdocs")
        rC.setHtmlTextFromTemplate(templateFilePath=templateFilePath, webIncludePath=webIncludePath, parameterDict=myD, insertContext=True)
        if self.__debug:
            self._lfh.write("\n+%s.%s dump response\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
            rC.dump()
        return rC
    #
    # ---------------------------------------------------------------------------------------------------
    #                      Status and check report options implementing JSON responses -
    #

    def _setIdCodeFetchModelOp(self):
        """ Set the active data set identifier - and fetch the associated model file -
        """
        idCode = self._reqObj.getValue('idcode')
        if (self._verbose):
            self._lfh.write("+CommonWebAppWorker._setIdCodeFetchModelOp() starting with idCode %s\n" % idCode)

        return self._makeIdFetchResponse(idCode, contentType='model', formatType='pdbx')

    def _idReportOps(self):
        """ Operations on data files identified by id and type.
        """
        operation = self._reqObj.getValue('operation')
        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._reviewDataInlineIdOps() starting with op %s\n" % operation)

        idCodes = self._reqObj.getValue('idcode')
        idCodeList = idCodes.split(' ')
        contentType = self._reqObj.getValue('contentType')

        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._reviewDataInlineIdOps() content %s fetch id(s) %r\n" % (contentType, idCodeList))
        #
        if (operation == "fetch_entry"):
            return self.__makeIdListFetchResponse(idCodeList, contentType='model', formatType='pdbx')
        elif (operation == "fetch_sf"):
            return self.__makeIdListFetchResponse(idCodeList, contentType='structure-factors', formatType='pdbx')
        elif (operation == "report"):
            return self.__makeIdListReportResponse(idCodeList, contentType)
        elif (operation in ['check', 'checkv4', 'checkNext']):
            return self.__makeIdListCheckResponse(idCodeList, contentType, operation=operation)
        else:
            pass

    def __makeIdListReportResponse(self, idCodeList, contentType='model', formatType='pdbx'):
        """  Prepare response for a report request for the input Id code list.
        """
        self._getSession()

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('json')
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        htmlList = []
        # layout='tabs'
        # layout='accordion'
        layout = 'multiaccordion'
        pR = PdbxReport(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        for idCode in idCodeList:
            ok = du.fetchId(idCode, contentType, formatType=formatType)
            if not ok:
                continue
            downloadPath = du.getDownloadPath()
            aTagList.append(du.getAnchorTag())
            htmlList.extend(pR.makeTabularReport(filePath=downloadPath, contentType=contentType, idCode=idCode, layout=layout))

        if len(aTagList) > 0:
            rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ','.join(aTagList))
            rC.setHtmlList(htmlList)
            rC.setStatus(statusMsg="Reports completed")
        else:
            rC.setError(errMsg='No corresponding data file(s)')
            # do nothing

        return rC

    def __makeIdListCheckResponse(self, idCodeList, contentType, operation='check', formatType='pdbx'):
        """  Prepare response for a check request for the input Id code list.
        """
        self._getSession()
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('json')
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        htmlList = []
        # fileFormat='cif'
        # layout='tabs'
        # layout='accordion'
        # layout='multiaccordion'

        for idCode in idCodeList:
            ok = du.fetchId(idCode, contentType, formatType=formatType)
            if not ok:
                continue

            if (operation in ['check', 'checkv4']):
                filePath = du.getDownloadPath()
                if operation in ['checkv4']:
                    logPath = os.path.join(self._sessionPath, idCode + '-check-v4.log')
                else:
                    logPath = os.path.join(self._sessionPath, idCode + '-check.log')
                hasDiags = self.__makeCifCheckReport(filePath, logPath, op=operation)
                if hasDiags:
                    duL = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
                    duL.copyToDownload(logPath)
                    aTagList.append(duL.getAnchorTag())
                    rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ','.join(aTagList))
                    rC.setStatus(statusMsg="Check completed")
                else:
                    rC.setStatus(statusMsg="No diagnostics for %s" % idCode)

        if len(aTagList) > 0:
            rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ','.join(aTagList))
            rC.setHtmlList(htmlList)
            rC.setStatus(statusMsg="Check report completed")
        else:
            rC.setError(errMsg='Check completed - no diagnostics')
            # do nothing

        return rC

    def __makeCifCheckReport(self, filePath, logPath, op='check'):
        """ Create CIF dictionary check on the input file and return diagnostics in logPath.

            Return True if a report is created (logPath exists and has non-zero size)
                or False otherwise
        """
        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker.__makeCifCheckReport() with site %s for file %s\n" % (self._siteId, filePath))
        dp = RcsbDpUtility(tmpPath=self._sessionPath, siteId=self._siteId, verbose=self._verbose, log=self._lfh)
        dp.imp(filePath)
        if op in ['check', 'updatewithcheck']:
            dp.op("check-cif")
        elif op in ['checkv4']:
            dp.op("check-cif-v4")
        else:
            # do something -
            dp.opt('check-cif')

        dp.exp(logPath)
        if (not self.__debug):
            dp.cleanup()
        #
        if os.access(logPath, os.R_OK) and os.stat(logPath).st_size > 0:
            return True
        else:
            return False

    # --------------------------------------------------------------------------------------------------------------------------------
    #                      File production options implementing JSON responses -
    #
    #
    def _createFileOps(self):
        """ Operations on data files identified by id and type.
        """
        self._getSession()
        operation = self._reqObj.getValue('operation')
        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._createFileOps() starting with op %s\n" % operation)

        idCode = self._reqObj.getValue('idcode')
        contentType = 'model'
        formatType = 'pdbx'
        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._createFileOps() content %s id %s\n" % (contentType, idCode))

        aTagList = []
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('json')
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            webPath = du.getWebDownloadPath()
            #
            #
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

            if (operation == "pdb"):
                pdbArchivePath = pI.getModelPdbFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
                pdbFileName = pI.getFileName(
                    dataSetId=idCode,
                    wfInstanceId=None,
                    contentType='model',
                    formatType='pdb',
                    fileSource="archive",
                    versionId="next",
                    partNumber='1',
                    mileStone=None)
                dfa = DataFileAdapter(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                dfa.cif2Pdb(filePath, pdbArchivePath)
                du.fetchId(idCode, 'model', formatType='pdb')
                aTagList.append(du.getAnchorTag())
                rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ','.join(aTagList))
                rC.setStatus(statusMsg="PDB format file created")
            elif (operation == "pdbx"):
                pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone='review')
                pdbxFileName = pI.getFileName(
                    dataSetId=idCode,
                    wfInstanceId=None,
                    contentType='model',
                    formatType='pdbx',
                    fileSource="archive",
                    versionId="next",
                    partNumber='1',
                    mileStone='review')
                dfa = DataFileAdapter(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                dfa.cif2Pdbx(filePath, pdbxArchivePath)
                du.fetchId(idCode, 'model', formatType='pdbx', mileStone='review')
                aTagList.append(du.getAnchorTag())
                rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ','.join(aTagList))
                rC.setStatus(statusMsg="PDBx format with public data subset file created")
            elif (operation == 'assembly'):
                archivePath = pI.getDirPath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", contentType='assembly-model', formatType='pdbx')
                downloadPath = os.path.join(self._sessionPath, "downloads")
                dfa = DataFileAdapter(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                indexFilePath = os.path.join(self._sessionPath, 'assembly-index.txt')
                dfa.pdbx2Assemblies(idCode, filePath, archivePath, indexFilePath=indexFilePath)
                fCount = 0
                try:
                    ifh = open(indexFilePath, 'r')
                    for line in ifh:
                        fCount += 1
                        fp = os.path.join(archivePath, line[:-1])
                        du.copyToDownload(fp)
                        aTagList.append(du.getAnchorTag())
                    ifh.close()
                except:
                    pass
                #
                if fCount > 0:
                    rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ','.join(aTagList))
                    rC.setStatus(statusMsg="Assembly files created")
                else:
                    rC.setStatus(statusMsg="No assembly files created")
            else:
                pass
        else:
            rC.setError(errMsg='File creation failed.')
            # do nothing

        return rC

    # --------------------------------------------------------------------------------------------------------------------------------
    #                      File production options implementing JSON responses -
    #
    #
    def _statusCodeUpdateOp(self):
        """ Status code updates on data files identified by id and type.
        """
        self._getSession(useContext=True)

        idCode = self._reqObj.getValue('idcode')
        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() starting with idCode %s\n" % idCode)
        contentType = 'model'
        formatType = 'pdbx'
        newHistoryFile = False

        # Values from the input form --
        #
        statusCode = self._reqObj.getValue('status-code')
        postRelStatusCode = self._reqObj.getValue('postrel-status-code')
        approvalType = self._reqObj.getValue('approval-type')
        annotatorInitials = self._reqObj.getValue('annotator-initials')
        authStatusHoldDate = self._reqObj.getValue('auth-status-hold-date')
        authStatusCode = self._reqObj.getValue('auth-status-code')
        processSite = self._reqObj.getValue('process-site')
        #
        #  Values from the current version of the model file --
        #
        orgStatusCode = self._reqObj.getValue('statuscode')
        orgPostRelStatusCode = self._reqObj.getValue('postrelstatuscode')
        orgInitialDepositionDate = self._reqObj.getValue('initialdepositdate')
        orgHoldCoordinatesDate = self._reqObj.getValue('holdcoordinatesdate')
        orgCoordinatesDate = self._reqObj.getValue('coordinatesdate')
        orgAuthRelCode = self._reqObj.getValue('authrelcode')
        expMethods = self._reqObj.getValue('experimental_methods')
        #
        # For already released entries, statusCode will be '', but orgStatusCode will = 'REL'
        logger.info("Status code change: statuscode %s -> %s, postrel %s -> %s" % (orgStatusCode, statusCode, 
                                                                                   orgPostRelStatusCode, postRelStatusCode))
        #
        try:
            #   Update status history - first create a new history file if required.
            shu = StatusHistoryUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
            if statusCode in ['AUTH', 'WAIT']:
                rL = shu.createHistory([idCode], overWrite=False, statusUpdateAuthWait=statusCode)
            else:
                rL = shu.createHistory([idCode], overWrite=False)
            if len(rL) > 0:
                if (self._verbose):
                    newHistoryFile = True
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s new status history file created\n" % idCode)
        except:
            if (self._verbose):
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history file create failed with exception\n" % idCode)
                traceback.print_exc(file=self._lfh)
        #
        msg = 'ok'
        # Test if any conditions are violated
        #

        if ((str(statusCode).upper() == 'HPUB') and (str(authStatusCode).upper() == 'HOLD')):
            # ((str(statusCode).upper() == 'HOLD') and (str(authStatusCode).upper() == 'HPUB')):
            msg = 'Processing status code and author release status are inconsistent'

        if ((str(orgStatusCode).upper() == 'PROC') and (str(statusCode).upper() in ['HPUB', 'HOLD'])):
            msg = 'Processing status code change from PROC to HPUB or HOLD prohibited'

        if str(orgStatusCode).upper() =='REL':
            if len(orgPostRelStatusCode) == 0:
                msg = 'Processing status code change from REL prohibited'
            else:
                # Web form does not set in this case
                statusCode='REL'

        if str(orgStatusCode).upper() =='OBS':
            msg = 'Processing status code change from OBS prohibited'

        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpateOp() id %s check status message is: %s\n" % (idCode, msg))
        #

        aTagList = []
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('json')
        #
        if msg != 'ok':
            rC.setError(errMsg=msg)
            return rC

        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            webPath = du.getWebDownloadPath()
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

            pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
            pdbxFileName = pI.getFileName(dataSetId=idCode, wfInstanceId=None, contentType='model', formatType='pdbx',
                                          fileSource="archive", versionId="next", partNumber='1', mileStone=None)
            if (self._verbose):
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() model input path %s model archive output path %s\n" %
                                (filePath, pdbxArchivePath))

            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            ok1 = sU.wfLoad(idCode, statusCode, annotatorInitials=annotatorInitials, initialDepositionDate=orgInitialDepositionDate, authRelCode=authStatusCode, \
                            postRelStatusCode=postRelStatusCode)
            if (self._verbose):
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() wf load completed %r\n" % ok1)
            if ok1:
                ok2 = sU.set(filePath, filePath, statusCode, approvalType, annotatorInitials, authStatusCode, authStatusHoldDate, expMethods, processSite, 
                             postRelStatusCode=postRelStatusCode)
                if ok2:
                    shutil.copyfile(filePath, pdbxArchivePath)

                status1 = killAllWF(idCode, 'statMod')
                if (self._verbose):
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() killallwf returns %r\n" % status1)

                ok3 = sU.dbLoad(filePath)
                if (self._verbose):
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() data file status update completed %r\n" % ok3)
                if ok2 & ok3:
                    du.fetchId(idCode, 'model', formatType='pdbx')
                    aTagList.append(du.getAnchorTag())
                    rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ','.join(aTagList))
                    rC.setStatus(statusMsg="Status updated")
                    rC.set("statuscode", statusCode)
                    #
                    myD = {}
                    myD['statuscode'] = statusCode
                    myD['authrelcode'] = authStatusCode
                    myD['holdcoordinatesdate'] = authStatusHoldDate
                    myD['approval_type'] = approvalType
                    myD['process_site'] = processSite
                    myD['annotator_initials'] = annotatorInitials
                    myD['initialdepositdate'] = orgInitialDepositionDate
                    myD['postrelstatuscode'] = postRelStatusCode

                    for k, v in myD.items():
                        rC.set(k, v)
                    self._saveSessionParameter(pvD=myD)
                    try:
                        okShLoad = False
                        shu = StatusHistoryUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                        okShUpdate = shu.updateEntryStatusHistory(
                            entryIdList=[idCode],
                            statusCode=statusCode,
                            annotatorInitials=annotatorInitials,
                            details="Update by status module",
                            statusCodePrior=orgStatusCode)
                        if (self._verbose):
                            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history file update status %r newHistoryFile %r\n" % (idCode, okShUpdate, newHistoryFile))
                        if okShUpdate or newHistoryFile:
                            okShLoad = shu.loadEntryStatusHistory(entryIdList=[idCode])
                        if (self._verbose):
                            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history database load status %r\n" % (idCode, okShLoad))
                    except:
                        if (self._verbose):
                            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOp() %s status history update and database load failed with exception\n")
                            traceback.print_exc(file=self._lfh)
                    #
                else:
                    rC.setError(errMsg='Data file status update failed.')
                    if ok1:
                        okRb = sU.wfRollBack(idCode=idCode)
                        if not okRb:
                            rC.setError(errMsg='Data file status update failed and workflow status roll back failed.')
                        else:
                            rC.setError(errMsg='Data file status update failed and workflow status rolled back.')
            else:
                rC.setError(errMsg='WF status database update failed.')
        else:
            rC.setError(errMsg='Status update failed, data file cannot be accessed.')
            # do nothing

        return rC
    #

    def _statusReloadOp(self):
        """ Status data reload/updates on data files identified by id.
        """
        self._getSession(useContext=True)

        idCode = self._reqObj.getValue('idcode')
        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._statusReloadOp() starting with idCode %s\n" % idCode)
        contentType = 'model'
        formatType = 'pdbx'
        #
        #  Values from the current version of the model file --
        #
        orgStatusCode = self._reqObj.getValue('statuscode')
        orgInitialDepositionDate = self._reqObj.getValue('initialdepositdate')
        orgHoldCoordinatesDate = self._reqObj.getValue('holdcoordinatesdate')
        orgCoordinatesDate = self._reqObj.getValue('coordinatesdate')
        orgAuthRelCode = self._reqObj.getValue('authrelcode')
        expMethods = self._reqObj.getValue('experimental_methods')
        annotatorInitials = self._reqObj.getValue('annotator_initials')
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('json')

        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            ok1 = sU.wfLoad(idCode, orgStatusCode, annotatorInitials=annotatorInitials, initialDepositionDate=orgInitialDepositionDate, authRelCode=orgAuthRelCode)
            if (self._verbose):
                self._lfh.write("+StatusUpdateWebAppWorker._statusReloadOp() wf load completed %r\n" % ok1)
            if ok1:

                status1 = killAllWF(idCode, 'statMod')
                if (self._verbose):
                    self._lfh.write("+StatusUpdateWebAppWorker._statusReloadOp() killallwf returns %r\n" % status1)

                ok2 = sU.dbLoad(filePath)
                if (self._verbose):
                    self._lfh.write("+StatusUpdateWebAppWorker._statusReloadOp() data file status update completed %r\n" % ok2)
                if ok1 & ok2:
                    rC.setStatus(statusMsg="Status updated using current contents of model file")
                else:
                    rC.setError(errMsg='Data file status update failed.')

            else:
                rC.setError(errMsg='WF status database update failed.')
        else:
            rC.setError(errMsg='Status update failed, data file cannot be accessed.')
            # do nothing

        return rC
    #

    def _mergeXyzCalcAltOp(self):
        """  Alternative merge coordinate operation
        """
        if (self._verbose):
            self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcAltOp() starting\n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")

        # get a copy of the current model -
        de = DataExchange(reqObj=self._reqObj, depDataSetId=entryId, fileSource="wf-archive", verbose=self._verbose, log=self._lfh)
        pth = de.copyToSession(contentType="model", formatType="pdbx", version="latest", partitionNumber=1)
        (dn, fileName) = os.path.split(pth)

        taskFormId = self._reqObj.getValue("taskformid")
        taskArgs = ''

        # merge file format
        xyzFileFormat = self._reqObj.getValue("xyzfileformat")
        #
        #
        wuu = WebUploadUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        xyzFileName = wuu.copyToSession(fileTag='xyzfilename')

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('json')
        #
        calc = MergeXyz(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if xyzFileName is not None and len(xyzFileName) > 0:
            calc.setReplacementXyzFile(xyzFileName, format=xyzFileFormat)
            self._saveSessionParameter(param="xyzfilename", value=xyzFileName, prefix=entryId)

            ok = calc.run(entryId, fileName)
            if (self._verbose):
                self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcAltOp() status %r\n" % ok)
            if (ok):
                #
                # copy the file back --
                #
                pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
                pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=entryId, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
                shutil.copyfile(pth, pdbxArchivePath)
                if (self._verbose):
                    self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcAltOp() updating model file in %s\n" % pdbxArchivePath)
                rC.setStatus(statusMsg="Merge completed and model updated.")
            else:
                rC.setError(errMsg='Merge failed.')
        else:
            ok = False
            rC.setError(errMsg='Merge failed.')
            if (self._verbose):
                self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcOp() no merge file provided\n")
        #
        aTagList = calc.getAnchorTagList(label=None, target='_blank', cssClass='')
        rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ','.join(aTagList))
        #

        return rC

    def _statusProcessSiteUpdateOp(self):
        """ Status  - processs site update and reload based on current annotator assignment --  Fixes mis-assigned process site --
        """
        self._getSession(useContext=True)

        idCode = self._reqObj.getValue('idcode')
        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._statusProcessSiteUpdateOp() starting with idCode %s\n" % idCode)
        contentType = 'model'
        formatType = 'pdbx'

        annotatorInitials = self._reqObj.getValue('annotator_initials')
        processSite = self._reqObj.getValue('process_site')
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('json')
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
            pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
            if (self._verbose):
                self._lfh.write("+StatusUpdateWebAppWorker._statusProcessSiteUpdateOp() model input path %s model archive output path %s\n" %
                                (filePath, pdbxArchivePath))
            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            tSite = sU.assignProcessSite(annotatorInitials)
            if tSite != processSite:
                ok1 = sU.setProcessSite(filePath, filePath, tSite)
                if ok1:
                    shutil.copyfile(filePath, pdbxArchivePath)

                    status1 = killAllWF(idCode, 'statMod')
                    if (self._verbose):
                        self._lfh.write("+StatusUpdateWebAppWorker._statusProcessSiteUpdateOp() killallwf returns %r\n" % status1)

                    ok2 = sU.dbLoad(filePath)
                    if (self._verbose):
                        self._lfh.write("+StatusUpdateWebAppWorker._statusProcessSiteUpdateOp() data file status update completed %r\n" % ok2)
                    if ok1 & ok2:
                        rC.setStatus(statusMsg="Process site updated and reloaded")
                    else:
                        rC.setError(errMsg='Process site update and reload failed.')

                else:
                    rC.setError(errMsg='Process site update failed.')
            else:
                rC.setError(errMsg='Process site update and reload not performed, no change required.')
                # do nothing
        else:
            rC.setError(errMsg='Process site update failed, data file cannot be accessed.')

        return rC


# ---------------------------------------------------------------------------------------------------------
#                                     EM --  entry points  --
#
    def _setIdCodeFetchEmOp(self):
        """ Set the active data set identifier - and fetch the associated EM data file  -
        """
        idCode = self._reqObj.getValue('idcode')
        if (self._verbose):
            self._lfh.write("+CommonWebAppWorker._setIdCodeFetchEmOp() starting with idCode %s\n" % idCode)

        return self._makeIdFetchResponse(idCode, contentType='model', formatType='pdbx')

    def __getHeaderReleaseDate(self):
        """
        Return the date 'yyyy-mm-dd' of the next release date (Wednesday) subject to the policy cutoff date.

        Compute the reference delta - Friday 14:30 GMT to next Wed 00:00 GMT

        """
        #
        #
        try:
            todayUTC = datetime.datetime.utcnow()
            nxtFriR = todayUTC + relativedelta(days=+1, weekday=FR(+1))
            nxtWedR = nxtFriR + relativedelta(days=+1, weekday=WE(+1))
            off1 = datetime.datetime(nxtWedR.year, nxtWedR.month, nxtWedR.day, 0, 0, 1)
            off2 = datetime.datetime(nxtFriR.year, nxtFriR.month, nxtFriR.day, 14, 30, 0)
            diffRef = (off1 - off2).total_seconds()
            # ------------------------------------
            todayUTC = datetime.datetime.utcnow()
            nxtWed = todayUTC + relativedelta(days=+1, weekday=WE(+1))
            nxtWedS = datetime.datetime(nxtWed.year, nxtWed.month, nxtWed.day, 0, 0, 1)
            #
            diffTest = (nxtWedS - todayUTC).total_seconds()
            #
            if diffTest < diffRef:
                #
                trg = todayUTC + relativedelta(days=+1, weekday=WE(+2))
            else:
                trg = nxtWed
            #
            retDate = trg.strftime("%Y-%m-%d")
        except:
            traceback.print_exc(file=self._lfh)
            retDate = None

        return retDate

    def _statusCodeUpdateEmOp(self):
        """ EM Status code updates on data files identified by id.

            Update the contents of the em_admin data category -


            ('_em_admin.current_status', '%s', 'str', ''),
            ('_em_admin.deposition_date', '%s', 'str', ''),
            ('_em_admin.deposition_site', '%s', 'str', ''),
            ('_em_admin.details', '%s', 'str', ''),
            ('_em_admin.entry_id', '%s', 'str', ''),
            ('_em_admin.last_update', '%s', 'str', ''),
            ('_em_admin.map_release_date', '%s', 'str', ''),
            ('_em_admin.obsoleted_date', '%s', 'str', ''),
            ('_em_admin.replace_existing_entry_flag', '%s', 'str', ''),
            ('_em_admin.title', '%s', 'str', ''),

        """
        kyPairListEm = [('em_entry_id', 'em_entry_id'),
                        ('em_current_status', 'em_current_status'),
                        ('em_deposition_date', 'em_deposition_date'),
                        ('em_deposition_site', 'em_deposition_site'),
                        ('em_obsoleted_date', 'em_obsoleted_date'),
                        ('em_details', 'em_details'),
                        ('em_last_update', 'em_last_update'),
                        ('em_map_release_date', 'em_map_release_date'),
                        ('em_map_hold_date', 'em_map_hold_date'),
                        ('em_header_release_date', 'em_header_release_date'),
                        ('em_replace_existing_entry_flag', 'em_replace_existing_entry_flag'),
                        ('em_title', 'em_title')
                        ]
        self._getSession(useContext=True, overWrite=False)

        idCode = self._reqObj.getValue('idcode')
        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateEmOp() starting with idCode %s\n" % idCode)
        contentType = 'model'
        formatType = 'pdbx'
        #
        #     Values from the input form -- pdbx_database_status -
        #
        # statusCode = self._reqObj.getValue('status-code')
        # authStatusHoldDate = self._reqObj.getValue('auth-status-hold-date')
        # authStatusCode = self._reqObj.getValue('auth-status-code')
        #
        processSite = self._reqObj.getValue('process-site')
        approvalType = self._reqObj.getValue('approval-type')
        annotatorInitials = self._reqObj.getValue('annotator-initials')
        statusD = {}
        emdbId = self._reqObj.getValue('emdb_id')
        releaseHeader = False
        for kyPair in kyPairListEm:
            statusD[kyPair[0]] = self._reqObj.getValue(kyPair[0])
        #
        # Update header_release_date if it is not set and status_code = HOLD|HPUB
        # Last update is updated everytime the header is released.
        #
        if (('em_current_status' in statusD) and (statusD['em_current_status'] in ['HOLD', 'HPUB'])):
            releaseHeader = True
            if ((statusD['em_header_release_date'] is not None) and (len(statusD['em_header_release_date']) > 1)):
                pass
            else:
                statusD['em_header_release_date'] = self.__getHeaderReleaseDate()
            # Always update last_update
            statusD['em_last_update'] = self.__getHeaderReleaseDate()

        #
        if (self._verbose):
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOpEm() releaseHeader %r\n" % releaseHeader)
            self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOpEm() statusD %r\n" % statusD.items())
        #
        #  Values from the current version of the model file --
        #
        # orgStatusCode = self._reqObj.getValue('statuscode')
        # orgInitialDepositionDate = self._reqObj.getValue('initialdepositdate')
        # orgHoldCoordinatesDate = self._reqObj.getValue('holdcoordinatesdate')
        # orgCoordinatesDate = self._reqObj.getValue('coordinatesdate')
        # orgAuthRelCode = self._reqObj.getValue('authrelcode')
        # expMethods = self._reqObj.getValue('experimental_methods')
        #
        msg = 'ok'
        ok4 = False
        ok5 = False
        # Test if any conditions are violated
        #

        aTagList = []
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('json')
        #
        if msg != 'ok':
            rC.setError(errMsg=msg)
            return rC

        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = du.fetchId(idCode, contentType, formatType=formatType)
        if ok:
            # target input model file -
            filePath = du.getDownloadPath()
            # webPath = du.getWebDownloadPath()
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

            pdbxArchivePath = pI.getModelPdbxFilePath(dataSetId=idCode, wfInstanceId=None, fileSource="archive", versionId="next", mileStone=None)
            # pdbxFileName = pI.getFileName(dataSetId=idCode, wfInstanceId=None, contentType='model', formatType='pdbx',
            #                              fileSource="archive", versionId="next", partNumber='1', mileStone=None)
            if (self._verbose):
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOpEm() model input path %s model archive output path %s\n" %
                                (filePath, pdbxArchivePath))

            sU = StatusUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

            # Determine if title suppression in effect
            sUD = sU.getV2(filePath)
            modTitleSupp = sUD['titleSupp']

            headerFilters = []
            if modTitleSupp == 'Y' and releaseHeader:
                # Release header in this code only happens for HPUB/HOLD
                headerFilters = ['all', 'prereleasetitle']

            if (self._verbose):
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateOpEm() title suppression is %s with filters %s\n" %
                                (modTitleSupp, headerFilters))


            # ok1 = sU.wfLoad(idCode, statusCode, annotatorInitials=annotatorInitials, initialDepositionDate=orgInitialDepositionDate, authRelCode=authStatusCode)
            # if (self._verbose):
            #    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateEmOp() wf load completed %r\n" % ok1)
            # if ok1:
            #
            # ok2 = sU.set(filePath, filePath, statusCode, approvalType, annotatorInitials, authStatusCode, authStatusHoldDate, expMethods, processSite)
            #
            ok2 = sU.setEmStatusDetails(filePath, filePath, statusD, processSite, annotatorInitials, approvalType)
            if ok2:
                shutil.copyfile(filePath, pdbxArchivePath)
            ok3 = sU.dbLoad(filePath)
            # load status.deposition --

            if (self._verbose):
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateEmOp() database da_internal update completed %r\n" % ok3)

            #
            ok3a = sU.wfEmLoad(idCode, statusCode=statusD['em_current_status'], title=statusD['em_title'], annotatorInitials=annotatorInitials)
            if (self._verbose):
                self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateEmOp() database status.deposition update completed %r\n" % ok3a)

            if ok2 & ok3 & ok3a:
                du.fetchId(idCode, 'model', formatType='pdbx')
                aTagList.append(du.getAnchorTag())
                # rC.set("statuscode", statusCode)
                #
                # New  ---
                emdFilePath = du.getFilePath(idCode, contentType='model-emd', formatType='pdbx', fileSource='session-download', versionId='latest')
                emdbLogPath = os.path.join(self._sessionPath, 'cif2emdbxml.log')
                emdbFilePath = du.getFilePath(idCode, contentType='em-volume-header', formatType='xml', fileSource='session', versionId='latest')
                # 
                # Clear out existing log file - so we get new errors only - not repeats
                if os.path.exists(emdbLogPath):
                    os.remove(emdbLogPath)
                #
                emhu = EmHeaderUtils(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
                emhu.transEmd(filePath, emdFilePath, tags=headerFilters)

                ok3c = emhu.transHeader(emdFilePath, emdbFilePath, emdbLogPath)
                #
                du.copyToDownload(emdFilePath)
                aTagList.append(du.getAnchorTag())
                if ok3c and os.access(emdbFilePath, os.R_OK):
                    du.copyToDownload(emdbFilePath)
                    aTagList.append(du.getAnchorTag())
                    ok5 = True
                    #
                    if (releaseHeader):
                        ok4 = emhu.releaseHeader(emdbFilePath, emdbId)
                        ok4a = emhu.releaseHeaderPdbx(emdFilePath, emdbId)
                else:
                    self._lfh.write("+StatusUpdateWebAppWorker._statusCodeUpdateEmOp() NO HEADER FILE CREATED %s" % emdbFilePath)
                #
                du.copyToDownload(emdbLogPath)
                aTagList.append(du.getAnchorTag())
                #
                #
                #
                rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ','.join(aTagList))
                htmlText = self.__getFileTextWithMarkup(emdbLogPath)
                rC.setHtmlText(htmlText)

                if ok4:
                    rC.setStatus(statusMsg="Status updated - header file released")
                else:
                    if ok5:
                        rC.setStatus(statusMsg="Status updated - header file produced")
                    else:
                        rC.setError(errMsg="Status updated - no header file produced")
                #
                myD = {}
                # myD['statuscode'] = statusCode
                # myD['authrelcode'] = authStatusCode
                # myD['holdcoordinatesdate'] = authStatusHoldDate
                myD['approval_type'] = approvalType
                myD['process_site'] = processSite
                myD['annotator_initials'] = annotatorInitials
                myD['emdb_id'] = emdbId
                myD.update(statusD)
                for k, v in myD.items():
                    rC.set(k, v)
                self._saveSessionParameter(pvD=myD)

            else:
                rC.setError(errMsg='Status update failed.')
                # if ok1:
                #    okRb = sU.wfRollBack(idCode=idCode)
                #    if not okRb:
                #        rC.setError(errMsg='Data file status update failed and workflow status roll back failed.')
                #    else:
                #        rC.setError(errMsg='Data file status update failed and workflow status rolled back.')
        else:
            rC.setError(errMsg='Status update failed, data file cannot be accessed.')
            # do nothing

        return rC
    #
    def __getFileTextWithMarkup(self, downloadPath):
        """  Internal methods used by _makeCheckReports()
        """
        try:
            oL = []
            ifh = open(downloadPath, 'r')
            oL.append('<div class="highlight">')
            oL.append('<pre>')
            oL.append(ifh.read())
            oL.append('</pre>')
            oL.append('</div>')
            ifh.close()
            return '\n'.join(oL)
        except:
            if (self._verbose):
                self._lfh.write("+ReviewDataWebApp.__getFileTextWithMarkup() - failed to read  %s\n" % downloadPath)
                traceback.print_exc(file=self._lfh)
        return ''
