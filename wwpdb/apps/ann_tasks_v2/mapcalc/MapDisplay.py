##
# File:  MapDisplay.py
# Date:  16-Jul-2014  J. Westbrook
#
# Update:
##
"""
Manage tabular presentation of local electron maps with options for 3D display --

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os

from mmcif_utils.pdbx.PdbxIo import PdbxLocalMapIndexIo


class MapDisplay(object):
    """
    Manage tabular presentation of local electron maps with options for 3D display --

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        # self.__debug = False
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__setup()

    def __setup(self):
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__rltvSessionPath = self.__sObj.getRelativePath()

    def readLocalMapIndex(self, indexPath):
        """-- Set the file path of the index file read any existing file --"""
        pio = PdbxLocalMapIndexIo(verbose=self.__verbose, log=self.__lfh)
        ok = pio.setFilePath(filePath=indexPath)
        if ok:
            return pio.getAttribDictList("dcc_ligand")
        else:
            return {}

    def renderLocalMapTable(self, rowDL, title="Table of local electron density maps for non-polymer chemical components", subdir="np-cc-maps"):
        """ """

        colList = [
            "id",
            "residue_name",
            "chain_id",
            "dcc_correlation",
            "real_space_R",
            "Biso_mean",
            "occupancy_mean",
            "warning",
            "file_name_map_html",
            "file_name_pdb",
            "file_name_map",
            "file_name_jmol",
        ]

        colDisplayD = {
            "id": "View in JSMol",
            "residue_name": "Residue Name",
            "chain_id": "Chain/Residue No.",
            "dcc_correlation": "Correlation",
            "real_space_R": "RSR",
            "Biso_mean": "Mean B (isotropic)",
            "occupancy_mean": "Mean Occupancy",
            "warning": "warning",
            "file_name_map_html": "file_name_map_html",
            "file_name_pdb": "file_name_pdb",
            "file_name_map": "file_name_map",
            "file_name_jmol": "file_name_jmol",
        }
        #
        #
        oL = []
        #
        oL.append("<BR />")
        oL.append("<h4>%s</h4>" % title)
        oL.append('<table class="table table-bordered table-striped">')

        # column headers --
        oL.append("<tr>")
        for col in colList:
            if col not in ["id", "residue_name", "chain_id", "dcc_correlation", "real_space_R", "Biso_mean", "occupancy_mean"]:
                continue
            oL.append("<th>")
            oL.append("%s" % colDisplayD[col])
            oL.append("</th>")
        oL.append("</tr>")
        #
        for idx, rowD in enumerate(rowDL):
            oL.append("<tr>")
            if idx == 0:
                pass
            for col in colList:
                if col in ["id"]:
                    fullPathCif = os.path.join(self.__sessionPath, subdir, rowD["file_name_pdb"])
                    fullPathMap = os.path.join(self.__sessionPath, subdir, rowD["file_name_map"])
                    if os.access(fullPathCif, os.R_OK) and os.access(fullPathMap, os.R_OK):
                        cifFilePath = os.path.join(self.__rltvSessionPath, subdir, rowD["file_name_pdb"])
                        mapFilePath = os.path.join(self.__rltvSessionPath, subdir, rowD["file_name_map"])
                        #  -----------------------
                        jsurl = 'javascript:loadFileWithMapJsmol("myApp1", "#jsmol-dialog-1","%s","%s","map-style-sig20")' % (cifFilePath, mapFilePath)
                        viewoptA = "<a href='%s'>&sigma;=2.0</a>" % (jsurl)
                        #  -----------------------
                        jsurl = 'javascript:loadFileWithMapJsmol("myApp1", "#jsmol-dialog-1","%s","%s","map-style-sig15")' % (cifFilePath, mapFilePath)
                        viewoptB = "<a href='%s'>&sigma;=1.5</a>" % (jsurl)

                        jsurl = 'javascript:loadFileWithMapJsmol("myApp1", "#jsmol-dialog-1","%s","%s","map-style-sig10")' % (cifFilePath, mapFilePath)
                        viewoptC = "<a href='%s'>&sigma;=1.0</a>" % (jsurl)

                        jsurl = 'javascript:loadFileWithMapJsmol("myApp1", "#jsmol-dialog-1","%s","%s","map-style-sig08")' % (cifFilePath, mapFilePath)
                        viewoptD = "<a href='%s'>&sigma;=0.8</a>" % (jsurl)

                        oL.append('<td class="width15">%s&nbsp;|&nbsp;%s&nbsp;|&nbsp;%s&nbsp;|&nbsp;%s</td>' % (viewoptA, viewoptB, viewoptC, viewoptD))
                elif col in ["residue_name", "chain_id", "dcc_correlation", "real_space_R", "Biso_mean", "occupancy_mean"]:
                    oL.append('<td class="width10 textleft">%s</td>' % rowD[col])
                else:
                    # self.__lfh.write("+MapDisplay.renderLocalMapTable() missing columnn %r\n" % col)
                    pass
                #    oL.append('<td>%s</td>' % rowD[col])

            oL.append("</tr>")
        #
        oL.append("</table>")
        oL.append("<br />")
        #
        return oL
