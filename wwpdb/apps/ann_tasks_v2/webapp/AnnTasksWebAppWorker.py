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
#   14-Jun-2019  zf  add automatical filling in assembly for NMR entry
#   28-Sep-2020  zf  add _getCloseContactContentOp() and _updateCloseContactContentOp()
#   22-Jan-2024  zf  add _getCovalentBondContentOp() and _updateCovalentBondContentOp()
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

import json
import os
import sys
import inspect
import logging

from wwpdb.apps.ann_tasks_v2.webapp.CommonTasksWebAppWorker import CommonTasksWebAppWorker
from wwpdb.apps.ann_tasks_v2.assembly.AssemblySelect import AssemblySelect
from wwpdb.apps.ann_tasks_v2.correspnd.ValidateXml import ValidateXml
from wwpdb.apps.ann_tasks_v2.expIoUtils.MtzTommCIF import MtzTommCIF
from wwpdb.apps.ann_tasks_v2.expIoUtils.ReSetFreeRinSFmmCIF import ReSetFreeRinSFmmCIF
from wwpdb.apps.ann_tasks_v2.related.Related import Related
from wwpdb.apps.ann_tasks_v2.utils.GetCloseContact import GetCloseContact
from wwpdb.apps.ann_tasks_v2.utils.GetCovalentBond import GetCovalentBond
from wwpdb.apps.ann_tasks_v2.utils.PdbFile import PdbFile
from wwpdb.apps.ann_tasks_v2.utils.PublicPdbxFile import PublicPdbxFile
from wwpdb.apps.ann_tasks_v2.utils.TaskSessionState import TaskSessionState
from wwpdb.apps.ann_tasks_v2.utils.TlsRange import TlsRange
from wwpdb.apps.ann_tasks_v2.utils.UpdateCloseContact import UpdateCloseContact
from wwpdb.apps.ann_tasks_v2.utils.UpdateCovalentBond import UpdateCovalentBond

from wwpdb.utils.session.WebRequest import ResponseContent
from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.io.locator.PathInfo import PathInfo

