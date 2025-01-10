##
# File:  PdbxReport.py
# Date:  11-July-2013
#
# Updates:
# 15-Jun-2014  jdw add accessor methods for struct_title/pdb_id
# 09-Dec-2024  zf  add "nmr-cs-validation-report" with CSValidationReportIo/CSValidationReportStyle
##
"""
PDBx general report generator -

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import shutil
import sys
import traceback

from mmcif_utils.style.PdbxGeometryReportCategoryStyle import PdbxGeometryReportCategoryStyle

from wwpdb.apps.ann_tasks_v2.report.PdbxReportDepictBootstrap import PdbxReportDepictBootstrap
from wwpdb.apps.ann_tasks_v2.report.styles.CSValidationReport import CSValidationReportStyle
from wwpdb.apps.ann_tasks_v2.report.styles.CSValidationReportIo import CSValidationReportIo
from wwpdb.apps.ann_tasks_v2.report.styles.DCCReport import PdbxXrayExpReportCategoryStyle
from wwpdb.apps.ann_tasks_v2.report.styles.ModelReport import PdbxReportCategoryStyle
from wwpdb.apps.ann_tasks_v2.report.styles.LinksReport import PdbxLinksReportCategoryStyle
from wwpdb.apps.ann_tasks_v2.report.styles.PdbxEmExtensionCategoryStyle import PdbxEmExtensionCategoryStyle
from wwpdb.apps.ann_tasks_v2.report.styles.PdbxIo import PdbxReportIo, PdbxGeometryReportIo, PdbxXrayExpReportIo, PdbxLinksReportIo, EmInfoReportIo


class PdbxReport(object):
    """PDBx report generator functions."""

    def __init__(self, reqObj, verbose=False, log=sys.stderr):
        """PRD report generator.

        :param `verbose`:  boolean flag to activate verbose logging.
        :param `log`:      stream for logging.

        """
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        #
        self.__reqObj = reqObj
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__sessionRelativePath = self.__sObj.getRelativePath()
        self.__sessionId = self.__sObj.getId()
        #
        self.__idCode = None
        self.__filePath = None
        self.__fileFormat = "cif"
        #
        self.__pdbIdCode = None
        self.__structTitle = None
        self.__primary_contour_level = None
        #

    def getPdbIdCode(self):
        return self.__pdbIdCode

    def getStructTitle(self):
        return self.__structTitle

    def getPrimaryContourlevel(self):
        return self.__primary_contour_level

    def makeTabularReport(self, filePath=None, contentType=None, idCode=None, layout="tabs", leadingHtmlL=None, trailingHtmlL=None):
        """Leading method to create a tabular report corresponding to the input Pdbx file.

        layout = tabs|accordion|multiaccordion|page-mutiaccordion|page-accordion

        Return data as a list of HTML markup for the section containing the tabular report.
        """
        if self.__verbose:
            self.__lfh.write("+PdbxReport.makeTabularReport() file path %s id code %s content type %s layout %s\n" % (filePath, idCode, contentType, layout))
        #
        templatePath = self.__reqObj.getValue("TemplatePath")
        includePath = os.path.join(templatePath, "includes")
        #
        oL = []
        fileFormat = "cif"
        #
        if filePath is not None and contentType is not None:
            if contentType in ["model"]:
                self.setFilePath(filePath, fileFormat=fileFormat, idCode=idCode)
                dd = self.doReport(contentType)
                #
                if "pdb_id" in dd:
                    self.__pdbIdCode = dd["pdb_id"]
                if "struct_title" in dd:
                    self.__structTitle = dd["struct_title"]
                if "primary_contour_level" in dd:
                    self.__primary_contour_level = dd["primary_contour_level"]
                #
                rdd = PdbxReportDepictBootstrap(styleObject=PdbxReportCategoryStyle(), includePath=includePath, verbose=self.__verbose, log=self.__lfh)
                oL = rdd.render(dd, style=layout, leadingHtmlL=leadingHtmlL, trailingHtmlL=trailingHtmlL)
            #
            if contentType in ["dcc-report"]:
                self.setFilePath(filePath, fileFormat=fileFormat, idCode=idCode)
                dd = self.doReport(contentType)
                rdd = PdbxReportDepictBootstrap(styleObject=PdbxXrayExpReportCategoryStyle(), includePath=includePath, verbose=self.__verbose, log=self.__lfh)
                oL = rdd.render(dd, style=layout, leadingHtmlL=leadingHtmlL, trailingHtmlL=trailingHtmlL)
            #
            if contentType in ["geometry-check-report"]:
                self.setFilePath(filePath, fileFormat=fileFormat, idCode=idCode)
                dd = self.doReport(contentType)
                rdd = PdbxReportDepictBootstrap(styleObject=PdbxGeometryReportCategoryStyle(), includePath=includePath, verbose=self.__verbose, log=self.__lfh)
                oL = rdd.render(dd, style=layout, leadingHtmlL=leadingHtmlL, trailingHtmlL=trailingHtmlL)
            #
            if contentType in ["links-report"]:
                self.setFilePath(filePath, fileFormat=fileFormat, idCode=idCode)
                dd = self.doReport(contentType)
                rdd = PdbxReportDepictBootstrap(styleObject=PdbxLinksReportCategoryStyle(), includePath=includePath, verbose=self.__verbose, log=self.__lfh)
                oL = rdd.render(dd, style=layout, leadingHtmlL=leadingHtmlL, trailingHtmlL=trailingHtmlL)
            #
            if contentType in ["em-map-info-report"]:
                self.setFilePath(filePath, fileFormat=fileFormat, idCode=idCode)
                dd = self.doReport(contentType)
                rdd = PdbxReportDepictBootstrap(styleObject=PdbxEmExtensionCategoryStyle(), includePath=includePath, verbose=self.__verbose, log=self.__lfh)
                oL = rdd.render(dd, style=layout, leadingHtmlL=leadingHtmlL, trailingHtmlL=trailingHtmlL)
            #
            if contentType in ["nmr-cs-validation-report"]:
                self.setFilePath(filePath, fileFormat=fileFormat, idCode=idCode)
                dd = self.doReport(contentType)
                rdd = PdbxReportDepictBootstrap(styleObject=CSValidationReportStyle(), includePath=includePath, verbose=self.__verbose, log=self.__lfh)
                oL = rdd.render(dd, style=layout, leadingHtmlL=leadingHtmlL, trailingHtmlL=trailingHtmlL)
            #
            if self.__debug:
                self.__lfh.write("+PdbxReport.makeTabularReport - generated HTML \n%s\n" % "\n".join(oL))
            #
        #
        return oL

    def setFilePath(self, filePath, fileFormat="cif", idCode=None):
        self.__filePath = filePath
        self.__fileFormat = fileFormat
        if not os.access(self.__filePath, os.R_OK):
            return False
        if idCode is not None:
            self.__idCode = str(idCode).upper()
        #
        return True

    def getFilePath(self):
        return self.__filePath

    def doReport(self, contentType="model"):
        """Return data content required to render report --"""
        #
        oD = {}
        oD["dataDict"] = {}
        filePath = self.__filePath
        fileFormat = self.__fileFormat
        #
        if self.__verbose:
            self.__lfh.write("\n\n+PdbxReport.doReport()  - starting for content type %s \n" % contentType)
            self.__lfh.write("+PdbxReport.doReport()  format %s file path  %s\n" % (fileFormat, filePath))
            self.__lfh.flush()
        #
        #
        # make a local copy of the file (if required)
        #
        (_pth, fileName) = os.path.split(filePath)
        dirPath = os.path.join(self.__sessionPath, "report")
        localPath = os.path.join(dirPath, fileName)
        localRelativePath = os.path.join(self.__sessionRelativePath, "report", fileName)
        if filePath != localPath:
            if not os.access(dirPath, os.F_OK):
                os.makedirs(dirPath)
            shutil.copyfile(filePath, localPath)
            #
            if self.__verbose:
                self.__lfh.write("+PdbxReport.doReport() - Copied input file %s to report session path %s \n" % (filePath, localPath))
                self.__lfh.flush()
        #
        # Path context --
        oD["idCode"] = self.__idCode
        oD["filePath"] = filePath
        oD["localPath"] = localPath
        oD["localRelativePath"] = localRelativePath
        oD["sessionId"] = self.__sessionId
        oD["editOpNumber"] = 0
        oD["requestHost"] = self.__reqObj.getValue("request_host")
        #
        try:
            if contentType == "model":
                pdbxR = PdbxReportIo(verbose=self.__verbose, log=self.__lfh)
            elif contentType == "geometry-check-report":
                pdbxR = PdbxGeometryReportIo(verbose=self.__verbose, log=self.__lfh)
            elif contentType == "dcc-report":
                pdbxR = PdbxXrayExpReportIo(verbose=self.__verbose, log=self.__lfh)
            elif contentType == "links-report":
                pdbxR = PdbxLinksReportIo(verbose=self.__verbose, log=self.__lfh)
            elif contentType == "em-map-info-report":
                pdbxR = EmInfoReportIo(verbose=self.__verbose, log=self.__lfh)
            elif contentType == "nmr-cs-validation-report":
                pdbxR = CSValidationReportIo(verbose=self.__verbose, log=self.__lfh)
            else:
                self.__lfh.write("+PdbxReport.doReport() - unknown contentType %s\n" % contentType)
                return oD

            pdbxR.setFilePath(localPath, idCode=None)
            # pdbxR.get()
            oD["blockId"] = pdbxR.getCurrentContainerId()
            if self.__verbose:
                self.__lfh.write("+PdbxReport.doReport() - category name list %r \n" % pdbxR.getCurrentCategoryNameList())
            for catName in pdbxR.getCurrentCategoryNameList():
                oD["dataDict"][catName] = pdbxR.getCategory(catName=catName)

            if contentType == "model":
                oD["pdb_id"] = pdbxR.getDbCode(dbId="PDB")
                oD["struct_title"] = pdbxR.getStructTitle()
                oD["primary_contour_level"] = pdbxR.getContourLevelMap(mapId="primary map")

            if self.__verbose:
                self.__lfh.write("+PdbxReport.doReport() - completed  - report object built\n")
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+PdbxReport.doReport() - report preparation failed for:  %s\n" % fileName)
                traceback.print_exc(file=self.__lfh)
                self.__lfh.flush()

        return oD


if __name__ == "__main__":
    pass
