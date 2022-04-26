##
# File:  ValidationTasksWebAppWorker.py
# Date:  22-Feb-2014  J.Westbrook
#
# Updates:
#  04-Mar-2014  jdw unified with annoation and common tasks.
#  15-Sep-2015  jdw add NMR & EM upload support --
#
##
"""
Manage web request and response processing for various validation tasks.

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

import os
import sys
import inspect

from wwpdb.apps.ann_tasks_v2.webapp.CommonTasksWebAppWorker import CommonTasksWebAppWorker

from wwpdb.apps.ann_tasks_v2.correspnd.CorresPNDTemplate import CorresPNDTemplate
from wwpdb.apps.ann_tasks_v2.utils.PdbFile import PdbFile
from wwpdb.apps.ann_tasks_v2.utils.PublicPdbxFile import PublicPdbxFile

from wwpdb.utils.session.WebRequest import ResponseContent
from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.io.locator.PathInfo import PathInfo


class ValidationTasksWebAppWorker(CommonTasksWebAppWorker):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        Worker methods for validation tasks.

        Performs URL - application mapping and application launching
        for annotation tasks module.

        """
        super(ValidationTasksWebAppWorker, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        #  URL to method mapping -----  the service names are case insensitive --
        #
        # fmt: off
        self.__appPathD = {'/service/validation_tasks_v2/env': '_dumpOp',
                           '/service/validation_tasks_v2/entryinfo': '_entryInfoOp',
                           '/service/validation_tasks_v2/upload': '_uploadFileOp',
                           '/service/validation_tasks_v2/uploadfromid': '_launchFromIdcodeOp',
                           '/service/validation_tasks_v2/newsession': '_newSessionOp',
                           '/service/validation_tasks_v2/launchjmol': '_launchJmolViewerOp',
                           '/service/validation_tasks_v2/launchjmolwithmap': '_launchJmolViewerWithMapOp',
                           '/service/validation_tasks_v2/dictcheck': '_dictCheckOp',
                           '/service/validation_tasks_v2/extracheck': '_extraCheckOp',
                           '/service/validation_tasks_v2/valreport': '_valReportOp',
                           '/service/validation_tasks_v2/mapcalc': '_mapCalcOp',
                           '/service/validation_tasks_v2/dcccalc': '_dccCalcOp',
                           '/service/validation_tasks_v2/dccrefinecalc': '_dccRefineCalcOp',
                           '/service/validation_tasks_v2/specialpositioncalc': '_specialPositionCalcOp',
                           '/service/validation_tasks_v2/reassignaltidscalc': '_reassignAltIdsCalcOp',
                           '/service/validation_tasks_v2/geomvalidcalc': '_geometryValidationCalcOp',
                           '/service/validation_tasks_v2/getsessioninfo': '_getSessionInfoOp',
                           '/service/validation_tasks_v2/start': '_launchOp',
                           '/service/validation_tasks_v2/new_session/wf': '_launchOp',
                           '/service/validation_tasks_v2/finish': '_finishOp',
                           '/service/validation_tasks_v2/getcorrespondencetemplate': '_getCorresPNDTemplateOp',
                           '/service/validation_tasks_v2/generatecorrespondence': '_generateCorresPNDOp',
                           '/service/validation_tasks_v2/getbusterreport': '_getBusterReportOp',
                           '/service/validation_tasks_v2/manualcoordeditorform': '_getCoordEditorFormOp',
                           '/service/validation_tasks_v2/manualcoordeditorsave': '_saveCoordEditorOp',
                           '/service/validation_tasks_v2/manualcoordeditorupdate': '_updateCoordEditorOp',
                           '/service/validation_tasks_v2/manualcseditorform': '_getCSEditorFormOp',
                           '/service/validation_tasks_v2/manualcseditorsave': '_saveCSEditorOp',
                           '/service/validation_tasks_v2/manualcseditorupdate': '_updateCSEditorOp',
                           '/service/validation_tasks_v2/checkreports': '_fetchAndReportIdOps',
                           'placeholder': '_dumpOp'
                           }
        # fmt: on
        self.addServices(self.__appPathD)

        #
        self.__doStatusUpdate = True
        if self._siteId in ["WWPDB_DEPLOY_MACOSX"]:
            self.__doStatusUpdate = False
        #
        self.__topPath = self._reqObj.getValue("TopPath")
        self.__templatePath = os.path.join(self.__topPath, "htdocs", "validation_tasks_v2")
        self._reqObj.setValue("TemplatePath", self.__templatePath)

    def _launchOp(self):
        """Launch annotation tasks module interface

        :Helpers:
            wwpdb.apps.validation_tasks_v2.XXXXXXX

        :Returns:
            Operation output is packaged in a ResponseContent() object.


            /service/validation_tasks_v2/start?classID=AnnMod&identifier=D_1000000001&filesource=wf-archive&instance=W_000

            /service/validation_tasks_v2/start?classID=AnnMod&identifier=D_082583&filesource=wf-archive&instance=W_000
            /service/validation_tasks_v2/start?classID=AnnMod&identifier=D_1100201006&filesource=wf-archive&skipstatus=y

            /service/validation_tasks_v2/start?classID=AnnMod&identifier=D_1000000000&filesource=wf-archive
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
        _ok = self._importFromWF(identifier, fileSource=fileSource, instanceWf=instanceWf)  # noqa: F841
        #
        # Get the sessionId, entryId and entryFileName  (identifier here is the archive data set id)
        #
        sessionId = self._sessionId
        entryId = identifier
        entryFileName = identifier + "_model_P1.cif"
        entryExpFileName = identifier + "_sf_P1.cif"
        entryCsFileName = identifier + "_cs_P1.cif"
        entryFscFileName = identifier + "_fsc-xml_P1.xml"
        #
        #  By convention we leave the volumes in archive directory rather than copying them around -
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        entryVolFilePath = pI.getEmVolumeFilePath(entryId, wfInstanceId=None, fileSource="archive", versionId="latest", mileStone=None)
        self._lfh.write("entryVolFilePath {}".format(entryVolFilePath))
        _dd, entryVolFileName = os.path.split(entryVolFilePath)
        #
        sfOk = False
        entryExpFilePath = os.path.join(self._sessionPath, entryExpFileName)
        if os.access(entryExpFilePath, os.R_OK):
            sfOk = True

        csOk = False
        entryCsFilePath = os.path.join(self._sessionPath, entryCsFileName)
        if os.access(entryCsFilePath, os.R_OK):
            csOk = True
        #
        fscOk = False
        entryFscPath = os.path.join(self._sessionPath, entryFscFileName)
        if os.access(entryFscPath, os.R_OK):
            fscOk = True

        volOk = False
        if os.access(entryVolFilePath, os.R_OK):
            volOk = True
        #
        if bIsWorkflow:
            self._setSessionInfoWf(entryId, entryFileName)
            #
            # Generating default correspondence-to-depositor letter - added by ZF
            self._reqObj.setValue("entryid", entryId)
            self._reqObj.setValue("entryfilename", entryFileName)
            CorresPNDTObj = CorresPNDTemplate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            _content = CorresPNDTObj.get()  # noqa: F841
        #
        htmlList = []
        htmlList.append("<!DOCTYPE html>")
        htmlList.append('<html lang="en">')
        htmlList.append("<head>")
        htmlList.append("<title>Validation Tasks Module</title>")

        plist = [
            "sessionid={}".format(sessionId),
            "entryid={}".format(entryId),
            "entryfilename={}".format(entryFileName),
            "wfstatus={}".format(wfStatus),
            "standalonemode={}".format(standaloneMode),
        ]
        if sfOk:
            plist.append("entryexpfilename={}".format(entryExpFileName))
        if csOk:
            plist.append("entrycsfilename={}".format(entryCsFileName))
        if fscOk:
            plist.append("entryfscfilename={}".format(entryFscFileName))
        if volOk:
            plist.append("entryvolfilename={}".format(entryVolFileName))

        query = "&".join(plist)

        htmlList.append('<meta http-equiv="REFRESH" content="0;url=/validation_tasks_v2/wf-startup-template.html?{}"></head>'.format(query))

        rC.setHtmlText("\n".join(htmlList))
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
                "\n\n+%s.%s() Finishing operation starting with status update flag %r\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, wfStatusUpdate)
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
        # sessionId = self._sessionId
        entryId = identifier
        entryFileName = identifier + "_model_P1.cif"
        #
        filelist = []
        filelist.append([entryFileName, "model", "pdbx"])

        # ----------
        # Generate PDB file
        #
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
                self._lfh.write("+%s.%s() Updating file %s in archive store with status %r\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, pdbxPath, ok))
        #
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
