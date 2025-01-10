##
# File:  AssemblySelect.py
# Date:  20-April-2012  J. Westbrook
#
# Update:
#   4-July-2012  jdw  Add optional assembly arguments -
#   6-July-2012  jdw  Use entry specific analysis report names.
#                     Save selection details in session file.
#   7-July-2012  jdw  add entryId prefix to all file names.
#  10-July-2012  jdw  add host name to load url --
#  26-July-2012  jdw  CPK style 3D display
#  30-Oct-2013   jdw  Use assembly set organization and trash the data tables presentation
#  17-Dec-2013   jdw  Add reasonable limit to size of the assembly table presented.  Avoid
#                     form request overflow limit (8192 char).
#  24-Dec-2013   jdw  update assembly model file content type.
#  16-Jan-2014   jdw  update jmol applet configuration
#  07-Jan-2014   jdw  handle long compositions in table formatting
#  19-Feb-2015   jdw  add edit support for _struct_biol.details.
#   3-Jul-2015   jdw  add def generateAssemblies(self, entryId, modelFilePath) and
#                         def makeAssemblyDetailsTable(self, entryId, modelFilePath)
#                     switch to core python IO adapter -
#  14-Jun-2019   zf   add autoAssignDefaultAssembly()
##
"""
Calculation, selection and depiction of coordinate assemblies.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

import sys
import os.path
import os
import traceback
import shutil
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.utils.dp.DataFileAdapter import DataFileAdapter
from wwpdb.apps.ann_tasks_v2.io.PisaReader import PisaAssemblyReader
from wwpdb.apps.ann_tasks_v2.io.PdbxIoUtils import PdbxFileIo, ModelFileIo
from mmcif.api.PdbxContainers import DataContainer
from mmcif.api.DataCategory import DataCategory
from mmcif.io.IoAdapterCore import IoAdapterCore
from wwpdb.io.file.mmCIFUtil import mmCIFUtil


class AssemblySelect(object):

    """
    AssemblySelect class encapsulates the calculation, selection and display of
    calculated assemblies.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__assemblyD = {}
        self.__assemblySetD = {}
        self.__contextEntryId = None
        self.__assemblyArgs = None

        # self.__modelPathRel = ""
        self.__setup()

    def __setup(self):
        self.__entryId = self.__reqObj.getValue("entryid")
        self.__entryFileName = self.__reqObj.getValue("entryfilename")
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__rltvSessionPath = self.__sObj.getRelativePath()
        self.__requestUrl = self.__reqObj.getValue("request_host")
        self.__allMonomerFlag = False
        allmonomerflag = self.__reqObj.getValue("allmonomerflag")
        if allmonomerflag == "yes":
            self.__allMonomerFlag = True
        #

    def setArguments(self, assemblyArgs):
        self.__assemblyArgs = assemblyArgs

    def run(self, entryId, inpFile, sessionName, maxAssems=50):
        """Run the assembly calculation and create coordinate files for each candidate assembly"""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            reportPath = os.path.join(self.__sessionPath, entryId + "_assembly-report_P1.xml")
            logPath = os.path.join(self.__sessionPath, entryId + "-assembly-report.log")
            for filePath in (reportPath, logPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            if self.__assemblyArgs is not None and len(self.__assemblyArgs) > 0:
                dp.addInput(name="pisa_assembly_arguments", value=self.__assemblyArgs)
            #
            dp.addInput(name="pisa_session_name", value=sessionName)
            dp.op("pisa-analysis")
            dp.expLog(logPath)
            dp.op("pisa-assembly-report-xml")

            dp.exp(reportPath)
            #
            inpPathDep = os.path.join(self.__sessionPath, entryId + "_model-deposit.cif")
            shutil.copyfile(inpPath, inpPathDep)
            #
            assemD, _assemSetD = self.__readAssemblyReport(reportPath)
            if len(assemD) > 0:
                if self.__debug:
                    self.__lfh.write("+AssemblySelect.run - assembly uid list %r\n" % assemD.keys())
                #
                for assemblyUid in sorted(assemD.keys()):
                    if assemblyUid > maxAssems:
                        break
                    if assemblyUid == 0:
                        continue
                    assemModelFileName = os.path.join(self.__sessionPath, entryId + "_assembly-model-xyz_P" + str(assemblyUid) + ".cif")
                    dp.addInput(name="pisa_assembly_id", value=str(assemblyUid))
                    dp.op("pisa-assembly-coordinates-cif")
                    dp.exp(assemModelFileName)
                    if self.__verbose:
                        self.__lfh.write("+AssemblySelect.run - creating assembly model %r file %s\n" % (assemblyUid, assemModelFileName))
                    #
                #
            #
            # dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False

    def setReportContext(self, entryId):
        """Set the analysis report context for subsequent operations."""
        try:
            reportPath = os.path.join(self.__sessionPath, entryId + "_assembly-report_P1.xml")
            if os.access(reportPath, os.F_OK):
                _assemD, _assemSetD = self.__readAssemblyReport(reportPath)
                self.__contextEntryId = entryId
                return True
            else:
                return False
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)

        return False

    def getAssemblyCount(self, entryId):
        """Return number of assemblies in the current analysis report context."""
        if self.__contextEntryId != entryId:
            self.setReportContext(entryId)

        return len(self.__assemblyD)

    def exportAssemblyAssignments(self, entryId, outFilePath):
        """Export assembly assignment data file --"""
        try:
            selectList, provenanceD, assemFormD, extraD = self.__getAssemblySelectionDetails(entryId)
            curContainer = DataContainer("assembly_assignments")
            #
            hasAssemData = False
            if len(selectList) > 0:
                hasAssemData = True
                t = DataCategory("ann_tasks_assem_sw_assign")
                t.appendAttribute("assem_id")
                t.appendAttribute("provenance")
                t.appendAttribute("method")
                t.appendAttribute("method_version")
                t.appendAttribute("method_assem_id")

                #
                for ii, s in enumerate(selectList, start=0):
                    t.setValue(str(ii + 1), "assem_id", ii)
                    prV = provenanceD[s]
                    t.setValue(prV, "provenance", ii)
                    if prV in ["author_defined_assembly"]:
                        t.setValue(None, "method", ii)
                        t.setValue(None, "method_version", ii)
                    else:
                        t.setValue("PISA", "method", ii)
                        t.setValue("V1.18", "method_version", ii)
                    t.setValue(s, "method_assem_id", ii)

                curContainer.append(t)
            #
            if len(assemFormD) > 0:
                hasAssemData = True
                keyList = ["assem_id", "provenance", "buried_area", "surface_area", "free_energy", "oligomeric_count"]
                t = DataCategory("ann_tasks_assem_annot_assign")
                for ky in keyList:
                    t.appendAttribute(ky)

                assemIdList = assemFormD.keys()
                for ii, assemId in enumerate(assemIdList):
                    d = assemFormD[assemId]
                    for ky in keyList:
                        t.setValue(str(d[ky]), ky, ii)

                curContainer.append(t)
                t = DataCategory("ann_tasks_assem_annot_assign_op_list")
                t.appendAttribute("ordinal")
                t.appendAttribute("assem_id")
                t.appendAttribute("auth_asym_id")
                t.appendAttribute("sym_op")
                iRow = 0
                for assemId in assemIdList:
                    d = assemFormD[assemId]
                    opTupList = d["op_list"]
                    for authAsymId, symOpS in opTupList:
                        symOpL = symOpS.split(",")
                        for symOp in symOpL:
                            t.setValue(str(iRow + 1), "ordinal", iRow)
                            t.setValue(assemId, "assem_id", iRow)
                            t.setValue(authAsymId, "auth_asym_id", iRow)
                            t.setValue(symOp, "sym_op", iRow)
                            iRow += 1
                curContainer.append(t)
            #
            if not hasAssemData:
                return False
            #
            if len(extraD) > 0:
                t = DataCategory("ann_tasks_assembly_details")
                t.appendAttribute("id")
                t.appendAttribute("details")
                #
                t.setValue("1", "id", 0)
                t.setValue(extraD["details"], "details", 0)
                curContainer.append(t)
            #
            branchInfoPath = os.path.join(self.__sessionPath, entryId + "-branch-info.cif")
            if os.access(branchInfoPath, os.R_OK):
                cifObj = mmCIFUtil(filePath=branchInfoPath)
                branchInfoList = cifObj.GetValue("branch_polymer_info")
                if len(branchInfoList) > 0:
                    t = DataCategory("branch_polymer_info")
                    t.appendAttribute("branch_polymer_chain_id")
                    t.appendAttribute("linear_polymer_chain_id")
                    t.appendAttribute("type")
                    #
                    for ii, branchInfoD in enumerate(branchInfoList, start=0):
                        for item in ("branch_polymer_chain_id", "linear_polymer_chain_id", "type"):
                            if item in branchInfoD:
                                t.setValue(str(branchInfoD[item]), item, ii)
                            #
                        #
                    #
                    curContainer.append(t)
                #
            #
            myContainerList = []
            myContainerList.append(curContainer)
            pf = PdbxFileIo(verbose=self.__verbose, log=self.__lfh)
            pf.writeContainerList(outFilePath, myContainerList)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.writeAssemblyAssign() failed\n")
                traceback.print_exc(file=self.__lfh)
            return False

    def updateModelFile(self, entryId, inpFile, assignPath, updateInput=True):
        """Merge the assembly data in the current session with the input model coordinate file
        using the current assembly assignment file -
        """
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_P1.cif")
            logPath = os.path.join(self.__sessionPath, entryId + "_assembly-merge.log")
            reportPath = os.path.join(self.__sessionPath, entryId + "_assembly-report_P1.xml")
            for filePath in (retPath, logPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.updateModelFile() input  path %s\n" % inpPath)
                self.__lfh.write("+AssemblySelect.updateModelFile() return path %s\n" % retPath)
                self.__lfh.write("+AssemblySelect.updateModelFile() log    path %s\n" % logPath)
                self.__lfh.write("+AssemblySelect.updateModelFile() report path %s\n" % reportPath)

            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            #
            dp.addInput(name="pisa_assembly_assignment_file_path", value=assignPath)
            dp.addInput(name="pisa_assembly_file_path", value=reportPath)
            #
            dp.op("pisa-assembly-merge-cif")
            dp.exp(retPath)
            if updateInput and os.access(retPath, os.R_OK):
                dp.exp(inpPath)
            #
            dp.expLog(logPath)
            #
            #  Added generation of assembly files to the model update.
            if os.access(retPath, os.R_OK):
                self.generateAssemblies(entryId, modelFilePath=retPath)
            #
            # dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.updateModelFile() failed\n")
                traceback.print_exc(file=self.__lfh)
            return False
        #

    def autoAssignDefaultAssembly(self, entryId, inpFile):
        """Automatically fill in default assembly. Merge the extra assembly data if assembly report xml file exists."""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            retPath = os.path.join(self.__sessionPath, entryId + "_model-assembly-updated_P1.cif")
            logPath = os.path.join(self.__sessionPath, entryId + "_assembly-merge.log")
            assignPath = os.path.join(self.__sessionPath, entryId + "_assembly-assign_P1.cif")
            reportPath = os.path.join(self.__sessionPath, entryId + "_assembly-report_P1.xml")
            for filePath in (retPath, logPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            #
            dp.addInput(name="auto_assembly_assignment", value="yes")
            if os.access(reportPath, os.R_OK):
                fth = open(assignPath, "w")
                fth.write("data_assembly_assignments\n\n")
                fth.write("_ann_tasks_assem_sw_assign.assem_id         1 \n")
                fth.write("_ann_tasks_assem_sw_assign.provenance       author_defined_assembly \n")
                fth.write("_ann_tasks_assem_sw_assign.method           ? \n")
                fth.write("_ann_tasks_assem_sw_assign.method_version   ? \n")
                fth.write("_ann_tasks_assem_sw_assign.method_assem_id  0 \n#\n")
                fth.close()
                #
                dp.addInput(name="pisa_assembly_assignment_file_path", value=assignPath)
                dp.addInput(name="pisa_assembly_file_path", value=reportPath)
            #
            dp.op("pisa-assembly-merge-cif")
            dp.exp(retPath)
            dp.expLog(logPath)
            #
            #  Added generation of assembly files to the model update.
            if os.access(retPath, os.R_OK):
                self.generateAssemblies(entryId, modelFilePath=retPath)
            #
            # dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.updateModelFile() failed\n")
                traceback.print_exc(file=self.__lfh)
            return False
        #

    def getAssemblyFormDetails(self, entryId):
        _sL, _pD, fD, eD = self.__getAssemblySelectionDetails(entryId)
        return fD, eD

    def __getAssemblySelectionDetails(self, entryId):
        sL = []
        pD = {}
        aD = {}
        eD = {}
        try:
            sS, pS, aD, eD = self.__readSelection(entryId)
            if (sS is not None) and (len(sS) > 0):
                tL = sS.split(",")
                for t in tL:
                    if (t is not None) and (len(t) > 0):
                        sL.append(int(t))
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.getAssemblySelectionList() -assembly list: %r\n" % sL)

            if (pS is not None) and (len(pS) > 0):
                tL = pS.split(",")
                for t in tL:
                    if (t is not None) and (len(t) > 0):
                        tt = t.split(":")
                        k = str(tt[0]).strip()
                        v = str(tt[1]).strip()
                        pD[int(k)] = v
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.getAssemblySelectionDetails() failed\n")
                traceback.print_exc(file=self.__lfh)

        return sL, pD, aD, eD

    def getAssemblySelection(self, entryId):
        sS, _pS, _aD, _eD = self.__readSelection(entryId)
        if sS is not None:
            return sS
        else:
            return ""

    def renderAssemblyDataTable(self, entryId, maxAssems=100):
        """ """
        colList = ["set_ser_no", "select", "provenance", "view", "serial_no", "composition", "score", "asa", "bsa", "int_energy", "diss_energy", "op_list"]
        colDisplayD = {
            "set_ser_no": "Set",
            "select": "Select",
            "provenance": "Provenance",
            "view": "View",
            "serial_no": "No",
            "composition": "Composition",
            "score": "Score",
            "asa": "ASA",
            "bsa": "BSA",
            "int_energy": "Internal<br />Energy",
            "diss_energy": "Dissociation<br />Energy",
            "op_list": "Operators",
        }
        #
        # Create form with table --
        #
        rowD = self.__assemblyDataPrep(entryId)
        oL = []
        #
        sD = {}
        for uid, rD in rowD.items():
            if rD["set_ser_no"] not in sD:
                sD[rD["set_ser_no"]] = []
            sD[rD["set_ser_no"]].append(uid)

        #
        oL.append("<form>")
        oL.append('<table class="table table-bordered table-striped">')
        # for each assembly set -
        oL.append("<tr>")
        for col in colList:
            oL.append("<th>")
            oL.append("%s" % colDisplayD[col])
            oL.append("</th>")
        oL.append("</tr>")
        #
        setIdList = sorted(sD)
        #
        numAssemsTotal = 0
        for setId in setIdList:
            numAssem = len(sD[setId])
            numAssemsTotal += numAssem
            if numAssemsTotal > maxAssems:
                break

            for idx, uid in enumerate(sD[setId]):
                if setId % 2 == 0:
                    oL.append('<tr class="row-even">')
                else:
                    oL.append('<tr class="row-odd">')
                if idx == 0:
                    oL.append('<td rowspan="%d">%s</td>' % (numAssem, setId))
                for col in colList[1:]:
                    if col in ["score"]:
                        oL.append('<td class="width15">%s</td>' % rowD[uid][col])
                    elif col in ["op_list"]:
                        oL.append('<td class="width40 textleft">%s</td>' % rowD[uid][col])
                    elif col in ["composition"]:
                        tS = "&nbsp;<wbr>".join(rowD[uid][col])
                        # if self.__debug:
                        #    self.__lfh.write("+AssemblySelect.renderAssemblyDataTable() tS %r\n" % tS)
                        oL.append('<td class="width20">%s</td>' % tS)
                    else:
                        oL.append("<td>%s</td>" % rowD[uid][col])

                oL.append("</tr>")
        #
        oL.append("</table>")
        oL.append("</form>")
        #
        # if self.__debug:
        #    self.__lfh.write("+AssemblySelect.renderAssemblyDataTable() ASSEMBLY TABLE\n%s\n" % '\n'.join(oL))
        #
        #
        return oL

    def __setAssemblyModelRelativePath(self, assemblyUid, entryId, generated=False):
        if generated:
            modelPathRel = os.path.join(self.__rltvSessionPath, entryId + "_assembly-model_P" + assemblyUid + ".cif.V1")
        else:
            if assemblyUid == "0":
                # self.__modelPathRel=os.path.join(self.__rltvSessionPath,entryId+'_model-deposit.cif')
                modelPathRel = os.path.join(self.__rltvSessionPath, entryId + "_model_P1.cif")
            else:
                modelPathRel = os.path.join(self.__rltvSessionPath, entryId + "_assembly-model-xyz_P" + assemblyUid + ".cif")

        return modelPathRel

    def getLaunchJmolHtml(self, assemblyUid, entryId, generated=False):
        """Return the HTML to launch a 3D viewer for the pre-calculated coordinate file containing the
        input assembly (assemblyUid).
        """
        modelPathRel = self.__setAssemblyModelRelativePath(assemblyUid, entryId, generated=generated)

        # setupCmds="background black; wireframe only; wireframe 0.05; labels off; slab 100; depth 40; slab on;"
        # setupCmds="background black; wireframe off; spacefill 0.75; labels off; slab 100; depth 40; slab on;"
        if generated:
            # setupCmds = "select *; background white; wireframe off; ribbons off;cartoons off; labels off; rockets only; color rockets structure; slab 100; depth 40; slab on; "
            setupCmds = (
                setupCmds
            ) = " select *; background white; wireframe off; ribbons off; cartoons on; labels off; spacefill off; color property modelindex; select ligands; spacefill on; slab 100; depth 10; slab on; "  # noqa: E501
        else:
            setupCmds = " background black; wireframe off; spacefill on; color chain; labels off; slab 100; depth 40; slab on; "
        #
        # apId="jmolApplet%s" % assemblyUid
        # apId = "jmolApplet%s" % "0"
        #
        htmlL = []
        # ts1='<applet name="%s" id="%s" ' %  (apId,apId)  + \
        #     ' code="JmolApplet" archive="JmolApplet0.jar" codebase="/applets/jmol" mayscript="true" height="90%" width="90%">'
        # ts1='<applet name="%s" id="%s" ' %  (apId,apId)  + \
        #    ' code="JmolApplet" archive="Jmol.jar" codebase="/applets/jmol-dev" mayscript="true" height="90%" width="90%">'
        # htmlL.append(ts1)
        #
        # htmlL.append('<applet name="jmolApplet0" id="jmolApplet0"
        # code="JmolApplet" archive="JmolAppletSigned0.jar"
        # codebase="/applets/jmol-dev/jsmol/java" mayscript="true" height="98%"
        # width="98%">')
        htmlL.append(
            '<applet name="jmolApplet0" id="jmolApplet0" code="JmolApplet" archive="JmolAppletSigned0.jar" codebase="/applets/jmol-latest/jsmol/java" mayscript="true" height="98%" width="98%">'  # noqa: E501
        )
        htmlL.append('<param name="progressbar" value="true">')
        htmlL.append('<param name="progresscolor" value="blue">')
        htmlL.append('<param name="boxbgcolor" value="white">')
        htmlL.append('<param name="boxfgcolor" value="black">')
        htmlL.append('<param name="boxmessage" value="Downloading JmolApplet ...">')
        # jdw
        loadUrl = "http://" + self.__requestUrl + modelPathRel
        #
        if generated:
            postOpts = " frame *; display *; "
            htmlL.append('<param name="script" value="load models ({0:100}) %s; %s %s">' % (loadUrl, setupCmds, postOpts))
        else:
            htmlL.append('<param name="script" value="load %s; %s">' % (loadUrl, setupCmds))
        #
        htmlL.append("</applet>")
        return str("".join(htmlL))

    def runPdb(self, entryId, inpFile, sessionName):
        """Run the assembly calculation and create coordinate files for each candidate assembly (pdb version)"""
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            reportPath = os.path.join(self.__sessionPath, entryId + "_assembly-report_P1.xml")
            logPath = os.path.join(self.__sessionPath, entryId + "_assembly-report.log")
            for filePath in (reportPath, logPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(inpPath)
            dp.addInput(name="pisa_session_name", value=sessionName)
            dp.op("pisa-analysis")
            dp.expLog(logPath)
            dp.op("pisa-assembly-report-xml")
            dp.exp(reportPath)
            #

            assemD, _assemSetD = self.__readAssemblyReport(reportPath)
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.runPdb - assembly uid list %r\n" % assemD.keys())
            for assemblyUid in assemD.keys():
                assemModelFileName = os.path.join(self.__sessionPath, entryId + "_assembly-model-xyz_P" + assemblyUid + ".pdb")
                dp.addInput(name="pisa_assembly_id", value=assemblyUid)
                dp.op("pisa-assembly-coordinates-pdb")
                dp.exp(assemModelFileName)
                if self.__verbose:
                    self.__lfh.write("+AssemblySelect.runPdb - creating assembly model %r file %s\n" % (assemblyUid, assemModelFileName))
            # dp.cleanup()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False

    def __readAssemblyReport(self, reportPath):
        """Read assembly calculation report and return a dictionary of assembly details."""
        pA = PisaAssemblyReader(verbose=self.__verbose, log=self.__lfh)
        ok = pA.read(reportPath)
        if not ok:
            return {}, {}
        self.__assemblyD = pA.getAssemblyDict()
        self.__assemblySetD = pA.getAssemblySetDict()
        return self.__assemblyD, self.__assemblySetD

    def saveAssemblySelection(self, entryId, selectString=None, provenanceString=None):
        """Public method to support saving assembly selections."""
        return self.__writeSelection(entryId, selectString=selectString, provenanceString=provenanceString)

    def saveAssemblyFormInput(self, entryId, assemFormD=None, extraD=None):
        """Public method to support saving assembly form input dictionary."""
        return self.__writeSelection(entryId, assemFormD=assemFormD, extraD=extraD)

    def saveAssemblyInput(self):
        """Public method to support saving single assembly or all monomer assembiles"""
        htmlS = ""
        assemDict = self.__getAssemblyDict()
        if len(assemDict) == 0:
            return False, htmlS
        #
        if not self.__writeSelection(self.__entryId, assemFormD=assemDict):
            return False, htmlS
        #
        assignPath = os.path.join(self.__sessionPath, self.__entryId + "_assembly-assign_P1.cif")
        if not self.exportAssemblyAssignments(self.__entryId, assignPath):
            return False, htmlS
        #
        if not self.updateModelFile(self.__entryId, self.__entryFileName, assignPath):
            return False, htmlS
        #
        modelFilePath = os.path.join(self.__sessionPath, self.__entryId + "_model-updated_P1.cif")
        htmlS = self.makeAssemblyDetailsTable(self.__entryId, modelFilePath=modelFilePath)
        return True, htmlS

    def __writeSelection(self, entryId, selectString=None, provenanceString=None, assemFormD=None, extraD=None):
        """Save assembly data in the session directory."""
        curSelectString, curProvenanceString, curAssemFormD, curExtraD = self.__readSelection(entryId)
        if selectString is not None:
            curSelectString = selectString
        if provenanceString is not None:
            curProvenanceString = provenanceString
        if assemFormD is not None:
            curAssemFormD = assemFormD
        if extraD is not None:
            curExtraD = extraD
        try:
            ofh = os.path.join(self.__sessionPath, entryId + "_assembly-session-data.pic")
            fb = open(ofh, "wb")
            if curSelectString is not None:
                pickle.dump(curSelectString, fb)
            else:
                pickle.dump("", fb)

            if curProvenanceString is not None:
                pickle.dump(curProvenanceString, fb)
            else:
                pickle.dump("", fb)

            if curAssemFormD is not None:
                pickle.dump(curAssemFormD, fb)
            else:
                pickle.dump({}, fb)

            if curExtraD is not None:
                pickle.dump(curExtraD, fb)
            else:
                pickle.dump({}, fb)

            fb.close()
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.__writeSelection() succeeded for entry %s\n" % entryId)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.__writeSelection() failed for entry %s\n" % entryId)
                traceback.print_exc(file=self.__lfh)
        return False

    def __getAssemblyDict(self):
        """Generate single assembly or all monomer assembiles dictionary"""
        assemFormD = {}
        modelFilePath = os.path.join(self.__sessionPath, self.__entryFileName)

        if (modelFilePath is not None) and (not os.access(modelFilePath, os.R_OK)):
            return assemFormD
        #
        c0 = PdbxFileIo(ioObj=IoAdapterCore(), verbose=self.__verbose, log=self.__lfh).getContainer(modelFilePath)
        sdf = ModelFileIo(dataContainer=c0, verbose=self.__verbose, log=self.__lfh)
        eD, _branchInstList = sdf.getPolymerEntityChainDict()
        #
        assemInstIdList = []
        if not self.__allMonomerFlag:
            instanceIdList = []
            for _eId, instL in eD.items():
                for inst in instL:
                    instanceIdList.append(inst)
                #
            #
            instanceIdList.sort()
            assemInstIdList.append(instanceIdList)
        else:
            branch2LinearMap = {}
            linear2BranchMap = {}
            branchInfoPath = os.path.join(self.__sessionPath, self.__entryId + "-branch-info.cif")
            if os.access(branchInfoPath, os.R_OK):
                cifObj = mmCIFUtil(filePath=branchInfoPath)
                status = cifObj.GetSingleValue("summary", "status")
                if status == "yes":
                    infoList = cifObj.GetValue("branch_polymer_info")
                    for infoD in infoList:
                        if (
                            ("branch_polymer_chain_id" not in infoD)
                            or (not infoD["branch_polymer_chain_id"])
                            or ("linear_polymer_chain_id" not in infoD)
                            or (not infoD["linear_polymer_chain_id"])
                            or ("type" not in infoD)
                            or (not infoD["type"])
                        ):
                            continue
                        #
                        branch2LinearMap[infoD["branch_polymer_chain_id"]] = infoD["linear_polymer_chain_id"]
                        if infoD["linear_polymer_chain_id"] in linear2BranchMap:
                            linear2BranchMap[infoD["linear_polymer_chain_id"]].append(infoD["branch_polymer_chain_id"])
                        else:
                            linear2BranchMap[infoD["linear_polymer_chain_id"]] = [infoD["branch_polymer_chain_id"]]
                        #
                    #
                #
            #
            linearInstIdList = []
            for _eId, instL in eD.items():
                for inst in instL:
                    if inst in branch2LinearMap:
                        continue
                    #
                    linearInstIdList.append(inst)
                #
            #
            linearInstIdList.sort()
            #
            for linearInstId in linearInstIdList:
                instanceIdList = []
                instanceIdList.append(linearInstId)
                if linearInstId in linear2BranchMap:
                    for branchInstId in linear2BranchMap[linearInstId]:
                        instanceIdList.append(branchInstId)
                    #
                #
                assemInstIdList.append(instanceIdList)
            #
        #
        for instIdList in assemInstIdList:
            op_list = []
            for inst in instIdList:
                op_list.append((inst, "1_555"))
            #
            assem_id = len(assemFormD) + 1
            assemFormD[assem_id] = self.__generateAssemblyDict(str(assem_id), op_list)
        #
        return assemFormD

    def __generateAssemblyDict(self, assem_id, op_list):
        """Generate a author define assembly"""
        assemDic = {}
        assemDic["assem_id"] = assem_id
        assemDic["provenance"] = "author_defined_assembly"
        for item in ("buried_area", "surface_area", "free_energy", "oligomeric_count"):
            assemDic[item] = "?"
        #
        assemDic["op_list"] = op_list
        return assemDic

    def __readSelection(self, entryId):
        """Read stored assembly data for the current session.

        Return None,None,{} if no data is found
        """
        ifh = os.path.join(self.__sessionPath, entryId + "_assembly-session-data.pic")
        if not os.access(ifh, os.R_OK):
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.__readSelection() no assembly session file for entry %s path %s\n" % (entryId, ifh))
            return (None, None, {}, {})

        try:
            fb = open(ifh, "rb")
            sS = pickle.load(fb)
            pS = pickle.load(fb)
            aD = pickle.load(fb)
            eD = pickle.load(fb)
            fb.close()
            if (sS is not None) and (len(sS) > 0):
                r1 = sS
            else:
                r1 = None

            if (pS is not None) and (len(pS) > 0):
                r2 = pS
            else:
                r2 = None

            if (aD is not None) and (len(aD) > 0):
                rD = aD
            else:
                rD = {}

            if (eD is not None) and (len(eD) > 0):
                reD = eD
            else:
                reD = {}

            #
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.__readSelection() entry %s reading selection %r provenance %r form data %r extra %r\n" % (entryId, r1, r2, rD, reD))
            #
            return (r1, r2, rD, reD)
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.__readSelection() failed for entry %s path %s\n" % (entryId, ifh))
                traceback.print_exc(file=self.__lfh)

        return (None, None, {}, {})

    def __assemblyDataPrep(self, entryId):
        """Reformat assembly data and return a dictionary of dictionaries containing the containing the computed details for each assembly.

        Prior selection details and view options are added to each dictionary.
        """
        rowD = {}
        colList = ["set_ser_no", "select", "provenance", "view", "serial_no", "composition", "score", "asa", "bsa", "int_energy", "diss_energy", "op_list"]
        #
        if self.__contextEntryId != entryId:
            self.setReportContext(entryId)

        #     Recover the state of prior selections -
        #
        #
        selectList, provSelectD, _assemFormD, _extraD = self.__getAssemblySelectionDetails(entryId)
        provenanceOptList = [("author_defined_assembly", "author"), ("software_defined_assembly", "software"), ("author_and_software_defined_assembly", "author+software")]
        if len(provSelectD) < 1:
            for uid in self.__assemblyD.keys():
                provSelectD[uid] = "software_defined_assembly"
        else:
            for uid in self.__assemblyD.keys():
                if uid not in provSelectD:
                    provSelectD[uid] = "software_defined_assembly"

        #
        if self.__debug:
            self.__lfh.write("++DEBUG - self.__assemblyD.keys() %r\n" % self.__assemblyD.keys())
            self.__lfh.write("++DEBUG - provSelectD             %r\n" % provSelectD.items())
        #
        for uid in self.__assemblyD.keys():
            cD = {}
            assem = self.__assemblyD[uid]
            #
            selectId = assem["serial_no"]
            assemSetId = assem["set_ser_no"]
            #
            #   User selection checkbox --
            #
            if uid in selectList:
                checkOpt = "checked"
            else:
                checkOpt = ""
            inputText = '<input id="%s" type="checkbox" value="%s" class="assem_select" %s />' % (uid, selectId, checkOpt)

            #
            # Provenance selection pulldown --
            #

            pL = []
            pL.append('<select id="prov_%s" name="%s" class="assem_prov">' % (uid, uid))
            for opTup in provenanceOptList:
                sT = ""
                if opTup[0] == provSelectD[uid]:
                    sT = ' selected="selected" '
                pL.append('<option %s   value="%s">%s</option>' % (sT, opTup[0], opTup[1]))
            pL.append("</select>")
            viewopt = ""
            if uid != 0:
                #
                #  <entryId>_assembly-model-xyz_P<assemId>.cif
                # <a href='javascript:loadFileJsmol("myApp1","#jmol-dialog-1","/files/1cbs.cif","cpk")'> Load 1cbs cpk </a>
                #
                # Add a test for file existence here --
                #
                fullPath = os.path.join(self.__sessionPath, self.__entryId + "_assembly-model-xyz_P" + str(uid) + ".cif")
                if os.access(fullPath, os.R_OK):
                    assemblyFilePath = os.path.join(self.__rltvSessionPath, self.__entryId + "_assembly-model-xyz_P" + str(uid) + ".cif")
                    jsurl = 'javascript:loadFileJsmol("myApp1","#jsmol-dialog-1","%s","cpk")' % assemblyFilePath
                    htjs = "<a href='%s'>Jsmol</a>" % (jsurl)
                    viewopt = htjs
            else:
                #
                fullPath = os.path.join(self.__sessionPath, self.__entryFileName)
                if os.access(fullPath, os.R_OK):
                    assemblyFilePath = os.path.join(self.__rltvSessionPath, self.__entryFileName)
                    jsurl = 'javascript:loadFileJsmol("myApp1","#jsmol-dialog-1","%s","cpk")' % assemblyFilePath
                    htjs = "<a href='%s'>Jsmol</a>" % (jsurl)
                    viewopt = htjs

            #
            #
            cD["select"] = inputText
            cD["provenance"] = "".join(pL)
            cD["view"] = viewopt
            cD["set_ser_no"] = int(assemSetId)
            #
            for col in colList[4:-1]:
                if col in ["asa", "bsa", "size", "mmsize"]:
                    cD[col] = int(float(str(assem[col])))
                elif col in ["int_energy", "diss_energy"]:
                    # JDW
                    cD[col] = "%.1f" % float(str(assem[col]))

                elif col in ["set_ser_no", "serial_no"]:
                    cD[col] = int(assem[col])
                elif col in ["score"] and (uid == "0" or uid == 0):
                    cD[col] = "Deposited coordinates<br /><i>as is</i>"
                elif col in ["score"] and ("not revealed any" in str(assem[col])):
                    cD[col] = "... no strong evidence of complex ..."
                elif col in ["composition"]:
                    tt = str(assem[col]).replace("[", "|[")
                    cD[col] = tt.split("|")
                    if self.__debug:
                        self.__lfh.write("+AssemblySelect.__assemblyDataPrep() formatted composition - %r \n" % cD[col])

                else:
                    cD[col] = str(assem[col])
            #
            opList = []
            for mol in assem["molecule_list"]:
                if mol["symId"] not in ["1_555", "0_555"]:
                    opList.append(str(mol["chain_id"] + "&nbsp;" + mol["symId"]))
                else:
                    opList.append(str(mol["chain_id"]))
            tS = ",&nbsp;<wbr> ".join(opList)
            # cD['op_list']=tS.replace('[','<br />[')
            cD["op_list"] = tS
            #
            rowD[int(uid)] = cD
        #
        return rowD

    ###
    def generateAssemblies(self, entryId, modelFilePath):
        """Materialize 'assembly-model' data files as described the assembly definitions in the
        input model file.
        """
        return self.__genAssemblies(entryId, modelFilePath)

    def makeAssemblyDetailsTable(self, entryId, modelFilePath):
        """Return HTML text for a table with display options for materialized 'assembly-model' data files."""
        colList, rowDL = self.__generatedAssemblyDataPrep(entryId, modelFilePath)
        if self.__verbose:
            self.__lfh.write("+AssemblySelect.makeAssemblyDetailTable()  colList     %r\n" % colList)
            for rowD in rowDL:
                self.__lfh.write("+AssemblySelect.makeAssemblyDetailTable()  rowD %r\n" % rowD.items())
        oL = self.__renderGeneratedAssemblyDataTable(colList, rowDL)
        return "\n".join(oL)

    def __genAssemblies(self, entryId, modelFilePath):
        try:
            dfa = DataFileAdapter(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            indexFilePath = os.path.join(self.__sessionPath, "assembly-index.txt")
            dfa.pdbx2Assemblies(entryId, modelFilePath, self.__sessionPath, indexFilePath=indexFilePath)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+AssemblySelect.__genAssemblies() failed\n")
                traceback.print_exc(file=self.__lfh)
            return False

    def __fetchAssemblyDetails(self, modelFilePath=None):
        """Return a list of dictionaries containing the current assembly details."""
        c0 = PdbxFileIo(ioObj=IoAdapterCore(), verbose=self.__verbose, log=self.__lfh).getContainer(modelFilePath)
        sdf = ModelFileIo(dataContainer=c0, verbose=self.__verbose, log=self.__lfh)

        assemL, assemGenL, assemOpL = sdf.getAssemblyDetails()

        if self.__verbose:
            self.__lfh.write("+AssemblySelect.__fetchAssemblyDetails()  assemL     %r\n" % assemL)
            self.__lfh.write("+AssemblySelect.__fetchAssemblyDetails()  assemGenL  %r\n" % assemGenL)
            self.__lfh.write("+AssemblySelect.__fetchAssemblyDetails()  assemOpL   %r\n" % assemOpL)
        return assemL, assemGenL, assemOpL

    def __generatedAssemblyDataPrep(self, entryId, modelFilePath):
        """Reformat ..."""
        rowL = []

        assemL, assemGenL, assemOpL = self.__fetchAssemblyDetails(modelFilePath=modelFilePath)
        #
        opD = {}
        for rD in assemOpL:
            if "id" in rD and "name" in rD:
                opD[rD["id"]] = rD["name"]
            #
        #
        intKey = []
        tD = {}
        for rD in assemL:
            if "id" in rD:
                aid = rD["id"]
                intKey.append(int(str(aid)))
                tD[aid] = {}
                if "details" in rD:
                    tD[aid]["details"] = rD["details"]
                #
            #
        #

        for k, v in tD.items():
            genL = []
            for rD in assemGenL:
                if "assembly_id" in rD and rD["assembly_id"] == k and "oper_expression" in rD and "asym_id_list" in rD:
                    opIdL = str(rD["oper_expression"]).split(",")
                    opL = []
                    for opId in opIdL:
                        if opId in opD:
                            opL.append(opD[opId])
                        #
                    #
                    opS = ",".join(opL)
                    genL.append(opS + "(" + rD["asym_id_list"] + ")")
                #
            #
            v["generator"] = ",".join(genL)
        #
        if self.__verbose:
            for k, v in tD.items():
                self.__lfh.write("+AssemblySelect.__generatedAsemblyDataPrep() %r %r\n" % (k, v.items()))
            #
        #
        colList = ["id", "viewop", "details", "generator"]
        #
        # Generate data for the table including the viewer commands --
        #
        # for k in sorted(tD.keys()):
        for k in sorted(intKey):
            rD = {}
            fullPath = os.path.join(self.__sessionPath, entryId + "_assembly-model_P" + str(k) + ".cif.V1")
            if os.access(fullPath, os.R_OK):
                assemblyFilePath = os.path.join(self.__rltvSessionPath, self.__entryId + "_assembly-model_P" + str(k) + ".cif.V1")
                jsurl = 'javascript:loadFileJsmol("myApp1","#jsmol-dialog-1","%s","secstruct1")' % assemblyFilePath
                htjs = "<a href='%s'>Jsmol</a>" % (jsurl)
                viewop = htjs
                rD["id"] = str(k)
                rD["viewop"] = viewop
                rD["details"] = tD[str(k)]["details"]
                rD["generator"] = tD[str(k)]["generator"]
                #
                rowL.append(rD)
            #
        #
        return colList, rowL

    def __renderGeneratedAssemblyDataTable(self, colList, rowDList):
        """ """
        colList = ["id", "viewop", "details", "generator"]
        colDisplayD = {"id": "Assembly", "viewop": "Display", "details": "Provenance", "generator": "Generator"}

        # Create form with table --
        #
        oL = []
        #
        oL.append('<table class="table table-bordered table-striped">')
        oL.append("<tr>")
        for col in colList:
            oL.append("<th>")
            oL.append("%s" % colDisplayD[col])
            oL.append("</th>")
        oL.append("</tr>")
        #
        #
        for idx, rowD in enumerate(rowDList):
            if idx % 2 == 0:
                oL.append('<tr class="row-even">')
            else:
                oL.append('<tr class="row-odd">')

            for col in colList:
                if col in ["id"]:
                    oL.append('<td class="width15">%s</td>' % rowD[col])
                elif col in ["generator"]:
                    oL.append('<td class="width40 textleft">%s</td>' % rowD[col])
                elif col in ["details"]:
                    # tS = '&nbsp;<wbr>'.join(rowD[col])
                    oL.append('<td class="width20">%s</td>' % rowD[col])
                else:
                    oL.append("<td>%s</td>" % rowD[col])

            oL.append("</tr>")
        #
        oL.append("</table>")

        #
        return oL
