##
# File:  TaskSessionState
# Date:  2-Mar-2014
#
# Updated:
#
##
"""
Accessors to encapsulate common task session details --

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import traceback


class TaskSessionState(object):
    """Accessors to encapsulate common task session details --"""

    #
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        """Input request object is used to determine session context."""
        # self.__verbose = verbose
        self.__lfh = log
        # self.__reqObj = reqObj
        #
        self.__D = {}
        self.__strKeyList = [
            "taskname",
            "entryid",
            "entryfilename",
            "entryexpfilename",
            "taskargs",
            "links",
            "statustext",
            "taskformid",
            "auxilaryfilename",
            "auxilaryfiletype",
            "errormessage",
            "warningmessage",
        ]
        self.__boolKeyList = ["errorflag", "warningflag"]
        self.clear()
        #

    def clear(self):
        self.__D = {}
        for ky in self.__strKeyList:
            self.__D[ky] = ""
        for ky in self.__boolKeyList:
            self.__D[ky] = False

    def set(self, dictval):
        try:
            for k, v in dictval.items():
                self.__D[k] = v
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def get(self):
        return self.__D

    def assign(self, name, formId=None, args=None, completionFlag=None, tagList=None, entryId=None, entryFileName=None, entryExpFileName=None):
        try:
            if name is not None:
                self.setTaskName(name)
            if formId is not None:
                self.setFormId(formId)
            if args is not None:
                self.setTaskArgs(args)
            if completionFlag is not None:
                self.setTaskCompletionFlag(completionFlag)
            if tagList is not None:
                self.setTaskLinks(tagList)
            if entryId is not None:
                self.setEntryId(entryId)
            if entryFileName is not None:
                self.setEntryFileName(entryFileName)
            if entryExpFileName is not None:
                self.setEntryExpFileName(entryExpFileName)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            return False

    def setTaskName(self, val):
        self.__D["taskname"] = val

    def getTaskName(self):
        return self.__D["taskname"]

    def setEntryId(self, val):
        self.__D["entryid"] = val

    def getEntryId(self):
        return self.__D["entryid"]

    def setEntryFileName(self, val):
        self.__D["entryfilename"] = val

    def getEntryFileName(self):
        return self.__D["entryfilename"]

    def setEntryExpFileName(self, val):
        self.__D["entryexpfilename"] = val

    def getEntryExpFileName(self):
        return self.__D["entryexpfilename"]

    def setTaskArgs(self, val):
        self.__D["taskargs"] = val

    def getTaskArgs(self):
        return self.__D["taskargs"]

    def setTaskLinks(self, val):
        self.__D["links"] = val

    def getTaskLinks(self):
        return self.__D["links"]

    def setTaskStatusText(self, val):
        self.__D["statustext"] = val

    def getTaskStatusText(self):
        return self.__D["statustext"]

    def setTaskCompletionFlag(self, val):
        self.__D["errorflag"] = not val

    def setTaskErrorFlag(self, val):
        self.__D["errorflag"] = val

    def getTaskErrorFlag(self):
        return self.__D["errorflag"]

    def setFormId(self, val):
        self.__D["taskformid"] = val

    def getFormId(self):
        return self.__D["taskformid"]

    def setTaskWarningFlag(self, val):
        self.__D["warningflag"] = val

    def getTaskWarningFlag(self):
        return self.__D["warningflag"]

    def setAuxilaryFileName(self, val):
        self.__D["auxilaryfilename"] = val

    def getAuxilaryFileName(self):
        return self.__D["auxilaryfilename"]

    def setAuxilaryFileType(self, val):
        self.__D["auxilaryfilename"] = val

    def getAuxilaryFileType(self):
        return self.__D["auxilaryfilename"]

    def setTaskErrorMessage(self, val):
        self.__D["errormessage"] = val

    def getTaskErrorMessage(self):
        return self.__D["errormessage"]

    def setTaskWarningMessage(self, val):
        self.__D["warningmessage"] = val

    def getTaskWarningMessage(self):
        return self.__D["warningmessage"]
