##
# File:  XmlCheck.py
# Date:  25-May-2023  Zukang Feng
#
# Update:
##
"""
PDBML/XML checking

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os
import traceback
import inspect

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.apps.ann_tasks_v2.utils.PublicPdbxFile import PublicPdbxFile


class XmlCheck(PublicPdbxFile):

    """
    Encapsulates PDBML/XML checking.
    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(XmlCheck, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__reportPath = None
        self.__reportFileSize = 0
        self.__checkArgs = None  # pylint: disable=unused-private-member
        self.__publicCifPath = None
        self.__xmlPath = None

    def setArguments(self, checkArgs):
        self.__checkArgs = checkArgs  # pylint: disable=unused-private-member

    def run(self, entryId, inpPath, publicCIFlag=True):
        """Run the PDBML/XML check on the input PDBx/mmCIF data file"""
        try:
            self.clearFileList()
            #
            self.__reportPath = os.path.join(self._exportPath, entryId + "_xml-check-report_P1.txt.V1")
            if os.access(self.__reportPath, os.R_OK):
                os.remove(self.__reportPath)
            #
            if not publicCIFlag:
                self.__publicCifPath = self.run_conversion("cif2pdbx-ext", entryId, inpPath)
            else:
                self.__publicCifPath = inpPath
            #
            if self.__publicCifPath is None:
                return
            #
            self.__generateXMLFile(entryId)
            if self.__xmlPath is None:
                return
            #
            self.__checkXMLFile(entryId, "annot-check-xml-xmllint")
            self.__checkXMLFile(entryId, "annot-check-xml-stdinparse")
            if self._verbose:
                self._lfh.write(
                    "+%s.%s PDBML XML check completed for entryId %s file %s report %s size %d\n"
                    % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath, self.__reportPath, self.__reportFileSize)
                )
            #
        except:  # noqa: E722 pylint: disable=bare-except
            if self._verbose:
                self._lfh.write("+%s.%s PDBML XML check failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, inpPath))
            #
            traceback.print_exc(file=self._lfh)
        #

    def getReportSize(self):
        return self.__reportFileSize

    def getReportPath(self):
        return self.__reportPath

    def __generateXMLFile(self, entryId):
        """Generate noatom xml file"""
        try:
            outputList = []
            outputList.append(os.path.join(self._exportPath, self.__publicCifPath + ".xml-noatom"))
            outputList.append(os.path.join(self._exportPath, entryId + "_generate_xml_v5.log"))
            outputList.append(os.path.join(self._exportPath, entryId + "_generate_xml_command_v5.log"))
            for filePath in outputList:
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self._sessionPath, siteId=self._siteId, verbose=self._verbose, log=self._lfh)
            if self._debug:
                dp.setDebugMode(flag=True)
            #
            dp.imp(self.__publicCifPath)
            dp.op("annot-public-pdbx-to-xml-noatom")
            dp.expList(outputList)
            #
            if os.access(os.path.join(self._exportPath, self.__publicCifPath + ".xml-noatom"), os.R_OK):
                self.__xmlPath = os.path.join(self._exportPath, self.__publicCifPath + ".xml-noatom")
            #
            if self._cleanup:
                dp.cleanup()
            #
        except:  # noqa: E722 pylint: disable=bare-except
            if self._verbose:
                self._lfh.write(
                    "+%s.%s XML conversion failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, entryId, self.__publicCifPath)
                )
            #
            traceback.print_exc(file=self._lfh)
        #

    def __checkXMLFile(self, entryId, op):
        """Check noatom xml file"""
        try:
            if (not self.__xmlPath) or (not os.access(self.__xmlPath, os.R_OK)):
                return
            #
            if op == "annot-check-xml-xmllint":
                statinfo = os.stat(self.__xmlPath)
                if statinfo.st_size > 100000000:
                    return
                #
            #
            inReportPath = os.path.join(self._exportPath, entryId + ".xml.diag")
            if os.access(inReportPath, os.R_OK):
                os.remove(inReportPath)
            #
            outputList = []
            outputList.append(inReportPath)
            #
            dp = RcsbDpUtility(tmpPath=self._sessionPath, siteId=self._siteId, verbose=self._verbose, log=self._lfh)
            if self._debug:
                dp.setDebugMode(flag=True)
            #
            dp.imp(self.__xmlPath)
            dp.op(op)
            dp.expList(outputList)
            #
            if os.access(inReportPath, os.R_OK):
                ith = open(inReportPath, "r")
                data = ith.read()
                ith.close()
                if len(data) > 0:
                    oth = open(self.__reportPath, "a")
                    for line in data.split("\n"):
                        strip_line = line.strip()
                        if (strip_line == "") or (strip_line == "input_file_1 validates") or strip_line.startswith("stdin:"):
                            continue
                        elif strip_line.startswith("input_file_1:") or strip_line.startswith("input_file_1 "):
                            oth.write("%s\n" % strip_line[13:])
                        else:
                            oth.write("%s\n" % strip_line)
                        #
                    #
                    oth.close()
                    statinfo = os.stat(self.__reportPath)
                    self.__reportFileSize = statinfo.st_size
                #
            #
            if self._cleanup:
                dp.cleanup()
            #
        except:  # noqa: E722 pylint: disable=bare-except
            if self._verbose:
                self._lfh.write(
                    "+%s.%s XML (%s) checking failed for entryId %s file %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, op, entryId, self.__xmlPath)
                )
            #
            traceback.print_exc(file=self._lfh)
        #
