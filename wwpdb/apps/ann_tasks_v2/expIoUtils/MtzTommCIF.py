##
# File:  MtzTommCIF.py
# Date:  29-May-2018  Zukang Feng
#
# Update:
##
"""
Manage utility to convert mtz to mmCIF

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os
import traceback

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
from wwpdb.apps.ann_tasks_v2.expIoUtils.PdbxExpIoUtils import PdbxExpFileIo, PdbxExpIoUtils
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class MtzTommCIF(SessionWebDownloadUtils):
    """
    MtzTommCIF class encapsulates converting mtz to mmCIF.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(MtzTommCIF, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__htmlText = ""
        self.__status = None
        #
        self.__setup()

    def run(self, entryId, expFileName):
        """Run the calculation"""
        try:
            logPath = os.path.join(self.__sessionPath, entryId + "-mtz2mmcif.log")
            retPath = os.path.join(self.__sessionPath, entryId + "-mtz2mmcif.cif")
            #
            for filePath in (self.__mtzLogPath, self.__htmlPath, self.__sfInfoPath, logPath, retPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            if self.__taskFormId == "#mtz-mmcif-conversion-form":
                return self.__generateInputForm(logPath)
            elif self.__taskFormId == "#mtz-mmcif-semi-auto-conversion-form":
                return self.__convertMtzTommCIF(expFileName, retPath, logPath)
            else:
                return False
            #
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            #
            return False
        #

    def getLastStatus(self):
        return self.__status

    def getHtmlText(self):
        """ """
        return self.__htmlText

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        self.__packagePath = self.__cICommon.get_site_packages_path()
        self.__topSessionPath = self.__cICommon.get_site_web_apps_sessions_path()
        #
        self.__mtzFileName = self.__reqObj.getValue("infile")
        self.__mtzDataSet = self.__reqObj.getValue("data_set")
        self.__taskFormId = self.__reqObj.getValue("taskformid")
        self.__intDataSet = 1
        if self.__mtzDataSet:
            self.__intDataSet = int(self.__mtzDataSet)
        #
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        self.__status = "none"
        #
        self.__mtzLogPath = os.path.join(self.__sessionPath, "mtzdmp.log")
        self.__htmlPath = os.path.join(self.__sessionPath, "get_mtz_infor.html")
        self.__sfInfoPath = os.path.join(self.__sessionPath, "sf_information.cif")

    def __bashSetting(self, html=False):
        setting = (
            " PACKAGE_DIR="
            + self.__packagePath
            + "; export PACKAGE_DIR; "
            + " SF_PATH=${PACKAGE_DIR}/sf-valid; export SF_PATH; "
            # + " CCP4_PATH=${PACKAGE_DIR}/ccp4; export CCP4_PATH; "
            # + " PHENIX_PATH=${PACKAGE_DIR}/phenix; export PHENIX_PATH; "
            # + " source ${CCP4_PATH}/bin/ccp4.setup-sh; source ${PHENIX_PATH}/phenix_env.sh; "
        )

        if html:
            setting += "${SF_PATH}/bin/sf_convert_html "
        else:
            setting += "${SF_PATH}/bin/sf_convert "
        return setting

    def __generateInputForm(self, logPath):
        """ """
        options = (
            " -mtz_man_html "
            + self.__mtzDataSet
            + " -url_users_data "
            + os.path.join("/sessions", self.__sessionId)
            + " -users_data "
            + self.__topSessionPath
            + " -cgi_bin  /cgi-bin/ -sf "
            + self.__mtzFileName
            + " > "
            + logPath
            + " 2>&1 ; "
        )
        self.__runCmd(options, html=True)
        #
        if os.access(self.__mtzLogPath, os.R_OK) and os.access(self.__htmlPath, os.R_OK):
            cmd = "cat " + self.__mtzLogPath + " >> " + logPath + " ; "
            os.system(cmd)
            self.addDownloadPath(logPath)
            #
            self.__readHtmlText()
            if self.__htmlText:
                self.__status = "ok"
                return True
            #
        #
        self.__status = "error"
        return False

    def __convertMtzTommCIF(self, expFileName, retPath, logPath):
        """ """
        labels = self.__parseSemiAutoForm()
        pdbid = self.__getPdbId()
        #
        options = " -i mtz -o mmcif -sf " + self.__mtzFileName + " -out " + retPath + " -pdb_id " + pdbid + " -label " + labels + " > " + logPath + " 2>&1 ; "
        self.__runCmd(options)
        #
        for filePath in (logPath, self.__mtzLogPath, self.__sfInfoPath):
            if os.access(filePath, os.R_OK):
                self.addDownloadPath(filePath)
            #
        #
        if os.access(retPath, os.R_OK):
            finalPath = os.path.join(self.__sessionPath, expFileName)
            if os.access(finalPath, os.R_OK):
                os.remove(finalPath)
            #
            os.rename(retPath, finalPath)
            #
            self.addDownloadPath(finalPath)
            #
            self.__status = "ok"
            return True
        #
        self.__status = "error"
        return False

    def __runCmd(self, options, html=False):
        """ """
        cmd = "cd " + self.__sessionPath + " ; " + self.__bashSetting(html) + options
        if self.__verbose:
            self.__lfh.write("MtzTommCIF command: %s\n" % cmd)
        os.system(cmd)

    def __readHtmlText(self):
        """ """
        try:
            ofh = open(self.__htmlPath, "r")
            data = ofh.read()
            ofh.close()
            #
            start = False
            for line in data.split("\n"):
                if line.startswith("<CENTER> <h3> Semi-auto conversion"):
                    start = True
                elif line.find("Data Column Selector") != -1:
                    self.__htmlText += "<br/><br/>"
                # elif line.startswith('<input type="hidden"  name='):
                #    break
                elif (
                    (not start)
                    or line.startswith("<form ENCTYPE=")
                    or line.startswith("<INPUT TYPE=SUBMIT NAME=")
                    or line.startswith("<INPUT TYPE=RESET VALUE")
                    or line.startswith("</form>")
                ):
                    continue
                #
                # line = line.replace('align=center cellpadding=8', 'cellpadding="15" cellspacing="15"')
                # line = line.replace('<td align=center>', '<td style="margin:30px;text-align:center;">')
                # line = line.replace('<td>', '<td style="margin:30px;">')
                self.__htmlText += line
            #
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            #
        #

    def __parseSemiAutoForm(self):
        """ """
        tokenNameList = [
            ["fp", " 'FP=%s', "],
            ["sigfp", " 'SIGFP=%s', "],
            ["i", " 'I=%s', "],
            ["sigi", " 'SIGI=%s', "],
            ["free", " 'FreeR_flag=%s', "],  # Gemmi will instantiate pdbx_r_free_flag as well. Undocumented feature
            ["phib", " 'PHIB=%s', "],
            ["fom", " 'FOM=%s', "],
            ["fc", " 'FC=%s', "],
            ["phic", " 'PHIC=%s', "],
            ["hla", " 'HLA=%s', "],
            ["hlb", " 'HLB=%s', "],
            ["hlc", " 'HLC=%s', "],
            ["hld", " 'HLD=%s', "],
            ["iplus", " 'I(+)=%s', "],
            ["sigiplus", " 'SIGI(+)=%s', "],
            ["ineg", " 'I(-)=%s', "],
            ["sigineg", " 'SIGI(-)=%s', "],
            ["fplus", " 'F(+)=%s', "],
            ["sigfplus", " 'SIGF(+)=%s', "],
            ["fneg", " 'F(-)=%s', "],
            ["sigfneg", " 'SIGF(-)=%s', "],
            ["dp", " 'DP=%s', "],
            ["sigdp", " 'SIGDP=%s', "],
            ["fwt", " 'FWT=%s', "],
            ["phwt", " 'PHWT=%s', "],
            ["delfwt", " 'DELFWT=%s', "],
            ["delphwt", " 'DELPHWT=%s', "],
            ["freer", " -freer %s "],
        ]
        #
        items = ""
        lastitem = None
        for i in range(self.__intDataSet):
            if (i > 0) and items:
                items += " : "
            #
            for tokenName in tokenNameList:
                value = self.__reqObj.getValue(tokenName[0] + "_" + str(i + 1))
                if not value:
                    continue
                #
                # This limits us to a single rfree across multiple sets.
                if tokenName[0] == "freer":
                    lastitem = tokenName[1] % value
                else:
                    items += tokenName[1] % value
            #
        #
        if lastitem:
            items += lastitem

        return items

    def __getPdbId(self):
        """ """
        pdbid = "xxxx"
        try:
            modelFileName = self.__reqObj.getValue("entryfilename")
            if not modelFileName:
                return pdbid
            #
            modelFilePath = os.path.join(self.__sessionPath, modelFileName)
            if not os.access(modelFilePath, os.R_OK):
                return pdbid
            #
            mIo = PdbxExpFileIo(verbose=self.__verbose, log=self.__lfh)
            modelContainerList = mIo.getContainerList(modelFilePath)
            if len(modelContainerList) < 1:
                return pdbid
            #
            mE = PdbxExpIoUtils(dataContainer=modelContainerList[0], verbose=self.__verbose, log=self.__lfh)
            pdbid = str(mE.getDbCode(dbId="PDB")).lower()
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        #
        return pdbid


if __name__ == "__main__":
    from wwpdb.utils.session.WebRequest import InputRequest

    #
    siteId = os.getenv("WWPDB_SITE_ID")
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH"))
    myReqObj.setValue("TopPath", cI.get("SITE_WEB_APPS_TOP_PATH"))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("sessionid", "92c737c7279b3c179bc8afd752d204135d5ec98c")
    myReqObj.setValue("data_set_mtz", "2")
    myReqObj.setValue("uploadmtzfile", "/net/users/zfeng/mtz/SF_file.inp")
    #
    calc = MtzTommCIF(reqObj=myReqObj, verbose=True, log=sys.stderr)
    calc.run("D_1000223249", "D_1000223249_sf_P1.cif")
    print(calc.getHtmlText())
