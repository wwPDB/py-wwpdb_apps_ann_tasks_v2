##
# File:  PdbxExpUpdate.py
# Date:  7-May-2014
#
# Updates:
#
##
"""
    Extract selected items from the current model file and update these in experimental reflection file -
"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import inspect
import os
import sys
import time
import re
import traceback

from wwpdb.apps.ann_tasks_v2.expIoUtils.PdbxExpIoUtils import PdbxExpFileIo, PdbxExpIoUtils
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class PdbxExpUpdate(SessionWebDownloadUtils):
    """
    Extract selected items from the current model file and update these in experimental reflection file -
    """

    def __init__(self, reqObj, verbose=True, log=sys.stderr):
        super(PdbxExpUpdate, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__reqObj = reqObj
        self.__verbose = verbose
        self.__lfh = log
        self.__warningMsg = []
        self.__diffFlag = False
        self.__maximalWavelengthNumber = 0
        self.__wavelengthInfo = {}
        self.__inputExpWvMap = {}
        self.__inputExpMuMap = {}
        self.__setup()
        self.__getUInputWValues()

    def __setup(self):
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__tempFilePath = os.path.join(self.__sessionPath, "temp-exp-file-1.cif")
        self.__logFilePath = os.path.join(self.__sessionPath, "update-reflection-file.log")

    def __getUInputWValues(self):
        """ """
        buttonValue = self.__reqObj.getValue("sf_submit_id")
        if buttonValue != "Update":
            return
        #
        input_number = int(self.__reqObj.getValue("total_input_text_count"))
        if input_number < 6:
            return
        #
        for i in range(0, input_number):
            wavelength = self.__reqObj.getValue("wavelength_" + str(i))
            if not wavelength:
                continue
            #
            blockname = self.__reqObj.getValue("blockname_" + str(i))
            if not blockname:
                continue
            #
            if blockname in self.__inputExpWvMap:
                self.__inputExpWvMap[blockname].append(wavelength)
            else:
                self.__inputExpWvMap[blockname] = [wavelength]
            #
        #
        for block, wvList in self.__inputExpWvMap.items():
            muList = []
            count = 1
            for wv in wvList:
                muList.append((str(count), wv, "1.0"))
                count += 1
            #
            self.__inputExpMuMap[block] = muList
        #

    def setArguments(self, taskArgs):
        pass

    def getWarningMessage(self):
        """ """
        return "<br />\n".join(self.__warningMsg)

    def getDiffFlag(self):
        """ """
        return self.__diffFlag

    def getWavelengthInfo(self):
        """ """
        return self.__wavelengthInfo

    def doUpdate(self, entryId, modelInputFile=None, expInputFile=None, expOutputFile=None, skipNotChanged=False):
        """Update selected items in reflection data file using the current contents of the model file.
        Will always output new SF file if possible unless skipNotNeeded is set
        """
        startTime = time.time()
        if self.__verbose:
            self.__lfh.write("\n\n========================================================================================================\n")
            self.__lfh.write("Starting %s %s at %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        #
        returnFlag = True
        try:
            if modelInputFile is None:
                modelFileName = entryId + "_model_P1.cif"
                modelFilePath = os.path.join(self.__sessionPath, modelFileName)
            else:
                modelFilePath = os.path.join(self.__sessionPath, modelInputFile)
            #
            if expInputFile is None:
                expFileName = entryId + "_sf_P1.cif"
                inpExpFilePath = os.path.join(self.__sessionPath, expFileName)
            else:
                inpExpFilePath = os.path.join(self.__sessionPath, expInputFile)
            #
            if expOutputFile is None:
                expFileName = entryId + "_sf_P1.cif"
                outExpFilePath = os.path.join(self.__sessionPath, expFileName)
            else:
                outExpFilePath = os.path.join(self.__sessionPath, expOutputFile)
            #
            mIo = PdbxExpFileIo(verbose=self.__verbose, log=self.__lfh)
            modelContainerList = mIo.getContainerList(modelFilePath)
            if len(modelContainerList) < 1:
                self.__warningMsg.append("Empty model coordinate file.")
                return returnFlag
            #
            #  Read relevant data items in the first model container --
            #
            mE = PdbxExpIoUtils(dataContainer=modelContainerList[0], verbose=self.__verbose, log=self.__lfh)
            # entryId=mE.getEntryId()
            pdbId = str(mE.getDbCode(dbId="PDB")).lower()
            modelDiffrnSourceIdList = mE.getDiffrnSourceIds()
            if not modelDiffrnSourceIdList:
                self.__warningMsg.append("No diffrn_id data found from '_diffrn_source.diffrn_id' in model coordinate file.")
                return returnFlag
            #
            modelWavelengthD = {}
            for diffrnId in modelDiffrnSourceIdList:
                modelWavelengthD[diffrnId] = mE.getDiffrnSourceWavelengthListAsList(diffrnId=diffrnId)
            #
            if not modelWavelengthD:
                self.__warningMsg.append("No wavelength data found from '_diffrn_source.pdbx_wavelength_list' in model coordinate file.")
                return returnFlag
            #
            sfIo = PdbxExpFileIo(verbose=self.__verbose, log=self.__lfh)
            containerList = sfIo.getContainerList(inpExpFilePath)
            if len(containerList) < 1:
                self.__warningMsg.append("Empty structure factor file.")
                return returnFlag
            #
            if self.__verbose:
                self.__lfh.write("+PdbxExpUpdate.doUpdate() In file %s found data %d sets\n" % (inpExpFilePath, len(containerList)))
            #
            anyUpdates = False
            containerNameList = []
            for container in containerList:
                if self.__verbose:
                    self.__lfh.write("+PdbxExpUpdate.doUpdate() In file %s found data set %s\n" % (inpExpFilePath, container.getName()))
                #
                # Read selected items from this container --
                #
                pE = PdbxExpIoUtils(dataContainer=container, verbose=self.__verbose, log=self.__lfh)
                curContainerName = pE.getContainerName()
                containerNameList.append(curContainerName)
                diffrnIdList = pE.getDiffrnIds()
                curMuList = pE.getDiffrnRadiationWavelengthList()
                #
                # Try to assign the diffrn_id for the current reflection data section ...
                #
                if not diffrnIdList:
                    diffrnIdList.append("1")
                #
                # Get wavelength list from model coordinate file for current reflection data section ...
                #
                modelWvList = []
                modelMuList = []
                model_wavelength_1 = ""
                for dId in diffrnIdList:
                    if (dId not in modelWavelengthD) or (not modelWavelengthD[dId]):
                        continue
                    #
                    for _muId, mu, wt in modelWavelengthD[dId]:
                        if (mu in [None, "", ".", "?"]) or (mu in modelWvList):
                            continue
                        #
                        if mu in ["1.0", "1.00", "1.000", "1.0000", "1.00000", "1.000000", "1.0000000"]:
                            if model_wavelength_1:
                                continue
                            #
                            model_wavelength_1 = mu
                        #
                        modelWvList.append(mu)
                        modelMuList.append((str(len(modelWvList)), mu, wt))
                    #
                #
                if len(modelWvList) > self.__maximalWavelengthNumber:
                    self.__maximalWavelengthNumber = len(modelWvList)
                #
                # Get wavelength list from current reflection data section ...
                #
                expWvList = []
                expMuList = []
                exp_wavelength_1 = ""
                cleanFlag = False
                if (
                    curContainerName in self.__inputExpWvMap
                    and self.__inputExpWvMap[curContainerName]
                    and curContainerName in self.__inputExpMuMap
                    and self.__inputExpMuMap[curContainerName]
                ):
                    expWvList = self.__inputExpWvMap[curContainerName]
                    expMuList = self.__inputExpMuMap[curContainerName]
                    cleanFlag = True
                elif len(curMuList) > 0:
                    for _muId, mu, wt in curMuList:
                        if (mu in [None, "", ".", "?"]) or (mu in expWvList):
                            cleanFlag = True
                            continue
                        #
                        if mu in ["1.0", "1.00", "1.000", "1.0000", "1.00000", "1.000000", "1.0000000"]:
                            if exp_wavelength_1:
                                cleanFlag = True
                                continue
                            #
                            if model_wavelength_1:
                                if mu != model_wavelength_1:
                                    cleanFlag = True
                                #
                                exp_wavelength_1 = model_wavelength_1
                            else:
                                exp_wavelength_1 = mu
                            #
                            expWvList.append(exp_wavelength_1)
                            expMuList.append((str(len(expWvList)), exp_wavelength_1, wt))
                        else:
                            expWvList.append(mu)
                            expMuList.append((str(len(expWvList)), mu, wt))
                        #
                    #
                #
                if len(expWvList) > self.__maximalWavelengthNumber:
                    self.__maximalWavelengthNumber = len(expWvList)
                #
                diffFlag = False
                updateFlag = True
                if modelMuList and expMuList:
                    tmpMdelWvList = self.__processList(modelWvList)
                    tmpExpWvList = self.__processList(expWvList)
                    modelExpFlag = self.__comparisonList(tmpMdelWvList, tmpExpWvList)
                    expModelFlag = self.__comparisonList(tmpExpWvList, tmpMdelWvList)
                    if modelExpFlag and expModelFlag:
                        # found matched
                        # if no changes
                        if not cleanFlag:
                            updateFlag = False
                        #
                    elif modelExpFlag:
                        # model file has more wavelengths, copy over
                        expMuList = modelMuList
                        expWvList = modelWvList
                    elif expModelFlag:
                        # sf file has more wavelengths, set diffFlag
                        diffFlag = True
                    else:
                        # check if has wavelength = 1 in sf file
                        if (len(expWvList) == 1) and exp_wavelength_1:
                            expMuList = modelMuList
                            expWvList = modelWvList
                        else:
                            # real difference
                            diffFlag = True
                        #
                    #
                elif modelMuList:
                    # only model file has wavelengths(s), copy over
                    expMuList = modelMuList
                    expWvList = modelWvList
                elif expMuList:
                    # only sf file has wavelengths(s)
                    if not cleanFlag:
                        updateFlag = False
                    #
                else:
                    # no data -- so move on
                    updateFlag = False
                #
                # create return json data here
                dataInfo = {}
                if modelWvList:
                    dataInfo["model"] = modelWvList
                #
                if expWvList:
                    dataInfo["sf"] = expWvList
                #
                if diffFlag:
                    dataInfo["diff"] = diffFlag
                    self.__diffFlag = True
                    self.__warningMsg.append("Wavelength conflict between model coordinate file and '" + curContainerName + "' data block in reflection data file.")
                #
                if dataInfo:
                    self.__wavelengthInfo[container.getName()] = dataInfo
                #
                if (not updateFlag) or self.__diffFlag:
                    continue
                #
                if self.__verbose:
                    self.__lfh.write("+PdbxExpUpdate.doUpdate() updating wavelength setting in container %r expMuList %r\n" % (curContainerName, expMuList))
                #
                ok = sfIo.updateRadiationWavelength(expMuList, container)
                if not ok:
                    self.__warningMsg.append("Update 'diffrn_radiation_wavelength' category failed for '" + curContainerName + "' data block.")
                    returnFlag = False
                    break
                anyUpdates = True
                #
            #
            self.__wavelengthInfo["datablock"] = containerNameList
            self.__wavelengthInfo["maximum_number"] = self.__maximalWavelengthNumber + 5
            #
            # ----------------------   write output file and add separator comments ------------------------
            #
            # Logic at end: If skipNotChanged False - always write. If skipNotChanged and anyUpdate is false, skip
            if (not self.__diffFlag) and returnFlag and not (skipNotChanged and not anyUpdates):
                if self.__verbose:
                    self.__lfh.write("+PdbxExpUpdate.doUpdate() writing container list to %r\n" % (outExpFilePath))
                #
                # ---- simple updates of identifiers ----
                sfIo.updateContainerNames(idCode=pdbId, containerList=containerList)
                sfIo.updateEntryIds(idCode=pdbId, containerList=containerList)
                #
                sfIo.writeContainerList(self.__tempFilePath, containerList)
                self.__insertComments(self.__tempFilePath, outExpFilePath)
                self.addDownloadPath(outExpFilePath)
                self.__warningMsg.append("Update wavelength in reflection data succeeded.")
                self.__wavelengthInfo = {}
            #
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            #
            self.__warningMsg.append("Update wavelength in reflection data failed.")
            returnFlag = False
        #
        self.__writeLog()
        #
        if self.__verbose:
            endTime = time.time()
            self.__lfh.write(
                "\nCompleted %s %s at %s (%.2f seconds)\n"
                % (self.__class__.__name__, inspect.currentframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - startTime)
            )
        #
        return returnFlag

    def __insertComments(self, inpFn, outFn):
        """Insert end of block/file comments in the input file --"""
        #
        try:
            pattern = r"[\r\n]+data_"
            replacement = r"\n#END\ndata_"
            reObj = re.compile(pattern, re.MULTILINE | re.DOTALL | re.VERBOSE)
            # Flush changes made to the in-memory copy of the file back to disk
            with open(outFn, "w") as ofh:
                with open(inpFn, "r") as ifh:
                    ofh.write(reObj.sub(replacement, ifh.read()) + "\n#END OF REFLECTIONS\n")
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False

    def __writeLog(self):
        """Insert end of block/file comments in the input file --"""
        #
        try:
            ofh = open(self.__logFilePath, "w")
            ofh.write("%s\n" % "\n".join(self.__warningMsg))
            ofh.close()
            self.addDownloadPath(self.__logFilePath)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False
        #

    def __processList(self, wvList):
        """ """
        newWvlist = []
        for val in wvList:
            if val.find(".") == -1:
                newWvlist.append(val)
                continue
            #
            while val[-1] == "0":
                val = val[:-1]
            #
            newWvlist.append(val)
        #
        return newWvlist

    def __comparisonList(self, firstList, secondList):
        """ """
        for val in secondList:
            if val not in firstList:
                return False
            #
        #
        return True


if __name__ == "__main__":
    from wwpdb.utils.config.ConfigInfo import ConfigInfo
    from wwpdb.utils.session.WebRequest import InputRequest

    #
    siteId = os.getenv("WWPDB_SITE_ID")
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH"))
    myReqObj.setValue("TopPath", cI.get("SITE_WEB_APPS_TOP_PATH"))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("sessionid", "eb961ee10712d1afe48efb151dd8dd9a1b45e673")
    #
    calc = PdbxExpUpdate(reqObj=myReqObj, verbose=True, log=sys.stderr)
    calc.doUpdate("D_1000001900", modelInputFile="D_1000001900_model_P1.cif", expInputFile="D_1000001900_sf_P1.cif", expOutputFile="D_1000001900_sf_P1.cif")
#   print calc.getDiffFlag()
#   print calc.getWarningMessage()
#   print calc.getWavelengthInfo()