logger = logging.getLogger(__name__)


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
        self.__appPathD = {
            "/service/ann_tasks_v2/env": "_dumpOp",
            "/service/ann_tasks_v2/entryinfo": "_entryInfoOp",
            "/service/ann_tasks_v2/uploadfromid": "_launchFromIdcodeOp",
            "/service/ann_tasks_v2/upload": "_uploadFileOp",
            "/service/ann_tasks_v2/uploadmulti": "_uploadMultipleFilesOp",
            "/service/ann_tasks_v2/nmr_cs_update": "_nmrCsUpdateOp",
            "/service/ann_tasks_v2/nmr_cs_upload_check": "_nmrCsUploadCheckOp",
            "/service/ann_tasks_v2/nmr_cs_atom_name_check": "_nmrCsAtomNameCheckOp",
            "/service/ann_tasks_v2/nmr_cs_misc_checks": "_nmrCsMiscChecksOp",
            "/service/ann_tasks_v2/nmr_rep_model_update": "_nmrRepresentativeModelUpdateOp",
            "/service/ann_tasks_v2/nmr_cs_archive_update": "_nmrCsArchiveUpdateOp",
            "/service/ann_tasks_v2/nmr_data_auto_processing": "_nmrDataAutoProcessingOp",
            "/service/ann_tasks_v2/nmr_cs_auto_processing": "_nmrCsAutoProcessingOp",
            "/service/ann_tasks_v2/get_nmr_processing_message": "_getNmrExpAutoProcessingMessageOp",
            "/service/ann_tasks_v2/newsession": "_newSessionOp",
            "/service/ann_tasks_v2/launchjmol": "_launchJmolViewerOp",
            "/service/ann_tasks_v2/launchjmolwithmap": "_launchJmolViewerWithMapOp",
            "/service/ann_tasks_v2/molstarmapsjson": "_molstarMapsJson",
            "/service/ann_tasks_v2/assemblycalc": "_assemblyCalcOp",
            "/service/ann_tasks_v2/assemblyrestart": "_assemblyRestartOp",
            "/service/ann_tasks_v2/assemblyview": "_assemblyViewOp",
            "/service/ann_tasks_v2/genassemblyview": "_genAssemblyViewOp",
            "/service/ann_tasks_v2/assemblyselect": "_assemblySelectOp",
            # '/service/ann_tasks_v2/sitecalc': '_siteCalcOp',
            "/service/ann_tasks_v2/dictcheck": "_dictCheckOp",
            "/service/ann_tasks_v2/extracheck": "_extraCheckOp",
            "/service/ann_tasks_v2/valreport": "_valReportOp",
            "/service/ann_tasks_v2/mapcalc": "_mapCalcOp",
            "/service/ann_tasks_v2/npccmapcalc": "_npCcMapCalcOp",
            "/service/ann_tasks_v2/localmapinfo": "_mapDisplayOp",
            "/service/ann_tasks_v2/dcccalc": "_dccCalcOp",
            "/service/ann_tasks_v2/dccrefinecalc": "_dccRefineCalcOp",
            "/service/ann_tasks_v2/specialpositioncalc": "_specialPositionCalcOp",
            "/service/ann_tasks_v2/specialpositionupdate": "_specialPositionUpdateOp",
            "/service/ann_tasks_v2/tlsrangecorrection": "_tlsRangeCorrectionOp",
            "/service/ann_tasks_v2/mtz_mmcif_conversion": "_mtzCifConversionOp",
            "/service/ann_tasks_v2/correcting_sf_free_r_set": "_sfFreeRCorrectionOp",
            "/service/ann_tasks_v2/correcting_database_releated": "_relatedCorrectionOp",
            "/service/ann_tasks_v2/reassignaltidscalc": "_reassignAltIdsCalcOp",
            "/service/ann_tasks_v2/bisofullcalc": "_bisoFullCalcOp",
            "/service/ann_tasks_v2/linkcalc": "_linkCalcOp",
            "/service/ann_tasks_v2/solventcalc": "_solventCalcOp",
            "/service/ann_tasks_v2/nafeaturescalc": "_naFeaturesCalcOp",
            "/service/ann_tasks_v2/secstructcalc": "_secondaryStructureCalcOp",
            "/service/ann_tasks_v2/transformcoordcalc": "_transformCoordCalcOp",
            #
            "/service/ann_tasks_v2/mergexyzcalc": "_mergeXyzCalcOp",
            "/service/ann_tasks_v2/terminalatomscalc": "_terminalAtomsCalcOp",
            "/service/ann_tasks_v2/geomvalidcalc": "_geometryValidationCalcOp",
            "/service/ann_tasks_v2/getsessioninfo": "_getSessionInfoOp",
            "/service/ann_tasks_v2/start": "_launchOp",
            "/service/ann_tasks_v2/new_session/wf": "_launchOp",
            "/service/ann_tasks_v2/finish": "_finishOp",
            "/service/ann_tasks_v2/wfadmin_upload": "_uploadFileOp",
            "/service/ann_tasks_v2/wfadmin_new_entry": "_newEntryWfOp",
            "/service/ann_tasks_v2/wfadmin_reset_entry": "_resetEntryWfOp",
            "/service/ann_tasks_v2/wfadmin_reassign_entry": "_reassignEntryWfOp",
            "/service/ann_tasks_v2/assemblyloadform": "_loadAssemblyFormOp",
            "/service/ann_tasks_v2/assemblysaveform": "_saveAssemblyFormOp",
            "/service/ann_tasks_v2/assemblysavedefaultinfo": "_saveDefaultAssemblyOp",
            "/service/ann_tasks_v2/assemblyloaddepinfo": "_loadAssemblyDepInfoOp",
            "/service/ann_tasks_v2/entityloadinfo": "_loadEntityInfoOp",
            "/service/ann_tasks_v2/symoploadinfo": "_loadSymopInfoOp",
            "/service/ann_tasks_v2/getcorrespondencetemplate": "_getCorresPNDTemplateOp",
            "/service/ann_tasks_v2/generatecorrespondence": "_generateCorresPNDOp",
            "/service/ann_tasks_v2/manualcoordeditorform": "_getCoordEditorFormOp",
            "/service/ann_tasks_v2/manualcoordeditorsave": "_saveCoordEditorOp",
            "/service/ann_tasks_v2/manualcoordeditorupdate": "_updateCoordEditorOp",
            "/service/ann_tasks_v2/cs_editor": "_launchCSEditorFormOp",
            "/service/ann_tasks_v2/manualcseditorform": "_getCSEditorFormOp",
            "/service/ann_tasks_v2/manualcseditorsave": "_saveCSEditorOp",
            "/service/ann_tasks_v2/manualcseditorupdate": "_updateCSEditorOp",
            "/service/ann_tasks_v2/checkreports": "_fetchAndReportIdOps",
            "/service/ann_tasks_v2/update_reflection_file": "_updateRefelectionFileOp",
            "/service/ann_tasks_v2/list_em_maps": "_listEmMapsOp",
            "/service/ann_tasks_v2/edit_em_map_header": "_editEmMapHeaderOp",
            "/service/ann_tasks_v2/edit_em_map_header_responder": "_editEmMapHeaderResponderOp",
            "/service/ann_tasks_v2/get_close_contact_content": "_getCloseContactContentOp",
            "/service/ann_tasks_v2/update_close_contact_content": "_updateCloseContactContentOp",
            "/service/ann_tasks_v2/get_covalent_bond_content": "_getCovalentBondContentOp",
            "/service/ann_tasks_v2/update_covalent_bond_content": "_updateCovalentBondContentOp",
            "placeholder": "_dumpOp",
        }
        self.addServices(self.__appPathD)
        #
        # self.__debug = False
        self.__doStatusUpdate = True
        if self._siteId in ["WWPDB_DEPLOY_MACOSX"]:
            self.__doStatusUpdate = False
        #
        self.__topPath = self._reqObj.getValue("TopPath")
        self.__templatePath = os.path.join(self.__topPath, "htdocs", "ann_tasks_v2")
        self._reqObj.setValue("TemplatePath", self.__templatePath)

    def _launchOp(self):
        """Launch annotation tasks module interface

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
        if self._verbose:
            self._lfh.write("\n+%s.%s() Starting now\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))

        self._getSession(useContext=True)
        #
        # determine if currently operating in Workflow Managed environment
        #
        standaloneMode = str(self._reqObj.getValue("standalonemode")).strip().lower()
        if standaloneMode not in ["y", "n"]:
            standaloneMode = "n"
        #
        if standaloneMode == "n":
            bIsWorkflow = self._isWorkflow()
        else:
            bIsWorkflow = False

        wfStatusUpdate = self.__doStatusUpdate

        if standaloneMode in ["y"]:
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
        if self._verbose:
            self._lfh.write(
                "+%s.%s() -- fileSource: %s identifier %s instance %s standalonemode %s\n"
                % (self.__class__.__name__, inspect.currentframe().f_code.co_name, fileSource, identifier, instanceWf, standaloneMode)
            )
        if bIsWorkflow:
            # save wf state for status update --
            d = {}
            d["classID"] = self._reqObj.getValue("classID")
            d["filesource"] = fileSource
            d["identifier"] = identifier
            d["instance"] = instanceWf
            d["standalonemode"] = standaloneMode
            self._saveSessionParameter(pvD=d, prefix=None)

        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("html")

        rC.set("standalonemode", standaloneMode)
        #
        if self._verbose:
            self._lfh.write("+%s.%s() workflow flag is %r\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, bIsWorkflow))

        if wfStatusUpdate and bIsWorkflow:
            # Update WF status database --
            bSuccess = self._updateWfTrackingDb("open")
            if not bSuccess:
                rC.setError(errMsg="Workflow database update/initiation failed")
                self._lfh.write(
                    "+%s.%s() - TRACKING status, update to 'open' failed for session %s \n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self._sessionId)
                )
            else:
                if self._verbose:
                    self._lfh.write("+%s.%s() Tracking status set to open\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
            #
            if bSuccess:
                wfStatus = "completed"
            else:
                wfStatus = "failed"
        else:
            bSuccess = True
            wfStatus = "none"
        #
        rC.setStatusCode(wfStatus)
        #
        #  Transfer files to the session directory using archive file naming semantics -
        #
        _ok = self._importFromWF(identifier, fileSource=fileSource, instanceWf=instanceWf, getMaps=True)  # noqa: F841
        #
        # Get the sessionId, entryId and entryFileName  (identifier here is the archive data set id)
        #
        sessionId = self._sessionId
        entryId = identifier
        #
        uploadVersionOp = "none"
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        entryFileName = pI.getFileName(identifier, contentType="model", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")

        sfOk = False
        entryExpFileName = pI.getFileName(identifier, contentType="structure-factors", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        filePath = os.path.join(self._sessionPath, entryExpFileName)
        if os.access(filePath, os.R_OK):
            sfOk = True
        #
        nmrDataOk = False
        entryNmrDataFileName = pI.getFileName(identifier, contentType="nmr-data-str", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        entryNmrDataFilePath = os.path.join(self._sessionPath, entryNmrDataFileName)
        if os.access(entryNmrDataFilePath, os.R_OK):
            nmrDataOk = True
        #
        csOk = False
        entryCsFileName = pI.getFileName(identifier, contentType="nmr-chemical-shifts", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        entryCsFilePath = os.path.join(self._sessionPath, entryCsFileName)
        if os.access(entryCsFilePath, os.R_OK):
            csOk = True
        #
        auto_assembly_status = ""
        if bIsWorkflow:
            hasAssemblyInfo = self.__checkAssemblyInfo(os.path.join(self._sessionPath, entryFileName))
            if hasAssemblyInfo:
                auto_assembly_status = "existed"
            method = str(self._reqObj.getValue("method")).strip().upper()
            auto_methods = [
                "SOLUTION NMR",
                "SOLID-STATE NMR",
                "NMR",
                # 'ELECTRON MICROSCOPY',
            ]
            if method in auto_methods:
                if not hasAssemblyInfo:
                    assem = AssemblySelect(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                    assem.autoAssignDefaultAssembly(entryId, entryFileName)
                    #
                    updatedModelPath = os.path.join(self._sessionPath, entryId + "_model-assembly-updated_P1.cif")
                    hasAssemblyInfo = self.__checkAssemblyInfo(updatedModelPath)
                    if hasAssemblyInfo:
                        auto_assembly_status = "updated"
                        os.rename(updatedModelPath, os.path.join(self._sessionPath, entryFileName))
                    else:
                        auto_assembly_status = "failed"
                        if os.access(updatedModelPath, os.F_OK):
                            os.remove(updatedModelPath)
                        #
                    #
                #
            #
            self._setSessionInfoWf(entryId, entryFileName)
        #
        auto_assembly_status_url = ""
        if auto_assembly_status:
            auto_assembly_status_url = "&assemblystatus=" + auto_assembly_status
        #
        htmlList = []
        htmlList.append("<!DOCTYPE html>")
        htmlList.append('<html lang="en">')
        htmlList.append("<head>")
        htmlList.append("<title>Annotation Tasks Module</title>")
        if sfOk:
            htmlList.append(
                '<meta http-equiv="REFRESH" content="0;url=/ann_tasks_v2/wf-startup-template.html?sessionid=%s&entryid=%s&entryfilename=%s&entryexpfilename=%s&wfstatus=%s&standalonemode=%s%s"></head>'  # noqa: E501
                % (sessionId, entryId, entryFileName, entryExpFileName, wfStatus, standaloneMode, auto_assembly_status_url)
            )
        elif nmrDataOk:
            htmlList.append(
                '<meta http-equiv="REFRESH" content="0;url=/ann_tasks_v2/wf-startup-template.html?sessionid=%s&entryid=%s&entryfilename=%s&entrynmrdatafilename=%s&wfstatus=%s&standalonemode=%s%s"></head>'  # noqa: E501
                % (sessionId, entryId, entryFileName, entryNmrDataFileName, wfStatus, standaloneMode, auto_assembly_status_url)
            )
        elif csOk:
            htmlList.append(
                '<meta http-equiv="REFRESH" content="0;url=/ann_tasks_v2/wf-startup-template.html?sessionid=%s&entryid=%s&entryfilename=%s&entrycsfilename=%s&wfstatus=%s&standalonemode=%s%s"></head>'  # noqa: E501
                % (sessionId, entryId, entryFileName, entryCsFileName, wfStatus, standaloneMode, auto_assembly_status_url)
            )
        else:
            htmlList.append(
                '<meta http-equiv="REFRESH" content="0;url=/ann_tasks_v2/wf-startup-template.html?sessionid=%s&entryid=%s&entryfilename=%s&wfstatus=%s&standalonemode=%s%s"></head>'
                % (sessionId, entryId, entryFileName, wfStatus, standaloneMode, auto_assembly_status_url)
            )
        # htmlList.append('<body>')
        # htmlList.append('</body>')
        # htmlList.append('</html>')
        rC.setHtmlText("\n".join(htmlList))

        if self._verbose:
            self._lfh.write("\n+%s.%s() Completed \n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))

        return rC

    def _finishOp(self):
        """Finish up annotation tasks --

        :Returns:
            Operation output is packaged in a ResponseContent() object.

        """
        wfStatusUpdate = self.__doStatusUpdate
        bSuccess = False
        bIsWorkflow = True
        if self._verbose:
            self._lfh.write(
                "\n\n+%s.%s() Finishing operation beginning using status update flag %r\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, wfStatusUpdate)
            )
        #
        self._getSession(useContext=True)
        #
        fileSource = str(self._reqObj.getValue("filesource")).strip()
        identifier = str(self._reqObj.getValue("identifier")).strip()
        instanceWf = str(self._reqObj.getValue("instance")).strip()
        #
        if self._verbose:
            self._lfh.write(
                "+%s.%s() recovered context fileSource: %s identifier %s instance %s\n"
                % (self.__class__.__name__, inspect.currentframe().f_code.co_name, fileSource, identifier, instanceWf)
            )
        #
        entryId = identifier
        uploadVersionOp = "none"
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        entryFileName = pI.getFileName(identifier, contentType="model", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        expFileName = pI.getFileName(identifier, contentType="structure-factors", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        csFileName = pI.getFileName(entryId, contentType="nmr-chemical-shifts", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        nefFileName = pI.getFileName(entryId, contentType="nmr-data-str", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        #
        filelist = []
        filelist.append([entryFileName, "model", "pdbx"])
        #
        # copy reflection file if updated
        resetFreeR = False
        rPath = os.path.join(self._sessionPath, identifier + "-reset_freer.log")
        if os.access(rPath, os.F_OK):
            ifh = open(rPath, "r")
            data = ifh.read()
            ifh.close()
            if data.find("Free R set was successfully relabeled.") > 0:
                resetFreeR = True
            #
        #
        tPath = os.path.join(self._sessionPath, "update-reflection-file.log")
        wPath = os.path.join(self._sessionPath, expFileName)
        if self._verbose:
            self._lfh.write(
                "+%s.%s() checking for structure factor log file filesource %s identifier %s path %s\n"
                % (self.__class__.__name__, inspect.currentframe().f_code.co_name, fileSource, identifier, tPath)
            )
            self._lfh.write(
                "+%s.%s() checking for structure factor file filesource %s identifier %s path %s\n"
                % (self.__class__.__name__, inspect.currentframe().f_code.co_name, fileSource, identifier, wPath)
            )
        #
        mtz2mmcifLogPath = os.path.join(self._sessionPath, identifier + "-mtz2mmcif.log")
        sfInfoPath = os.path.join(self._sessionPath, "sf_information.cif")
        if os.access(mtz2mmcifLogPath, os.F_OK) and os.access(sfInfoPath, os.F_OK):
            cifObj = mmCIFUtil(filePath=sfInfoPath)
            error = cifObj.GetSingleValue("sf_convert", "error")
            if not error:
                resetFreeR = True
            #
        #
        if resetFreeR or os.access(tPath, os.F_OK):
            filelist.append([expFileName, "structure-factors", "pdbx"])
        #
        if os.access(os.path.join(self._sessionPath, csFileName), os.F_OK):
            filelist.append([csFileName, "nmr-chemical-shifts", "pdbx"])
        #
        if os.access(os.path.join(self._sessionPath, nefFileName), os.F_OK):
            filelist.append([nefFileName, "nmr-data-str", "pdbx"])
        #
        # ----------
        # Generate PDB file
        #
        if self._verbose:
            self._lfh.write(
                "+%s.%s() creating PDB format file: filesource %s identifier %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, fileSource, identifier)
            )
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
        if self._verbose:
            self._lfh.write(
                "+%s.%s() creating PDBx public file: filesource %s identifier %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, fileSource, identifier)
            )
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
        if self._verbose:
            self._lfh.write(
                "+%s.%s() creating correspondence file: filesource %s identifier %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, fileSource, identifier)
            )

        pdbxPath = os.path.join(self._sessionPath, entryId + "_correspondence-to-depositor_P1.txt")
        if os.access(pdbxPath, os.F_OK):
            filelist.append([entryId + "_correspondence-to-depositor_P1.txt", "correspondence-to-depositor", "txt"])
        #
        dE = DataExchange(reqObj=self._reqObj, depDataSetId=identifier, wfInstanceId=instanceWf, fileSource=fileSource, verbose=self._verbose, log=self._lfh)
        #
        for flist in filelist:
            pdbxPath = os.path.join(self._sessionPath, flist[0])
            ok = dE.export(pdbxPath, contentType=flist[1], formatType=flist[2], version="next")
            if self._verbose:
                self._lfh.write("+%s.%s() Updating file %s in workflow store with status %r\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, pdbxPath, ok))
        #
        if fileSource not in ["archive", "wf-archive"]:
            dEAr = DataExchange(reqObj=self._reqObj, depDataSetId=identifier, fileSource="archive", verbose=self._verbose, log=self._lfh)
            for flist in filelist:
                if flist[1] in ["structure-factors", "nmr-chemical-shifts", "nmr-data-str"]:
                    pdbxPath = os.path.join(self._sessionPath, flist[0])
                    ok = dEAr.export(pdbxPath, contentType=flist[1], formatType=flist[2], version="next")
                    if self._verbose:
                        self._lfh.write(
                            "+%s.%s() Updating file %s in archive store with status %r\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, pdbxPath, ok)
                        )

        # ---------------------------------------------------------------------------------------------------------------------------------------------------------
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        if self._verbose:
            self._lfh.write(
                "+%s.%s() workflow flag is %r and status update flag is %r \n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, bIsWorkflow, wfStatusUpdate)
            )

        if wfStatusUpdate and bIsWorkflow:
            # Update WF status database --
            bSuccess = self._updateWfTrackingDb("closed(0)")
            if not bSuccess:
                rC.setError(errMsg="Workflow database status update has failed")
                self._lfh.write(
                    "+%s.%s() - updating tracking status to closed(0) failed for session %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self._sessionId)
                )
            else:
                if self._verbose:
                    self._lfh.write("+%s.%s() Tracking status set to closed(0)\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
        #
        else:
            bSuccess = True
        #
        if bSuccess:
            rC.setStatusCode("completed")
        else:
            rC.setStatusCode("failed")

        #
        rC.setHtmlText("Module completed successfully")
        return rC

    def _tlsRangeCorrectionOp(self):
        """Run TLS range correction procedure"""
        if self._verbose:
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

        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._tlsRangeCorrectionOp() status %r\n" % ok)

        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="TLS range correction", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _mtzCifConversionOp(self):
        """Run mtz to mmCIF conversion"""
        if self._verbose:
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

        if self._verbose:
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

    def _sfFreeRCorrectionOp(self):
        """Correcting free R set of SF file"""
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._sfFreeRCorrectionOp() starting\n")
        #
        self._getSession(useContext=True)
        expFileName = self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = ""
        taskFormId = self._reqObj.getValue("taskformid")
        #
        calc = ReSetFreeRinSFmmCIF(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = calc.run()
        #
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._sfFreeRCorrectionOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Correcting free R set form", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryExpFileName=expFileName)
        rC = self._makeTaskResponse(tssObj=tss)
        #
        return rC

    def _relatedCorrectionOp(self):
        """Correcting pdbx_database_related OneDep Refereces"""
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._relatedCorrectionOp() starting\n")
        #
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        fileName = self._reqObj.getValue("entryfilename")
        taskFormId = self._reqObj.getValue("taskformid")
        #
        calc = Related(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = calc.run(entryId, fileName, updateInput=True)
        #
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._reltaedCorrectionOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Correcting Related form", formId=taskFormId, args="", completionFlag=ok, tagList=tagL, entryId=entryId)
        rC = self._makeTaskResponse(tssObj=tss)
        #
        return rC

    def _nmrDataAutoProcessingOp(self):
        """Run automatic chemical shift processing"""
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._nmrDataAutoProcessingOp() starting\n")
        #
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        taskFormId = self._reqObj.getValue("taskformid")
        #
        self._autoProcessNmrCombinedDataFile(entryId)
        #
        tagL = []
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        for contentType in ("model", "nmr-data-str"):
            fileName = pI.getFileName(entryId, contentType=contentType, formatType="pdbx", versionId="none", partNumber="1")
            filePath = os.path.join(self._sessionPath, fileName)
            if os.access(filePath, os.R_OK):
                tagL.append('<a class="" href="/sessions/' + self._sessionId + "/" + fileName + '" target="_blank">' + fileName + "</a>")
            #
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Chemical shift processing", formId=taskFormId, args="", completionFlag=True, tagList=tagL, entryId=entryId)
        rC = self._makeTaskResponse(tssObj=tss)
        rC.setHtmlText(self.__getNmrDiagnosticsHtmlText(entryId))

        return rC

    def _nmrCsAutoProcessingOp(self):
        """Run automatic chemical shift processing"""
        if self._verbose:
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
        for contentType in ("model", "nmr-chemical-shifts"):
            fileName = pI.getFileName(entryId, contentType=contentType, formatType="pdbx", versionId="none", partNumber="1")
            filePath = os.path.join(self._sessionPath, fileName)
            if os.access(filePath, os.R_OK):
                tagL.append('<a class="" href="/sessions/' + self._sessionId + "/" + fileName + '" target="_blank">' + fileName + "</a>")
            #
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Chemical shift processing", formId=taskFormId, args="", completionFlag=True, tagList=tagL, entryId=entryId)
        rC = self._makeTaskResponse(tssObj=tss)
        rC.setHtmlText(self.__getNmrDiagnosticsHtmlText(entryId))

        return rC

    def _getNmrExpAutoProcessingMessageOp(self):
        """Read automatic chemical shift processing result messages and return to NMR tab page"""
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._getNmrExpAutoProcessingMessageOp() starting\n")
        #
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setHtmlText(self.__getNmrDiagnosticsHtmlText(entryId))

        return rC

    def _getCloseContactContentOp(self):
        """Read close contact information from coordinate model file"""
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._getCloseContactContentOp() starting\n")
        #
        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        #
        calc = GetCloseContact(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        retD = calc.run(entryId, fileName)

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=retD)

        return rC

    def _updateCloseContactContentOp(self):
        """Update selected close contact(s) as linkage(s) in coordinate model file"""
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._updateCloseContactContentOp() starting\n")
        #
        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        close_contact_list = []
        close_contact_num_str = self._reqObj.getValue("total_close_contact_num")
        if close_contact_num_str:
            close_contact_num = int(close_contact_num_str)
            for i in range(0, close_contact_num):
                close_contact = self._reqObj.getValue("close_contact_" + str(i))
                if close_contact:
                    close_contact_list.append(close_contact)
                #
            #
        #
        if not close_contact_list:
            rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            rC.setReturnFormat("json")
            rC.setError(errMsg="No record selected")
            return rC
        #
        calc = UpdateCloseContact(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = calc.run(entryId, fileName, close_contact_list)

        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._updateCloseContactContentOp() status %r\n" % ok)

        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Update link from close contact", formId="#review-close-contact-form", args="", completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _getCovalentBondContentOp(self):
        """Read covalent bond information from coordinate model file"""
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._getCovalentBondContentOp() starting\n")
        #
        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        #
        calc = GetCovalentBond(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        retD = calc.run(entryId, fileName)

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=retD)

        return rC

    def _updateCovalentBondContentOp(self):
        """Remove selected covalent bond(s) in coordinate model file"""
        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._updateCovalentBondContentOp() starting\n")
        #
        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        covalent_bond_list = []
        covalent_bond_num_str = self._reqObj.getValue("total_covalent_bond_num")
        if covalent_bond_num_str:
            covalent_bond_num = int(covalent_bond_num_str)
            for i in range(0, covalent_bond_num):
                covalent_bond = self._reqObj.getValue("covalent_bond_" + str(i))
                if covalent_bond:
                    covalent_bond_list.append(covalent_bond)
                #
            #
        #
        if not covalent_bond_list:
            rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            rC.setReturnFormat("json")
            rC.setError(errMsg="No record selected")
            return rC
        #
        calc = UpdateCovalentBond(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = calc.run(entryId, fileName, covalent_bond_list)

        if self._verbose:
            self._lfh.write("+AnnTasksWebAppWorker._updateCovalentBondContentOp() status %r\n" % ok)

        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Remove covalent bond(s)", formId="#review-covalent-bond-form", args="", completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def __checkAssemblyInfo(self, modelFile):
        """Check if model file already has assembly information"""
        if not os.access(modelFile, os.F_OK):
            return False
        #
        cifObj = mmCIFUtil(filePath=modelFile)
        assemblyList = cifObj.GetValue("pdbx_struct_assembly")
        genList = cifObj.GetValue("pdbx_struct_assembly_gen")
        operList = cifObj.GetValue("pdbx_struct_oper_list")
        if (len(assemblyList) > 0) and (len(genList) > 0) and (len(operList) > 0):
            return True
        #
        return False

    def __getNmrDiagnosticsHtmlText(self, entryId):
        """Get diagnostics from validation xml and nmr-shift-error-report json files"""
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        #
        csFileName = self._reqObj.getValue("entrycsfilename")
        nefFileName = self._reqObj.getValue("entrynmrdatafilename")
        if nefFileName and (not csFileName):
            return ""
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
                for msgType in ("system_msg", "error_msg"):
                    if (msgType not in jsonObj) or (not jsonObj[msgType]):
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
                        htmlText += "<tr>"
                        for record in recordList:
                            htmlText += '<td class="td_css_class">' + record + "</td>"
                        #
                        htmlText += "</tr>"
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
