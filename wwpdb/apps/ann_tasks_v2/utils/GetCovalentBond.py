##
# File:  GetCovalentBond.py
# Date:  28-Sep-2020  Zukang Feng
#
# Update:
##
"""
Manage utility to correct covalent bond problems

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


class GetCovalentBond(object):
    """
    GetCovalentBond class encapsulates correcting covalent bond problems.
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
            logPath = os.path.join(self.__sessionPath, entryId + "-get-covalent-bond.log")
            retPath = os.path.join(self.__sessionPath, entryId + "-covalent-bond.json")
            for filePath in (logPath, retPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            #
            dp.imp(inpPath)
            dp.op("annot-get-covalent-bond")
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
        if (not jsonObj) or ("covalent_bond" not in jsonObj) or (not jsonObj["covalent_bond"]):
            return ""
        #
        htmlTemplate = """
        <input type="hidden" name="total_covalent_bond_num" value="%s" />
        <table class="table table-borderedless width80">
          <tr><th colspan="3">Select Links that you would like to remove and transform into close contacts and press “Delete Link(s)” button.</th></tr>
          <tr>
            <th><input id="covalent_bond_select_all" class="btn btn-primary my-task-form-submit" value="Select All" type="button"
                 onClick="select_close_contact_covalent_bond('update-covalent-bond-form', 'covalent_bond_', 'covalent_bond_select_all', '');" /></th>
            <th><input id="covalent_bond_submit" class="btn btn-primary my-task-form-submit" value="Delete Link(s)" type="submit" /></th>
            <th><input id="covalent_bond_exit" class="btn btn-primary my-task-form-submit" value="Exit" type="button"
                 onClick="exit_close_contact_covalent_bond_page();" /></th>
          </tr>
        </table>
        <br/>
        <table class="table table-bordered table-striped width100">
          <tr>
            <th rowspan="2">Id</th>
            <th colspan="5">Atom1</th>
            <th colspan="5">Atom2</th>
            <th rowspan="2">Leaving<br/>atoms</th>
            <th rowspan="2">Distance</th>
          </tr>
          <tr>
            <th>Chain ID</th>
            <th>Residue</th>
            <th>Number</th>
            <th>Atom</th>
            <th>Symmetry</th>
            <th>Chain ID</th>
            <th>Residue</th>
            <th>Number</th>
            <th>Atom</th>
            <th>Symmetry</th>
          </tr>
          %s
        </table>
        """
        #
        tablerow = ""
        count = 0
        for tupL in jsonObj["covalent_bond"]:
            tablerow += "<tr>"
            #
            atom = tupL[4]
            if tupL[5]:
                atom += "(" + tupL[5] + ")"
            #
            tablerow += "<td>" + tupL[16] + "</td><td>" + tupL[0] + "</td><td>" + tupL[1] + "</td><td>" + tupL[2] + tupL[3] + "</td><td>" \
                + atom + "</td><td>" + tupL[6] + "</td>"
            atom = tupL[11]
            if tupL[12]:
                atom += "(" + tupL[12] + ")"
            #
            tablerow += "<td>" + tupL[7] + "</td><td>" + tupL[8] + "</td><td>" + tupL[9] + tupL[10] + "</td><td>" + atom + "</td><td>" \
                + tupL[13] + "</td><td>" + tupL[14] + "</td>"
            #
            tupL[6] = tupL[6].replace("_", "-")
            tupL[13] = tupL[13].replace("_", "-")
            bond_id = "covalent_bond_" + str(count)
            #
            tablerow += "<td>" + tupL[15] + '&nbsp; &nbsp; &nbsp; &nbsp; <input type="checkbox" id="' + bond_id + '" name="' + bond_id \
                + '" value="' + "_".join(tupL[:16]) + '"/></td>'
            #
            tablerow += "</tr>\n"
            count += 1
        #
        return htmlTemplate % (str(count), tablerow)


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
    calc = GetCovalentBond(reqObj=myReqObj, verbose=True, log=sys.stderr)
    retD = calc.run("D_1000001900", "D_1000001900_model_P1.cif")
    for k, v in retD.items():
        print(k + "=" + v)


if __name__ == "__main__":
    main()
