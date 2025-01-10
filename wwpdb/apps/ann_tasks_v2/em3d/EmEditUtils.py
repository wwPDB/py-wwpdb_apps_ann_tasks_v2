##
# File:  EmEditUtils.py
# Date:  28-Aug-2015  J. Westbrook
#
# Update:
#
##
"""
Edit volume data file header records and related data stored in model files.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os
import json
import traceback
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.io.locator.DataReference import ReferenceFileComponents
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils


class EmEditUtils(SessionWebDownloadUtils):
    """
    Edit volume data file header records and related data stored in model files.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(EmEditUtils, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__debug = True
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        self.__cleanup = True

        self.__headerKeyList = [
            ("Map title", "label", True),
            ("Pixel sampling on x, y, and z", "voxel", True),
            ("Start points on columns, rows, and sections", "gridstart", True),
            ("Grid sampling on x, y, and z", "gridsampling", False),
            ("Cell dimensions (x, y, and z, alpha, beta, gamma)", "cell", False),
            ("Space group number", "", False),
            ("Number of columns, rows, and sections", "", False),
            ("Origin in MRC format", "", False),
            ("Maximum density", "", False),
            ("Minimum density", "", False),
            ("Average density", "", False),
            ("RMS deviation from mean density", "", False),
            ("Fast, medium and slow axes", "", False),
            ("Map mode", "", False),
            ("Map endianness", "", False),
        ]
        #                        modelKey (label), opid (internal store), eFlag (editable), selectKey
        self.__modelKeyList = [
            ("Contour level", "contour_level", True, None),
            ("Contour level source", "contour_level_source", True, "contour_level_source"),
            ("Annotation details", "annotation_details", True, None),
        ]
        # Enumerations for selectKey
        self.__selectKeyList = {"contour_level_source": ["author", "emdb", "software"]}

    def getMapFileNameDetails(self, fileName):
        """
        Return:  dictionary content type and file partition number for the input file name.
        """
        mD = {"em-volume": "primary map", "em-mask-volume": "mask", "em-additional-volume": "additional map", "em-half-volume": "half map", "em-volume-header": "map header"}
        try:
            rfc = ReferenceFileComponents(fileName=fileName, verbose=self.__verbose, log=self.__lfh)
            cT = rfc.getContentType()
            pN = rfc.getPartitionNumber()
            if self.__verbose:
                self.__lfh.write("+EmEditUtils.getMapFileNameDetails - file %s type %r part %r\n" % (fileName, cT, pN))
            rcT = mD[cT]
            return rcT, pN
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmEditUtils.getMapFileNameDetails - failed for file %s\n" % fileName)
                traceback.print_exc(file=self.__lfh)
        return None, None

    def getArchiveMapHeader(self, entryId, mapFileName):
        """Return the path of the json snippet representing the header details for the input archive map file."""
        mapFilePath = os.path.join(self.__pI.getArchivePath(entryId), mapFileName)
        return self.getMapHeader(entryId, mapFilePath)

    def getMapHeader(self, entryId, mapFilePath):
        """Get the the metadata from the header section of the input map file.

        Return the path of a json snipet in session directory containing the header details.
        """
        try:
            resultPath = os.path.join(self.__sessionPath, entryId + "_mapfix-header-report_P1.json")
            logPath = os.path.join(self.__sessionPath, entryId + "_mapfix-report_P1.txt")
            for filePath in (resultPath, logPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.setDebugMode(flag=True)
            dp.addInput(name="map_file_path", value=mapFilePath, type="file")
            # dp.imp(mapFilePath)
            dp.op("annot-read-map-header-in-place")
            dp.expLog(logPath)
            dp.exp(resultPath)
            #
            if self.__verbose:
                self.__lfh.write("+EmEditUtils.getMapHeader -  completed for entryId %s file %s\n" % (entryId, mapFilePath))
                self.__lfh.write("+EmEditUtils.getMapHeader -  output file written to %s\n" % (resultPath))
            if self.__cleanup:
                dp.cleanup()
            return True, resultPath, logPath
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmEditUtils.getMapHeader - failed with exception for entryId %s file %s\n" % (entryId, mapFilePath))
                traceback.print_exc(file=self.__lfh)
        return False, None, None

    def renderMapHeaderEditForm(self, entryId, mapHeaderFilePath, mapFileName, modelD=None, mapType=None, partition=None):
        """Return the rendered table corresponding to the input mapHeaderFile -"""
        try:
            #
            mD = json.load(open(mapHeaderFilePath, "r"))
            #
            # JDW - reassign header file label tag with id code --
            #
            if self.__debug:
                self.__lfh.write("Map header keys: %r\n" % mD.keys())
            oL = self.__renderHeaderTable(mD["input_header"], modelD=modelD, entryId=entryId, mapFileName=mapFileName, mapType=mapType, partition=partition)
            #
            return True, "\n".join(oL)

        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmEditUtils.renderMapHeader - failed with exception for entryId %s file %s\n" % (entryId, mapHeaderFilePath))
                traceback.print_exc(file=self.__lfh)
        return False, None

    def __renderHeaderTable(self, mapHeaderD, modelD, entryId, mapFileName, mapType, partition):
        """Render map header data and return

        # -cell <x> <y> <z>         : set x/y/z-length x/y/z
        # -label <DepCode>          : write new label
        # -gridsampling <x> <y> <z> : set x/y/z- grid sampling
        # -gridstart <x> <y> <z>    : set x/y/z- grid start point
        # -voxel <x> <y> <z>        : set x/y/z-length values to N[X/Y/Z]-length

            oL.append('<td><span  id="a_ba_%d"   class="ief greyedout">%s</span></td>' %  (assemId,defaultValue))
        """
        colList = ["Header Parameter", "Values"]

        #
        oL = []
        oL.append("<h4>Map Header Edit Form For %s</h4>" % mapFileName)
        oL.append('<div id="em-map-edit-status"></div>')
        oL.append('<div id="em-map-edit-links"></div>')

        oL.append('<form id="map-edit-form" name="map-edit-form" class="map_ajaxform form-inline')
        oL.append('<span><input type="submit" name="submit" value="Submit edits" class="btn btn-primary map-edit-form-submit"  /> </span>')
        #
        oL.append('<input type="hidden" name="sessionid" value="%s" />' % self.__sessionId)
        oL.append('<input type="hidden" name="map_file_name" value="%s" />' % mapFileName)
        oL.append('<input type="hidden" name="entryid" value="%s" />' % entryId)
        oL.append('<input type="hidden" name="mapentryId" value="%s" />' % entryId)
        oL.append('<input type="hidden" name="maptype" value="%s" />' % mapType)
        oL.append('<input type="hidden" name="partition" value="%s" />' % partition)
        #
        # removed class ->table-striped
        oL.append('<table class="table table-bordered">')
        #
        oL.append("<tr>")
        for col in colList:
            oL.append("<th>")
            oL.append("%s" % col)
            oL.append("</th>")
        oL.append("</tr>")
        #
        #
        for modelKey, opid, eFlag, selectKey in self.__modelKeyList:
            if eFlag:
                oL.append('<tr class="info">')
            else:
                oL.append("<tr>")

            if len(modelD[opid]) > 0:
                edCss = "ief"
            else:
                edCss = "ief greyedout"
            oL.append('<td class="width15">%s</td>' % modelKey)
            #

            if selectKey:
                sels = self.__selectKeyList[selectKey]
                # '[{"label":"author",value:"author"}, {"label":"emdb",value:"emdb"}]'
                dataSelVars = "'[%s]'" % ", ".join(map(lambda x: '{"label":"%s","value":"%s"}' % (x, x), sels))

            dVal = modelD[opid]
            if eFlag:
                if selectKey:
                    oL.append('<td id="m_%s" class="%s width15" data-ief-edittype="select" data-ief-selectvalues=%s>%s</td>' % (opid, edCss, dataSelVars, dVal))
                else:
                    oL.append('<td id="m_%s" class="%s width15">%s</td>' % (opid, edCss, dVal))
            else:
                oL.append('<td class="width15">%s</td>' % dVal)
            oL.append("</tr>")
        #
        for headerKey, opid, eFlag in self.__headerKeyList:
            if eFlag:
                oL.append('<tr class="info">')
            else:
                oL.append("<tr>")

            if len(mapHeaderD[headerKey]) > 0:
                edCss = "ief"
            else:
                edCss = "ief greyedout"
            oL.append('<td class="width15">%s</td>' % headerKey)
            #
            dVal = mapHeaderD[headerKey]
            if opid in ["label"]:
                try:
                    ff = dVal.split(":")
                    dVal = ff[8]
                except:  # noqa: E722 pylint: disable=bare-except
                    dVal = ""
                if ("emdb_id" in modelD) and (modelD["emdb_id"] != dVal):
                    dVal = modelD["emdb_id"]

            if eFlag:
                oL.append('<td id="m_%s" class="%s width15">%s</td>' % (opid, edCss, dVal))
            else:
                oL.append('<td class="width15">%s</td>' % dVal)
            oL.append("</tr>")
        #
        oL.append("</table>")
        oL.append('<span><input name="m_auto" type="checkbox"/> Automatic correction option ')
        oL.append('&nbsp; &nbsp; <input  type="submit" name="submit" value="Submit edits" class="btn btn-primary map-edit-form-submit"  /> </span>')
        oL.append("</form>")
        #
        return oL

    def __getNextVersion(self, fN):
        fParts = fN.split(".")
        #
        nParts = fParts[0].split("_")
        dataSetId = nParts[0] + "_" + nParts[1]
        cT = nParts[2]
        pN = nParts[3][1:]
        ofN = self.__pI.getFileName(dataSetId, contentType=cT, formatType=fParts[1], fileSource="archive", versionId="next", partNumber=pN)
        nextMapPath = os.path.join(self.__pI.getArchivePath(dataSetId), ofN)

        return nextMapPath

    def updateMapHeader(self, entryId, inputMapFileName, outputMapFilePath=None):
        """Get the the metadata from the header section of the input map file.

        Return the path of a json snipet in session directory containing the header details.
        """
        try:
            inputMapFilePath = os.path.join(self.__pI.getArchivePath(entryId), inputMapFileName)
            argD = {}
            for tup in self.__headerKeyList:
                if tup[2]:
                    tId = "m_" + tup[1]
                    tVal = self.__reqObj.getValue(tId)
                    if tVal is not None and len(tVal) > 0:
                        if tId in ["label"]:
                            argD[tup[1]] = tVal
                        else:
                            tL = tVal.split(",")
                            argD[tup[1]] = " ".join(tL[:3])

            autoOpt = ""
            tVal = self.__reqObj.getValue("m_auto")
            if tVal is not None and len(tVal) > 0:
                autoOpt = "y"

            resultPath = os.path.join(self.__sessionPath, entryId + "_mapfix-header-report_P1.json")
            logPath = os.path.join(self.__sessionPath, entryId + "_mapfix-report_P1.txt")
            for filePath in (resultPath, logPath):
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.setDebugMode(flag=True)
            dp.addInput(name="input_map_file_path", value=inputMapFilePath, type="file")
            ofp = outputMapFilePath
            if ofp is not None:
                dp.addInput(name="output_map_file_path", value=ofp, type="file")
            else:
                ofp = self.__getNextVersion(fN=inputMapFileName)
                dp.addInput(name="output_map_file_path", value=ofp, type="file")
            #
            if argD is not None:
                for k, v in argD.items():
                    dp.addInput(name=k, value=v)
            #
            if autoOpt == "y":
                dp.addInput(name="auto", value="y")
            dp.op("annot-update-map-header-in-place")
            dp.expLog(logPath)
            dp.exp(resultPath)
            #
            if self.__verbose:
                self.__lfh.write("+EmEditUtils.updateMapHeader -  completed for entryId %s file %s\n" % (entryId, inputMapFilePath))
                self.__lfh.write("+EmEditUtils.updateMapHeader -  output map file written to %s\n" % (ofp))
            if self.__cleanup:
                dp.cleanup()
            return True, resultPath, logPath, ofp
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmEditUtils.updateMapHeader - failed with exception for entryId %s file %s\n" % (entryId, inputMapFileName))
                traceback.print_exc(file=self.__lfh)
        return False, None, None, None
