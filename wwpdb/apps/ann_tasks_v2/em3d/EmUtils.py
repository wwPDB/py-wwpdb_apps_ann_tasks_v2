##
# File:  EmUtils.py
# Date:  25-Jun-2014  J. Westbrook
#
# Update:
# 1-July-2014  jdw  -   Working with edits directly in archive directory --
# 23-Jan-2015  jdw  -   Add auto correction option and adjust editable map header fields.
# 17-Aug-2015  jdw  -   Include half-maps in the map display -
# 30-Aug-2015  jdw  -   refactor into EmEditUtils.py
##
"""
Manage mapfix (view and edit) and em2m operations.

    'fsc': (['xml'], 'fsc-xml'),
    'fsc-report': (['txt'], 'fsc-report'),
    'em2em-report': (['txt'], 'em2em-report'),
    'img-emdb': (['any'], 'img-emdb'),
    'img-emdb-report': (['txt'], 'img-emdb-report'),
    'layer-lines': (['any'], 'layer-lines'),
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
import math
import traceback

from wwpdb.io.file.DataExchange import DataExchange

from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils

import matplotlib

matplotlib.use("Agg")  # Not sure if safe to move down
import matplotlib.pyplot as plt  # noqa: E402

import pygal  # noqa: E402
from pygal.style import LightGreenStyle  # noqa: E402


class EmUtils(SessionWebDownloadUtils):
    """
    Manages mapfix (view and edit) and em2m operations.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(EmUtils, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__debug = True
        #
        self.__setup()

    def __setup(self):
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        # self.__cleanup = False

    def renderEmMapFileList(self, entryId, contentType="em-volume", formatType="map", fileSource="archive", colTextHtml="Archive map files"):
        """General listing methods for em data objects --"""
        if self.__verbose:
            self.__lfh.write("+EmUtils.renderEmMapFileList for %r type %r format %r title %s\n" % (entryId, contentType, formatType, colTextHtml))
        oL = []
        tupL = []
        try:
            de = DataExchange(reqObj=self.__reqObj, depDataSetId=entryId, wfInstanceId=None, fileSource=fileSource, verbose=self.__verbose, log=self.__lfh)
            tupL = de.getPartitionFileList(fileSource=fileSource, contentType=contentType, formatType=formatType, mileStone=None)
            if self.__verbose:
                self.__lfh.write("+EmUtils.renderEmMapFileList - tupL %r\n" % tupL)
            #
            oL.append('<table class="table table-bordered table-striped">')
            oL.append("<tr><th>%s</th><th>Modification Time</th><th>Size (KBytes)</th></tr>" % colTextHtml)
            for tup in tupL:
                (_dN, fN) = os.path.split(tup[0])
                oL.append("<tr>")
                href = self.__makeEditMapHref(entryId, fN)
                oL.append("<td>%s</td>" % href)
                oL.append("<td>%s</td>" % tup[1])
                if tup[2] > 1:
                    oL.append("<td>%d</td>" % int(tup[2]))
                else:
                    oL.append("<td>%.3f</td>" % tup[2])

                oL.append("</tr>")
            oL.append("</table>")
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmUtils.renderEmMapFileList - failing %s\n" % entryId)
                traceback.print_exc(file=self.__lfh)

        return len(tupL), "\n".join(oL)

    def renderMapFileList(self, entryId):
        self.__lfh.write("+EmUtils.renderMapFileList for %r\n" % entryId)
        de = DataExchange(reqObj=self.__reqObj, depDataSetId=entryId, wfInstanceId=None, fileSource="archive", verbose=self.__verbose, log=self.__lfh)
        tupL = de.getVersionFileList(contentType="em-volume", formatType="map", partitionNumber="1", mileStone=None)
        self.__lfh.write("+EmUtils.renderMapFileList path list %r\n" % (tupL))
        oL = []
        oL.append('<table class="table table-bordered table-striped">')
        oL.append("<tr><th>Archive Map Files</th><th>Modification Time</th><th>Size (KBytes)</th></tr>")
        for tup in tupL:
            (_dN, fN) = os.path.split(tup[0])
            oL.append("<tr>")
            href = self.__makeEditMapHref(entryId, fN)
            oL.append("<td>%s</td>" % href)
            oL.append("<td>%s</td>" % tup[1])
            if tup[2] > 1:
                oL.append("<td>%d</td>" % int(tup[2]))
            else:
                oL.append("<td>%.3f</td>" % tup[2])

            oL.append("</tr>")
        oL.append("</table>")

        return len(tupL), "\n".join(oL)

    def renderMaskFileList(self, entryId):
        self.__lfh.write("+EmUtils.renderMaskFileList for %r\n" % entryId)
        de = DataExchange(reqObj=self.__reqObj, depDataSetId=entryId, wfInstanceId=None, fileSource="archive", verbose=self.__verbose, log=self.__lfh)
        tupL = de.getVersionFileList(contentType="em-mask-volume", formatType="map", partitionNumber="1", mileStone=None)
        self.__lfh.write("+EmUtils.renderMaskFileList path list %r\n" % (tupL))
        oL = []
        oL.append('<table class="table table-bordered table-striped">')
        oL.append("<tr><th>Archive Mask Files</th><th>Modification Time</th><th>Size (KBytes)</th></tr>")
        for tup in tupL:
            (_dN, fN) = os.path.split(tup[0])
            oL.append("<tr>")
            href = self.__makeEditMapHref(entryId, fN)
            oL.append("<td>%s</td>" % href)
            oL.append("<td>%s</td>" % tup[1])
            if tup[2] > 1:
                oL.append("<td>%d</td>" % int(tup[2]))
            else:
                oL.append("<td>%.3f</td>" % tup[2])
            oL.append("</tr>")
        oL.append("</table>")
        return len(tupL), "\n".join(oL)

    def renderAdditionalMapFileList(self, entryId):
        self.__lfh.write("+EmUtils.renderAdditionalVolumeFileList for %r\n" % entryId)
        de = DataExchange(reqObj=self.__reqObj, depDataSetId=entryId, wfInstanceId=None, fileSource="archive", verbose=self.__verbose, log=self.__lfh)
        tupL = de.getPartitionFileList(contentType="em-additional-volume", formatType="map", mileStone=None)
        tupL.extend(de.getPartitionFileList(contentType="em-half-volume", formatType="map", mileStone=None))
        self.__lfh.write("+EmUtils.renderAdditionalMapFileList path list %r\n" % (tupL))
        oL = []
        oL.append('<table class="table table-bordered table-striped">')
        oL.append("<tr><th>Archive Additional Map Files</th><th>Modification Time</th><th>Size (KBytes)</th></tr>")
        for tup in tupL:
            (_dN, fN) = os.path.split(tup[0])
            oL.append("<tr>")
            href = self.__makeEditMapHref(entryId, fN)
            oL.append("<td>%s</td>" % href)
            oL.append("<td>%s</td>" % tup[1])
            if tup[2] > 1:
                oL.append("<td>%d</td>" % int(tup[2]))
            else:
                oL.append("<td>%.3f</td>" % tup[2])
            oL.append("</tr>")
        oL.append("</table>")
        return len(tupL), "\n".join(oL)

    def plotSessionMapDensity(self, entryId, maskNumber=None):
        mapHeaderFilePath = None
        try:
            if maskNumber is not None:
                mapHeaderFilePath = os.path.join(self.__sessionPath, entryId + "_em-mask-header_P" + str(maskNumber) + ".json")
                mapDensityPlotFile = entryId + "_em-mask-density_P" + str(maskNumber) + ".svg"
            else:
                mapHeaderFilePath = os.path.join(self.__sessionPath, entryId + "_em-volume-header_P1.map")
                mapDensityPlotFile = entryId + "_em-volume-density_P1.svg"
            #
            return self.plotMapDensityPygal(mapHeaderFilePath, mapDensityPlotFile)

        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmUtils.plotSessionMapDensity - failed with exception for entryId %s file %s\n" % (entryId, mapHeaderFilePath))
                traceback.print_exc(file=self.__lfh)
        return False, None

    def plotMapDensity(self, mapHeaderFilePath, mapDensityPlotFile, plotFormat="svg", plotPack="pygal"):
        if plotPack in ["pygal"]:
            return self.plotMapDensityPygal(mapHeaderFilePath, mapDensityPlotFile)
        elif plotPack in ["mpl"]:
            return self.plotMapDensityMpl(mapHeaderFilePath, mapDensityPlotFile, plotFormat=plotFormat)
        else:
            return False, None, None

    def plotMapDensityMpl(self, mapHeaderFilePath, mapDensityPlotFile, plotFormat="svg"):
        try:
            mD = json.load(open(mapHeaderFilePath, "r"))
            if self.__debug:
                self.__lfh.write("Map header keys: %r\n" % mD.keys())
                # self.__lfh.write("Map header: %r\n" % mD.items())

            #
            x = mD["input_histogram_categories"]
            y = mD["input_histogram_values"]
            logy = []
            for v in y:
                if float(v) <= 0.0:
                    logy.append(math.log10(0.1))
                else:
                    logy.append(math.log10(float(v)))

            #
            width = float(x[-1] - x[0]) / float(len(x))
            # width = 2.0

            plt.bar(x, y, width, color="r", log=True)
            plt.title("Map density distribution")
            plt.ylabel("Voxels (log(10))")
            plt.xlabel("Density")

            mapDensityPlotPath = os.path.join(self.__sessionPath, mapDensityPlotFile)
            plt.savefig(mapDensityPlotPath, format=plotFormat)
            urlPath = '<img src="/sessions/%s/%s" alt="%s">' % (self.__sessionId, mapDensityPlotFile, "Density histogram")
            return True, mapDensityPlotPath, urlPath

        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmUtils.plotMapDensity - failed with exception for file %s\n" % (mapHeaderFilePath))
                traceback.print_exc(file=self.__lfh)
        return False, None, None

    def plotMapDensityPygal(self, mapHeaderFilePath, mapDensityPlotFile):
        try:
            mD = json.load(open(mapHeaderFilePath, "r"))
            if self.__debug:
                self.__lfh.write("Map header keys: %r\n" % mD.keys())
                # self.__lfh.write("Map header: %r\n" % mD.items())

            #
            x = mD["input_histogram_categories"]
            y = mD["input_histogram_values"]
            logy = []
            for v in y:
                if float(v) <= 0.0:
                    logy.append(math.log10(0.1))
                else:
                    logy.append(math.log10(float(v)))

            #
            nL = int(len(x) / 10)
            if self.__verbose:
                self.__lfh.write("Starting plot len x %d len y %d number of major tics %d \n" % (len(x), len(logy), nL))
                self.__lfh.write("+EmUtils.plotMapDensity - x array: %r\n" % x)

            #
            # bar_chart = pygal.Bar(x_label_rotation=20, show_minor_x_labels=False,style=LightColorizedStyle)
            bar_chart = pygal.Bar(x_label_rotation=20, show_minor_x_labels=False, style=LightGreenStyle)
            # bar_chart = pygal.Bar(show_minor_x_labels=False,style=LightGreenStyle)

            bar_chart.title = "Map density distribution"

            bar_chart.x_labels = list(map(str, x))
            bar_chart.x_labels_major = list(map(str, [t for t in x[::nL]]))

            bar_chart.add("Voxels (log(10)", logy)

            mapDensityPlotPath = os.path.join(self.__sessionPath, mapDensityPlotFile)
            bar_chart.render_to_file(mapDensityPlotPath)

            urlPath = '<figure> <embed type="image/svg+xml" src="/sessions/%s/%s" /></figure>' % (self.__sessionId, mapDensityPlotFile)

            return True, mapDensityPlotPath, urlPath

        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmUtils.plotMapDensity - failed with exception for file %s\n" % (mapHeaderFilePath))
                traceback.print_exc(file=self.__lfh)
        return False, None, None

    def __makeEditMapHref(self, entryId, mapFileName):
        tS = "/service/ann_tasks_v2/edit_em_map_header?sessionid=" + self.__sessionId + "&entryid=" + entryId + "&map_file_name=" + mapFileName
        href = "<a class='my-map-selectable' href='" + tS + "'>" + mapFileName + "</a>"
        return href
