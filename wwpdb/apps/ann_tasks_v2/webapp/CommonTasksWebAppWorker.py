##
# File:  CommonTasksWebAppWorker.py
# Date:  22-Feb-2014  J.Westbrook
#
# Updates:
#   2-Apr-2014  jdw  remove version details from uploaded files -
#   2-Jul-2014  jdw  Add EM map edit methods
#   5-Jul-2014  jdw  add filer and download methods
#  16-Jul-2014  jdw  add  _npCcMapCalcOp()
#  18-Jul-2014  jdw  add  _mapDisplayOp()
#  20-Sep-2014  jdw  add file support for NMR experimental data files -
#  26-Sep-2014  jdw  revise validation calling protocol
#  19-Feb-2015  jdw  add edit support for _struct_biol.*.
#   3-Jul-2015  jdw  add support for materializing and visualizing generated assemblies.
#  17-Jul-2015  ep   add download support for map, CS and NEF
#   2-Aug-2015  jdw  add support for deposit/process_site in _entryInfoOp()
#  29-Aug-2015  jdw  add model update in map edit operations --
#  21-Feb-2016  jdw  add header_release_date  to _entryInfoOp
#  26-Aug-2016  ep   Set my_entryid in pkl cache in _entryInfoOp so cache works
#  29-Nov-2016  ep   add support for checkNext in _idReportOps (V5RC checking)
#  18-Dec-2016  ep   remove use disabled runAlt in validation
#  13-Jan-2017  ep   add _specialPositionUpdateOp
#  05-Oct-2017  zf   add _loadEntityInfoOp(), _loadSymopInfoOp()
#  12-Feb-2018  ep   add reqacctypes to data returned from _entryInfoOp()
##
"""
Common  annotation tasks.

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

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

import glob

# from json import loads, dumps
import inspect
import logging
import ntpath
import operator
import os
import shutil
import sys
import time
import traceback

from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.io.file.DataFile import DataFile
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.detach.DetachUtils import DetachUtils
from wwpdb.utils.dp.DataFileAdapter import DataFileAdapter
from wwpdb.utils.session.FileUtils import FileUtils
from wwpdb.utils.session.UtilDataStore import UtilDataStore
from wwpdb.utils.session.WebAppWorkerBase import WebAppWorkerBase
from wwpdb.utils.session.WebRequest import ResponseContent
from wwpdb.utils.session.WebUploadUtils import WebUploadUtils

#
from wwpdb.utils.wf.dbapi.WfTracking import WfTracking
from wwpdb.utils.wf.process.ProcessRunner import ProcessRunner
from wwpdb.utils.wf.WfDataObject import WfDataObject

from wwpdb.apps.ann_tasks_v2.assembly.AssemblyInput import AssemblyInput
from wwpdb.apps.ann_tasks_v2.assembly.AssemblySelect import AssemblySelect
from wwpdb.apps.ann_tasks_v2.check.Check import Check
from wwpdb.apps.ann_tasks_v2.check.XmlCheck import XmlCheck
from wwpdb.apps.ann_tasks_v2.check.EmdXmlCheck import EmdXmlCheck
from wwpdb.apps.ann_tasks_v2.check.EmMapCheck import EmMapCheck
from wwpdb.apps.ann_tasks_v2.check.ExtraCheck import ExtraCheck
from wwpdb.apps.ann_tasks_v2.check.FormatCheck import FormatCheck
from wwpdb.apps.ann_tasks_v2.check.GeometryCalc import GeometryCalc
from wwpdb.apps.ann_tasks_v2.check.GeometryCheck import GeometryCheck

#
from wwpdb.apps.ann_tasks_v2.correspnd.CorresPNDGenerator import CorresPNDGenerator
from wwpdb.apps.ann_tasks_v2.correspnd.CorresPNDTemplate import CorresPNDTemplate
from wwpdb.apps.ann_tasks_v2.editCoord.CSEditorForm import CSEditorForm
from wwpdb.apps.ann_tasks_v2.editCoord.CSEditorUpdate import CSEditorUpdate

#
from wwpdb.apps.ann_tasks_v2.editCoord.CoordEditorForm_v2 import CoordEditorForm
from wwpdb.apps.ann_tasks_v2.editCoord.CoordEditorUpdate import CoordEditorUpdate
from wwpdb.apps.ann_tasks_v2.em3d.EmEditUtils import EmEditUtils
from wwpdb.apps.ann_tasks_v2.em3d.EmModelUtils import EmModelUtils
from wwpdb.apps.ann_tasks_v2.em3d.EmUtils import EmUtils
from wwpdb.apps.ann_tasks_v2.expIoUtils.PdbxExpUpdate import PdbxExpUpdate
from wwpdb.apps.ann_tasks_v2.link.Link import Link
from wwpdb.apps.ann_tasks_v2.mapcalc.BisoFullCalc import BisoFullCalc
from wwpdb.apps.ann_tasks_v2.mapcalc.DccCalc import DccCalc
from wwpdb.apps.ann_tasks_v2.mapcalc.DccRefineCalc import DccRefineCalc
from wwpdb.apps.ann_tasks_v2.mapcalc.MapCalc import MapCalc
from wwpdb.apps.ann_tasks_v2.mapcalc.MapDisplay import MapDisplay
from wwpdb.apps.ann_tasks_v2.mapcalc.NpCcMapCalc import NpCcMapCalc
from wwpdb.apps.ann_tasks_v2.mapcalc.ReassignAltIdsCalc import ReassignAltIdsCalc
from wwpdb.apps.ann_tasks_v2.mapcalc.SpecialPositionCalc import SpecialPositionCalc
from wwpdb.apps.ann_tasks_v2.mapcalc.SpecialPositionUpdate import SpecialPositionUpdate
from wwpdb.apps.ann_tasks_v2.nafeatures.NAFeatures import NAFeatures
from wwpdb.apps.ann_tasks_v2.nmr.NmrChemShiftProcessUtils import NmrChemShiftProcessUtils
from wwpdb.apps.ann_tasks_v2.nmr.NmrChemShiftsMiscChecks import NmrChemShiftsMiscChecks

#
from wwpdb.apps.ann_tasks_v2.nmr.NmrChemShiftsUtils import NmrChemShiftsUtils
from wwpdb.apps.ann_tasks_v2.nmr.NmrModelUtils import NmrModelUtils
from wwpdb.apps.ann_tasks_v2.report.PdbxReport import PdbxReport
from wwpdb.apps.ann_tasks_v2.secstruct.SecondaryStructure import SecondaryStructure

#
from wwpdb.apps.ann_tasks_v2.site.Site import Site
from wwpdb.apps.ann_tasks_v2.solvent.Solvent import Solvent

#
from mmcif.io.IoAdapterCore import IoAdapterCore

#
from wwpdb.apps.ann_tasks_v2.transformCoord.TransformCoord import TransformCoord
from wwpdb.apps.ann_tasks_v2.utils.MergeXyz import MergeXyz
from wwpdb.apps.ann_tasks_v2.utils.PdbFile import PdbFile
from wwpdb.apps.ann_tasks_v2.utils.SessionDownloadUtils import SessionDownloadUtils
from wwpdb.apps.ann_tasks_v2.utils.TaskSessionState import TaskSessionState

#
from wwpdb.apps.ann_tasks_v2.utils.TerminalAtoms import TerminalAtoms
from wwpdb.apps.ann_tasks_v2.validate.Validate import Validate
from wwpdb.apps.ann_tasks_v2.view3d.ModelViewer3D import ModelViewer3D

#
try:
    from wwpdb.apps.validation.src.lvw.LVW_GetLOI import LVW_GetLOI
    from wwpdb.apps.validation.src.lvw.LVW_GetHTML import LVW_GetHTML
    from wwpdb.apps.validation.src.lvw.LVW_Mogul import LVW_Mogul
except ImportError:
    pass
#
from mmcif_utils.pdbx.PdbxIo import PdbxEntryInfoIo

logger = logging.getLogger(__name__)


class CommonTasksWebAppWorker(WebAppWorkerBase):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        Worker methods for annotation tasks.

        Performs URL - application mapping and application launching
        for annotation tasks module.


        All operations can be driven from this interface which can
        supplied with control information from web application requestor from a testing application.
        """
        super(CommonTasksWebAppWorker, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        self.__debug = False

    ################################################################################################################
    # ------------------------------------------------------------------------------------------------------------
    #      Top-level REST methods
    # ------------------------------------------------------------------------------------------------------------
    #
    def _dumpOp(self):
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setHtmlList(self._reqObj.dump(format="html"))
        return rC

    def _makeIdFetchResponse(self, idCode, contentType, formatType="pdbx"):
        """Copies input content object to the sessions download directory returns status - x"""
        self._getSession()
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        if du.fetchId(idCode, contentType, formatType=formatType):
            aTagList.append(du.getAnchorTag())

        if len(aTagList) > 0:
            rC.set("entryid", idCode)
            rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
            rC.setStatus(statusMsg="Fetch completed")
        else:
            rC.setError(errMsg="No corresponding file(s)")
            # do nothing

        return rC

    def _makeIdMultiFetchResponse(self, idCode, contentFormatList, minContentMatch=1):
        """ """
        self._getSession()

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        missingList = []
        for contentType, formatType in contentFormatList:
            if du.fetchId(idCode, contentType, formatType=formatType):
                aTagList.append(du.getAnchorTag())
            else:
                missingList.append(contentType)

        if len(aTagList) >= minContentMatch:
            rC.set("entryid", idCode)
            rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
            rC.setStatus(statusMsg="Fetch completed")
        else:
            rC.setError(errMsg="No corresponding file(s) for: %s" % " ".join(missingList))

        return rC

    def _launchJmolViewerOp(self):
        """Launch the 3D viewer to display the currently uploaded model coordinate file."""
        self._getSession(useContext=True)
        self._rltvSessionPath = self._sObj.getRelativePath()
        fileName = self._reqObj.getValue("entryfilename")
        rPath = os.path.join(self._rltvSessionPath, fileName)
        viewer = ModelViewer3D(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        viewer.setModelRelativePath(rPath)
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setHtmlText(viewer.getLaunchJmolHtml())
        return rC

    def _launchJmolViewerWithMapOp(self):
        """Launch the 3D viewer to display the currently uploaded model coordinate file."""
        self._getSession(useContext=True)
        self._rltvSessionPath = self._sObj.getRelativePath()
        #
        entryId = self._reqObj.getValue("entryid")
        fileName = self._reqObj.getValue("entryfilename")

        rModelPath = os.path.join(self._rltvSessionPath, fileName)
        rMapPath = os.path.join(self._rltvSessionPath, entryId + "_map-2fofc_P1.map")

        viewer = ModelViewer3D(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

        viewer.setModelRelativePath(rModelPath)
        viewer.setMapRelativePath(rMapPath)

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setHtmlText(viewer.getLaunchJmolWithMapHtml())
        return rC

    def _assemblyCalcOp(self):
        """Run an assembly calculation and return tabular report of results."""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._assemblyCalcOp() starting\n")
        self._getSession(useContext=True)

        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        assemArgs = self._reqObj.getValue("assemblyargs")
        #
        assem = AssemblySelect(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        #
        if assemArgs is not None and len(assemArgs) > 0:
            assem.setArguments(assemArgs)
            self._saveSessionParameter(param="assembly_arguments", value=assemArgs, prefix=entryId)

        assemSessionName = "session-" + entryId
        ok = assem.run(entryId, fileName, assemSessionName)

        assem.setReportContext(entryId)
        aCount = assem.getAssemblyCount(entryId)

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.set("assemcount", aCount)

        if aCount > 0:
            # cL,rowList=assem.getAssemblyDataTable(entryId)
            oL = assem.renderAssemblyDataTable(entryId)
            if self.__debug:
                # self._lfh.write("+CommonTasksWebAppWorker._assemblyCalcOp() report %r\n" % cL)
                self._lfh.write("+CommonTasksWebAppWorker._assemblyCalcOp() report %r\n" % oL)
            #
            rC.setHtmlText("Assembly calculation completed")
            self._saveSessionParameter(param="assemanalcomplete", value=True, prefix=entryId)
            # rC.set("rowdata",rowList)
            rC.set("tablecontent", "\n".join(oL))
        else:
            if ok:
                rC.setHtmlText("No assemblies predicted")
                self._saveSessionParameter(param="assemanalcomplete", value=True, prefix=entryId)
            else:
                # rC.setError(errMsg="Assembly calculation failed")
                rC.setHtmlText("Assembly calculation failed")
                self._saveSessionParameter(param="assemanalcomplete", value=False, prefix=entryId)
        return rC

    def _assemblyRestartOp(self):
        """Refresh an assembly page using previously calculated results - Return tabular report of results.
        not getting entry id data
        """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._assemblyRestartOp() starting\n")
        self._getSession(useContext=True)

        entryId = self._reqObj.getValue("entryid")
        #
        #
        uds = UtilDataStore(reqObj=self._reqObj, prefix=entryId, verbose=self._verbose, log=self._lfh)
        aArgs = uds.get("assembly_arguments")
        #
        assem = AssemblySelect(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        #
        ok = assem.setReportContext(entryId)

        aCount = assem.getAssemblyCount(entryId)
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.set("assemcount", aCount)
        rC.set("assemblyargs", aArgs)

        if aCount > 0:
            oL = assem.renderAssemblyDataTable(entryId)
            # cL,rowList=assem.getAssemblyDataTable(entryId)
            selectString = assem.getAssemblySelection(entryId)
            if self.__debug:
                self._lfh.write("+CommonTasksWebAppWorker._assemblyRestartOp() rowlist       %r\n" % oL)
                self._lfh.write("+CommonTasksWebAppWorker._assemblyRestartOp() select string %r\n" % selectString)
            #
            rC.setHtmlText("Assembly calculation completed")
            rC.set("tablecontent", "\n".join(oL))
            # rC.set("rowdata",rowList)
            if len(selectString) > 0:
                rC.set("selecttext", "(assemblies %s assigned)" % selectString)
            else:
                rC.set("selecttext", "")
            genT = uds.get("assemgentable")
            if len(genT) > 0:
                rC.set("assemgentable", genT)
        else:
            if ok:
                rC.setHtmlText("No assemblies predicted")
            else:
                # rC.setError(errMsg="Assembly calculation failed")
                pass
        return rC

    def _assemblyViewOp(self):
        """Return the HTML to launch viewer applet for the specified assembly."""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._assemblyViewOp() starting\n")
        self._getSession(useContext=True)
        self._rltvSessionPath = self._sObj.getRelativePath()
        #
        assem = AssemblySelect(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        #        assemSessionName="session-"+entryId

        assemblyId = self._reqObj.getValue("assemblyid")
        entryId = self._reqObj.getValue("entryid")

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setHtmlText(assem.getLaunchJmolHtml(assemblyId, entryId, generated=False))
        return rC

    def _genAssemblyViewOp(self):
        """Return the HTML to launch viewer applet for the specified assembly."""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._generatedAssemblyViewOp() starting\n")
        self._getSession(useContext=True)
        self._rltvSessionPath = self._sObj.getRelativePath()
        #
        assem = AssemblySelect(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

        assemblyId = self._reqObj.getValue("assemblyid")
        entryId = self._reqObj.getValue("entryid")

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setHtmlText(assem.getLaunchJmolHtml(assemblyId, entryId, generated=True))
        return rC

    def _assemblySelectOp(self):
        """Add selected assembly data to the current model data file."""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._assemblySelectOp() starting\n")
        self._getSession(useContext=True)
        #
        entryId = self._reqObj.getValue("entryid")
        entryFileName = self._reqObj.getValue("entryfilename")
        selectString = self._reqObj.getValue("selected")
        provenanceString = self._reqObj.getValue("provenance")
        #
        assem = AssemblySelect(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        assem.saveAssemblySelection(entryId, selectString=selectString, provenanceString=provenanceString)
        assignPath = os.path.join(self._sessionPath, entryId + "_assembly-assign_P1.cif")
        ok = assem.exportAssemblyAssignments(entryId, outFilePath=assignPath)
        if ok:
            ok = assem.updateModelFile(entryId, entryFileName, assignPath=assignPath)
        #

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        if ok:
            modelFilePath = os.path.join(self._sessionPath, entryId + "_model-updated_P1.cif")
            htmlS = assem.makeAssemblyDetailsTable(entryId, modelFilePath=modelFilePath)
            rC.set("assemgentable", htmlS)
            self._saveSessionParameter(param="assemgentable", value=htmlS, prefix=entryId)

        if ok:
            # tS="(assemblies %s updated in model file)" % selectString
            tS = "(assemblies updated in model file)"
            rC.setHtmlText(tS)
            self._saveSessionParameter(param="assemupdatestatus", value=tS, prefix=entryId)
            self._saveSessionParameter(param="assemcomplete", value=True, prefix=entryId)
        else:
            rC.setError(errMsg="<p style='color:red'>(Assembly update failed)</p>")
            self._saveSessionParameter(param="assemupdatestatus", value="(Assembly update failed)", prefix=entryId)
            self._saveSessionParameter(param="assemcomplete", value=False, prefix=entryId)
        return rC

    def _loadAssemblyDepInfoOp(self):
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        entryFileName = self._reqObj.getValue("entryfilename")
        cD = self.__makeAssemblyDepInfoTable(entryId=entryId, entryFileName=entryFileName)
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=cD)
        return rC

    def __makeAssemblyDepInfoTable(self, entryId, entryFileName):
        rD = {}
        adi = AssemblyInput(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rD["htmlcontent"] = adi.makeDepositorAssemblyDetailsTable(entryId=entryId, entryFileName=entryFileName)
        return rD

    def _loadEntityInfoOp(self):
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        entryFileName = self._reqObj.getValue("entryfilename")
        adi = AssemblyInput(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        cD = {}
        cD["htmlcontent"] = adi.makeEntityInfoTable(entryId=entryId, entryFileName=entryFileName)
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=cD)
        return rC

    def _loadSymopInfoOp(self):
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        entryFileName = self._reqObj.getValue("entryfilename")
        adi = AssemblyInput(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        cD = {}
        cD["htmlcontent"] = adi.makeSymopInfoTable(entryId=entryId, entryFileName=entryFileName)
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=cD)
        return rC

    def _loadAssemblyFormOp(self):
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        entryFileName = self._reqObj.getValue("entryfilename")

        cD = self.__makeAssemblyEditForm(entryId=entryId, entryFileName=entryFileName)
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=cD)
        return rC

    def __makeAssemblyEditForm(self, entryId, entryFileName):
        rD = {}
        adi = AssemblyInput(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rD["htmlcontent"] = adi.makeAssemblyEditForm(entryId=entryId, entryFileName=entryFileName)
        return rD

    def _saveAssemblyFormOp(self):
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")

        adi = AssemblyInput(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        fD, eD = adi.assemblyInputFormReader()

        ads = AssemblySelect(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = ads.saveAssemblyFormInput(entryId=entryId, assemFormD=fD, extraD=eD)

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        if ok:
            tS = "Assembly form input captured."
            rC.setHtmlText(tS)
            # self._saveSessionParameter(param="assemformstatus",value=tS,prefix=entryId)
            # self._saveSessionParameter(param="assemcomplete",value=True,prefix=entryId)
        else:
            rC.setError(errMsg="(Assembly form update failed)")
            # self._saveSessionParameter(param="assemupdatestatus",value="(Assembly update failed)",prefix=entryId)
            # self._saveSessionParameter(param="assemcomplete",value=False,prefix=entryId)
        return rC

    def _saveDefaultAssemblyOp(self):
        entryId = self._reqObj.getValue("entryid")
        ads = AssemblySelect(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok, htmlS = ads.saveAssemblyInput()
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        if ok:
            rC.set("assemgentable", htmlS)
            rC.setHtmlText("(assemblies updated in model file)")
            self._saveSessionParameter(param="assemgentable", value=htmlS, prefix=entryId)
            self._saveSessionParameter(param="assemupdatestatus", value="(assemblies updated in model file)", prefix=entryId)
            self._saveSessionParameter(param="assemcomplete", value=True, prefix=entryId)
        else:
            rC.setError(errMsg="<p style='color:red'>(Assembly update failed)</p>")
            self._saveSessionParameter(param="assemupdatestatus", value="(Assembly update failed)", prefix=entryId)
            self._saveSessionParameter(param="assemcomplete", value=False, prefix=entryId)
        #
        return rC

    def _makeTaskResponse(self, tssObj):
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")

        #        rC.setHtmlLinkText('<span class="my-task-form-url-list">Download: %s</span>' % '&nbsp; '.join(tssObj.getTaskLinks()) )

        if not tssObj.getTaskStatusText():
            taskName = tssObj.getTaskName()
            if not tssObj.getTaskErrorFlag():
                if tssObj.getTaskWarningFlag():
                    tssObj.setTaskStatusText("%s task completed with warnings." % taskName)
                else:
                    tssObj.setTaskStatusText("%s task completed." % taskName)
                #
            else:
                tssObj.setTaskStatusText("%s task failed." % taskName)
            #
        #

        rC.set(tssObj.getFormId(), tssObj.get())
        self._saveSessionParameter(param=tssObj.getFormId(), value=tssObj.get(), prefix=tssObj.getEntryId())

        if self.__debug:
            self._lfh.write("CommonTaskWebAppWorker()._makeTaskResponse() rC %s\n" % "\n".join(rC.dump()))
        return rC

    def _linkCalcOp(self):
        """Run link calculation --"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._linkCalcOp() starting\n")

        self._getSession(useContext=True)

        entryId = self._reqObj.getValue("entryid")
        fileName = self._reqObj.getValue("entryfilename")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #
        calc = Link(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        ok = calc.run(entryId, fileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._linkCalcOp() status %r\n" % ok)
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Link", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _dictCheckOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._dictCheckOp() starting\n")

        self._getSession(useContext=True)

        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #

        filePath = os.path.join(self._sessionPath, fileName)
        calc = Check(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        # Default - first block only
        calc.setCheckFirstBlock(True)

        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        ok = calc.run(entryId, filePath)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._dictCheckOp() status %r\n" % ok)

        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Dictionary check", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        if ok:
            rS = calc.getReportSize()
            if rS > 0:
                tss.setTaskWarningFlag(True)
                tss.setTaskWarningMessage("Dictionary check completed with issues.")

        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _extraCheckOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._extraCheckOp() starting\n")

        self._getSession(useContext=True)

        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        # extraCheckArgs = self._reqObj.getValue("extracheckargs")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #

        filePath = os.path.join(self._sessionPath, fileName)
        calc = ExtraCheck(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)

        ok = calc.run(entryId, filePath)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._extraCheckOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Extra checks", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        if ok:
            rS = calc.getReportSize()
            if rS > 0:
                tss.setTaskWarningFlag(True)
                tss.setTaskWarningMessage("Extra checks completed with issues.")

        rC = self._makeTaskResponse(tssObj=tss)
        #
        return rC

    def _updateRefelectionFileOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._updateReflectionFileOp() starting\n")

        self._getSession(useContext=True)

        modelFileName = self._reqObj.getValue("entryfilename")
        expFileName = self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")

        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #
        calc = PdbxExpUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        #
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)

        ok = calc.doUpdate(entryId, modelInputFile=modelFileName, expInputFile=expFileName, expOutputFile=expFileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._updateReflectionFileOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.setTaskStatusText(calc.getWarningMessage())
        tss.assign(name="Reflection file update", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        rC = self._makeTaskResponse(tssObj=tss)
        if ok:
            wvInfo = calc.getWavelengthInfo()
            if wvInfo:
                rC.set("wvinfo", wvInfo)
            #
        #

        return rC

    def _valReportOp(self):
        """Performs setup to run validation report code --"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._valReportOp() starting\n")
        self._getSession(useContext=True)
        uploadVersionOp = "none"
        modelFileName = self._reqObj.getValue("entryfilename")
        expFileName = self._reqObj.getValue("entryexpfilename")
        volFileName = self._reqObj.getValue("entryvolfilename")
        authorFscName = self._reqObj.getValue("entryfscfilename")
        entryId = self._reqObj.getValue("entryid")

        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")

        calc = Validate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        #
        # implement test version selectively --
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._valReportOp() USING runAll VERSION on site %s\n" % self._siteId)
            #
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        starFileName = pI.getFileName(entryId, contentType="nmr-chemical-shifts", formatType="nmr-star", versionId=uploadVersionOp, partNumber="1")
        pdbxCsFileName = pI.getFileName(entryId, contentType="nmr-chemical-shifts", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        pdbxNmrDataFileName = pI.getFileName(entryId, contentType="nmr-data-str", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        if not os.access(os.path.join(self._sessionPath, starFileName), os.R_OK):
            if os.access(os.path.join(self._sessionPath, pdbxCsFileName), os.R_OK):
                outFileName = pI.getFileName(entryId, contentType="nmr-chemical-shifts", formatType="nmr-star", versionId=uploadVersionOp, partNumber="1")
                ok = self.__uploadConversion(entryId, pdbxCsFileName, "nmr-chemical-shifts", "pdbx", "pdbx2nmrstar", outFileName, "nmr-chemical-shifts", "nmr-star", timeOut=0)
                if not ok:
                    starFileName = None
            else:
                starFileName = None
            #
        # nmr-data trumps CS
        pdbxResFile = None
        if os.access(os.path.join(self._sessionPath, pdbxNmrDataFileName), os.R_OK):
            pdbxCsFileName = pdbxNmrDataFileName
            pdbxResFile = pdbxCsFileName

        if self._verbose:
            self._lfh.write(
                "+CommonTasksWebAppWorker._valReportOp() calling runAll with modelInputFile %s reflnInputFile %s csInputFile %s restrainFile %s volInputFile %s\n"
                % (modelFileName, expFileName, pdbxCsFileName, pdbxResFile, volFileName)
            )
            #
        ok = calc.runAll(
            entryId,
            modelInputFile=modelFileName,
            reflnInputFile=expFileName,
            csInputFile=pdbxCsFileName,
            volInputFile=volFileName,
            authorFscFile=authorFscName,
            restraintInputFile=pdbxResFile,
            annotationContext=True,
        )

        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._valReportOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Validation report", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _mapCalcOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._mapCalcOp() starting\n")

        self._getSession(useContext=True)

        modelFileName = self._reqObj.getValue("entryfilename")
        expFileName = self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")

        calc = MapCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        ok = calc.run(entryId, modelInputFile=modelFileName, expInputFile=expFileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._mapCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Map", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        rC = self._makeTaskResponse(tssObj=tss)
        return rC

    def _npCcMapCalcOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._npCcMapCalcOp() starting\n")

        self._getSession(useContext=True)

        modelFileName = self._reqObj.getValue("entryfilename")
        expFileName = self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")

        calc = NpCcMapCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        ok = calc.run(entryId, modelInputFile=modelFileName, expInputFile=expFileName, doOmit=True)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._npCcMapCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Non-polymer CC Map", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        rC = self._makeTaskResponse(tssObj=tss)
        return rC

    def _specialPositionCalcOp(self):
        """Special position calculation -"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._specialPositionCalcOp() starting\n")

        self._getSession(useContext=True)

        modelFileName = self._reqObj.getValue("entryfilename")
        # expFileName=self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #

        calc = SpecialPositionCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        ok = calc.run(entryId, modelInputFile=modelFileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._specialPositionCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Special position", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        rC = self._makeTaskResponse(tssObj=tss)
        return rC

    def _specialPositionUpdateOp(self):
        """Special position update occupancy calculation -"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._specialPositionUpdateOp() starting\n")

        self._getSession(useContext=True)

        modelFileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #

        calc = SpecialPositionUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)

        ok = calc.run(entryId, modelFileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._specialPositionUpdateOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Special position update", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        # Need to improve warning message display on front end...
        # if ok:
        #    updated = calc.modelUpdated()
        #    if not updated:
        #        tss.setTaskWarningFlag(True)
        #        tss.setTaskWarningMessage("No changes to model file.")

        rC = self._makeTaskResponse(tssObj=tss)
        return rC

    def _dccRefineCalcOp(self):
        """DCC refinement calculation --"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._dccRefineCalcOp() starting\n")

        self._getSession(useContext=True)
        modelFileName = self._reqObj.getValue("entryfilename")
        expFileName = self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #

        calc = DccRefineCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        ok = calc.run(entryId, modelInputFile=modelFileName, expInputFile=expFileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._dccRefineCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="DCC refinement", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        rC = self._makeTaskResponse(tssObj=tss)
        return rC

    def _dccCalcOp(self):
        """DCC  RSR calculation -"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._dccCalcOp() starting\n")

        self._getSession(useContext=True)

        modelFileName = self._reqObj.getValue("entryfilename")
        expFileName = self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #

        calc = DccCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)

        modelFilePath = os.path.join(self._sessionPath, modelFileName)
        expFilePath = os.path.join(self._sessionPath, expFileName)

        ok = calc.run(entryId, modelInputPath=modelFilePath, expInputPath=expFilePath)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._dccCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="DCC", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _bisoFullCalcOp(self):
        """Replace partial b-values with full isotropic values --"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._bisoFullCalcOp() starting\n")

        self._getSession(useContext=True)

        modelFileName = self._reqObj.getValue("entryfilename")
        expFileName = self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #

        calc = BisoFullCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        ok = calc.run(entryId, modelInputFile=modelFileName, expInputFile=expFileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._bisoFullCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Isotropic B-value replacement", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        rC = self._makeTaskResponse(tssObj=tss)
        return rC

    def _reassignAltIdsCalcOp(self):
        """Reassign alt ids --"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._reassignAltIdsCalcOp() starting\n")

        self._getSession(useContext=True)

        modelFileName = self._reqObj.getValue("entryfilename")
        expFileName = self._reqObj.getValue("entryexpfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #

        calc = ReassignAltIdsCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        ok = calc.run(entryId, modelInputFile=modelFileName, expInputFile=expFileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._reassignAltIdsCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Alt Id reassignment", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=modelFileName)
        rC = self._makeTaskResponse(tssObj=tss)
        return rC

    def _siteCalcOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._siteCalcOp() starting\n")

        self._getSession(useContext=True)

        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        #

        calc = Site(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)

        ok = calc.run(entryId, fileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._siteCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Site", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)
        return rC

    def _naFeaturesCalcOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._naFeaturesCalcOp() starting\n")

        self._getSession(useContext=True)

        entryId = self._reqObj.getValue("entryid")
        fileName = self._reqObj.getValue("entryfilename")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")

        calc = NAFeatures(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)
        ok = calc.run(entryId, fileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._naFeaturesCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="NA features", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _secondaryStructureCalcOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._secondaryStructureCalcOp() starting\n")

        self._getSession(useContext=True)

        entryId = self._reqObj.getValue("entryid")
        fileName = self._reqObj.getValue("entryfilename")
        taskFormId = self._reqObj.getValue("taskformid")
        taskArgs = ""
        #
        wuu = WebUploadUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        topFileName = wuu.copyToSession(fileTag="topfile")

        #
        calc = SecondaryStructure(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if topFileName is not None and len(topFileName) > 0:
            calc.setTopologyFile(topFileName)

        ok = calc.run(entryId, fileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._secondaryStructureCalcOp() status %r\n" % ok)

        _warnFlag = calc.getLastStatus() != "ok"  # noqa: F841
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Secondary structure", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)

        tss.setTaskWarningFlag(True)
        tss.setAuxilaryFileName(topFileName)
        tss.setAuxilaryFileType("topfile")
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _transformCoordCalcOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._tranformCoordCalcOp() starting\n")

        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        taskFormId = self._reqObj.getValue("taskformid")
        taskArgs = ""

        transFileType = self._reqObj.getValue("transfiletype")
        #
        #
        wuu = WebUploadUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        transFileName = wuu.copyToSession(fileTag="transfile")

        #
        calc = TransformCoord(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

        if transFileName is not None and len(transFileName) > 0:
            calc.setTransformFile(transFileName)
            ok = calc.run(entryId, fileName, fileType=transFileType)
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._transformCoordCalcOp() status %r\n" % ok)

            tss.setAuxilaryFileName(transFileName)
            tss.setAuxilaryFileType(transFileType)
        else:
            ok = False
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._transformCoordCalcOp() failing no control file provided.")

        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss.assign(name="Transform coordinates", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _mergeXyzCalcOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcOp() starting\n")

        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        taskFormId = self._reqObj.getValue("taskformid")
        taskArgs = ""

        xyzFileFormat = self._reqObj.getValue("xyzfileformat")
        #
        #
        wuu = WebUploadUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        xyzFileName = wuu.copyToSession(fileTag="file")

        #
        calc = MergeXyz(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

        if xyzFileName is not None and len(xyzFileName) > 0:
            calc.setReplacementXyzFile(xyzFileName, format=xyzFileFormat)
            self._saveSessionParameter(param="xyzfilename", value=xyzFileName, prefix=entryId)

            ok = calc.run(entryId, fileName)
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcOp() status %r\n" % ok)
            tss.setAuxilaryFileName(xyzFileName)
            tss.setAuxilaryFileType(xyzFileFormat)
        else:
            ok = False
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._mergeXyzCalcOp() no merge file provided\n")
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss.assign(name="Merge replacement coordinates", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _solventCalcOp(self):
        """Run solvent reposition calculation -"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._solventCalcOp() starting\n")

        self._getSession(useContext=True)

        entryId = self._reqObj.getValue("entryid")
        fileName = self._reqObj.getValue("entryfilename")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")

        calc = Solvent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setArguments(taskArgs)

        ok = calc.run(entryId, fileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._solventCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Solvent", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _terminalAtomsCalcOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._terminalAtomsCalcOp() starting\n")

        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = ""
        taskFormId = self._reqObj.getValue("taskformid")

        terminalAtomsOption = self._reqObj.getValue("terminalatomsoption")
        #
        calc = TerminalAtoms(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        ok = calc.run(entryId, fileName, updateOption=terminalAtomsOption)

        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._terminalAtomsCalcOp() status %r\n" % ok)

        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Terminal atom replacement", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    #

    def _geometryValidationCalcOp(self):
        """ """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._geometryValidationCalcOp() starting\n")

        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        taskArgs = ""
        taskFormId = self._reqObj.getValue("taskformid")
        #
        # wuu=WebUploadUtils(reqObj=self._reqObj,verbose=self._verbose, log=self._lfh)
        #
        calc = GeometryCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

        ok = calc.run(entryId, fileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._geometryValidationCalcOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Geometry validation", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _setSessionInfoWf(self, entryId, entryFileName):
        if self._verbose:
            self._lfh.write("\n\n+CommonTasksWebAppWorker._setSessionInfoWf() entryId %s entryFileName %s\n" % (entryId, entryFileName))

        #
        # uds=UtilDataStore(reqObj=self._reqObj,prefix=entryId, verbose=self._verbose, log=self._lfh)
        wfFormIdTupleList = [
            ("#solvent-task-form", "Solvent"),
            ("#link-task-form", "Link"),
            ("#secstruct-task-form", "Secondary structure"),
            ("#nafeature-task-form", "NA features"),
            ("#site-task-form", "Site"),
        ]
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        for formId, formName in wfFormIdTupleList:
            tss.clear()
            tss.setTaskName(formName)
            tss.setFormId(formId)
            tss.setEntryId(entryId)
            tss.setEntryFileName(entryFileName)
            tss.setTaskErrorFlag(False)
            tss.setTaskStatusText("%s calculation run by workflow." % formName)
            # rC.set(tssObj.getFormId(),tssObj.get())
            self._saveSessionParameter(param=tss.getFormId(), value=tss.get(), prefix=entryId)

    def _getSessionInfoOp(self):
        """Recover any saved session details for the current entry context."""
        if self._verbose:
            self._lfh.write("\n\n+CommonTasksWebAppWorker._getSessionInfoOp() starting\n")

        try:
            self._getSession(useContext=True)

            # sId = self._reqObj.getSessionId()
            fileName = self._reqObj.getValue("entryfilename")
            entryId = self._reqObj.getValue("entryid")
            uploadFileFormId = self._reqObj.getValue("uploadfileformid")

            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._getSessionInfoOp() using entryId %s and entryFileName %s\n" % (entryId, fileName))

            rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            rC.setReturnFormat("json")

            if uploadFileFormId:
                uploadFileFormIdMap = {"#tls-range-correction-form": ["model-upload", ["pdb", "pdbx"]], "#mtz-mmcif-conversion-form": ["structure-factors-upload", ["mtz"]]}
                #
                uploadFileFormIdList = uploadFileFormId.split(",")
                pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
                for formId in uploadFileFormIdList:
                    if formId not in uploadFileFormIdMap:
                        continue
                    #
                    uploadFileList = self.__getUploadedFileList(pI, entryId, uploadFileFormIdMap[formId])
                    if uploadFileList:
                        rC.set(formId + "-uploadfilelist", uploadFileList)
                    #
                #
            #

            uds = UtilDataStore(reqObj=self._reqObj, prefix=entryId, verbose=self._verbose, log=self._lfh)

            keyList = ["assemanalcomplete", "assemupdatestatus", "assemcomplete"]

            for key in keyList:
                val = uds.get(key)
                rC.set(key, val)

            formIdList = [
                "#solvent-task-form",
                "#link-task-form",
                "#secstruct-task-form",
                "#nafeature-task-form",
                "#site-task-form",
                "#extracheck-task-form",
                "#valreport-task-form",
                "#npcc-mapcalc-task-form",
                "#mapcalc-task-form",
                "#dcc-calc-task-form",
                "#dcc-refine-calc-task-form",
                "#trans-coord-task-form",
                "#special-position-task-form",
                "#special-position-update-task-form",
                "#biso-full-task-form",
                "#terminal-atoms-task-form",
                "#merge-xyz-task-form",
                "#geom-valid-task-form",
                "#dict-check-task-form",
                "#reassign-altids-task-form",
                "#reflection-file-update-task-form",
                "#nmr-cs-upload-check-form",
                "#nmr-cs-atom-name-check-form",
                "#nmr-rep-model-update-form",
                "#nmr-cs-update-archive-form",
                "#nmr-cs-update-form",
                "#nmr-data-processing-form",
                "#nmr-cs-processing-form",
                "#nmr-cs-edit-form",
                "#tls-range-correction-form",
                "#mtz-mmcif-conversion-form",
                "#mtz-mmcif-semi-auto-conversion-form",
                "#sf-mmcif-free-r-correction-form",
                "#database-related-correction-form",
            ]
            tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            for key in formIdList:
                val = uds.get(key)
                if not isinstance(val, dict):
                    tss.clear()
                    val = tss.get()
                rC.set(key, val)
            #
            # get files --
            # ---
            fpattern = self._sessionPath + "/" + entryId + "_assembly-model-xyz_*"
            pthList = []
            pthList = glob.glob(fpattern)
            fList = []
            for pth in pthList:
                (_dirp, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("assemblymodelfiles", fList)
            #
            fpattern = self._sessionPath + "/" + entryId + "_assembly-model_*"
            pthList = []
            pthList = glob.glob(fpattern)
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("genassemblymodelfiles", fList)
            #
            fpattern = self._sessionPath + "/" + entryId + "*.log"
            pthList = []
            pthList = glob.glob(fpattern)
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("logfiles", fList)
            #
            fpattern = self._sessionPath + "/" + entryId + "_assembly-report_P1.xml"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)

            fpattern = self._sessionPath + "/" + entryId + "_assembly-assign_*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("pisareports", fList)

            #
            fpattern = self._sessionPath + "/" + entryId + "_dcc-*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("dccfiles", fList)
            #
            fpattern = self._sessionPath + "/" + entryId + "_emd-xml-header-report_*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                # Only list if size is not zero
                df = DataFile(fPath=pth)
                if df.srcFileSize() > 0:
                    (_dir, fileName) = os.path.split(pth)
                    fList.append(fileName)
            rC.set("emdxmlreportfiles", fList)

            #
            fpattern = self._sessionPath + "/" + entryId + "_site-anal_P1.cif"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("siteresultfiles", fList)
            #
            fpattern = self._sessionPath + "/" + entryId + "_dict-check-report_*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("checkreportfiles", fList)

            # PDBML report
            fpattern = self._sessionPath + "/" + entryId + "_xml-check-report_*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("checkxmlreportfiles", fList)

            fpattern = self._sessionPath + "/" + entryId + "_misc-check-report_*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("extracheckreportfiles", fList)

            fpattern = self._sessionPath + "/" + entryId + "_special-position-report_*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("specialpositionreportfiles", fList)

            fpattern = self._sessionPath + "/" + entryId + "_val-report*"
            pthList = []
            pthList = glob.glob(fpattern)
            fpattern = self._sessionPath + "/" + entryId + "_val-data*"

            pthList.extend(glob.glob(fpattern))
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("valreportfiles", fList)

            fpattern = self._sessionPath + "/" + entryId + "_map-*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            mapDisplayFlag = False
            omitMapDisplayFlag = False
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                if pth.find("_map-2fofc_") > 0:
                    mapDisplayFlag = True
                if pth.find("_map-omit-2fofc_") > 0:
                    omitMapDisplayFlag = True
                fList.append(fileName)
            rC.set("mapfiles", fList)
            #
            if mapDisplayFlag:
                rC.set("mapdisplayflag", True)
            if omitMapDisplayFlag:
                rC.set("omitmapdisplayflag", True)
            #
            fpattern = self._sessionPath + "/" + entryId + "_correspondence-to-depositor_P1.txt*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)
            rC.set("correspondencefile", fList)
            #
            #
            #
            # Chemical shift files -
            #
            fpattern = self._sessionPath + "/" + entryId + "_cs_P1.*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            fList = []
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)

            fpattern = self._sessionPath + "/" + entryId + "_cs-auth_P*"
            pthList = []
            pthList = glob.glob(fpattern)
            #
            for pth in pthList:
                (_dir, fileName) = os.path.split(pth)
                fList.append(fileName)

            rC.set("csfiles", fList)

        except:  # noqa: E722 pylint: disable=bare-except
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._getSessionInfoOp() failing\n")
                traceback.print_exc(file=self._lfh)
        # ---
        if self._verbose:
            if self.__debug:
                rL = rC.dump()
                self._lfh.write("+CommonTasksWebAppWorker._getSessionInfoOp() response object %s\n" % "\n".join(rL))
            self._lfh.write("+CommonTasksWebAppWorker._getSessionInfoOp() completed --  leaving\n")

        return rC

    def _importFromWF(self, identifier, fileSource="wf-archive", instanceWf="", getMaps=False):
        """Import annotation data files from the input workflow storage into this annotation session"""
        #
        de = DataExchange(reqObj=self._reqObj, depDataSetId=identifier, wfInstanceId=instanceWf, fileSource=fileSource, verbose=self._verbose, log=self._lfh)
        #
        # model file -
        #
        pth = de.copyToSession(contentType="model", formatType="pdbx", version="latest", partitionNumber=1)
        #
        if pth is None:
            return False
        #
        # assembly report file and assignment
        #
        pth = de.copyToSession(contentType="assembly-report", formatType="xml", version="latest", partitionNumber=1)
        pth = de.copyToSession(contentType="assembly-assign", formatType="txt", version="latest", partitionNumber=1)

        # assembly model files
        #
        for ii in range(1, 50):
            pth = de.copyToSession(contentType="assembly-model-xyz", formatType="pdbx", version="latest", partitionNumber=ii)
            if pth is None:
                break
        #
        pth = de.copyToSession(contentType="site-assign", formatType="pdbx", version="latest", partitionNumber=1)
        #
        # Validation files
        #
        pth = de.copyToSession(contentType="validation-report", formatType="pdf", version="latest", partitionNumber=1)
        pth = de.copyToSession(contentType="validation-report-full", formatType="pdf", version="latest", partitionNumber=1)
        pth = de.copyToSession(contentType="validation-report-slider", formatType="svg", version="latest", partitionNumber=1)
        pth = de.copyToSession(contentType="validation-data", formatType="xml", version="latest", partitionNumber=1)
        pth = de.copyToSession(contentType="validation-data", formatType="pdbx", version="latest", partitionNumber=1)
        pth = de.copyToSession(contentType="validation-report-2fo-map-coef", formatType="pdbx", version="latest", partitionNumber=1)
        pth = de.copyToSession(contentType="validation-report-fo-map-coef", formatType="pdbx", version="latest", partitionNumber=1)
        #
        # dictionary check file
        #
        pth = de.copyToSession(contentType="dict-check-report", formatType="txt", version="latest", partitionNumber=1)
        #
        # PDBML XML check file
        #
        pth = de.copyToSession(contentType="xml-check-report", formatType="txt", version="latest", partitionNumber=1)
        #
        #  Handle maps if input option is set --
        if getMaps:
            pth = de.copyToSession(contentType="map-2fofc", formatType="map", version="latest", partitionNumber=1)
            pth = de.copyToSession(contentType="map-fofc", formatType="map", version="latest", partitionNumber=1)
            pth = de.copyToSession(contentType="map-omit-2fofc", formatType="map", version="latest", partitionNumber=1)
            pth = de.copyToSession(contentType="map-omit-fofc", formatType="map", version="latest", partitionNumber=1)
            de.copyDirToSession(dirName="np-cc-maps")
            de.copyDirToSession(dirName="np-cc-omit-maps")

        #
        # SF file
        #
        pth = de.copyToSession(contentType="structure-factors", formatType="pdbx", version="latest", partitionNumber=1)
        #
        if pth is None:
            deArchive = DataExchange(reqObj=self._reqObj, depDataSetId=identifier, wfInstanceId=instanceWf, fileSource="archive", verbose=self._verbose, log=self._lfh)
            pth = deArchive.copyToSession(contentType="structure-factors", formatType="pdbx", version="latest", partitionNumber=1)

        # CS file (PDBx)
        #
        pth = de.copyToSession(contentType="nmr-chemical-shifts", formatType="pdbx", version="latest", partitionNumber=1)
        if pth is None:
            deArchive = DataExchange(reqObj=self._reqObj, depDataSetId=identifier, wfInstanceId=None, fileSource="archive", verbose=self._verbose, log=self._lfh)
            pth = deArchive.copyToSession(contentType="nmr-chemical-shifts", formatType="pdbx", version="latest", partitionNumber=1)
        #
        # NEF file (nmr-star)
        #
        pth = de.copyToSession(contentType="nmr-data-str", formatType="pdbx", version="latest", partitionNumber=1)
        if pth is None:
            deArchive = DataExchange(reqObj=self._reqObj, depDataSetId=identifier, wfInstanceId=None, fileSource="archive", verbose=self._verbose, log=self._lfh)
            pth = deArchive.copyToSession(contentType="nmr-data-str", formatType="pdbx", version="latest", partitionNumber=1)
        #
        pth = de.copyToSession(contentType="nmr-shift-error-report", formatType="json", version="latest", partitionNumber=1)
        pth = de.copyToSession(contentType="nmr-data-error-report", formatType="json", version="latest", partitionNumber=1)

        # fsc file (xml)
        #
        pth = de.copyToSession(contentType="fsc", formatType="xml", version="latest", partitionNumber=1)
        return True

    # def _viewOp(self):
    #     """Call to display data for given chem component in comparison grid of standalone version of chem comp module.
    #     Delegates primary processing to ChemCompView class.

    #     :Helpers:
    #         wwpdb.apps.ccmodule.view.ChemCompView.ChemCompView

    #     :Returns:
    #         Operation output is packaged in a ResponseContent() object.
    #     """
    #     if self._verbose:
    #         self._lfh.write("--------------------------------------------\n")
    #         self._lfh.write("+CommonTasksWebAppWorker._viewOp() starting\n")
    #     #
    #     self._getSession(useContext=True)
    #     sessionId = self._sessionId
    #     if self._verbose:
    #         self._lfh.write("+CommonTasksWebAppWorker._viewOp() session ID is: %s\n" % sessionId)
    #     #
    #     rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
    #     rC.setReturnFormat("json")
    #     #
    #     # ccV=ChemCompView(reqObj=self._reqObj,verbose=self._verbose,log=self._lfh)
    #     # rtrnCode=ccV.doView()
    #     #
    #     if self._verbose:
    #         self._lfh.write("+CommonTasksWebAppWorker._viewOp() - return code is %s\n" % str(rtrnCode))

    #     rC.addDictionaryItems({"sessionid": str(sessionId)})
    #     rC.setStatusCode(str(rtrnCode))

    #     return rC

    def _getBusterReportOp(self):
        """Getting buster report html context"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._getBusterReportOp() starting\n")
        #
        self._getSession(useContext=True)
        #
        content = ""
        try:
            entryId = self._reqObj.getValue("entryid")
            rundir = os.path.join(self._sessionPath, "LVW_" + entryId.upper())
            if os.access(rundir, os.F_OK):
                loiUtil = LVW_GetLOI(siteId=self._siteId, rundir=rundir, verbose=self._verbose, log=self._lfh)
                if loiUtil.readLOIMap():
                    loiMap = loiUtil.getLOIMap()
                    if loiMap:
                        mogulUtil = LVW_Mogul(siteId=self._siteId, rundir=rundir, LOIMap=loiMap, verbose=self._verbose, log=self._lfh)
                        mogulUtil.readMogulResult()
                        loiMap = mogulUtil.getLOIMap()
                        #
                        topHtmlPath = os.path.join("/sessions", str(self._sessionId), "LVW_" + entryId.upper())
                        htmlUtil = LVW_GetHTML(siteId=self._siteId, rundir=rundir, topHtmlPath=topHtmlPath, LOIMap=loiMap, verbose=self._verbose, log=self._lfh)
                        htmlUtil.setLigandOfInterestingList(loiUtil.getLOIList())
                        content = htmlUtil.getHtmlText()
                    #
                #
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self._lfh)
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setHtmlText(content)
        return rC

    def _getCorresPNDTemplateOp(self):
        """Generating correspondence template"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._getCorresPNDTemplateOp() starting\n")
        self._getSession(useContext=True)
        #
        CorresPNDTObj = CorresPNDTemplate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        content = CorresPNDTObj.get()
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setHtmlText(content)
        return rC

    def _generateCorresPNDOp(self):
        """Generating correspondence text"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._generateCorresPNDOp() starting\n")
        self._getSession(useContext=True)
        #
        CorresPNDGOp = CorresPNDGenerator(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        content = CorresPNDGOp.get()
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setText(text=content)
        return rC

    def _getCoordEditorFormOp(self):
        """Generating coordinate editor form"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._getCoordEditorFormOp() starting\n")
        self._getSession(useContext=True)
        #
        dU = DetachUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        coordEditorFormOp = CoordEditorForm(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        #
        myD = {}
        sph = self._reqObj.getSemaphore()
        delayValue = self._reqObj.getValue("delay")
        if sph:
            if dU.semaphoreExists(sph):
                myD = coordEditorFormOp.get()
            else:
                time.sleep(int(delayValue))
                myD["statuscode"] = "running"
            #
        else:
            entryId = self._reqObj.getValue("entryid")
            identifier = self._reqObj.getValue("display_identifier")
            if (identifier == entryId) or identifier.startswith("chain_"):
                dU.set(workerObj=coordEditorFormOp, workerMethod="run")
                dU.runDetach()
                myD["statuscode"] = "running"
            else:
                myD = coordEditorFormOp.get()
            #
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(myD)
        return rC

    def _launchCSEditorFormOp(self):
        """Generating chemical shift editor form"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._launchCSEditorFormOp() starting\n")
        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        taskFormId = self._reqObj.getValue("taskformid")
        #
        tagL = []
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        fileName = pI.getFileName(entryId, contentType="nmr-chemical-shifts", formatType="pdbx", versionId="none", partNumber="1")
        filePath = os.path.join(self._sessionPath, fileName)
        if os.access(filePath, os.R_OK):
            tagL.append('<a class="" href="/sessions/' + self._sessionId + "/" + fileName + '" target="_blank">' + fileName + "</a>")
        #
        csEditorFormOp = CSEditorForm(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        myD = csEditorFormOp.get()
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Launch chemical shift editor", formId=taskFormId, args="", completionFlag=True, tagList=tagL, entryId=entryId)
        rC = self._makeTaskResponse(tssObj=tss)
        for key, value in myD.items():
            rC.set(key, value)
        #
        return rC

    def _getCSEditorFormOp(self):
        """Generating chemical shift editor form"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._getCSEditorFormOp() starting\n")
        self._getSession(useContext=True)
        #
        csEditorFormOp = CSEditorForm(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        myD = csEditorFormOp.get()
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        for key, value in myD.items():
            rC.set(key, value)
        return rC

    def _saveCoordEditorOp(self):
        """Save editing from coord editor form's editable event"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._saveCoordEditorOp() starting\n")
        self._getSession(useContext=True)
        #
        value = self.__saveEditorValue("_coord_pickle.db")

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("html")
        rC.setHtmlText(value)
        return rC

    def _saveCSEditorOp(self):
        """Save editing from chemical shift editor form's editable event"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._saveCSEditorOp() starting\n")
        self._getSession(useContext=True)
        #
        value = self.__saveEditorValue("_cs_pickle.db")

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("html")
        rC.setHtmlText(value)
        return rC

    def __saveEditorValue(self, extension):
        did = self._reqObj.getValue("id")
        value = self._reqObj.getValue("value")
        entryId = self._reqObj.getValue("entryid")
        pickleFile = os.path.join(self._sessionPath, entryId + extension)
        #
        mapping = {}
        if os.access(pickleFile, os.F_OK):
            fb = open(pickleFile, "rb")
            mapping = pickle.load(fb)
            fb.close()
        #
        mapping[did] = value
        fb = open(pickleFile, "wb")
        pickle.dump(mapping, fb)
        fb.close()
        #
        return value

    def _updateCoordEditorOp(self):
        """Update model file"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._updateCoordEditorOp() starting\n")
        self._getSession(useContext=True)

        #
        try:
            coordEditorUpdateOp = CoordEditorUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            content = coordEditorUpdateOp.run()
        except Exception as e:
            logger.exception("In updatign editor value")
            raise e
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        if content == "OK":
            entryId = self._reqObj.getValue("entryid")
            rC.setText(text="Entry " + entryId + " updated.")
        else:
            rC.setError(errMsg=content)
        return rC

    def _updateCSEditorOp(self):
        """Update chemical shift file"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._updateCSEditorOp() starting\n")
        self._getSession(useContext=True)
        #
        #
        csEditorUpdateOp = CSEditorUpdate(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        content = csEditorUpdateOp.run()
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        if content == "OK":
            entryId = self._reqObj.getValue("entryid")
            rC.setText(text="Entry " + entryId + " CS file updated.")
        else:
            rC.setError(errMsg=content)
        return rC

    def _isWorkflow(self):
        """Determine if currently operating in Workflow Managed environment

        :Returns:
            boolean indicating whether or not currently operating in Workflow Managed environment
        """
        #
        fileSource = str(self._reqObj.getValue("filesource")).lower()
        #
        if self._verbose:
            self._lfh.write("+%s.%s() - filesource is %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, fileSource))
        #
        # add wf_archive to fix PDBe wfm issue -- jdw 2011-06-30
        #
        if fileSource in ["archive", "wf-archive", "wf_archive", "wf-instance", "wf_instance"]:
            # if the file source is any of the above then we are in the workflow manager environment
            return True
        else:
            # else we are in the standalone dev environment
            return False

    def _updateWfTrackingDb(self, p_status):
        """Private function used to udpate the Workflow Status Tracking Database

        :Params:
            ``p_status``: the new status value to which the deposition data set is being set

        :Helpers:
            wwpdb.apps.ann_tasks_v2.utils.WfTracking.WfTracking

        :Returns:
            ``bSuccess``: boolean indicating success/failure of the database update
        """
        #
        bSuccess = False
        #
        sessionId = self._sessionId
        depId = self._reqObj.getValue("identifier").upper()
        instId = self._reqObj.getValue("instance")
        classId = str(self._reqObj.getValue("classID"))
        #
        try:
            wft = WfTracking(verbose=self._verbose, log=self._lfh)
            bSuccess = wft.setInstanceStatus(depId=depId, instId=instId, classId=classId, status=p_status)
            if self._verbose:
                self._lfh.write(
                    "+%s.%s() -TRACKING status updated to '%s' for session %s \n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, p_status, sessionId)
                )
        except:  # noqa: E722 pylint: disable=bare-except
            bSuccess = False
            if self._verbose:
                self._lfh.write(
                    "+%s.%s() - TRACKING status, update to '%s' failed for session %s \n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, p_status, sessionId)
                )
            traceback.print_exc(file=self._lfh)
        #
        return bSuccess

    def __molstarDisplay(self, entryId, fileSource="archive", instance=None):
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        molDisDict = {}
        # map display in binary cif
        # list of em file types to find
        ok = du.getFilePath(entryId)
        ioObj = IoAdapterCore(verbose=self._verbose, log=self._lfh)
        dIn = ioObj.readFile(inputFilePath=ok, selectList=["em_map"])
        # initiate data_files with map-xray to be appended with em files
        data_files = [("map-xray", "bcif", "1")]
        if dIn and len(dIn) != 0:
            cObj = dIn[0].getObj("em_map")
            if cObj:
                # loop through all the map file names in the mmcif file, get content type partition num and contour
                for mapNumber in range(0, len(cObj)):
                    mapLocation = cObj.getValue("file", mapNumber)
                    if (not mapLocation) or (mapLocation == "?") or (mapLocation == "."):
                        continue
                    #
                    mapContour = cObj.getValue("contour_level", mapNumber)
                    # contour level can be a non-numerical value when not provided so some logic to fix when required
                    try:
                        float(mapContour)
                    except ValueError:
                        mapContour = float(1)
                    #
                    mapContentType = du.getContentTypeFromFileName(mapLocation)
                    mapPartitionNumber = du.getPartitionNumberFromFileName(mapLocation)

                    if (mapContentType is not None) and (mapPartitionNumber is not None):
                        data_files.append((mapContentType, "bcif", mapPartitionNumber, mapContour))
                    #
                #
            #
        #

        for data_file in data_files:
            ok = du.fetchId(entryId, contentType=data_file[0], formatType=data_file[1], fileSource=fileSource, instance=instance, partNumber=data_file[2])
            if ok:
                # Get download path and populate dictionary with information
                downloadPath = du.getWebPath()
                logging.info(downloadPath)

                mapInfoDictionary = {"url_name": downloadPath, "displayName": "{}-{}".format(data_file[0], data_file[2])}
                # If data_file == 4 then contour level should be present, I'm sure this could be made more intelligent
                # Add to dictionary if present
                if len(data_file) == 4:
                    mapInfoDictionary["contourLevel"] = float(data_file[3])

                # Assign colours to different map types and add to dictionary
                if data_file[0] == "em-volume":
                    mapColour = "0x666666"
                    mapInfoDictionary["mapColor"] = mapColour
                elif data_file[0] == "em-half-volume" and int(data_file[2]) == 1:
                    mapColour = "0x8FCE00"
                    mapInfoDictionary["mapColor"] = mapColour
                elif data_file[0] == "em-half-volume" and int(data_file[2]) == 2:
                    mapColour = "0x38761D"
                    mapInfoDictionary["mapColor"] = mapColour
                elif data_file[0] == "em-mask-volume":
                    mapColour = "0x3D85C6"
                    mapInfoDictionary["mapColor"] = mapColour
                else:
                    mapColour = "0xFF9900"
                    mapInfoDictionary["mapColor"] = mapColour
                # append molDisDict with dictionary populated above
                molDisDict.setdefault("molStar-maps", []).append(mapInfoDictionary)

        return molDisDict

    def _molstarMapsJson(self):
        self._getSession(useContext=True)
        self._rltvSessionPath = self._sObj.getRelativePath()

        self._lfh.write("launchMolstarDisplayOp started")
        entryId = self._reqObj.getValue("entryid")
        self._lfh.write("Entry id = {}".format(entryId))
        molstarDisplayDict = self.__molstarDisplay(entryId)
        self._lfh.write("{}".format(molstarDisplayDict))

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.setHtmlText(json.dumps(molstarDisplayDict.get("molStar-maps", [])))
        return rC

    def _renderCheckReports(self, entryId, fileSource="archive", instance=None, contentTypeList=None, useModelFileVersion=True):
        """Prepare HTML rendered reports for existing check report content for input Id code and fileSource.

             Rendered content is returned in a dictionary with the following content keys plus a tag list
             of the data files containing the report data for each content type.

        Content types --

        'model'                       :  (['pdbx'], 'model'),
        'model-pdb'                   :  (['pdb'], 'model'),
        'dict-check-report'           :  (['txt'], 'dict-check-report'),
        'dict-check-report-r4'        :  (['txt'], 'dict-check-report-r4'),
        'dict-check-report-next'      :  (['txt'], 'dict-check-report-next'),
        'xml-check-report'            :  (['txt'], 'xml-check-report'),
        'format-check-report'         :  (['txt'], 'format-check-report'),
        'misc-check-report'           :  (['txt'], 'misc-check-report'),
        'special-position-report'     :  (['txt'], 'special-position-report'),
        'dcc-report'                  :  (['pdbx','txt'], 'dcc-report'),
        'geometry-check-report'       :  (['pdbx'],'geometry-check-report'),

        Special key 'entry-info' contains a dictionary of items to populate page  header/title -

        'entry-info'                  :  {'pdb_id' : value, 'struct_title': value, 'my_entry_id': value, 'useversion': '1'}

        """
        self._lfh.write("+CommonTasksWebAppWorker._renderCheckReports contentTypeList %s\n" % contentTypeList)
        if contentTypeList is None:
            contentTypeList = []
        layout = "multiaccordion"
        #
        myD = {}
        for ky in [
            "model",
            "dcc-report",
            "geometry-check-report",
            "misc-check-report",
            "format-check-report",
            "dict-check-report",
            "dict-check-report-r4",
            "dict-check-report-next",
            "xml-check-report",
            "special-position-report",
            "emd-xml-header-report",
            "em-map-check-report",
            "downloads",
        ]:
            myD[ky] = None
        myD["entry-info"] = {
            "pdb_id": "",
            "struct_title": "",
            "my_entry_id": entryId,
            "useversion": "1",
            "usesaved": "yes",
        }
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        dTagList = []
        vTagList = []
        #
        pR = PdbxReport(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        #
        for cT in contentTypeList:
            if cT == "model":
                # Model report
                if useModelFileVersion:
                    versionId = "latest"
                else:
                    versionId = "none"
                ok = du.fetchId(entryId, contentType="model", formatType="pdbx", fileSource=fileSource, instance=instance, versionId=versionId)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = "\n".join(pR.makeTabularReport(filePath=downloadPath, contentType="model", idCode=entryId, layout=layout))

                    downloadWebPath = du.getWebPath()
                    myD["model-session"] = downloadWebPath
                    # pdb_id = pR.getPdbIdCode()
                    # if pdb_id:
                    #    pass
                    myD.setdefault("molStar-display-objects", []).append('molecule_url:"{}"'.format(downloadWebPath))

                else:
                    myD[cT] = self.__getMessageTextWithMarkup("No model data file.")
                    myD["model-session"] = ""

                myD["entry-info"] = {"pdb_id": pR.getPdbIdCode(), "struct_title": pR.getStructTitle(), "my_entry_id": entryId, "useversion": "1", "usesaved": "yes"}

            elif cT == "model-pdb":
                ok = du.fetchId(entryId, contentType="model", formatType="pdb", fileSource=fileSource, instance=instance, versionId="none")
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getMessageTextWithMarkup("Download converted PDB format file.")

            elif cT == "dcc-report":
                # DCC report
                ok = du.fetchId(entryId, contentType="dcc-report", formatType="pdbx", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = "\n".join(pR.makeTabularReport(filePath=downloadPath, contentType="dcc-report", idCode=entryId, layout=layout))

                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No X-ray experimental data check report.')
                    myD[cT] = self.__getMessageTextWithMarkup("")
            elif cT == "geometry-check-report":
                # Geometry report
                ok = du.fetchId(entryId, contentType="geometry-check-report", formatType="pdbx", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = "\n".join(pR.makeTabularReport(filePath=downloadPath, contentType="geometry-check-report", idCode=entryId, layout=layout))
                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No geometry issues.')
                    myD[cT] = self.__getMessageTextWithMarkup("")
            elif cT == "misc-check-report":
                # Misc check report
                ok = du.fetchId(entryId, contentType="misc-check-report", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)
                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No miscellaneous issues.')
                    myD[cT] = self.__getMessageTextWithMarkup("")
            elif cT == "format-check-report":
                # Format check report
                ok = du.fetchId(entryId, contentType="format-check-report", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)
                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No format check issues.')
                    myD[cT] = self.__getMessageTextWithMarkup("")
            elif cT == "dict-check-report":
                # Dictionary check report
                ok = du.fetchId(entryId, contentType="dict-check-report", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)
                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No dictionary check issues.')
                    myD[cT] = self.__getMessageTextWithMarkup("")
            elif cT == "xml-check-report":
                # Dictionary check report
                ok = du.fetchId(entryId, contentType="xml-check-report", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)
                else:
                    myD[cT] = self.__getMessageTextWithMarkup("")
            elif cT == "dict-check-report-r4":
                # Dictionary check report
                ok = du.fetchId(entryId, contentType="dict-check-report-r4", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)
                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No dictionary check issues.')
                    myD[cT] = self.__getMessageTextWithMarkup("")
            elif cT == "dict-check-report-next":
                # Dictionary check report
                ok = du.fetchId(entryId, contentType="dict-check-report-next", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)
                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No dictionary check issues.')
                    myD[cT] = self.__getMessageTextWithMarkup("")
            elif cT == "xml-check-report":
                # Xml check report
                ok = du.fetchId(entryId, contentType="xml-check-report", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)
                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No xml check issues.')
                    myD[cT] = self.__getMessageTextWithMarkup("")
            elif cT == "special-position-report":
                #
                ok = du.fetchId(entryId, contentType="special-position-report", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)

                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No special positions.')
                    # Biocuration requested no message be returned
                    myD[cT] = ""

            elif cT == "emd-xml-header-report":
                # EMD XML header generation report
                ok = du.fetchId(entryId, contentType="emd-xml-header-report", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)
                else:
                    # myD[cT] = self.__getMessageTextWithMarkup('No XML generation report.')
                    myD[cT] = self.__getMessageTextWithMarkup("")

            elif cT == "em-map-check-report":
                # em_map checking report
                ok = du.fetchId(entryId, contentType="em-map-check-report", formatType="txt", fileSource=fileSource, instance=instance)
                if ok:
                    downloadPath = du.getDownloadPath()
                    aTagList.append(du.getAnchorTag())
                    myD[cT] = self.__getFileTextWithMarkup(downloadPath)
                else:
                    myD[cT] = self.__getMessageTextWithMarkup("")

        # downloads

        for data_file in (
            ("model", "pdbx"),
            ("model", "pdb"),
            ("structure-factors", "pdbx"),
            ("nmr-chemical-shifts", "pdbx"),
            ("nmr-data-str", "pdbx"),
            # ('em-volume', 'map')
        ):
            ok = du.fetchId(entryId, contentType=data_file[0], formatType=data_file[1], fileSource=fileSource, instance=instance)
            if ok:
                downloadPath = du.getDownloadPath()
                dTagList.append(du.getAnchorTag())
                data_file_report = "{}-report".format(data_file[0])
                # myD[data_file_report] = self.__getFileTextWithMarkup(downloadPath)
                myD[data_file_report] = self.__getMessageTextWithMarkup(downloadPath)

        if len(dTagList) > 0:
            myD["data-downloads"] = '<div class="container"><p> <span class="url-list">%s</span></p></div>' % "<br />".join(dTagList)
        else:
            myD["data-downloads"] = ""

        # EM image

        ok = du.fetchId(entryId, contentType="img-emdb", formatType="png", fileSource=fileSource, instance=instance)
        if ok:
            downloadPath = du.getWebPath()
            myD["em_image"] = '<div class="container"><p><img src={} alt="EM image "style="width:600px"></p></div><br />'.format(downloadPath)
            myD["em_image_sidebar"] = '<img src={} alt="EM image "style="max-width:99%">'.format(downloadPath)
        else:
            myD["em_image"] = ""
            myD["em_image_sidebar"] = ""

        ok = du.fetchId(entryId, contentType="validation-report-slider", formatType="png", fileSource=fileSource, instance=instance)
        if ok:
            downloadPath = du.getWebPath()
            myD["val_image"] = '<div class="container"><p><img src={} alt="validation slider "style="width:600px"></p></div><br />'.format(downloadPath)
        else:
            myD["val_image"] = ""

        # validation downloads

        for val_file in (("validation-report-full", "pdf"), ("validation-data", "xml"), ("validation-data", "pdbx"), ("validation-report-slider", "png")):
            ok = du.fetchId(entryId, contentType=val_file[0], formatType=val_file[1], fileSource=fileSource, instance=instance)
            if ok:
                downloadPath = du.getDownloadPath()
                vTagList.append(du.getAnchorTag())
                # myD[val_file[0]] = self.__getFileTextWithMarkup(downloadPath)
                myD[val_file[0]] = self.__getMessageTextWithMarkup(downloadPath)

        if len(vTagList) > 0:
            myD["validation-downloads"] = '<div class="container"><p> <span class="url-list">%s</span></p></div>' % "<br />".join(vTagList)
        else:
            myD["validation-downloads"] = ""

        if len(aTagList) > 0:
            myD["downloads"] = '<div class="container"><p> <span class="url-list">%s</span></p></div>' % "<br />".join(aTagList)
        myD["identifier"] = entryId
        myD["aTagList"] = aTagList

        # Generate a dictionary with EM map URLs, contour levels and colours
        molstarDisplayDictionary = self.__molstarDisplay(entryId)

        if myD.get("molStar-display-objects"):
            molStarMapsJson = "mapsList:{}".format(json.dumps(molstarDisplayDictionary.get("molStar-maps", [])))
            display_object_str = ",".join(myD.get("molStar-display-objects", []) + [molStarMapsJson])
            logging.debug("MOLSTAR COMMAND: %s", display_object_str)
            myD["molStar"] = """onLoad='display_mol_star({{{}}})'""".format(display_object_str)
            myD["molStar-display"] = '<div id="myViewer">display_mol_star()</div>'

        else:
            myD["molStar"] = ""
            myD["molStar-display"] = "no model available"
        #
        return myD

    def _makeCheckReports(self, entryIdList, fileSource="wf-archive", operationList=None, useFileVersions=True):
        """Create reports from the input operation list, using data files from the input fileSource.
             Copy reports to the session download directory (e.g. output file source = 'session-download')
             and return a list of html anchors tags for the report files.

        Content type list --

        'dict-check-report'           :  (['txt'], 'dict-check-report'),
        'dict-check-report-r4'        :  (['txt'], 'dict-check-report-r4'),
        'dict-check-report-next'      :  (['txt'], 'dict-check-report-next'),
        'xml-check-report'            :  (['txt'], 'xml-check-report'),
        'format-check-report'         :  (['txt'], 'format-check-report'),
        'misc-check-report'           :  (['txt'], 'misc-check-report'),
        'special-position-report'     :  (['txt'], 'special-position-report'),
        'dcc-report'                  :  (['pdbx','txt'], 'dcc-report'),
        'geometry-check-report'       :  (['pdbx'],'geometry-check-report'),
        'emd-xml-header-report'       :  (['txt'], 'emd-xml-header-report'),
        'em-map-check-report'         :  (['txt'], 'em-map-check-report'),

        """
        #
        if operationList is None:
            operationList = ["check"]

        if useFileVersions:
            versionId = "latest"
        else:
            versionId = "none"
        duL = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        formatType = "pdbx"

        self._lfh.write("+CommonTasksWebAppWorker._makeCheckReports() starting ops %s \n" % operationList)

        for entryId in entryIdList:
            ok = duL.fetchId(entryId, "model", formatType=formatType, fileSource=fileSource, versionId=versionId)
            if not ok:
                continue

            modelFilePath = duL.getDownloadPath()
            if "cif2pdb" in operationList:
                chk = PdbFile(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                ok = chk.runAlt(entryId=entryId, inpPath=modelFilePath)
                if ok:
                    pdbPath = chk.getPdbFilePath()
                    duL.copyToDownload(pdbPath)
                    aTagList.append(duL.getAnchorTag())

            if "checkv5" in operationList:
                chk = Check(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                chk.setDictionaryVersion(version="V5")
                # Internal model file - check first block only
                chk.setCheckFirstBlock(True)

                chk.run(entryId=entryId, inpPath=modelFilePath)
                rptPath = chk.getReportPath()
                hasDiags = chk.getReportSize() > 0
                if hasDiags:
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())
                else:
                    duL.removeFromDownload(rptPath)

            if "checkv4" in operationList:
                chk = Check(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                chk.setDictionaryVersion(version="V4")
                chk.run(entryId=entryId, inpPath=modelFilePath)
                rptPath = chk.getReportPath()
                hasDiags = chk.getReportSize() > 0
                if hasDiags:
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())
                else:
                    duL.removeFromDownload(rptPath)

            if "checkNext" in operationList:
                self._lfh.write("+CommonTasksWebAppWorker._makeCheckReports() starting checkNext\n")

                chk = Check(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                # Public check - should have first block only
                chk.setDictionaryVersion(version="archive_next")
                chk.run(entryId=entryId, inpPath=modelFilePath)
                rptPath = chk.getReportPath()
                hasDiags = chk.getReportSize() > 0
                if hasDiags:
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())
                else:
                    duL.removeFromDownload(rptPath)

            if "checkxml" in operationList:
                self._lfh.write("+CommonTasksWebAppWorker._makeCheckReports() starting checkxml\n")

                xchk = XmlCheck(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                pdbxPath = os.path.join(self._sessionPath, entryId + "_model-next_P1.cif")
                if os.access(pdbxPath, os.R_OK):
                    self._lfh.write("+CommonTasksWebAppWorker._makeCheckReports() starting checkxml using %s\n" % pdbxPath)
                    xchk.run(entryId=entryId, inpPath=pdbxPath, publicCIFlag=True)
                else:
                    self._lfh.write("+CommonTasksWebAppWorker._makeCheckReports() starting checkxml using %s\n" % modelFilePath)
                    xchk.run(entryId=entryId, inpPath=modelFilePath, publicCIFlag=False)
                #
                rptPath = xchk.getReportPath()
                hasDiags = xchk.getReportSize() > 0
                if hasDiags:
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())
                else:
                    duL.removeFromDownload(rptPath)

            if "check-format" in operationList:
                chk = FormatCheck(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                chk.run(entryId=entryId, inpPath=modelFilePath)
                hasDiags = chk.getReportSize() > 0
                if hasDiags:
                    rptPath = chk.getReportPath()
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())

            if "check-misc" in operationList:
                chk = ExtraCheck(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                chk.run(entryId=entryId, inpPath=modelFilePath)
                hasDiags = chk.getReportSize() > 0
                if hasDiags:
                    rptPath = chk.getReportPath()
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())

            if "check-geometry" in operationList:
                chk = GeometryCheck(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                chk.run(entryId=entryId, inpPath=modelFilePath)
                hasDiags = chk.getReportSize() > 0
                if hasDiags:
                    rptPath = chk.getReportPath()
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())

            if "check-special-position" in operationList:
                chk = SpecialPositionCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                chk.run(entryId=entryId, modelInputFile=modelFilePath)
                hasDiags = chk.getReportSize() > 0
                if hasDiags:
                    rptPath = chk.getReportPath()
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())

            if "check-emd-xml" in operationList:
                try:
                    chk = EmdXmlCheck(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                    chk.run(entryId=entryId, modelInputFile=modelFilePath)
                except Exception as e:
                    logger.error("Error running EmdXmlCheck %s", e)
                hasDiags = chk.getReportSize() > 0
                rptPath = chk.getReportPath()
                if hasDiags:
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())
                else:
                    duL.removeFromDownload(rptPath)

            if "check-em-map" in operationList:
                try:
                    chk = EmMapCheck(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                    chk.run(entryId=entryId, modelInputFile=modelFilePath)
                except Exception as e:
                    logger.error("Error running EmMapCheck %s", e)
                hasDiags = chk.getReportSize() > 0
                rptPath = chk.getReportPath()
                if hasDiags:
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())
                else:
                    duL.removeFromDownload(rptPath)

            if "check-sf" in operationList:
                ok = duL.fetchId(entryId, contentType="structure-factors", formatType="pdbx", fileSource=fileSource, versionId=versionId)
                expFilePath = duL.getDownloadPath()
                chk = DccCalc(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                ok = chk.run(entryId=entryId, modelInputPath=modelFilePath, expInputPath=expFilePath)
                if ok:
                    rptPath = chk.getReportPath()
                    duL.copyToDownload(rptPath)
                    aTagList.append(duL.getAnchorTag())

        self._lfh.write("+CommonTasksWebAppWorker._makeCheckReports() complete\n")

        return aTagList

    def __getMessageTextWithMarkup(self, message):
        """Internal methods used by _makeCheckReports()"""
        oL = []
        oL.append('<div class="highlight">')
        oL.append("<pre>")
        oL.append(message)
        oL.append("</pre>")
        oL.append("</div>")
        return "\n".join(oL)

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

    # --------------------------------------------------------------------------------------------------
    #               ID-level check and report operations - returning content in JSON objects --
    #
    def _fetchAndReportIdOps(self):
        """Entry point to handle fetch and report operations on data files identified by id and type.

        Returns Json object containing download links and HTML reports
        """
        self._getSession()
        operation = self._reqObj.getValue("operation")
        if self._verbose:
            self._lfh.write("+ReviewDataWebAppWorker._fetchAndReportIdOps() starting with op %s\n" % operation)

        entryIds = self._reqObj.getValue("entryid")
        entryIdList = entryIds.strip().split(" ")  # Handles case of space at end of list
        contentType = self._reqObj.getValue("contentType")

        fileSource = self._reqObj.getValue("filesource")

        if fileSource in ["archive", "wf-archive", "wf-instance"]:
            useFileVersions = True
        else:
            useFileVersions = False

        if self._verbose:
            self._lfh.write("+ReviewDataWebAppWorker._fetchAndReportIdOps() content %s fetch id(s) %r\n" % (contentType, entryIdList))
        #
        if operation == "fetch_entry":
            return self._makeIdListFetchResponse(entryIdList, contentType="model", formatType="pdbx", fileSource=fileSource)
        elif operation == "fetch_sf":
            return self._makeIdListFetchResponse(entryIdList, contentType="structure-factors", formatType="pdbx", fileSource=fileSource)
        elif operation == "fetch_map":
            return self._makeIdListFetchResponse(entryIdList, contentType="em-volume", formatType="map", fileSource=fileSource)
        elif operation == "fetch_cs":
            return self._makeIdListFetchResponse(entryIdList, contentType="nmr-chemical-shifts", formatType="pdbx", fileSource=fileSource)
        elif operation == "fetch_mr":
            return self._makeIdListFetchResponse(entryIdList, contentType="nmr-restraints", formatType="mr", fileSource=fileSource)
        elif operation == "fetch_nmr_data":
            return self._makeIdListFetchResponse(entryIdList, contentType="nmr-data-str", formatType="pdbx", fileSource=fileSource)
        elif operation == "report":
            return self._makeIdListModelReportResponse(entryIdList, contentType, fileSource=fileSource, useFileVersions=useFileVersions)
        #
        elif operation == "files-archive":
            return self._listFilesResponse(entryIdList[0], fileSource="archive")
        elif operation == "files-deposit":
            return self._listFilesResponse(entryIdList[0], fileSource="deposit")
        elif operation == "files-instance":
            return self._listFilesResponse(entryIdList[0], fileSource="wf-instance")
        elif operation in [
            "check-all",
            "cif2pdb",
            "checkv5",
            "checkNext",
            "check-format",
            "check-misc",
            "check-geometry",
            "check-special-position",
            "check-sf",
            "check-emd-xml",
            "checkxml",
        ]:
            #
            templateFilePath = os.path.join(self._reqObj.getValue("TemplatePath"), "consolidated_section_template.html")
            self._lfh.write("+ReviewDataWebAppWorker._fetchAndReportIdOps() templateFilePath %s\n" % templateFilePath)

            webIncludePath = os.path.join(self._reqObj.getValue("TopPath"), "htdocs")
            return self._generateCheckReportsJson(
                entryIdList[0], operation, fileSource=fileSource, templateFilePath=templateFilePath, webIncludePath=webIncludePath, useFileVersions=useFileVersions
            )
        else:
            pass

    def _generateCheckReportsJson(self, entryId, operation, fileSource="wf-archive", templateFilePath=None, webIncludePath=None, useFileVersions=True):
        """Generate"""
        #
        # opCtD - this dictionary maps input check request operation names to project report content types -
        #
        opCtD = {
            "checkv5": "dict-check-report",
            # 'checkv4': 'dict-check-report-r4',
            "checkNext": "dict-check-report-next",
            "checkxml": "xml-check-report",
            "check-misc": "misc-check-report",
            "check-format": "format-check-report",
            "check-geometry": "geometry-check-report",
            "check-sf": "dcc-report",
            "check-special-position": "special-position-report",
            "cif2pdb": "model-pdb",
            "check-emd-xml": "emd-xml-header-report",
            "check-em-map": "em-map-check-report",
        }

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        if operation in ["check-all"]:
            opList = [
                "cif2pdb",
                "checkv5",
                "checkNext",
                "checkxml",
                "check-format",
                "check-misc",
                "check-geometry",
                "check-special-position",
                "check-sf",
                "check-emd-xml",
                "check-em-map",
            ]
            aTagList = self._makeCheckReports([entryId], operationList=opList, fileSource=fileSource, useFileVersions=useFileVersions)
            cTList = ["model"]
            cTList.extend(sorted(opCtD.values()))
            if self._verbose:
                self._lfh.write("+ReviewDataWebAppWorker._reviewDataInlineIdOps() content type list %r\n" % cTList)
            myD = self._renderCheckReports(entryId, fileSource="session-download", instance=None, contentTypeList=cTList, useModelFileVersion=useFileVersions)
            rC.setHtmlTextFromTemplate(templateFilePath=templateFilePath, webIncludePath=webIncludePath, parameterDict=myD, insertContext=True)
            rC.setStatus(statusMsg="Check reports completed")
        else:
            opList = [operation]
            aTagList = self._makeCheckReports([entryId], operationList=opList, fileSource=fileSource, useFileVersions=useFileVersions)
            #
            cT = opCtD[operation]
            myD = self._renderCheckReports(entryId, fileSource="session-download", instance=None, contentTypeList=[cT], useModelFileVersion=useFileVersions)

            html = myD[cT]
            if len(aTagList) > 0:
                rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
                if html is not None:
                    rC.setHtmlList([html])
                else:
                    rC.setHtmlList([])
                rC.setStatus(statusMsg="Check report(s) completed")
            else:
                rC.setError(errMsg="Checks completed - no diagnostics")

        return rC

    #
    # Internal methods for creating json packaged responses to fetch, model-report and check report requests
    # starting from a request containing a data set id code & content type.

    def _makeIdListFetchResponse(self, entryIdList, contentType, formatType="pdbx", fileSource="wf-archive"):  # pylint: disable=unused-argument
        """Fetch files of the input content type and present download links."""
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        if len(entryIdList) > 0:
            rC.set("entryid", entryIdList[0])
        #
        du = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        for entryId in entryIdList:
            if du.fetchId(entryId, contentType, formatType=formatType):
                aTagList.append(du.getAnchorTag())

        if len(aTagList) > 0:
            rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
            rC.setStatus(statusMsg="Fetch completed")
        else:
            rC.setError(errMsg="No corresponding file(s)")
            # do nothing

        return rC

    def _makeIdListModelReportResponse(self, entryIdList, contentType="model", formatType="pdbx", fileSource="archive", useFileVersions=True):  # pylint: disable=unused-argument
        """Prepare JSON response for a report request for the input Id code list."""
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        if len(entryIdList) > 0:
            rC.set("entryid", entryIdList[0])
        #
        aTagList = []
        htmlList = []

        for entryId in entryIdList:
            myD = self._renderCheckReports(entryId, fileSource=fileSource, instance=None, contentTypeList=[contentType], useModelFileVersion=useFileVersions)
            htmlList.append(myD[contentType])
            aTagList.extend(myD["aTagList"])

        if len(aTagList) > 0:
            rC.setHtmlLinkText('<span class="url-list">Download: %s</span>' % ",".join(aTagList))
            rC.setHtmlList(htmlList)
            rC.setStatus(statusMsg="Reports completed")
        else:
            rC.setError(errMsg="No corresponding data file(s)")
            # do nothing

        return rC

    ##
    ##

    def _entryInfoOp(self):
        """Return json object containing essential entry information  (e.g. accession codes, title)."""
        # [(application key,  attribute key), ....]  --
        kyPairList = [
            ("struct_title", "struct_title"),
            ("pdb_id", "pdb_id"),
            ("emdb_id", "emdb_id"),
            ("bmrb_id", "bmrb_id"),
            ("experimental_methods", "experimental_methods"),
            ("statuscode", "status_code"),
            ("authrelcode", "auth_release_code"),
            ("initialdepositdate", "deposit_date"),
            ("holdcoordinatesdate", "hold_coord_date"),
            ("coordinatesdate", "coord_date"),
            ("approval_type", "approval_type"),
            ("annotator_initials", "annotator_initials"),
            ("deposit_site", "deposit_site"),
            ("process_site", "process_site"),
            ("reqacctypes", "reqacctypes"),
            ("postrelstatuscode", "post_rel_status_code"),
            ("postrelrecvdcoord", "post_rel_recvd_coord"),
            ("postrelrecvdcoorddate", "post_rel_recvd_coord_date"),
        ]

        kyPairListEm = [
            ("em_entry_id", "em_entry_id"),
            ("em_current_status", "em_current_status"),
            ("em_deposition_date", "em_deposition_date"),
            ("em_deposition_site", "em_deposition_site"),
            ("em_obsoleted_date", "em_obsoleted_date"),
            ("em_details", "em_details"),
            ("em_last_update", "em_last_update"),
            ("em_map_release_date", "em_map_release_date"),
            ("em_map_hold_date", "em_map_hold_date"),
            ("em_replace_existing_entry_flag", "em_replace_existing_entry_flag"),
            ("em_title", "em_title"),
            ("em_header_release_date", "em_header_release_date"),
        ]

        # Limit what is returned
        kyPairListEmDepui = [
            # ('em_depui_entry_id', 'em_depui_entry_id'),
            ("em_depui_depositor_hold_instructions", "em_depui_depositor_hold_instructions"),
            # ('em_depui_macromolecule_description', 'em_depui_macromolecule_description'),
            # ('em_depui_obsolete_instructions', 'em_depui_obsolete_instructions'),
            # ('em_depui_same_authors_as_pdb', 'em_depui_same_authors_as_pdb'),
            # ('em_depui_same_title_as_pdb', 'em_depui_same_title_as_pdb')
        ]

        kyPairList.extend(kyPairListEm)
        kyPairList.extend(kyPairListEmDepui)
        #
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._entryInfoOp() starting\n")

        self._getSession(useContext=True)
        fileName = self._reqObj.getValue("entryfilename")
        entryId = self._reqObj.getValue("entryid")
        myEntryId = self._reqObj.getValue("my_entryid")
        useFileVersion = self._reqObj.getValue("useversion")
        useSaved = self._reqObj.getValue("usesaved")

        if self._verbose:
            self._lfh.write(
                "+CommonTasksWebAppWorker._entryInfoOp() entryId %r myEntryId %r fileName %r useFileVersion %r useSaved %r\n"
                % (entryId, myEntryId, fileName, useFileVersion, useSaved)
            )
        #
        # use any existing session data values as appropriate
        #
        myD = {}
        if useSaved == "yes":
            for kyPair in kyPairList:
                myD[kyPair[0]] = self._reqObj.getValue(kyPair[0])
            myD["my_entryid"] = self._reqObj.getValue("my_entryid")
        elif entryId is None or (len(entryId) < 1) or entryId != myEntryId:
            for kyPair in kyPairList:
                myD[kyPair[0]] = ""
            myD["my_entryid"] = ""
        else:
            for kyPair in kyPairList:
                myD[kyPair[0]] = self._reqObj.getValue(kyPair[0])
            myD["my_entryid"] = self._reqObj.getValue("my_entryid")
        #
        #   Reload the model file if the context has changed  (e.g. missing or changed entryId/pdbId)
        #
        # if (((entryId is not None) and (len(entryId) > 2)) and ((entryId != myEntryId) or (myD['pdb_id'] is None) or (len(myD['pdb_id']) < 1))):
        if (entryId is not None) and (len(entryId) > 2) and (entryId != myEntryId):
            pdbxI = PdbxEntryInfoIo(verbose=self._verbose, log=self._lfh)
            pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
            if useFileVersion == "1":
                filePath = pI.getModelPdbxFilePath(dataSetId=entryId, fileSource="session-download", versionId="latest")
            else:
                filePath = pI.getModelPdbxFilePath(dataSetId=entryId, fileSource="session", versionId="none")
            #
            pdbxI.setFilePath(filePath)
            pdbxI.get()
            #
            oD = pdbxI.getInfoD(contextType="info")
            if ("emdb_id" in oD) and (oD["emdb_id"] is not None) and (len(oD["emdb_id"]) > 0):
                oD.update(pdbxI.getInfoD(contextType="em_admin"))
                oD.update(pdbxI.getInfoD(contextType="em_depui"))
            #
            for kyPair in kyPairList:
                if kyPair[1] in oD:
                    myD[kyPair[0]] = oD[kyPair[1]]
                else:
                    myD[kyPair[0]] = ""
            # Save entryid in pkl file
            myD["my_entryid"] = entryId
            self._saveSessionParameter(pvD=myD, prefix=self._udsPrefix)
        #
        comb_id = ""
        for key in ("pdb_id", "emdb_id", "bmrb_id", "my_entryid"):
            if (key not in myD) or (not myD[key]):
                continue
            #
            if comb_id != "":
                comb_id += "/"
            #
            comb_id += myD[key]
        #
        if comb_id:
            myD["comb_id"] = comb_id
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=myD)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._entryInfoOp() COMPLETED with return data\n")
            for k, v in myD.items():
                self._lfh.write("%30s = %s\n" % (k, v))
        return rC
        ##
        ##

    def _listEmMapsOp(self):
        """Return json object containing a rendered list of masks and maps linked to edit/update operations."""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._listEmMapsOp() starting\n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        #
        # Use any existing session data values as appropriate
        #
        #
        myD = {}
        myD["map_list"] = ""
        myD["mask_list"] = ""
        myD["additional_map_list"] = ""
        myD["half_map_list"] = ""
        myD["em_download_files"] = ""
        myD["my_entryid"] = entryId

        # if (useSaved =='never'):
        #    myD['map_list']=self._reqObj.getValue("map_list")
        #    myD['mask_list']=self._reqObj.getValue("mask_list")
        #
        #
        if len(entryId) > 0:
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._listEmMapsOp() map list for %r\n" % entryId)
            myD.update(self.__emListMaps(entryId))
            for ky in myD.keys():
                self._lfh.write("+CommonTasksWebAppWorker._listEmMapsOp() ky %s length %d\n" % (ky, len(myD[ky])))
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=myD)
        return rC

    def __emListMaps(self, entryId, fileSource="archive"):
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker.__emListMaps() map list for %r\n" % entryId)

        myD = {}
        ctupL = [
            ("em-volume", "map file", "map_list"),
            ("em-mask-volume", "mask files", "mask_list"),
            ("em-additional-volume", "additional map files", "additional_map_list"),
            ("em-half-volume", "half volume files", "half_map_list"),
        ]
        #
        emu = EmUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        for ctup in ctupL:
            title = "Edit " + fileSource + " " + ctup[1]
            nMap, htmlText = emu.renderEmMapFileList(entryId, contentType=ctup[0], fileSource=fileSource, colTextHtml=title)
            if nMap > 0:
                myD[ctup[2]] = htmlText
        #
        # Make a separate table EM related content types for download -
        #
        fu = FileUtils(entryId, reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        nFiles, htmlList = fu.renderFileList(fileSource=fileSource, rDList=["3DEM Files"], titleSuffix=" for Download ", displayImageFlag=True)
        if nFiles > 0:
            myD["em_download_files"] = "\n".join(htmlList)
        #
        if self._verbose:
            for k, v in myD.items():
                self._lfh.write("+CommonTasksWebAppWorker.__emListMaps() ky %s  v %r\n" % (k, v))

        return myD

    def _editEmMapHeaderOp(self):
        """Return json object containing a rendered collection forms displaying map header details and edit operations."""
        doFigure = True
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._editEmMapHeaderOp() starting \n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")

        # selected archive map/mask file ---
        mapFileName = self._reqObj.getValue("map_file_name")
        emdbId = self._reqObj.getValue("emdb_id")
        #
        # use any existing session data values as appropriate
        #
        myD = {}
        myD["my_entryid"] = entryId
        myD["map_header_html"] = ""
        myD["map_density_plot"] = ""
        myD["map_edit_status"] = ""

        # if (useSaved =='yes'):
        #    myD['map_header_html']=self._reqObj.getValue("map_header_html")
        #
        duL = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        if (len(entryId) > 0) and (len(mapFileName) > 0):
            emu = EmUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            emed = EmEditUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            #  mapHeaderFilePath will contain the json encoding of the map header info ---
            ok, mapHeaderFilePath, mapHeaderLogFilePath = emed.getArchiveMapHeader(entryId, mapFileName)
            #
            duL.copyToDownload(mapHeaderLogFilePath)
            aTagList.append(duL.getAnchorTag())
            duL.copyToDownload(mapHeaderFilePath)
            aTagList.append(duL.getAnchorTag())
            #
            #
            mD = {}
            mapType = None
            partitionNo = None
            try:
                pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
                modelFilePath = pI.getModelPdbxFilePath(dataSetId=entryId, fileSource="session", versionId="none")
                emx = EmModelUtils(verbose=self._verbose, log=self._lfh)
                ok1 = emx.setModelFilePath(modelFilePath)
                if ok1:
                    mapType, partitionNo = emed.getMapFileNameDetails(mapFileName)
                    mD = emx.getDepositorMapDetails(mapType, partitionNo)

                if self._verbose:
                    self._lfh.write("+CommonTasksWebAppWorker._editEmMapHeaderOp() type %r partitionNo %r modelD %r\n" % (mapType, partitionNo, mD.items()))
            except:  # noqa: E722 pylint: disable=bare-except
                if self._verbose:
                    self._lfh.write("+CommonTasksWebAppWorker._editEmMapHeaderOp() failing model file %r\n" % modelFilePath)
                    traceback.print_exc(file=self._lfh)
            #
            if emdbId is not None and len(emdbId) > 1:
                mD["emdb_id"] = emdbId
            #
            if ok:
                ok1, htmlText = emed.renderMapHeaderEditForm(entryId, mapHeaderFilePath, mapFileName, modelD=mD, mapType=mapType, partition=partitionNo)
                if ok1 and len(htmlText) > 0:
                    myD["map_header_html"] = htmlText
                if doFigure:
                    ok2, _imgFp, imgTag = emu.plotMapDensity(mapHeaderFilePath, "figure.svg", plotFormat="svg")
                    if ok2:
                        myD["map_density_plot"] = imgTag

            else:
                myD["map_edit_status"] = "Reading map header failed"
        else:
            myD["map_edit_status"] = "Reading map header failed"

        #
        if len(aTagList) > 0:
            myD["map_edit_links"] = '<span class="url-list">Download: %s</span>' % ",&nbsp;".join(aTagList)

        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._editEmMapHeaderOp() data object k %r\n" % myD.keys())
            self._lfh.write("+CommonTasksWebAppWorker._editEmMapHeaderOp() link atags %r\n" % aTagList)

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=myD)
        return rC

    def _editEmMapHeaderResponderOp(self):
        """Reponder to edit operations from editEmMapHeaderResponderOp() --"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._editEmMapHeaderResponderOp() starting\n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")

        # selected archive map/mask file ---
        mapFileName = self._reqObj.getValue("map_file_name")
        #
        # Use any existing session data values as appropriate
        #
        myD = {}
        myD["my_entryid"] = entryId
        myD["my_edit_status"] = ""

        # if (useSaved =='yes'):
        #    pass
        #
        duL = SessionDownloadUtils(self._reqObj, verbose=self._verbose, log=self._lfh)
        aTagList = []
        #
        if (len(entryId) > 0) and (len(mapFileName) > 0):
            emu = EmUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            emed = EmEditUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            _ok, nextJsonPath, nextLogPath, nextMapFilePath = emed.updateMapHeader(entryId, mapFileName)
            duL.copyToDownload(nextLogPath)
            aTagList.append(duL.getAnchorTag())
            duL.copyToDownload(nextJsonPath)
            aTagList.append(duL.getAnchorTag())
            try:
                pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
                modelFilePath = pI.getModelPdbxFilePath(dataSetId=entryId, fileSource="session", versionId="none")
                emx = EmModelUtils(verbose=self._verbose, log=self._lfh)
                _ok1 = emx.setModelFilePath(modelFilePath)  # noqa: F841
                emx.setMapHeaderFilePath(nextJsonPath)
                modelD = {}
                for tky in ["annotation_details", "contour_level", "contour_level_source"]:
                    modelD[tky] = self._reqObj.getValue("m_" + tky)
                #
                emx.updateHeader(modelD)
                if nextMapFilePath:
                    emx.setMapFileName(os.path.basename(nextMapFilePath))
                #
                mapType = self._reqObj.getValue("maptype")
                partitionNo = self._reqObj.getValue("partition")
                if self._verbose:
                    self._lfh.write("+CommonTasksWebAppWorker._editEmMapHeaderResponderOp() type %r partitionNo %r modelD %r\n" % (mapType, partitionNo, modelD.items()))
                emx.updateModelFromHeader(entryId, mapType=mapType, partition=partitionNo, outModelFilePath=modelFilePath)

                wfoInp = WfDataObject()
                wfoInp.setDepositionDataSetId(entryId)
                wfoInp.setStorageType("archive")
                wfoInp.setContentTypeAndFormat("model", "pdbx")
                wfoInp.setVersionId("latest")

                # Convert map files to bcif files when header updated
                pR = ProcessRunner(verbose=self._verbose, log=self._lfh)
                pR.setInput("src", wfoInp)
                op = "em-volume-bcif-conversion"
                ok = pR.setAction(op)
                self._lfh.write("setAction() for %s returns status %r\n" % (op, ok))
                ok = pR.preCheck()
                self._lfh.write("preCheck() for %s returns status %r\n" % (op, ok))
                ok = pR.run()

            except:  # noqa: E722 pylint: disable=bare-except
                if self._verbose:
                    self._lfh.write("+CommonTasksWebAppWorker._editEmMapResponderOp() failing model file %r\n" % modelFilePath)
                    traceback.print_exc(file=self._lfh)

            #
            myD["map_edit_status"] = "Map edits completed"
            #
            nMap, htmlMapList = emu.renderMapFileList(entryId)
            if nMap > 0:
                myD["map_list"] = htmlMapList
            nMask, htmlMaskList = emu.renderMaskFileList(entryId)
            if nMask > 0:
                myD["mask_list"] = htmlMaskList
            nAddMap, htmlAdditionalMapList = emu.renderAdditionalMapFileList(entryId)
            if nAddMap > 0:
                myD["additional_map_list"] = htmlAdditionalMapList
        else:
            myD["map_edit_status"] = "Map edit failed"

        #
        if len(aTagList) > 0:
            myD["map_edit_links"] = '<span class="url-list">Download: %s</span>' % ",&nbsp;".join(aTagList)
        #
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._editEmMapHeaderResponderOp() data object keys %r\n" % myD.keys())

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.addDictionaryItems(cD=myD)
        return rC

    def _listFilesResponse(self, entryId, fileSource="archive"):
        """Prepare JSON response for a report request for the input Id code."""
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.set("entryid", entryId)
        #

        myD = {}
        myD["file_list"] = []
        myD["my_entryid"] = entryId

        fu = FileUtils(entryId, reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        nFiles, htmlList = fu.renderFileList(fileSource=fileSource)

        if nFiles > 0:
            rC.setHtmlLinkText("")
            rC.setHtmlList(htmlList)
            rC.setStatus(statusMsg="File lists completed")
        else:
            rC.setError(errMsg="No corresponding data file(s)")
            # do nothing

        return rC

    def _downloadResponderOp(self):
        """Return json object containing a rendered list of masks and maps linked to edit/update operations."""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._downloadResponderOp() starting\n")
        self._getSession(useContext=True)
        filePath = self._reqObj.getValue("file_path")
        return self.__makeDownloadResponse(filePath, attachmentFlag=True, compressFlag=False)

    def __makeDownloadResponse(self, filePath, attachmentFlag=True, compressFlag=False):
        """Create a response content object for the input file"""
        if self._verbose:
            self._lfh.write("+() starting with file path %s\n" % filePath)
        #
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if filePath is not None and os.access(filePath, os.F_OK):
            rC.setReturnFormat("binary")
            rC.setBinaryFile(filePath, attachmentFlag=attachmentFlag, serveCompressed=compressFlag)
        else:
            rC.setReturnFormat("json")
            rC.setError(errMsg="Download failure for %s" % filePath)

        return rC

    def _mapDisplayOp(self):
        """Return a content object with view options for rendering local density maps -"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._mapDisplayOp() starting\n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")

        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        #
        #
        myD = {}
        #
        mpd = MapDisplay(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        htmlList = []
        indexPath = os.path.join(self._sessionPath, "np-cc-maps", "np-cc-maps-index.cif")
        if os.access(indexPath, os.R_OK):
            mapIdx = mpd.readLocalMapIndex(indexPath)
            htmlList.extend(mpd.renderLocalMapTable(rowDL=mapIdx, title="Table of local electron density maps for non-polymer chemical components"))
            if self.__debug:
                self._lfh.write("+CommonTasksWebAppWorker._mapDisplayOp() html list %r\n" % htmlList)
                self._lfh.write("+CommonTasksWebAppWorker._mapDisplayOp() data object %r\n" % myD.items())

        indexPath = os.path.join(self._sessionPath, "np-cc-omit-maps", "np-cc-omit-maps-index.cif")
        if os.access(indexPath, os.R_OK):
            mapIdx = mpd.readLocalMapIndex(indexPath)
            htmlList.extend(mpd.renderLocalMapTable(rowDL=mapIdx, title="Table of local electron density omit maps for non-polymer chemical components", subdir="np-cc-omit-maps"))
            if self.__debug:
                self._lfh.write("+CommonTasksWebAppWorker._mapDisplayOp() html list %r\n" % htmlList)
                self._lfh.write("+CommonTasksWebAppWorker._mapDisplayOp() data object %r\n" % myD.items())

        if len(htmlList) > 1:
            rC.setHtmlList(htmlList)
            rC.addDictionaryItems(cD=myD)
        else:
            rC.setError(errMsg="Map display failed for %s" % entryId)

        return rC

    def _uploadMultipleFilesOp(self):
        """Upload multiple files callback method --"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._uploadMultipleFilesOp() starting ... \n")

        self._getSession(useContext=True)
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.set("standalonemode", "y")

        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        pI.setDebugFlag(False)
        wuu = WebUploadUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

        if not wuu.isFileUpload():
            rC.setError(errMsg="No file uploaded")
            return rC
        #
        # Get content type and increment-by (e.g. by partition or version id)
        #
        formTag = self._reqObj.getValue("formid")
        defaultIdCode = "D_0000000000"
        #
        entryId = self._reqObj.getValue("entryid")
        if entryId is None or len(entryId) < 1:
            entryId = defaultIdCode

        #
        if formTag == "cs_auth_file_upload":
            #
            # Optional name associated with input file -
            csAuthName = self._reqObj.getValue("cs-auth-name")
            #
            # Fetch file / metadata dictionary --
            #
            # uds=UtilDataStore(reqObj=self._reqObj,prefix=entryId, verbose=self._verbose, log=self._lfh)
            # fD=uds.get('cs_file_dict')
            #
            fD = self._getSessionParameter(param="cs_file_dict", prefix=entryId)
            if len(fD) < 1:
                fD = {}
            #
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._uploadMultipleFilesOp() cs_auth_file_upload with fD %r\n" % fD.items())

            csAuthFileName = wuu.getUploadFileName(fileTag="file")
            #
            # Is this a standard project filename for an author chemical shifts file?
            #
            ok = pI.isValidFileName(fileName=csAuthFileName)
            # if (ok and (pI.splitFileName(fileName=csAuthFileName)[1] in ['nmr-chemical-shifts','nmr-chemical-shifts-auth','cs','cs-auth'])):
            if ok and (pI.splitFileName(fileName=csAuthFileName)[1] in ["nmr-chemical-shifts-auth", "cs-auth"]):
                # make a session copy using the compliant uploaded file name -
                csFileName = wuu.copyToSession(fileTag="file")
                fD[csFileName] = {"authName": csAuthName, "fileName": csFileName, "authFileName": csFileName}
                rC.setHtmlText("Uploaded file %s " % (csFileName))
            else:
                # make a session copy using a generated standard file name -
                formatType = "pdbx"
                try:
                    (_bN, eN) = os.path.splitext(csAuthFileName)
                    fExt = eN[1:]
                    if fExt in ["str"]:
                        formatType = "nmr-star"
                except:  # noqa: E722 pylint: disable=bare-except
                    pass
                tPath = pI.getAuthChemcialShiftsFilePath(entryId, formatType=formatType, partNumber="next", fileSource="session", versionId="latest")

                if self._verbose:
                    self._lfh.write("+CommonTasksWebAppWorker._uploadMultipleFilesOp() csAuthFileName %s session path is %s\n" % (csAuthFileName, tPath))

                _dN, fN = os.path.split(tPath)
                csFileName = wuu.copyToSession(fileTag="file", sessionFileName=fN, uncompress=True)
                fD[csFileName] = {"authName": csAuthName, "fileName": csFileName, "authFileName": csAuthFileName}
                rC.setHtmlText("Uploaded file %s renamed to standard file name %s" % (csAuthFileName, csFileName))
            rC.set("entryid", entryId)
            self._saveSessionParameter(param="cs_file_dict", value=fD, prefix=entryId)
        else:
            rC.setError(errMsg="File upload failed")

        return rC

    def _nmrCsUploadCheckOp(self):
        """Combine author provided CS files and perform a check sanity check on the result -"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrCsUploadCheckOp() starting\n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        taskArgs = ""
        taskFormId = self._reqObj.getValue("taskformid")
        #
        fD = self._getSessionParameter(param="cs_file_dict", prefix=entryId)

        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if len(fD) > 0:
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._nmrCsUploadCheckOp() for id %s recovered CS files %r\n" % (entryId, fD.items()))
            #
            authFilePathList = []
            authNameList = []
            #
            # fD[csFileName]={'authName' : csAuthName, 'fileName' : csFileName, 'authFileName' : csAuthFileName}
            #
            for fN, vD in fD.items():
                authFilePathList.append(os.path.join(self._sessionPath, fN))
                if (vD["authName"] is not None) and (len(vD["authName"]) > 0):
                    authNameList.append(vD["authName"])
                else:
                    authNameList.append(vD["authFileName"])
            #
            calc = NmrChemShiftsUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            calc.setAuthFiles(authFilePathList, authNameList)

            ok = calc.runPrep(entryId)
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._nmrCsUploadCheckOp() status %r\n" % ok)
            #
            tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
            #
            tss.assign(name="CS Upload Check", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId)
            rC = self._makeTaskResponse(tssObj=tss)
        else:
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._nmrCsUploadCheckOp() for id %s no files recovered\n" % entryId)
            tss.setTaskErrorFlag(True)
            tss.assign(name="CS Upload File Combination and Check", formId=taskFormId, args=taskArgs, completionFlag=False, tagList=[], entryId=entryId)
            rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _nmrCsAtomNameCheckOp(self):
        """Perform atom nomenclature checks on a 'combined/preprocessed' CS file -"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrCsAtomNameCheckOp() starting\n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        entryFileName = self._reqObj.getValue("entryfilename")
        taskArgs = ""
        taskFormId = self._reqObj.getValue("taskformid")
        #
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrCsAtomNameCheckOp() for id %s model file %s\n" % (entryId, entryFileName))

        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        # xyzFilePath=pI.getModelPdbxFilePath(dataSetId=entryId,fileSource='session-download',versionId='latest')
        xyzFilePath = os.path.join(self._sessionPath, entryFileName)
        csInpFilePath = pI.getChemcialShiftsFilePath(entryId, formatType="pdbx", fileSource="session", versionId="none", mileStone=None)
        csOutFilePath = pI.getChemcialShiftsFilePath(entryId, formatType="pdbx", fileSource="session", versionId="none", mileStone=None)

        if os.access(csInpFilePath, os.R_OK) and os.access(xyzFilePath, os.R_OK):
            calc = NmrChemShiftsUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            ok = calc.runAtomNameCheck(entryId, csInpFilePath, xyzFilePath, csOutFilePath)
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._nmrCsAtomNameCheckOp() status %r\n" % ok)
            #
            tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
            tss.assign(name="CS Atom Name Check", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId)
            rC = self._makeTaskResponse(tssObj=tss)
        else:
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._nmrCsAtomNameCheckOp() for id %s no files recovered\n" % entryId)
            tss.setTaskErrorFlag(True)
            tss.assign(name="CS Atom Name Check", formId=taskFormId, args=taskArgs, completionFlag=False, tagList=[], entryId=entryId)
            rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _nmrCsUpdateOp(self):
        """Perform CS update relative to changes in atom nomenclature in the input model file .."""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrCsUpdateOp() starting\n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        entryFileName = self._reqObj.getValue("entryfilename")
        taskArgs = ""
        taskFormId = self._reqObj.getValue("taskformid")
        #
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrCsUpdateOp() for id %s model file %s\n" % (entryId, entryFileName))

        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

        xyzFilePath = os.path.join(self._sessionPath, entryFileName)
        csInpFilePath = pI.getChemcialShiftsFilePath(entryId, formatType="pdbx", fileSource="session", versionId="none", mileStone=None)
        csOutFilePath = pI.getChemcialShiftsFilePath(entryId, formatType="pdbx", fileSource="session", versionId="none", mileStone=None)

        if os.access(csInpFilePath, os.R_OK) and os.access(xyzFilePath, os.R_OK):
            calc = NmrChemShiftsUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            ok = calc.runUpdate(entryId, csInpFilePath, xyzFilePath, csOutFilePath)
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._nmrCsUpdateOp() status %r\n" % ok)
            #
            tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
            tss.assign(name="CS Update", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId)
            rC = self._makeTaskResponse(tssObj=tss)
        else:
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._nmrCsUpdateOp() for id %s missing input files\n" % entryId)
            tss.setTaskErrorFlag(True)
            tss.assign(name="CS Update", formId=taskFormId, args=taskArgs, completionFlag=False, tagList=[], entryId=entryId)
            rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _nmrRepresentativeModelUpdateOp(self):
        """Run solvent reposition calculation -"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrRepresentativeModelUpdateOp() starting\n")

        self._getSession(useContext=True)

        entryId = self._reqObj.getValue("entryid")
        fileName = self._reqObj.getValue("entryfilename")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")

        calc = NmrModelUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        if taskArgs is not None and len(taskArgs) > 0:
            calc.setRepresentativeModelNumber(taskArgs)
        ok = calc.run(entryId, fileName)
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrRepresentativeModelUpdateOp() status %r\n" % ok)
        #
        tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
        #
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Representative model update", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _nmrCsMiscChecksOp(self):
        """Perform miscellaneous CS checks implemented within the validation pipeline file -"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrCsMiscCheckOp() starting\n")

        self._getSession(useContext=True)
        entryId = self._reqObj.getValue("entryid")
        entryFileName = self._reqObj.getValue("entryfilename")
        taskArgs = ""
        taskFormId = self._reqObj.getValue("taskformid")
        #
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrCsMiscCheckOp() for id %s model file %s\n" % (entryId, entryFileName))

        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        # xyzFilePath=pI.getModelPdbxFilePath(dataSetId=entryId,fileSource='session-download',versionId='latest')
        xyzFilePath = os.path.join(self._sessionPath, entryFileName)
        csInpFilePath = pI.getChemcialShiftsFilePath(entryId, formatType="pdbx", fileSource="session", versionId="none", mileStone=None)

        if os.access(csInpFilePath, os.R_OK) and os.access(xyzFilePath, os.R_OK):
            calc = NmrChemShiftsMiscChecks(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            ok = calc.run(entryId, csInpFilePath, xyzFilePath)
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._nmrCsMiscCheckOp() status %r\n" % ok)
            #
            tagL = calc.getAnchorTagList(label=None, target="_blank", cssClass="")
            tss.assign(name="CS Miscellaneous Checks", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=tagL, entryId=entryId)
            rC = self._makeTaskResponse(tssObj=tss)
        else:
            if self._verbose:
                self._lfh.write("+CommonTasksWebAppWorker._nmrCsMiscCheckOp() for id %s no files recovered\n" % entryId)
            tss.setTaskErrorFlag(True)
            tss.assign(name="CS Miscellaneous Checks", formId=taskFormId, args=taskArgs, completionFlag=False, tagList=[], entryId=entryId)
            rC = self._makeTaskResponse(tssObj=tss)

        return rC

    def _nmrCsArchiveUpdateOp(self):
        """Update the archive CS file --"""
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._nmrCsArchiveUpdateOp() starting\n")

        self._getSession(useContext=True)

        entryId = self._reqObj.getValue("entryid")
        fileName = self._reqObj.getValue("entryfilename")
        taskArgs = self._reqObj.getValue("task-form-args")
        taskFormId = self._reqObj.getValue("taskformid")
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        csInpFilePath = pI.getChemcialShiftsFilePath(entryId, formatType="pdbx", fileSource="session", versionId="none", mileStone=None)
        csOutFilePath = pI.getChemcialShiftsFilePath(entryId, formatType="pdbx", fileSource="archive", versionId="next", mileStone=None)
        #
        self._lfh.write("+CommonTasksWebAppWorker._nmrCsArhiveUpdateOp() copying %s to %s\n" % (csInpFilePath, csOutFilePath))
        #
        try:
            shutil.copyfile(csInpFilePath, csOutFilePath)
            ok = True
        except:  # noqa: E722 pylint: disable=bare-except
            ok = False
        tss = TaskSessionState(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        tss.assign(name="Archive CS file update", formId=taskFormId, args=taskArgs, completionFlag=ok, tagList=[], entryId=entryId, entryFileName=fileName)
        rC = self._makeTaskResponse(tssObj=tss)

        return rC

    ##
    # Shared upload methods
    ##

    def _uploadFileOp(self):
        """Upload callback method -- for model and experimental files -

        Copy input model and experimental data files to the current session directory and
        return file name and entry id details to the caller.

        """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._uploadFileOp() starting\n")

        self._getSession(useContext=True)
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.set("standalonemode", "y")
        #
        # transfer any existing input parameters to the output content object
        #
        reqKeyList = ["entryid", "entryfilename", "entryexpfilename", "entrynmrdatafilename", "entrycsfilename"]
        for ky in reqKeyList:
            val = self._reqObj.getValue(ky)
            if val is not None and len(val) > 0:
                rC.set(ky, val)

        wuu = WebUploadUtils(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

        if not wuu.isFileUpload():
            rC.setError(errMsg="No file uploaded")
            return rC
        #
        # What kind of file?
        #
        # formTag=self._reqObj.getValue("formid")
        defaultIdCode = "D_0000000000"
        uploadVersionOp = "none"
        #
        # Each fileType value will include:
        #
        #   <input content type>, <input format type>, <cnv op|none>, <output content type>, <output format type>, <timeout>
        #
        fileType = self._reqObj.getValue("filetype")
        fileTypeTup = [vS.strip() for vS in str(fileType).split(",")]
        #
        if len(fileTypeTup) < 6:
            rC.setError(errMsg="Incomplete file upload details")
            return rC
        inpContentType, inpFormatType, cnvOp, outContentType, outFormatType, timeOut = fileTypeTup
        if self._verbose:
            self._lfh.write(
                "+CommonTasksWebApp.py._uploadFileOp() inpContentType %s inpFormatType %s cnvOp %s outContentType %s outFormatType %s \n"
                % (inpContentType, inpFormatType, cnvOp, outContentType, outFormatType)
            )
        #
        #
        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        uploadFileName = wuu.copyToSession(fileTag="file")
        #
        # Try to detect a project compliant file name  --
        #
        entryId, fSource = wuu.perceiveIdentifier(uploadFileName)
        # fExt = wuu.getFileExtension(uploadFileName, ignoreVersion=True)
        #
        # Standardize the upload file - use existing ID code if this is detected, or default Id otherwise ...
        #
        if fSource not in ["WF_INSTANCE", "WF_ARCHIVE"]:
            entryId = defaultIdCode

        inpFileName = pI.getFileName(entryId, contentType=inpContentType, formatType=inpFormatType, versionId=uploadVersionOp, partNumber="1")
        wuu.renameSessionFile(uploadFileName, inpFileName)
        outFileName = pI.getFileName(entryId, contentType=outContentType, formatType=outFormatType, versionId=uploadVersionOp, partNumber="1")

        ok = True
        if cnvOp is not None and len(cnvOp) > 0:
            ok = self.__uploadConversion(entryId, inpFileName, inpContentType, inpFormatType, cnvOp, outFileName, outContentType, outFormatType, timeOut)
        else:
            # support simple renaming content types and format types on input --
            wuu.renameSessionFile(inpFileName, outFileName)

        rC.set("entryid", entryId)
        if ok:
            if outContentType == "model":
                rC.set("entryfilename", outFileName)
            elif outContentType == "structure-factors":
                rC.set("entryexpfilename", outFileName)
            elif outContentType == "nmr-chemical-shifts":
                # note the choice on inp versus out FileNames here -
                rC.set("entrycsfilename", inpFileName)
            ##
            if outFileName.startswith(defaultIdCode):
                if inpFileName == outFileName:
                    rC.setHtmlText("Uploaded file %s renamed to standard file name %s" % (uploadFileName, outFileName))
                else:
                    rC.setHtmlText("Uploaded file %s renamed to standard file name %s and converted to %s" % (uploadFileName, inpFileName, outFileName))
            else:
                rC.setHtmlText("%s successfully uploaded!" % outFileName)
        else:
            rC.setError(errMsg="File upload failed")

        if self._verbose:
            self._lfh.write("CommonTaskWebAppWorker()._uploadFileOp() rC %s\n" % "\n".join(rC.dump()))

        return rC

    def _launchFromIdcodeOp(self):
        """Standalone launch from Idcode input callback method --

        Copy input model and experimental data files to the current session directory and
        return file name and entry id details to the caller.

        """
        identifier = str(self._reqObj.getValue("identifier")).strip()
        ann_tasks = str(self._reqObj.getValue("ann_tasks")).strip()
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._launchFromIdcodeOp() starting with identifier %s\n" % identifier)

        self._getSession(useContext=True)
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setReturnFormat("json")
        rC.set("standalonemode", "y")
        rC.set("entryid", identifier)
        #
        uploadVersionOp = "none"

        if not self._importFromWF(identifier, fileSource="wf-archive", instanceWf="", getMaps=True):
            rC.setError(errMsg="No model file uploaded")
            return rC

        pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        fileName = pI.getFileName(identifier, contentType="model", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        rC.set("entryfilename", fileName)
        #

        fileName = pI.getFileName(identifier, contentType="structure-factors", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        filePath = os.path.join(self._sessionPath, fileName)
        if os.access(filePath, os.R_OK):
            rC.set("entryexpfilename", fileName)

        fileName = pI.getFileName(identifier, contentType="nmr-data-str", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
        filePath = os.path.join(self._sessionPath, fileName)
        if os.access(filePath, os.R_OK):
            rC.set("entrynmrdatafilename", fileName)
            #
            if ann_tasks == "y":
                self._autoProcessNmrCombinedDataFile(identifier)
            #
        else:
            fileName = pI.getFileName(identifier, contentType="nmr-chemical-shifts", formatType="pdbx", versionId=uploadVersionOp, partNumber="1")
            filePath = os.path.join(self._sessionPath, fileName)
            if os.access(filePath, os.R_OK):
                rC.set("entrycsfilename", fileName)
                #
                if ann_tasks == "y":
                    self._autoProcessNmrChemShifts(identifier)
                #
            #
        #
        rC.setStatusCode(None)
        rC.setHtmlText("Upload completed!")

        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._launchFromIdcodeOp() completed for identifier %s\n" % identifier)
        #
        return rC

    def _autoProcessNmrCombinedDataFile(self, identifier):
        """
        """
        if self._verbose:
            self._lfh.write("+CommonTasksWebAppWorker._autoProcessNmrCombinedDataFile() starting with identifier %s\n" % identifier)
        #
        try:
            csUtil = NmrChemShiftProcessUtils(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
            csUtil.setWorkingDirPath(dirPath=self._sessionPath)
            csUtil.setIdentifier(identifier=identifier)
            csUtil.runNefProcess(identifier=identifier)
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self._lfh)
        #

    def _autoProcessNmrChemShifts(self, identifier):
        """
        """
        try:
            csUtil = NmrChemShiftProcessUtils(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
            csUtil.setWorkingDirPath(dirPath=self._sessionPath)
            csUtil.setIdentifier(identifier=identifier, nmrDataFlag=False)
            csUtil.run()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self._lfh)
        #

    ##
    ##
    def __uploadConversion(
        self, entryId, inpFileName, inpContentType, inpFormatType, cnvOp, outFileName, outContentType, outFormatType, timeOut=0
    ):  # pylint: disable=unused-argument
        """Worker method supporting the conversion operations for uploaded in current session ..."""
        if self._verbose:
            self._lfh.write(
                "+CommonTasksWebApp.py._uploadConversionOp() entryId %s inpFileName %s inpContentType %s inpFormatType %s cnvOp %s\n"
                % (entryId, inpFileName, inpContentType, inpFormatType, cnvOp)
            )
        ok = True
        if inpContentType == "model":
            filePath = os.path.join(self._sessionPath, inpFileName)
            dfa = DataFileAdapter(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            if cnvOp == "rcsb-mmcif":
                ok = dfa.rcsb2Pdbx(filePath, filePath, stripFlag=False)
            elif cnvOp == "rcsb-mmcif-strip":
                ok = dfa.rcsb2Pdbx(filePath, filePath, stripFlag=True)
            elif cnvOp == "rcsb-cifeps":
                ok = dfa.rcsbEps2Pdbx(filePath, filePath, stripFlag=False)
            elif cnvOp == "rcsb-cifeps-strip":
                ok = dfa.rcsbEps2Pdbx(filePath, filePath, stripFlag=True)
            elif cnvOp == "rcsb-mmcif-alt":
                ok = dfa.rcsb2PdbxWithPdbIdAlt(filePath, filePath)
            elif cnvOp == "rcsb-mmcif-strip-plus-entity":
                ok = dfa.rcsb2Pdbx(filePath, filePath, stripFlag=True, stripEntityFlag=True)
            elif cnvOp == "rcsb-cifeps-strip-plus-entity":
                ok = dfa.rcsbEps2Pdbx(filePath, filePath, stripFlag=True, stripEntityFlag=True)
            #
        elif inpContentType == "structure-factors":
            if inpFormatType == "mtz" and cnvOp == "mtz2pdbx":
                dfa = DataFileAdapter(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)

                inpFilePath = os.path.join(self._sessionPath, inpFileName)
                outFilePath = os.path.join(self._sessionPath, outFileName)
                diagsFilePath = os.path.join(self._sessionPath, entryId + "-sf-diags.log")
                dumpFilePath = os.path.join(self._sessionPath, entryId + "-sf-dump.log")
                logFilePath = os.path.join(self._sessionPath, entryId + "-sf-convert.log")
                self._lfh.write("+CommonTasksWebApp.py._uploadFileOp() calling mtz2Pdbx() with %s %s\n" % (inpFilePath, outFilePath))
                ok = dfa.mtz2Pdbx(inpFilePath, outFilePath, pdbxFilePath=None, logFilePath=logFilePath, diagsFilePath=diagsFilePath, dumpFilePath=dumpFilePath, timeout=timeOut)
                if ok:
                    df = DataFile(fPath=outFilePath)
                    if df.srcFileExists() and df.srcFileSize() > 0:
                        ok = True
                    else:
                        ok = False
            else:
                pass

        elif inpContentType == "nmr-chemical-shifts":
            if inpFormatType == "pdbx" and cnvOp == "pdbx2nmrstar":
                inpFilePath = os.path.join(self._sessionPath, inpFileName)
                outFilePath = os.path.join(self._sessionPath, outFileName)
                dfa = DataFileAdapter(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                idCode = self._reqObj.getValue("pdb_id")
                if idCode is None or len(idCode) < 1:
                    idCode = entryId
                ok = dfa.pdbx2nmrstar(inpFilePath, outFilePath, pdbId=idCode)
            else:
                pass

        else:
            pass
        #
        return ok

    def __getUploadedFileList(self, pathIofo, entryId, content_format_type):
        """ """
        fileTimeList = []
        for fileFormat in content_format_type[1]:
            latestFile = pathIofo.getFilePath(
                dataSetId=entryId, wfInstanceId=None, contentType=content_format_type[0], formatType=fileFormat, fileSource="archive", versionId="latest", partNumber="1"
            )
            #
            if (not latestFile) or (not os.access(latestFile, os.F_OK)):
                continue
            #
            statinfo = os.stat(latestFile)
            _head, tail = ntpath.split(latestFile)
            fileTimeList.append([tail, latestFile, statinfo.st_mtime])
            #
            vList = tail.split(".V")
            if len(vList) != 2:
                continue
            #
            for i in range(1, int(vList[1])):
                previousFile = pathIofo.getFilePath(
                    dataSetId=entryId, wfInstanceId=None, contentType=content_format_type[0], formatType=fileFormat, versionId=str(i), partNumber="1"
                )
                #
                if (not previousFile) or (not os.access(previousFile, os.F_OK)):
                    continue
                #
                statinfo1 = os.stat(previousFile)
                _head, tail = ntpath.split(previousFile)
                fileTimeList.append([tail, previousFile, statinfo1.st_mtime])
                #
        #
        if len(fileTimeList) > 1:
            fileTimeList.sort(key=operator.itemgetter(2), reverse=True)
        #
        fileList = []
        for fileTimeTuple in fileTimeList:
            fileList.append([fileTimeTuple[0], fileTimeTuple[1]])
        #
        return fileList
