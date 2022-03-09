##
# File:  ReSetFreeRinSFmmCIF.py
# Date:  26-Feb-2019  Zukang Feng
#
# Update:
##
"""
Utility to reset free R set of sf file in mmCIF format

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys
import traceback

from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class ReSetFreeRinSFmmCIF(SessionWebDownloadUtils):
    """
    ReSetFreeRinSFmmCIF class encapsulates resetting free R set of sf file in mmCIF format

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(ReSetFreeRinSFmmCIF, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__reqObj = reqObj
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        #
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #
        self.__entryId = self.__reqObj.getValue("entryid")
        self.__modelFileName = self.__reqObj.getValue("entryfilename")
        self.__expFileName = self.__reqObj.getValue("entryexpfilename")
        #
        self.__status = False
        self.__message = ""

    def run(self):
        """Run the calculation"""
        try:
            logPath = os.path.join(self.__sessionPath, self.__entryId + "-reset_freer.log")
            if os.access(logPath, os.R_OK):
                os.remove(logPath)
            #
            for i in range(20):
                if (not self.__generate_mmCIFFile(str(i))) or self.__runDccValidation(str(i)):
                    break
                #
            #
            fh = open(logPath, "w")
            fh.write("%s\n" % self.__message)
            fh.close()
            #
            self.addDownloadPath(logPath)
            if self.__status:
                self.addDownloadPath(os.path.join(self.__sessionPath, self.__expFileName))
            #
            return self.__status
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            #
            return False
        #

    def __generate_mmCIFFile(self, set_id):
        """Manipulate SF file"""
        try:
            logPath = os.path.join(self.__sessionPath, "logfile")
            outputPath = os.path.join(self.__sessionPath, self.__entryId + "_sf.cif")
            for filePath in (logPath, outputPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(os.path.join(self.__sessionPath, self.__expFileName))
            dp.addInput(name="set_num", value=set_id)
            dp.op("annot-correct-freer-set")
            dp.exp(outputPath)
            dp.expLog(logPath)
            dp.cleanup()
            #
            hasError = False
            for fileName in ("logfile", "clogfile"):
                logFile = os.path.join(self.__sessionPath, fileName)
                if not os.access(logFile, os.R_OK):
                    continue
                #
                fh = open(logFile, "r")
                data = fh.read()
                fh.close()
                #
                if (data == "") or (data == "Finished!\n"):
                    continue
                #
                if self.__message:
                    self.__message += "\n"
                #
                self.__message += data
                hasError = True
            #
            if hasError:
                return False
            #
            if not os.access(outputPath, os.R_OK):
                if self.__message:
                    self.__message += "\n"
                #
                self.__message += "Generated 'SF-'" + set_id + ".cif' file failed."
                return False
            #
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            self.__message += "Generated 'SF-'" + set_id + ".cif' file failed:\n" + traceback.format_exc()
            return False
        #

    def __runDccValidation(self, set_id):
        """Run dcc program to verify if the mainpulated sf file is correct."""
        try:
            logPath = os.path.join(self.__sessionPath, "dcc_logfile")
            outputPath = os.path.join(self.__sessionPath, self.__entryId + "_dcc.cif")
            for filePath in (logPath, outputPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(os.path.join(self.__sessionPath, self.__entryId + "_sf.cif"))
            dp.addInput(name="model_file", value=os.path.join(self.__sessionPath, self.__modelFileName))
            dp.op("annot-dcc-validation")
            dp.exp(outputPath)
            dp.expLog(logPath)
            dp.cleanup()
            #
            logData = "Calculating R/Rfree for (" + self.__modelFileName + " & SF-" + set_id + ".cif):"
            if os.access(logPath, os.R_OK):
                fh = open(logPath, "r")
                data = fh.read()
                fh.close()
                #
                for line in data.split("\n"):
                    if not line:
                        continue
                    #
                    if (line.find("Error") != -1) or (line.find("Warn") != -1):
                        if logData:
                            logData += "\n"
                        #
                        logData += line
                    #
                #
            #
            if os.access(outputPath, os.R_OK):
                try:
                    # vec[0]: ls_d_res_high
                    # vec[1]: ls_R_factor_R_all/ls_R_factor_R_work
                    # vec[2]: ls_R_factor_R_free
                    # vec[3]: correlation_coeff_Fo_to_Fc
                    res_pdb = [-1.0, -1.0, -1.0, -1.0]
                    res_tls = [-1.0, -1.0, -1.0, -1.0]
                    res_best = [-1.0, -1.0, -1.0, -1.0]
                    #
                    cifObj = mmCIFUtil(filePath=outputPath)
                    tlist = cifObj.GetValue("pdbx_density_corr")
                    items = ("ls_d_res_high", "ls_R_factor_R_work", "ls_R_factor_R_all", "ls_R_factor_R_free", "correlation_coeff_Fo_to_Fc", "details")
                    #
                    for tdir in tlist:
                        data = []
                        for item in items:
                            if (item in tdir) and tdir[item]:
                                data.append(tdir[item])
                            else:
                                data.append("")
                            #
                        #
                        res = -1.0
                        if data[0] != "":
                            res = float(data[0])
                        #
                        r_all = -1.0
                        if data[2] != "":
                            r_all = float(data[2])
                        elif data[1] != "":
                            r_all = float(data[1])
                        #
                        r_free = -1.0
                        if data[3] != "":
                            r_free = float(data[3])
                        #
                        corr = -1.0
                        if data[4] != "":
                            corr = float(data[4])
                        #
                        if data[5] == "PDB reported":
                            res_pdb = [res, r_all, r_free, corr]
                        elif data[5].find("TLS") != -1:
                            res_tls = [res, r_all, r_free, corr]
                        elif data[5].find("Best") != -1:
                            res_best = [res, r_all, r_free, corr]
                        #
                    #
                    logData += "\n\nset  reso  R_rep  Rf_rep  CC_rep    R_cal  Rf_cal  CC_cal\n"
                    logData += " %2s  %4.2f  %5.3f  %5.3f   %5.3f    %5.3f  %5.3f   %5.3f " % (
                        set_id,
                        res_pdb[0],
                        res_pdb[1],
                        res_pdb[2],
                        res_pdb[3],
                        res_best[1],
                        res_best[2],
                        res_best[3],
                    )
                    #
                    if (res_tls[2] - res_tls[1]) > 0.02:
                        os.path.join(self.__sessionPath, self.__entryId + "_sf.cif")
                        ifh = open(os.path.join(self.__sessionPath, self.__entryId + "_sf.cif"), "r")
                        sfData = ifh.read()
                        ifh.close()
                        #
                        ofh = open(os.path.join(self.__sessionPath, self.__expFileName), "w")
                        ofh.write(sfData)
                        ofh.write("#END OF REFLECTIONS\n")
                        ofh.close()
                        #
                        self.__status = True
                        self.__message = logData + "\n\nFree R set was successfully relabeled."
                        return True
                    #
                    if self.__message:
                        self.__message += "\n\n"
                    #
                    self.__message += logData
                except:  # noqa: E722 pylint: disable=bare-except
                    if self.__verbose:
                        traceback.print_exc(file=self.__lfh)
                    #
                #
            #
            return False
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            self.__message += "Calculating R/Rfree for (" + self.__modelFileName + " & SF-" + set_id + ".cif):\n" + traceback.format_exc()
            return False
        #


if __name__ == "__main__":
    from wwpdb.utils.session.WebRequest import InputRequest

    #
    siteId = os.getenv("WWPDB_SITE_ID")
    cI = ConfigInfo(siteId)
    #
    # example from DAOTHER-3749
    #
    myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH"))
    myReqObj.setValue("TopPath", cI.get("SITE_WEB_APPS_TOP_PATH"))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("sessionid", "055ac3ebcdf64e5d4066f5c3950b8465a44dc9d1")
    myReqObj.setValue("entryid", "D_1000225001")
    myReqObj.setValue("entryfilename", "D_1000225001_model_P1.cif.V11")
    myReqObj.setValue("entryexpfilename", "D_1000225001_sf_P1.cif-wrong")
    #
    calc = ReSetFreeRinSFmmCIF(reqObj=myReqObj, verbose=True, log=sys.stderr)
    calc.run()
