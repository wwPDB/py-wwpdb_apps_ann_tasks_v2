##
# File:  EmModelUtils.py
# Date:  23-Jul-2015  J. Westbrook
#
# Update:
#   18-Aug-2015 - jdw add support for  map type and partition alignment in em_map category update.
##
"""
Manage map header updates in model file -


"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import json
import traceback

from mmcif_utils.style.PdbxStyleIoUtil import PdbxStyleIoUtil
from mmcif_utils.style.PdbxEmExtensionCategoryStyle import PdbxEmExtensionCategoryStyle
from mmcif.io.IoAdapterCore import IoAdapterCore

#


class EmModelUtils(PdbxStyleIoUtil):

    """
    Manage map header updates in model file -

    Here are the model data items with direct correspondences with binary map header -


        The following items are exported in JSON object from the one of the various mapfix applications -

          "output_header": {
                "Fast, medium and slow axes": "X, Y, Z",
                "RMS deviation from mean density": "0.9027101",
                "Average density": "-2.0916369E-9",
                "Origin in MRC format": "0.0, 0.0, 0.0",
                "Map title": "::::EMDATABANK.org::::test::::                                                  ",
                "Space group number": "1",
                "Map mode": "Image stored as floating point number (4 bytes)",
                "Grid sampling on x, y, and z": "80, 80, 80",
                "Minimum density": "-3.3407848",
                "Map endianness": "Big endian",
                "Number of columns, rows, and sections": "80, 80, 80",
                "Cell dimensions (x, y, and z, alpha, beta, gamma)": "80.0, 80.0, 80.0, 90.0, 90.0, 90.0",
                "Pixel sampling on x, y, and z": "1.0, 1.0, 1.0",
                "Start points on columns, rows, and sections": "-40, -40, -40",
                "Maximum density": "14.395242"
            },
            "output_header_long": {
                "axis_order_slow": "Z",
                "cell_gamma": "90.0",
                "dimensions_sec": "80",
                "dimensions_col": "80",
                "endian_type": "big",
                "statistics_maximum": "14.395242",
                "statistics_minimum": "-3.3407848",
                "dimensions_row": "80",
                "origin_col": "-40",
                "limit_col": "39",
                "limit_row": "39",
                "data_type": "Image stored as floating point number (4 bytes)",
                "statistics_std": "0.9027101",
                "limit_sec": "39",
                "origin_sec": "-40",
                "size_kb": "2049024",
                "axis_order_fast": "X",
                "cell_c": "80.0",
                "label": "::::EMDATABANK.org::::test::::                                                  ",
                "cell_a": "80.0",
                "format": "CCP4",
                "cell_b": "80.0",
                "axis_order_medium": "Y",
                "pixel_spacing_x": "1.0",
                "origin_row": "-40",
                "symmetry_space_group": "1",
                "pixel_spacing_y": "1.0",
                "cell_alpha": "90.0",
                "pixel_spacing_z": "1.0",
                "cell_beta": "90.0",
                "statistics_average": "-2.0916369E-9",
                "spacing_z": "80",
                "spacing_y": "80",
                "spacing_x": "80"
            }


            These items may be separately provided by the depositor and are not resident in the map header records.

            _em_map.contour_level          4
            _em_map.contour_level_source   author
            _em_map.annotation_details     'some details'


             The following are cardinal identifiers for the map with the em_map category -
            _em_map.type                   'primary map'
            _em_map.partition              1

    """

    def __init__(self, verbose=False, log=sys.stderr):
        super(EmModelUtils, self).__init__(styleObject=PdbxEmExtensionCategoryStyle(), IoAdapter=IoAdapterCore(), verbose=verbose, log=log)

        self.__verbose = verbose
        self.__lfh = log
        self.__debug = True
        self.__headD = {}
        self.__depHeadD = {}
        self.__mappingD = {
            "axis_order_fast": "_em_map.axis_order_fast",
            "axis_order_medium": "_em_map.axis_order_medium",
            "axis_order_slow": "_em_map.axis_order_slow",
            "cell_a": "_em_map.cell_a",
            "cell_alpha": "_em_map.cell_alpha",
            "cell_b": "_em_map.cell_b",
            "cell_beta": "_em_map.cell_beta",
            "cell_c": "_em_map.cell_c",
            "cell_gamma": "_em_map.cell_gamma",
            "data_type": "_em_map.data_type",
            "dimensions_col": "_em_map.dimensions_col",
            "dimensions_row": "_em_map.dimensions_row",
            "dimensions_sec": "_em_map.dimensions_sec",
            "endian_type": "_em_map.endian_type",
            "format": "_em_map.format",
            "label": "_em_map.label",
            "limit_col": "_em_map.limit_col",
            "limit_row": "_em_map.limit_row",
            "limit_sec": "_em_map.limit_sec",
            "origin_col": "_em_map.origin_col",
            "origin_row": "_em_map.origin_row",
            "origin_sec": "_em_map.origin_sec",
            "pixel_spacing_x": "_em_map.pixel_spacing_x",
            "pixel_spacing_y": "_em_map.pixel_spacing_y",
            "pixel_spacing_z": "_em_map.pixel_spacing_z",
            "size_kb": "_em_map.size_kb",
            "spacing_x": "_em_map.spacing_x",
            "spacing_y": "_em_map.spacing_y",
            "spacing_z": "_em_map.spacing_z",
            "statistics_average": "_em_map.statistics_average",
            "statistics_maximum": "_em_map.statistics_maximum",
            "statistics_minimum": "_em_map.statistics_minimum",
            "statistics_std": "_em_map.statistics_std",
            "symmetry_space_group": "_em_map.symmetry_space_group",
            "id": "_em_map.id",
            "entry_id": "_em_map.entry_id",
            "file": "_em_map.file",
            "type": "_em_map.type",
            "partition": "_em_map.partition",
            #  depositor provided items --
            "contour_level": "_em_map.contour_level",
            "contour_level_source": "_em_map.contour_level_source",
            "annotation_details": "_em_map.annotation_details",
        }

    def setMapType(self, mapType):
        if mapType in ["primary map", "mask", "additional map", "half map"]:
            self.__headD["type"] = mapType

    def setEntryId(self, entryId):
        self.__headD["entry_id"] = entryId

    def setMapFileName(self, mapFileName):
        self.__headD["file"] = mapFileName

    def setMapHeaderFilePath(self, jsonFilePath):
        """ """
        rD = None
        try:
            with open(jsonFilePath) as ifh:
                rD = json.load(ifh)
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmModelUtils.setMapHeaderFilePath - failed for file %s\n" % jsonFilePath)
                traceback.print_exc(file=self.__lfh)
        #
        for k, v in rD["output_header_long"].items():
            self.__headD[k] = v

        return rD

    def setModelFilePath(self, modelFilePath):
        """Specify the mapping file path."""
        try:
            if self.readFile(modelFilePath):
                return self.setContainer(containerIndex=0)
            else:
                return False
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmModelUtils.setModelHeaderFilePath - failed for file %s\n" % modelFilePath)
                traceback.print_exc(file=self.__lfh)

        return False

    def getDepositorMapDetails(self, mapType, partition):
        """Fetch depositor map details from the current model file --

        Return these as a dictionary and store internally for export --
        """
        d = {"contour_level": "_em_map.contour_level", "contour_level_source": "_em_map.contour_level_source", "annotation_details": "_em_map.annotation_details"}
        rD = {}
        for ky in d.keys():
            rD[ky] = ""
        try:
            curContainer = self.getCurrentContainer()
            cObj = curContainer.getObj("em_map")
            rL = []
            nRows = self.getRowCount("em_map")
            if self.__verbose:
                self.__lfh.write("+EmModelUtils.getDepositorMapDetails - found %d rows of map data\n" % nRows)
            if nRows > 0:
                rL = cObj.selectIndicesFromList(attributeValueList=[str(mapType), str(partition)], attributeNameList=["type", "partition"])
                if self.__verbose:
                    self.__lfh.write("+EmModelUtils.getDepositorMapDetails - found matching rows %d \n" % len(rL))
                if len(rL) > 0:
                    iRow = rL[0]
                    for ky, _itemName in d.items():
                        val = cObj.getValue(attributeName=ky, rowIndex=iRow)
                        rD[ky] = val
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmModelUtils.getDepositorMapDetails - failed for type %r partition %r\n" % (mapType, partition))
                traceback.print_exc(file=self.__lfh)

        # save a copy
        self.__depHeadD.update(rD)

        return rD

    def updateHeader(self, updD):
        """Add content from the input dictionary to current contents of the map header -"""
        try:
            self.__headD.update(updD)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    def updateModelFromHeader(self, entryId, mapType="primary map", partition="1", outModelFilePath=None):
        """ """
        try:
            curContainer = self.getCurrentContainer()
            # create a stub category if none exists --
            ok = self.newCategory("em_map", container=None, overWrite=False)
            if ok:
                self.__headD["type"] = mapType
                self.__headD["partition"] = str(partition)
                # ...
                self.__headD["entry_id"] = entryId

                nRows = self.getRowCount("em_map")
                if self.__debug:
                    self.__lfh.write("+EmModelUtils.updateModelFromHeader - em_map category length nRows %d\n" % nRows)
                cObj = curContainer.getObj("em_map")
                rL = []
                if nRows > 0:
                    rL = cObj.selectIndicesFromList(attributeValueList=[str(mapType), str(partition)], attributeNameList=["type", "partition"])
                if nRows > 0 and len(rL) > 0:
                    # update the first matching row -
                    iRow = rL[0]
                else:
                    # update/append the next row -
                    if nRows > 0:
                        tIdList = []
                        for ii in range(0, nRows):
                            tId = cObj.getValue(attributeName="id", rowIndex=ii)
                            tIdList.append(int(tId))
                        nId = sorted(tIdList)[-1]
                    else:
                        nId = "1"
                    self.__headD["id"] = nId
                    #
                    iRow = nRows
                #
                for ky, val in self.__headD.items():
                    if ky in self.__mappingD:
                        itemName = self.__mappingD[ky]
                        if itemName is not None:
                            self.updateItem(itemName, val, iRow=iRow)
                #
                return self.writeFile(outModelFilePath)
            else:
                if self.__verbose:
                    self.__lfh.write("+EmModelUtils.updateModelFromHeader - cannot create em_map category for %s\n" % entryId)
                return False
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+EmModelUtils.updateModelFromHeader - failed for file %s\n" % outModelFilePath)
                traceback.print_exc(file=self.__lfh)
        return False
