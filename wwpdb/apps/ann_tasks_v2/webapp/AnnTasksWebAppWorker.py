##
# File:  AnnTasksWebAppWorker.py
# Date:  22-Feb-2014  J.Westbrook
#
# Updates:
#   04-Mar-2014  jdw Simplify session state maintenance
#   29-Sep-2014  jdw update file handling at lauch and completion
#   18-Sep-2015  jdw add NMR data file support
#   13-Jan-2017  ep  add support for correcting occupancy on special position
#   02-Oct-2017  zf  add /service/ann_tasks_v2/entityloadinfo, /service/ann_tasks_v2/symoploadinfo
#
##
"""
Manage web request and response processing for miscellaneous annotation tasks.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2010-2014 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import json,os,sys,traceback

from wwpdb.apps.ann_tasks_v2.webapp.CommonTasksWebAppWorker import CommonTasksWebAppWorker
from wwpdb.apps.ann_tasks_v2.correspnd.ValidateXml import ValidateXml
from wwpdb.apps.ann_tasks_v2.expIoUtils.MtzTommCIF import MtzTommCIF
from wwpdb.apps.ann_tasks_v2.utils.PdbFile import PdbFile
from wwpdb.apps.ann_tasks_v2.utils.PublicPdbxFile import PublicPdbxFile
from wwpdb.apps.ann_tasks_v2.utils.TaskSessionState import TaskSessionState
from wwpdb.apps.ann_tasks_v2.utils.TlsRange import TlsRange

from wwpdb.utils.session.WebRequest import ResponseContent
from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.io.locator.PathInfo import PathInfo


class AnnTasksWebAppWorker(CommonTasksWebAppWorker):

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
         Worker methods for annotation tasks.

         Performs URL - application mapping and application launching
         for annotation tasks module.

        """
        super(AnnTasksWebAppWorker, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        #  URL to method mapping -----  the service names are case insensitive --
        #
        self.__appPathD = {'/service/ann_tasks_v2/env': '_dumpOp',
                           '/service/ann_tasks_v2/entryinfo': '_entryInfoOp',
                           '/service/ann_tasks_v2/uploadfromid': '_launchFromIdcodeOp',
                           '/service/ann_tasks_v2/upload': '_uploadFileOp',
                           '/service/ann_tasks_v2/uploadmulti': '_uploadMultipleFilesOp',
                           '/service/ann_tasks_v2/nmr_cs_update': '_nmrCsUpdateOp',
                           '/service/ann_tasks_v2/nmr_cs_upload_check': '_nmrCsUploadCheckOp',
                           '/service/ann_tasks_v2/nmr_cs_atom_name_check': '_nmrCsAtomNameCheckOp',
                           '/service/ann_tasks_v2/nmr_cs_misc_checks': '_nmrCsMiscChecksOp',
                           '/service/ann_tasks_v2/nmr_rep_model_update': '_nmrRepresentativeModelUpdateOp',
                           '/service/ann_tasks_v2/nmr_cs_archive_update': '_nmrCsArchiveUpdateOp',
                           '/service/ann_tasks_v2/nmr_cs_auto_processing': '_nmrCsAutoProcessingOp',
                           '/service/ann_tasks_v2/get_nmr_processing_message': '_getNmrCsAutoProcessingMessageOp',
                           '/service/ann_tasks_v2/newsession': '_newSessionOp',
                           '/service/ann_tasks_v2/launchjmol': '_launchJmolViewerOp',
                           '/service/ann_tasks_v2/launchjmolwithmap': '_launchJmolViewerWithMapOp',
                           '/service/ann_tasks_v2/assemblycalc': '_assemblyCalcOp',
                           '/service/ann_tasks_v2/assemblyrestart': '_assemblyRestartOp',
                           '/service/ann_tasks_v2/assemblyview': '_assemblyViewOp',
                           '/service/ann_tasks_v2/genassemblyview': '_genAssemblyViewOp',
                           '/service/ann_tasks_v2/assemblyselect': '_assemblySelectOp',
                           '/service/ann_tasks_v2/sitecalc': '_siteCalcOp',
                           '/service/ann_tasks_v2/dictcheck': '_dictCheckOp',
                           '/service/ann_tasks_v2/extracheck': '_extraCheckOp',
                           '/service/ann_tasks_v2/valreport': '_valReportOp',
                           '/service/ann_tasks_v2/mapcalc': '_mapCalcOp',
                           '/service/ann_tasks_v2/npccmapcalc': '_npCcMapCalcOp',
                           '/service/ann_tasks_v2/localmapinfo': '_mapDisplayOp',
                           '/service/ann_tasks_v2/dcccalc': '_dccCalcOp',
                           '/service/ann_tasks_v2/dccrefinecalc': '_dccRefineCalcOp',
                           '/service/ann_tasks_v2/specialpositioncalc': '_specialPositionCalcOp',
                           '/service/ann_tasks_v2/specialpositionupdate': '_specialPositionUpdateOp',
                           '/service/ann_tasks_v2/tlsrangecorrection': '_tlsRangeCorrectionOp',
                           '/service/ann_tasks_v2/mtz_mmcif_conversion': '_mtzCifConversionOp',
                           '/service/ann_tasks_v2/reassignaltidscalc': '_reassignAltIdsCalcOp',
                           '/service/ann_tasks_v2/bisofullcalc': '_bisoFullCalcOp',
                           '/service/ann_tasks_v2/linkcalc': '_linkCalcOp',
                           '/service/ann_tasks_v2/solventcalc': '_solventCalcOp',
                           '/service/ann_tasks_v2/nafeaturescalc': '_naFeaturesCalcOp',
                           '/service/ann_tasks_v2/secstructcalc': '_secondaryStructureCalcOp',
                           '/service/ann_tasks_v2/transformcoordcalc': '_transformCoordCalcOp',
                           #
                           '/service/ann_tasks_v2/mergexyzcalc': '_mergeXyzCalcOp',
                           '/service/ann_tasks_v2/terminalatomscalc': '_terminalAtomsCalcOp',
                           '/service/ann_tasks_v2/geomvalidcalc': '_geometryValidationCalcOp',
                           '/service/ann_tasks_v2/getsessioninfo': '_getSessionInfoOp',
                           '/service/ann_tasks_v2/start': '_launchOp',
                           '/service/ann_tasks_v2/new_session/wf': '_launchOp',
                           '/service/ann_tasks_v2/finish': '_finishOp',
                           '/service/ann_tasks_v2/wfadmin_upload': '_uploadFileOp',
                           '/service/ann_tasks_v2/wfadmin_new_entry': '_newEntryWfOp',
                           '/service/ann_tasks_v2/wfadmin_reset_entry': '_resetEntryWfOp',
                           '/service/ann_tasks_v2/wfadmin_reassign_entry': '_reassignEntryWfOp',
                           '/service/ann_tasks_v2/assemblyloadform': '_loadAssemblyFormOp',
                           '/service/ann_tasks_v2/assemblysaveform': '_saveAssemblyFormOp',
                           '/service/ann_tasks_v2/assemblyloaddepinfo': '_loadAssemblyDepInfoOp',
                           '/service/ann_tasks_v2/entityloadinfo': '_loadEntityInfoOp',
                           '/service/ann_tasks_v2/symoploadinfo':  '_loadSymopInfoOp',
                           '/service/ann_tasks_v2/getcorrespondencetemplate': '_getCorresPNDTemplateOp',
                           '/service/ann_tasks_v2/generatecorrespondence': '_generateCorresPNDOp',
                           '/service/ann_tasks_v2/manualcoordeditorform': '_getCoordEditorFormOp',
                           '/service/ann_tasks_v2/manualcoordeditorsave': '_saveCoordEditorOp',
                           '/service/ann_tasks_v2/manualcoordeditorupdate': '_updateCoordEditorOp',
                           '/service/ann_tasks_v2/cs_editor': '_launchCSEditorFormOp',
                           '/service/ann_tasks_v2/manualcseditorform': '_getCSEditorFormOp',
                           '/service/ann_tasks_v2/manualcseditorsave': '_saveCSEditorOp',
                           '/service/ann_tasks_v2/manualcseditorupdate': '_updateCSEditorOp',
                           '/service/ann_tasks_v2/checkreports': '_fetchAndReportIdOps',
                           '/service/ann_tasks_v2/update_reflection_file': '_updateRefelectionFileOp',
                           '/service/ann_tasks_v2/list_em_maps': '_listEmMapsOp',
                           '/service/ann_tasks_v2/edit_em_map_header': '_editEmMapHeaderOp',
                           '/service/ann_tasks_v2/edit_em_map_header_responder': '_editEmMapHeaderResponderOp',
                           'placeholder': '_dumpOp'
                           }
        self.addServices(self.__appPathD)
        #
        self.__debug = False
        self.__doStatusUpdate = True
        if self._siteId in ["WWPDB_DEPLOY_MACOSX"]:
            self.__doStatusUpdate = False
        #
        self.__topPath = self._reqObj.getValue("TopPath")
        self.__templatePath = os.path.join(self.__topPath, "htdocs", "ann_tasks_v2")
        self._reqObj.setValue("TemplatePath", self.__templatePath)

    def _launchOp(self):
        """ Launch annotation tasks module interface

            :Helpers:
                wwpdb.apps.ann_tasks_v2.XXXXXXX

            :Returns:
                Operation output is packaged in a ResponseContent() object.


                /service/ann_tasks_v2/start?classID=AnnMod&identifier=D_1000000001&filesource=wf-archive&instance=W_000

                /service/ann_tasks_v2/start?classID=AnnMod&identifier=D_082583&filesource=wf-archive&instance=W_000
                /service/ann_tasks_v2/start?classID=AnnMod&identifier=D_1100201006&filesource=wf-archive&skipstatus=y

                /service/ann_tasks_v2/start?classID=AnnMod&identifier=D_1000000000&filesource=wf-archive
        """

        bSuccess = False
        if (self._verbose):
            self._lfh.write("\n+%s.%s() Starting now\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))

        self._getSession(useContext=True)
        #
        # determine if currently operating in Workflow Managed environment
        #
        standaloneMode = str(self._reqObj.getValue("standalonemode")).strip().lower()
        if (standaloneMode not in ['y', 'n']):
            standaloneMode = 'n'
        #
        if standaloneMode == 'n':
            bIsWorkflow = self._isWorkflow()
        else:
            bIsWorkflow = False

        wfStatusUpdate = self.__doStatusUpdate

        if standaloneMode in ['y']:
            wfStatusUpdate = False
        else:
            skipStatus = str(self._reqObj.getValue("skipstatus")).strip()
            if skipStatus.lower() in ["yes", "y"]:
                wfStatusUpdate = False
            elif skipStatus.lower() in ["no", "n"]:
                wfStatusUpdate = False
        #
        #
        fileSource = str(self._reqObj.getValue("filesource")).strip()
        identifier = str(self._reqObj.getValue("identifier")).strip()
        instanceWf = str(self._reqObj.getValue("instance")).strip()
        #
        if (self._verbose):
            self._lfh.write("+%s.%s() -- fileSource: %s identifier %s instance %s standalonemode %s\n" % (self.__class__.__name__,
                                                                                                          sys._getframe().f_code.co_name,
                                                                                                          fileSource, identifier, instanceWf, standaloneMode))
        if bIsWorkflow:
            # save wf state for status update --
            d = {}
            d['classID'] = self._reqObj.getValue("classID")
            d['filesource'] = fileSource
            d['identifier'] = identifier
            d['instance'] = instanceWf
            d['standalonemode'] = standaloneMode
            self._saveSessionParameter(pvD=d, prefix=None)

        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat('html')

        rC.set('standalonemode', standaloneMode)
        #
        if (self._verbose):
            self._lfh.write("+%s.%s() workflow flag is %r\n" % (self.__class__.__name__, sys._getframe().f_code.co_name, bIsWorkflow))

        if (wfStatusUpdate and bIsWorkflow):
            # Update WF status database --
            bSuccess = self._updateWfTrackingDb("open")
            if(not bSuccess):
                rC.setError(errMsg="Workflow database update/initiation failed")
                self._lfh.write("+%s.%s() - TRACKING status, update to 'open' failed for session %s \n" %
                                (self.__class__.__name__, sys._getframe().f_code.co_name, self._sessionId))
            else:
                if (self._verbose):
                    self._lfh.write("+%s.%s() Tracking status set to open\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
            #
            if bSuccess:
                wfStatus = 'completed'
            else:
                wfStatus = 'failed'
        else:
            bSuccess = True
            wfStatus = 'none'
        #
        rC.setStatusCode(wfStatus)
        #
        #  Transfer files to the session directory using archive file naming semantics -
        #
        ok = self._importFromWF(identifier, fileSource=fileSource, instanceWf=instanceWf, getMaps=True)
        #
        # Get the sessionId, entryId and entryFileName  (identifier here is the archive data set id)
        #
        sessionId = self._sessionId
        entryId = identifier
        #
        uploadVersionOp = "none"
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        entryFileName = pI.getFileName(identifier, contentType="model", formatType="pdbx", versionId=uploadVersionOp, partNumber='1')

        sfOk = False
        entryExpFileName = pI.getFileName(identifier, contentType="structure-factors", formatType="pdbx", versionId=uploadVersionOp, partNumber='1')
        filePath = os.path.join(self._sessionPath, entryExpFileName)
        if os.access(filePath, os.R_OK):
            sfOk = True
        #
        csOk = False
        entryCsFileName = pI.getFileName(identifier, contentType="nmr-chemical-shifts", formatType="pdbx", versionId=uploadVersionOp, partNumber='1')
        entryCsFilePath = os.path.join(self._sessionPath, entryCsFileName)
        if os.access(entryCsFilePath, os.R_OK):
            csOk = True

        if bIsWorkflow:
            self._setSessionInfoWf(entryId, entryFileName)
        #
        htmlList = []
        htmlList.append('<!DOCTYPE html>')
        htmlList.append('<html lang="en">')
        htmlList.append('<head>')
        htmlList.append('<title>Annotation Tasks Module</title>')
        if sfOk:
            htmlList.append('<meta http-equiv="REFRESH" content="0;url=/ann_tasks_v2/wf-startup-template.html?sessionid=%s&entryid=%s&entryfilename=%s&entryexpfilename=%s&wfstatus=%s&standalonemode=%s"></head>' %
                            (sessionId, entryId, entryFileName, entryExpFileName, wfStatus, standaloneMode))
        elif csOk:
            htmlList.append('<meta http-equiv="REFRESH" content="0;url=/ann_tasks_v2/wf-startup-template.html?sessionid=%s&entryid=%s&entryfilename=%s&entrycsfilename=%s&wfstatus=%s&standalonemode=%s"></head>' %
                            (sessionId, entryId, entryFileName, entryCsFileName, wfStatus, standaloneMode))
        else:
            htmlList.append('<meta http-equiv="REFRESH" content="0;url=/ann_tasks_v2/wf-startup-template.html?sessionid=%s&entryid=%s&entryfilename=%s&wfstatus=%s&standalonemode=%s"></head>' %
                            (sessionId, entryId, entryFileName, wfStatus, standaloneMode))
        # htmlList.append('<body>')
        # htmlList.append('</body>')
        # htmlList.append('</html>')
        rC.setHtmlText('\n'.join(htmlList))

        if (self._verbose):
            self._lfh.write("\n+%s.%s() Completed \n" % (self.__class__.__name__, sys._getframe().f_code.co_name))

        return rC

    def _finishOp(self):
        """ Finish up annotation tasks --

            :Returns:
                Operation output is packaged in a ResponseContent() object.

        """
        wfStatusUpdate = self.__doStatusUpdate
        bSuccess = False
        bIsWorkflow = True
        if (self._verbose):
            self._lfh.write("\n\n+%s.%s() Finishing operation beginning using status update flag %r\n" %
                            (self.__class__.__name__, sys._getframe().f_code.co_name, wfStatusUpdate))
        #
        self._getSession(useContext=True)
        #
        fileSource = str(self._reqObj.getValue("filesource")).strip()
        identifier = str(self._reqObj.getValue("identifier")).strip()
        instanceWf = str(self._reqObj.getValue("instance")).strip()
        #
        if (self._verbose):
            self._lfh.write("+%s.%s() recovered context fileSource: %s identifier %s instance %s\n" %
                            (self.__class__.__name__, sys._getframe().f_code.co_name, fileSource, identifier, instanceWf))
        #
        sessionId = self._sessionId
        entryId = identifier
        uploadVersionOp = "none"
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        entryFileName = pI.getFileName(identifier, contentType="model", formatType="pdbx", versionId=uploadVersionOp, partNumber='1')
        expFileName = pI.getFileName(identifier, contentType="structure-factors", formatType="pdbx", versionId=uploadVersionOp, partNumber='1')
        csFileName = pI.getFileName(entryId, contentType="nmr-chemical-shifts", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")

        #
        filelist = []
        filelist.append([entryFileName, "model", "pdbx"])
        #
        # copy reflection file if updated
        tPath = os.path.join(self._sessionPath, 'update-reflection-file.log')
        wPath = os.path.join(self._sessionPath, expFileName)
        if (self._verbose):
            self._lfh.write("+%s.%s() checking for structure factor log file filesource %s identifier %s path %s\n" %
                            (self.__class__.__name__, sys._getframe().f_code.co_name, fileSource, identifier, tPath))
            self._lfh.write("+%s.%s() checking for structure factor file filesource %s identifier %s path %s\n" %
                            (self.__class__.__name__, sys._getframe().f_code.co_name, fileSource, identifier, wPath))

        if os.access(tPath, os.F_OK):
            filelist.append([expFileName, "structure-factors", "pdbx"])
        #
        if os.access(os.path.join(self._sessionPath, csFileName), os.F_OK):
            filelist.append([csFileName, "nmr-chemical-shifts", "pdbx"])
        #
        # ----------
        # Generate PDB file
        #
        if (self._verbose):
            self._lfh.write("+%s.%s() creating PDB format file: filesource %s identifier %s\n" %
                            (self.__class__.__name__, sys._getframe().f_code.co_name, fileSource, identifier))
        convertPDB = PdbFile(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = convertPDB.run(entryId, entryFileName)
        if ok:
            pdbxPath = os.path.join(self._sessionPath, entryId + "_model_P1.pdb")
            if os.access(pdbxPath, os.F_OK):
                filelist.append([entryId + "_model_P1.pdb", "model", "pdb"])
        #
        # ------------
        # Generate Public pdbx cif file
        #
        if (self._verbose):
            self._lfh.write("+%s.%s() creating PDBx public file: filesource %s identifier %s\n" %
                            (self.__class__.__name__, sys._getframe().f_code.co_name, fileSource, identifier))
        convertPublicPdbx = PublicPdbxFile(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = convertPublicPdbx.run(entryId, entryFileName)
        if ok:
            pdbxPath = os.path.join(self._sessionPath, entryId + "_model-review_P1.cif")
            if os.access(pdbxPath, os.F_OK):
                filelist.append([entryId + "_model-review_P1.cif", "model-review", "pdbx"])
        #
        #
        # Add correspondence-to-depositor file
        #
        if (self._verbose):
            self._lfh.write("+%s.%s() creating correspondence file: filesource %s identifier %s\n" %
                            (self.__class__.__name__, sys._getframe().f_code.co_name, fileSource, identifier))

        pdbxPath = os.path.join(self._sessionPath, entryId + "_correspondence-to-depositor_P1.txt")
        if os.access(pdbxPath, os.F_OK):
            filelist.append([entryId + "_correspondence-to-depositor_P1.txt", "correspondence-to-depositor", "txt"])
        #
        dE = DataExchange(reqObj=self._reqObj, depDataSetId=identifier, wfInstanceId=instanceWf, fileSource=fileSource,
                          verbose=self._verbose, log=self._lfh)
        #
        for list in filelist:
            pdbxPath = os.path.join(self._sessionPath, list[0])
            ok = dE.export(pdbxPath, contentType=list[1], formatType=list[2], version="next")
            if (self._verbose):
                self._lfh.write("+%s.%s() Updating file %s in workflow store with status %r\n" %
                                (self.__class__.__name__, sys._getframe().f_code.co_name, pdbxPath, ok))
        #
        if fileSource not in ['archive', 'wf-archive']:
            dEAr = DataExchange(reqObj=self._reqObj, depDataSetId=identifier, fileSource='archive', verbose=self._verbose, log=self._lfh)
            for list in filelist:
                if list[1] in ["structure-factors", "nmr-chemical-shifts"]:
                    pdbxPath = os.path.join(self._sessionPath, list[0])
                    ok = dEAr.export(pdbxPath, contentType=list[1], formatType=list[2], version="next")
                    if (self._verbose):
                        self._lfh.write("+%s.%s() Updating file %s in archive store with status %r\n" %
                                        (self.__class__.__name__, sys._getframe().f_code.co_name, pdbxPath, ok))

        # ---------------------------------------------------------------------------------------------------------------------------------------------------------
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        if (self._verbose):
            self._lfh.write("+%s.%s() workflow flag is %r and status update flag is %r \n" %
                            (self.__class__.__name__, sys._getframe().f_code.co_name, bIsWorkflow, wfStatusUpdate))

        if (wfStatusUpdate and bIsWorkflow):
            # Update WF status database --
            bSuccess = self._updateWfTrackingDb("closed(0)")
            if(not bSuccess):
                rC.setError(errMsg="Workflow database status update has failed")
                self._lfh.write("+%s.%s() - updating tracking status to closed(0) failed for session %s\n" %
                                (self.__class__.__name__, sys._getframe().f_code.co_name, self._sessionId))
            else:
                if (self._verbose):
                    self._lfh.write("+%s.%s() Tracking status set to closed(0)\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        #
        else:
            bSuccess = True
        #
        if bSuccess:
            rC.setStatusCode('completed')
        else:
            rC.setStatusCode('failed')

        #
        rC.setHtmlText("Module completed successfully")
        return rC

    def _tlsRangeCorrectionOp(self):
        """ Run TLS range correction procedure
        """
        if (self._verbose):
            self._lfh.write("+AnnTasksWebAppWorker._tlsRangeCorrectionOp() starting\n")
        #
        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = ""
        taskFormId = self._reqObj.getValue("taskformid")
        depFileName = self._reqObj.getValue("tlsuploadfileoption")
        #
        calc = TlsRange(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = calc.run(entryId, depFileName, fileName)

        if (self._verbose):
            self._lfh.write("+AnnTasksWebAppWorker._tlsRangeCorrectionOp() status %r\n" % ok)

        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="TLS range correction", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _mtzCifConversionOp(self):
        """ Run mtz to mmCIF conversion
        """
        if (self._verbose):
            self._lfh.write("+AnnTasksWebAppWorker._mtzCifConversionOp() starting\n")
        #
        self._getSession(useContext=True)
        expFileName = self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = ""
        taskFormId = self._reqObj.getValue("taskformid")
        displayTaskFormId = taskFormId
        #
        calc = MtzTommCIF(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = calc.run(entryId, expFileName)
        #
        displayTaskFormId = taskFormId
        displayName = "Generating semi-auto form"
        if taskFormId == "#mtz-mmcif-semi-auto-conversion-form":
            displayName = "MTZ to mmCIF conversion"
            if ok:
                displayTaskFormId = "#mtz-mmcif-conversion-form"
            #
        #

        if (self._verbose):
            self._lfh.write("+AnnTasksWebAppWorker._mtzCifConversionOp() status %r\n" % ok)

        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name=displayName, formId=displayTaskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryExpFileName=expFileName)
        rC = self._makeTaskResponse(tssObj=tss)
        if ok:
             html = calc.getHtmlText()
             if html:
                 rC.set("mtzinfo", html)
             #
        else:
             rC.set("errorflag", True)
        #

        return rC

    def _nmrCsAutoProcessingOp(self):
        """ Run automatic chemical shift processing
        """
        if (self._verbose):
            self._lfh.write("+AnnTasksWebAppWorker._nmrCsAutoProcessingOp() starting\n")
        #
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        taskFormId = self._reqObj.getValue("taskformid")
        #
        self._autoProcessNmrChemShifts(entryId)
        #
        tagL = []
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        for contentType in ( "model", "nmr-chemical-shifts" ):
            fileName = pI.getFileName(entryId, contentType=contentType, formatType="pdbx", versionId="none", partNumber="1")
            filePath = os.path.join(self._sessionPath, fileName)
            if os.access(filePath, os.R_OK):
                tagL.append('<a class="" href="/sessions/' + self._sessionId + '/' + fileName + '" target="_blank">' + fileName + '</a>')
            #
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Chemical shift processing", formId=taskFormId, args="", completionFlag=True, tagList=tagL, entryId=entryId)
        rC = self._makeTaskResponse(tssObj=tss)
        rC.setHtmlText(self.__getNmrDiagnosticsHtmlText(entryId))

        return rC

    def _getNmrCsAutoProcessingMessageOp(self):
        """ Read automatic chemical shift processing result messages and return to NMR tab page
        """
        if (self._verbose):
            self._lfh.write("+AnnTasksWebAppWorker._nmrCsAutoProcessingOp() starting\n")
        #
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setHtmlText(self.__getNmrDiagnosticsHtmlText(entryId))

        return rC

    def __getNmrDiagnosticsHtmlText(self, entryId):
        """ Get diagnostics from validation xml and nmr-shift-error-report json files
        """
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        #
        csFileName = pI.getFileName(entryId, contentType="nmr-chemical-shifts", formatType="pdbx", versionId="none", partNumber="1")
        csFilePath = os.path.join(self._sessionPath, csFileName)
        #
        xmlFileName = pI.getFileName(entryId, contentType="validation-data", formatType="xml", versionId="none", partNumber="1")
        xmlFilePath = os.path.join(self._sessionPath, xmlFileName)
        #
        diagText = ""
        diagFileName = pI.getFileName(entryId, contentType="nmr-shift-error-report", formatType="json", versionId="none", partNumber="1")
        diagFilePath = os.path.join(self._sessionPath, diagFileName)
        if os.access(diagFilePath, os.R_OK):
            with open(diagFilePath, "r") as infile:
                jsonObj = json.load(infile)
                for msgType in ( "system_msg", "error_msg" ):
                    if (not msgType in jsonObj) or (not jsonObj[msgType]):
                        continue
                    #
                    if diagText:
                        diagText += "\n\n"
                    #
                    diagText += jsonObj[msgType]
                #
            #
        #
        htmlText = ""
        if not os.access(csFilePath, os.R_OK):
            htmlText += "<h2>Diagnostics from update of chemical shifts:</h2>"
            htmlText += "<br/>Chemical shifts file '" + csFileName + "' not found."
        elif os.access(xmlFilePath, os.R_OK):
            if diagText:
                htmlText += "<h2>Diagnostics from update of chemical shifts:</h2>"
                htmlText += "<pre>" + diagText + "</pre>"
            #
            validObj = ValidateXml(FileName=xmlFilePath)
            mappingErrorNumber = validObj.getCsMappingErrorNumber()
            notFoundCsList = validObj.getNotFoundInStructureCsList()
            #
            htmlText += "<h2>CS parsing diagnostics from misc. Validation:"
            if mappingErrorNumber or notFoundCsList:
                htmlText += "<ul>"
                if mappingErrorNumber:
                    htmlText += "<li>Number of shifts with mapping errors: " + str(mappingErrorNumber) + "</li>"
                #
                if notFoundCsList:
                    htmlText += "<li>Residues not found in the structure:<br/>"
                    htmlText += '<table class="table_css_class">'
                    htmlText += '<tr><th class="th_css_class" rowspan="2">Chain</th><th class="th_css_class" rowspan="2">Res</th>'
                    htmlText += '<th class="th_css_class" rowspan="2">Type</th><th class="th_css_class" rowspan="2">Atom</th>'
                    htmlText += '<th class="th_css_class" colspan="3">Shift Data</th></tr><tr><th class="th_css_class">Value</th>'
                    htmlText += '<th class="th_css_class">Uncertainty</th><th class="th_css_class">Ambiguity</th></tr>'
                    for recordList in notFoundCsList:
                        htmlText += '<tr>'
                        for record in recordList:
                            htmlText += '<td class="td_css_class">' + record + '</td>'
                        #
                        htmlText += '</tr>'
                    #
                    htmlText += "</table></li>"
                #
                htmlText += "</ul>"
            else:
                htmlText += "No issue found."
            #
        elif diagText:
            htmlText += "<h2>Diagnostics from update of chemical shifts:</h2>"
            htmlText += "<pre>" + diagText + "</pre>"
        else:
            htmlText += "<h2>Diagnostics from update of chemical shifts:</h2>"
            htmlText += "Validation failed, XML file'" + xmlFileName + "' not found."
        #
        return htmlText
