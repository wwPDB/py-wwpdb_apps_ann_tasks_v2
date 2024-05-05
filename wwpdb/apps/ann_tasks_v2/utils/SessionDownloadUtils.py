##
# File:  SessionDownloadUtils
# Date:  26-Feb-2014
#
# Updated:
#  27-Feb-2014  jdw --  add version parameters --
#
"""
Common methods for managing download operations for project files within the session context.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os
import os.path
import shutil
import traceback

from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.io.locator.DataReference import ReferenceFileComponents


class SessionDownloadUtils(object):
    """Common methods for managing download operations for project files within the session context."""

    #

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """Input request object is used to determine session context."""
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        #
        self.__sessionId = self.__reqObj.getSessionId()
        self.__sessionPath = self.__reqObj.getSessionPath()
        sP = os.path.join(self.__sessionPath, self.__sessionId)
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=sP, verbose=self.__verbose, log=self.__lfh)
        #
        self.__sessionDir = "sessions"
        self.__downloadDir = "downloads"
        #
        self.__downloadDirPath = os.path.join(self.__sessionPath, self.__sessionId, self.__downloadDir)
        self.__webDownloadDirPath = os.path.join("/", self.__sessionDir, self.__sessionId, self.__downloadDir)
        self.__webDownloadFilePath = None
        #
        self.__targetFilePath = None
        self.__targetFileName = None
        self.__downloadFilePath = None
        self.__setup()

    def __setup(self):
        if not os.access(self.__downloadDirPath, os.W_OK):
            os.makedirs(self.__downloadDirPath, 0o755)

    def getFilePath(self, idCode, contentType="model", formatType="pdbx", fileSource="archive", instance=None, mileStone=None, versionId="latest"):
        return self.__pI.getFilePath(idCode, contentType=contentType, formatType=formatType, fileSource=fileSource, wfInstanceId=instance, mileStone=mileStone, versionId=versionId)

    def getWebDownloadPath(self):
        return self.__webDownloadDirPath

    def getDownloadFileName(self):
        return os.path.split(self.__downloadFilePath)[1]

    def getIdFromFileName(self, filePath):
        try:
            (_pth, fileName) = os.path.split(filePath)
            rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
            rfc.set(fileName)
            idCode = rfc.getDepositionDataSetId()
            return idCode
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+SessionDownloadUtils.getIdFromFileName() + failed for file %s\n" % filePath)
                traceback.print_exc(file=self.__lfh)
        return None

    def getContentTypeFromFileName(self, filePath):
        try:
            (_pth, fileName) = os.path.split(filePath)

            rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
            rfc.set(fileName)
            # fields=fileName.split('_')
            # return fields[2]
            cType = rfc.getContentType()
            return cType
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+SessionDownloadUtils.getContetTypeFromFileName() + failed for file %s\n" % filePath)
                traceback.print_exc(file=self.__lfh)
            return None

    def getContentFormatFromFileName(self, filePath):
        try:
            (_pth, fileName) = os.path.split(filePath)

            rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
            rfc.set(fileName)
            fmt = rfc.getContentFormat()
            return fmt
            # fields=fileName.split('.')
            # if fields[1] in ['cif']:
            #    return 'pdbx'
            # else:
            #    return fields[1]
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+SessionDownloadUtils.getContetFormatFromFileName() + failed for file %s\n" % filePath)
            return None

    def getPartitionNumberFromFileName(self, filePath):
        try:
            (_pth, fileName) = os.path.split(filePath)
            rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
            rfc.set(fileName)
            partNo = rfc.getPartitionNumber()
            return partNo
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+SessionDownloadUtils.getContetFormatFromFileName() + failed for file %s\n" % filePath)
            return 1

    def fetchId(self, idCode, contentType="model", formatType="pdbx", fileSource="archive", instance=None, mileStone=None, versionId="latest", partNumber="1"):
        """Copy the file with the input signature from the fileSource directory to the session download directory."""
        filePath = self.__pI.getFilePath(
            idCode, contentType=contentType, formatType=formatType, fileSource=fileSource, wfInstanceId=instance, mileStone=mileStone, versionId=versionId, partNumber=partNumber
        )
        if self.__verbose:
            self.__lfh.write(
                "+SessionDownloadUtils.fetchId() id %s contentType %s format %s file source %s mileStone %s \n                       path %s\n"
                % (idCode, contentType, formatType, fileSource, mileStone, filePath)
            )
        if filePath is not None:
            return self.__fetchFile(filePath)
        else:
            return False

    def removeFromDownload(self, filePath):
        """Removes a previously setuop download file"""
        (_pth, targetFileName) = os.path.split(filePath)
        downloadFilePath = os.path.join(self.__downloadDirPath, targetFileName)
        if os.path.exists(downloadFilePath):
            os.unlink(downloadFilePath)

    def copyToDownload(self, filePath):
        self.__fetchFile(filePath)

    def __fetchFile(self, filePath):
        """Save input file in session download directory -"""
        try:
            self.__webDownloadFilePath = None
            #
            self.__targetFilePath = None
            self.__targetFileName = None
            self.__downloadFilePath = None
            if not os.access(filePath, os.R_OK):
                if self.__verbose:
                    self.__lfh.write("+SessionDownloadUtils.fetchFile() input file not found %s\n" % filePath)
                return False
            if self.__verbose:
                self.__lfh.write("+SessionDownloadUtils.fetchFile() copying input path %s\n" % filePath)
            self.__targetFilePath = filePath
            (_pth, self.__targetFileName) = os.path.split(self.__targetFilePath)
            self.__downloadFilePath = os.path.join(self.__downloadDirPath, self.__targetFileName)
            if self.__targetFilePath != self.__downloadFilePath:
                shutil.copyfile(self.__targetFilePath, self.__downloadFilePath)
            self.__webDownloadFilePath = os.path.join(self.__webDownloadDirPath, self.__targetFileName)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+SessionDownloadUtils.fetchFile() failed for file %s\n" % filePath)
                traceback.print_exc(file=self.__lfh)
        return False

    def getWebPath(self):
        """ """
        return self.__webDownloadFilePath

    def getDownloadPath(self):
        """ """
        return self.__downloadFilePath

    def getDownloadSubFolderName(self):
        """

        :return: sub folder for downloads folder
        """
        return self.__downloadDir

    def getAnchorTag(self, label=None, target="_blank"):
        """Return the anchor tag corresponding the current download file selection."""
        if label is not None and len(label) > 0:
            txt = label
        else:
            txt = self.__targetFileName

        return '<a href="%s" target="%s">%s</a>' % (self.__webDownloadFilePath, target, txt)
