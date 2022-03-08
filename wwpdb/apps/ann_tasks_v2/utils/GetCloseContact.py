##
# File:  GetCloseContact.py
# Date:  28-Sep-2020  Zukang Feng
#
# Update:
##
"""
Manage utility to correct TLS problems

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import json
import os
import sys
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class GetCloseContact(object):
    """
    GetCloseContact class encapsulates correcting close contact problems.
    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__reqObj = reqObj
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def run(self, entryId, inpFile):
        """Run the calculation"""
        retD = {}
        retD["found"] = "no"
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath = os.path.join(self.__sessionPath, entryId + "-close-contact.log")
            retPath = os.path.join(self.__sessionPath, entryId + "-close-contact.json")
            for filePath in (logPath, retPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            #
            dp.imp(inpPath)
            dp.op("annot-get-close-contact")
            dp.expLog(dstPath=logPath, appendMode=False)
            dp.exp(retPath)
            #
            if os.access(retPath, os.R_OK):
                with open(retPath) as ifh:
                    jsonObj = json.load(ifh)
                    htmlcontent = self.__processCloseContactContent(jsonObj)
                    if htmlcontent:
                        retD["htmlcontent"] = htmlcontent
                        retD["found"] = "yes"
                    #
                #
            #
            dp.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #
        return retD

    def __processCloseContactContent(self, jsonObj):
        """ """
        if (not jsonObj) or ("close_contact" not in jsonObj) or (not jsonObj["close_contact"]):
            return ""
        #
        htmlTemplate = """
        <input type="hidden" name="total_close_contact_num" value="%s" />
        <table class="table table-borderedless width80">
          <tr>
            <th><input id="close_contact_select_all" class="btn btn-primary my-task-form-submit" value="Select All" type="button"
                 onClick="select_close_contact('close_contact_select_all', '');" /></th>
            %s
            <th><input id="close_contact_submit" class="btn btn-primary my-task-form-submit" value="Submit" type="submit" /></th>
            <th><input id="close_contact_exit" class="btn btn-primary my-task-form-submit" value="Exit" type="button" onClick="exit_close_contact_page();" /></th>
          </tr>
        </table>
        <br/>
        <table class="table table-bordered table-striped width100">
          <tr>
            <th colspan="4">Atom1</th>
            <th colspan="4">Atom2</th>
            <th rowspan="2">Distance</th>
          </tr>
          <tr>
            <th>Chain ID</th>
            <th>Residue</th>
            <th>Number</th>
            <th>Atom</th>
            <th>Chain ID</th>
            <th>Residue</th>
            <th>Number</th>
            <th>Atom</th>
          </tr>
          %s
        </table>
        """
        #
        green_count = 0
        tablerow = ""
        count = 0
        for tupL in jsonObj["close_contact"]:
            if tupL[13] == "green":
                green_count += 1
            #
            tablerow += "<tr>"
            #
            atom = tupL[4]
            if tupL[5]:
                atom += "(" + tupL[5] + ")"
            #
            tablerow += "<td>" + tupL[0] + "</td>" + "<td>" + tupL[1] + "</td>" + "<td>" + tupL[2] + tupL[3] + "</td>" + "<td>" + atom + "</td>"
            atom = tupL[10]
            if tupL[11]:
                atom += "(" + tupL[11] + ")"
            #
            tablerow += "<td>" + tupL[6] + "</td>" + "<td>" + tupL[7] + "</td>" + "<td>" + tupL[8] + tupL[9] + "</td>" + "<td>" + atom + "</td>"
            #
            if tupL[13]:
                tablerow += '<td style="color:' + tupL[13] + ';">' + tupL[12]
            else:
                tablerow += "<td>" + tupL[12]
            #
            close_id = "close_contact_" + str(count)
            tablerow += '&nbsp; &nbsp; &nbsp; &nbsp; <input type="checkbox" id="' + close_id + '" name="' + close_id + '" value="' + "_".join(tupL[:13]) + '"'
            if tupL[13]:
                tablerow += ' class="' + tupL[13] + '"'
            #
            tablerow += "/></td>"
            tablerow += "</tr>\n"
            count += 1
        #
        select_green_button = ""
        if (green_count > 0) and (green_count < len(jsonObj["close_contact"])):
            select_green_button = (
                '<th><input id="close_contact_select_all_green" class="btn btn-primary my-task-form-submit" value="Select All green" '
                + "type=\"button\" onClick=\"select_close_contact('close_contact_select_all_green', 'green');\" /></th>"
            )
        #
        return htmlTemplate % (str(count), select_green_button, tablerow)


def main():
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
    myReqObj.setValue("sessionid", "d581f7aa63cc8feba7d96fb9fd103866fca45a7d")
    #
    calc = GetCloseContact(reqObj=myReqObj, verbose=True, log=sys.stderr)
    retD = calc.run("D_1000001900", "D_1000001900_model_P1.cif")
    for k, v in retD.items():
        print(k + "=" + v)


if __name__ == "__main__":
    main()
