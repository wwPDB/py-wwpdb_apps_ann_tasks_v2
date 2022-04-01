##
# File:  SessionWebDownloadUtils
# Date:  28-Feb-2014
#
# Updated:
#
#  2-Mar-2014  jdw  addDownloadPath(self,filePath,label=None)
##
"""
Common methods for managing web download path information and markup.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os
import os.path


class SessionWebDownloadUtils(object):
    """Common methods for managing web download path information and markup."""

    #
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        """Input request object is used to determine session context."""
        # self.__verbose = verbose
        # self.__lfh = log
        self.__reqObj = reqObj
        #
        #  The default download path is based on the session path --
        self.__sessionId = self.__reqObj.getSessionId()
        self.__sessionPath = self.__reqObj.getSessionPath()
        self.__sessionDir = "sessions"
        self.__downloadDirPath = os.path.join(self.__sessionPath, self.__sessionId)
        self.__webDownloadDirPath = os.path.join("/", self.__sessionDir, self.__sessionId)
        #
        self.__downloadFileNameList = []

    def clearFileList(self):
        self.__downloadFileNameList = []

    def setDownloadDirPath(self, path):
        """Set the full path of the download directory --"""
        self.__downloadDirPath = path

    def setWebDownloadDirPath(self, path):
        """Set the web path of the download directory --"""
        self.__webDownloadDirPath = path

    def addDownloadFile(self, fileName, label=None):
        """Add the input filename to the list of download targets."""
        try:
            if os.access(os.path.join(self.__downloadDirPath, fileName), os.R_OK):
                if label is not None:
                    self.__downloadFileNameList.append((fileName, label))
                else:
                    self.__downloadFileNameList.append((fileName, fileName))
                return True
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    def addDownloadPath(self, filePath, label=None):
        """Add the input filename to the list of download targets."""
        try:
            if os.access(os.path.join(filePath), os.R_OK):
                (_d, fileName) = os.path.split(filePath)
                if label is not None:
                    self.__downloadFileNameList.append((fileName, label))
                else:
                    self.__downloadFileNameList.append((fileName, fileName))
                return True
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    def getAnchorTagList(self, label=None, target="_blank", cssClass=""):
        """Return the anchor tag corresponding the current download file selection."""
        tagList = []
        try:
            for fn, label in self.__downloadFileNameList:
                wP = os.path.join(self.__webDownloadDirPath, fn)
                tagList.append('<a class="%s" href="%s" target="%s">%s</a>' % (cssClass, wP, target, label))
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return tagList

    def getWebDownloadPath(self):
        return self.__webDownloadDirPath
