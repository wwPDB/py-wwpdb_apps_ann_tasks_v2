##
#
# File:    FileInventoryUtils.py
# Author:  jdw
# Date:    13-June-2015
# Version: 0.001
#
##
import sys
import os
import os.path
import traceback
import scandir
import datetime

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.dp.DataMaintenance import DataMaintenance

from mmcif.io.PdbxWriter import PdbxWriter
from mmcif.api.PdbxContainers import DataContainer
from mmcif.api.DataCategory import DataCategory


class FileInventoryUtils(object):
    def __init__(self, verbose=True, log=sys.stderr):
        self.__lfh = log
        self.__verbose = verbose
        self.__debug = False
        self.__siteId = getSiteId(defaultSiteId="WWPDB_DEPLOY_TEST")
        self.__cI = ConfigInfo(self.__siteId)

    def __subdirs(self, path):
        """Return the list of entries in the archive directory names and paths"""
        pathList = []
        dataList = []
        for entry in scandir.scandir(path):
            if entry.name.startswith("D_") and entry.is_dir():
                pathList.append(os.path.join(path, entry.name))
                dataList.append(entry.name)
        return dataList, pathList

    def __makeEntryPathList(self, archivePath):
        """Return the list of entries in the archive directory names and paths -"""
        pathList = []
        dataList = []
        for root, dirs, files in scandir.walk(archivePath, topdown=False):
            for dir in dirs:
                if dir.startswith("D_") and len(dir) == 12:
                    pathList.append(os.path.join(root, dir))
                    dataList.append(dir)
        return dataList, pathList

    def __splitFilePath(self, pth):
        id = None
        contentType = None
        fileFormat = None
        partNo = None
        versionNo = None
        try:
            dn, fn = os.path.split(pth)
            fFields = fn.split(".")
            fileName = fFields[0]
            fileFormat = fFields[1]
            if len(fFields) > 2:
                versionNo = int(fFields[2][1:])
            else:
                versionNo = int(0)

            fParts = fileName.split("_")
            id = fParts[0] + "_" + fParts[1]
            contentType = fParts[2]
            partNo = int(fParts[3][1:])
            return id, contentType, fileFormat, partNo, versionNo
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__debug:
                traceback.print_exc(file=self.__lfh)
        return id, contentType, fileFormat, partNo, versionNo

    def getFileInventory(self):
        """ """
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        rowList = []
        try:
            archivePath = os.path.join(self.__cI.get("SITE_ARCHIVE_STORAGE_PATH"), "archive")
            # idList, pathList = self.__makeEntryPathList(archivePath)
            self.__lfh.write("+testGetFileInventoryList- inventory in directory  %s\n" % (archivePath))
            idList, pathList = self.__subdirs(archivePath)
            dm = DataMaintenance(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                dirPath = os.path.join(archivePath, id, "*")
                self.__lfh.write("+testGetFileInventoryList- inventory in directory  %s\n" % (dirPath))
                pL = dm.getMiscFileList(fPatternList=[dirPath], sortFlag=True)
                self.__lfh.write("\n\n+testGetFileInventoryList- id %s file list\n" % (id))
                for ii, p in enumerate(pL):
                    tup0 = self.__splitFilePath(p[0])
                    retR = []
                    retR.append(ii)
                    retR.extend([t for t in tup0])
                    if retR[2] is None or len(retR[2]) < 2:
                        continue
                    # "2015-May-28 08:47:45     %Y-%a %b %d %H:%M:%S "
                    #  datetime_obj = datetime.datetime.strptime(self.__refDate, "%Y-%m-%d %H:%M:%S")
                    #  datetime.datetime.strftime('%Y-%m-%d %H:%M:%S')
                    #   timeFormatOut = "%Y-%m-%d %H:%M:%S"
                    #   timeFormatIn = "%Y-%b-%d %H:%M:%S"
                    datetime_obj = datetime.datetime.strptime(p[1], "%Y-%b-%d %H:%M:%S")
                    ot = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
                    retR.append(ot)
                    retR.append(p[2])
                    rowList.append(retR)
                    if self.__debug:
                        self.__lfh.write("+testGetFileInventoryList- %r  %r\n" % (ii, retR))
            return rowList
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)

    def writeFileInventory(self, filePath, rowList):
        """Write the ...."""
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            #
            myDataList = []
            curContainer = DataContainer("fileinventory")
            aCat = DataCategory("pdbx_archive_file_inventory")
            aCat.appendAttribute("ordinal")
            aCat.appendAttribute("entry_id")
            aCat.appendAttribute("content_type")
            aCat.appendAttribute("format_type")
            aCat.appendAttribute("partition_number")
            aCat.appendAttribute("version_number")
            aCat.appendAttribute("timestamp")
            aCat.appendAttribute("file_size")
            #
            for row in rowList:
                aCat.append(row)
            curContainer.append(aCat)
            myDataList.append(curContainer)
            ofh = open(filePath, "w")
            pdbxW = PdbxWriter(ofh)
            pdbxW.write(myDataList)
            ofh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)


if __name__ == "__main__":
    fiu = FileInventoryUtils(verbose=True, log=sys.stderr)
    rL = fiu.getFileInventory()
    fiu.writeFileInventory("test_file_inventory.cif", rL)
