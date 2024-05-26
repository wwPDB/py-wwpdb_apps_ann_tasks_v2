##
# File:  ReviewDataWebAppWorker.py
# Date:  22-Feb-2014
#
# Updates:
#   5-July-2104 jdw add download options
#  29-Nov-2016  ep   add support for checkNext in _updateAndReportFileOps (V5RC checking)
##
"""
Data review tool web request and response processing modules.

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

#
from wwpdb.apps.ann_tasks_v2.webapp.CommonTasksWebAppWorker import CommonTasksWebAppWorker

# from wwpdb.utils.rcsb.WebAppWorkerBase                        import WebAppWorkerBase

from wwpdb.apps.ann_tasks_v2.report.PdbxReport import PdbxReport
from wwpdb.apps.ann_tasks_v2.utils.SessionDownloadUtils import SessionDownloadUtils

#
from wwpdb.apps.ann_tasks_v2.check.Check import Check
from wwpdb.apps.ann_tasks_v2.check.ExtraCheck import ExtraCheck

# from wwpdb.apps.ann_tasks_v2.check.FormatCheck import FormatCheck
# from wwpdb.apps.ann_tasks_v2.check.GeometryCheck import GeometryCheck
# from wwpdb.apps.ann_tasks_v2.mapcalc.DccCalc import DccCalc


# from wwpdb.utils.config.ConfigInfo import ConfigInfo
# from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.utils.session.WebRequest import ResponseContent

#


class ReviewDataWebAppWorker(CommonTasksWebAppWorker):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        Worker methods for the review data module.

        Performs URL -> application mapping for this module.

        All operations can be driven from this interface which can
        supplied with control information from web application request
        or from a testing application.

        """
        super(ReviewDataWebAppWorker, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        # Service items include:
        #
        self._appPathD = {
            "/service/environment/dump": "_dumpOp",
            "/service/review_v2/newsession": "_newSessionOp",
            "/service/review_v2/entryinfo": "_entryInfoOp",
            "/service/review_v2/inline_idops": "_fetchAndReportIdOps",
            "/service/review_v2/inline_fileops": "_updateAndReportFileOps",
            "/service/review_v2/report": "_modelReportIdOp",
            "/service/review_v2/full_report": "_fullReportIdOp",
            "/service/review_v2/download_file": "_downloadResponderOp",
        }
        self.addServices(self._appPathD)
        #
        self.__topPath = self._reqObj.getValue("TopPath")
        self.__templatePath = os.path.join(self.__topPath, "htdocs", "review_v2")
        self._reqObj.setValue("TemplatePath", self.__templatePath)
        #

    def _dumpOp(self):
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setHtmlList(self._reqObj.dump(format="html"))
        return rC

    # ---------------------------------------------------------------------------------------------------
    #                            Various operations on upload files -
    #
    def _updateAndReportFileOps(self):
        """Review data operations on uploaded files. -

        Upload files of various content types -

        Check PDBx files against v4/5 dictionaries.

        Update the uploaded file as the next version of this content type in the archive directory
        """
        self._getSession()

        operation = self._reqObj.getValue("operation")
        if self._verbose:
            self._lfh.write("+ReviewDataWebAppWorker._updateAndReportFileOps() starting with op %s\n" % operation)

        isFile = False

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")

        contentType = contentFormat = partitionNumber = None
        if self._isFileUpload():
            # make a copy of the file in the session directory and set 'fileName'
            self._uploadFile()
            fileName = self._reqObj.getValue("fileName")
            filePath = os.path.join(self._sessionPath, fileName)
            (_rootName, _ext) = os.path.splitext(fileName)
            isFile = True
            #
            du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
            du.copyToDownload(filePath)
            idCode = du.getIdFromFileName(filePath)
            downloadPath = du.getDownloadPath()
            contentType = du.getContentTypeFromFileName(filePath)
            contentFormat = du.getContentFormatFromFileName(filePath)
            partitionNumber = du.getPartitionNumberFromFileName(filePath)
            # add entry id --
            rC.set("entryid", idCode)

        if self._verbose:
            self._lfh.write(
                "+ReviewDataWebAppWorker._updateAndReportFileOps() filePath %s idcode %r content type %r format %r partno %r\n"
                % (filePath, idCode, contentType, contentFormat, partitionNumber)
            )

        #
        aTagList = []
        htmlList = []
        hasDiags = False

        if not isFile or fileName is None or len(fileName) < 1:
            rC.setError(errMsg="File upload failed.")

        elif operation in ["report"]:
            #
            pR = PdbxReport(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            aTagList.append(du.getAnchorTag())
            downloadPath = du.getDownloadPath()
            layout = "multiaccordion"
            htmlList.extend(pR.makeTabularReport(filePath=downloadPath, contentType=contentType, idCode=idCode, layout=layout))
            if len(aTagList) > 0:
                rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                rC.setHtmlList(htmlList)
                rC.setStatus(statusMsg="Reports completed")
            else:
                rC.setError(errMsg="Report preparation failed")
            #
        elif operation in ["checkv5", "checkv4", "checkNext", "updatewithcheck"]:
            filePath = du.getDownloadPath()
            chk = Check(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            if operation in ["checkv4"]:
                chk.setDictionaryVersion(version="V4")
            elif operation in ["checkv5"]:
                chk.setDictionaryVersion(version="V5")
            elif operation in ["checkNext"]:
                chk.setDictionaryVersion(version="archive_next")

            # Dictionary check first data block only
            chk.setCheckFirstBlock(True)

            chk.run(entryId=idCode, inpPath=filePath)
            hasDiags = chk.getReportSize() > 0
            rptPath = chk.getReportPath()
            duL = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
            if hasDiags:
                duL.copyToDownload(rptPath)
                aTagList.append(duL.getAnchorTag())
                rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                rC.setStatus(statusMsg="Check completed")
            else:
                duL.removeFromDownload(rptPath)
                rC.setStatus(statusMsg="No diagnostics for %s" % fileName)
            #
        elif operation in ["check-misc"]:
            filePath = du.getDownloadPath()
            chk = ExtraCheck(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            chk.run(entryId=idCode, inpPath=filePath)
            hasDiags = chk.getReportSize() > 0
            rptPath = chk.getReportPath()
            duL = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
            if hasDiags:
                duL.copyToDownload(rptPath)
                aTagList.append(duL.getAnchorTag())
                rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                rC.setStatus(statusMsg="Check completed")
            else:
                duL.removeFromDownload(rptPath)
                rC.setStatus(statusMsg="No diagnostics for %s" % fileName)
            #
        #

        if hasDiags and operation in ["updatewithcheck"]:
            return rC

        if operation in ["update", "updatewithcheck"]:
            if (idCode is None) or (len(idCode) < 1) or (contentType is None) or (len(contentType) < 1) or (contentFormat is None) or (len(contentFormat) < 1):
                rC.setError(errMsg="File update failed - unrecognized file name ")
            else:
                dE = DataExchange(reqObj=self._reqObj, depDataSetId=idCode, wfInstanceId=None, fileSource="archive", verbose=self._verbose, log=self._lfh)
                ok = dE.export(inpFilePath=filePath, contentType=contentType, formatType=contentFormat, version="next", partitionNumber=partitionNumber)
                if ok:
                    rC.setStatus(statusMsg="File update completed")
                else:
                    rC.setError(errMsg="File update failed")
        return rC

    # ---------------------------------------------------------------------------------------------------
    #
    #
    #                    ID-level operations producing rendered model files returned as an HTML response
    #
    def _modelReportIdOp(self):
        """Entry point to create for model reports for idcodes in the input request.

        Returns a full HTML page derived from the input template file -
        """
        self._getSession()
        #
        idCodes = self._reqObj.getValue("identifier")

        if self._verbose:
            self._lfh.write("+ReviewDataWebAppWorker._modelReportIdOp() starting with idcodes %s\n" % idCodes)
        idCodeList = idCodes.split(" ")

        templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "report_template.html")
        webIncludePath = os.path.join(self._reqObj.getValue("TopPath"), "htdocs")

        return self._generateModelReportHTML(idCodeList=idCodeList, templateFilePath=templateFilePath, webIncludePath=webIncludePath)

    def _generateModelReportHTML(self, idCodeList, fileSource="wf-archive", instance=None, templateFilePath=None, webIncludePath=None):  # pylint: disable=unused-argument
        """Prepare a response object contaiing a model report rendered in HTML for the entries in input idCodeList.

        Returns a full HTML page derived from the input template file -
        """
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("html")
        #
        aTagList = []
        htmlList = []

        for idCode in idCodeList:
            myD = self._renderCheckReports(idCode, fileSource=fileSource, instance=None, contentTypeList=["model"])
            htmlList.append(myD["model"])
            aTagList.extend(myD["aTagList"])

        if len(aTagList) > 0:
            myD = {}
            myD["identifier"] = ",".join(idCodeList)
            myD["reportMarkup"] = "\n".join(htmlList)
            myD["linkMarkup"] = '<span class="url-list">Download: %s</span>' % ",".join(aTagList)
            #
            myD["sessionid"] = self._reqObj.getSessionId()
            myD["entryid"] = idCodeList[0]

            #
            rC.setHtmlTextFromTemplate(templateFilePath=templateFilePath, webIncludePath=webIncludePath, parameterDict=myD, insertContext=True)
            rC.setStatus(statusMsg="Reports completed")
        else:
            rC.setError(errMsg="No corresponding data file(s)")
            # do nothing

        return rC

    #
    # ------------------------------------------------------------------------------------------------------------
    #
    #                    ID-level operations producing a consolidated check reports returned in HTML response
    #

    def _fullReportIdOp(self):
        """Entry point to create for complete check reports for the idcode in the input request.

        Returns a full HTML page derived from the input template file -
        """
        self._getSession()
        idCode = self._reqObj.getValue("identifier")
        fileSource = self._reqObj.getValue("filesource")
        instance = self._reqObj.getValue("instance")
        templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "consolidated_report_template.html")
        webIncludePath = os.path.join(self._reqObj.getValue("TopPath"), "htdocs")

        return self._generateFullCheckReportHtml(idCode, fileSource=fileSource, instance=instance, templateFilePath=templateFilePath, webIncludePath=webIncludePath)

    def _generateFullCheckReportHtml(self, idCode, fileSource="wf-archive", instance=None, templateFilePath=None, webIncludePath=None):
        """Create a full check report in HTML format integrating content to input template file using web include path.

        Use existing report content if the file source /workflow instance details are provided.   Otherwise recaulate the report content.

        Return response object is a complete HTML page derived from the input template file -
        """
        if self._verbose:
            self._lfh.write("\n\n+ReviewDataWebAppWorker._generateFullHtmlCheckReport() idcode %s fileSource %s instance %s\n" % (idCode, fileSource, instance))

        #
        # Create report content --
        #
        if (fileSource is None) or (len(fileSource) < 1) or (fileSource in ["session", "session-download"]):
            fileSource = "session-download"
            # Make reports in session directory --
            opList = [
                "checkv5",
                "check-format",
                "check-misc",
                "check-geometry",
                "check-sf",
                # 'cif2pdb',
                "check-special-position",
                "check-emd-xml",
                "check-em-map",
            ]
            _aTagList = self._makeCheckReports([idCode], operationList=opList)  # noqa: F841
        #
        #
        if self._verbose:
            self._lfh.write("\n\n+ReviewDataWebAppWorker._generateFullHtmlCheckReport() idCode %s generating reports from data files in fileSource %s\n" % (idCode, fileSource))
        #
        cTL = [
            "model",
            "dcc-report",
            "special-position-report",
            "geometry-check-report",
            "links-report",
            "misc-check-report",
            "format-check-report",
            "dict-check-report",
            "xml-check-report",
            # 'model-pdb',
            "emd-xml-header-report",
            "em-map-check-report",
            "em-map-info-report",
            "downloads",
        ]
        reportD = self._renderCheckReports(idCode, fileSource=fileSource, instance=instance, contentTypeList=cTL)
        #
        reportD["sessionid"] = self._reqObj.getSessionId()
        reportD["entryid"] = idCode
        #

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("html")
        rC.setHtmlTextFromTemplate(templateFilePath=templateFilePath, webIncludePath=webIncludePath, parameterDict=reportD, insertContext=True)
        rC.setStatus(statusMsg="Reports completed")
        return rC
