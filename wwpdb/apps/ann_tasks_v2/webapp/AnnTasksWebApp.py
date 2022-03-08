##
# File:  AnnTasksWebApp.py
# Date:  22-Feb-2014  J.Westbrook
# Updates:
#
# 22-Feb-2014 jdw   Beginning version 2 consolidation  -
#
##
"""
Manage web request and response processing for miscellaneous annotation tasks.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2010-2014 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys
import inspect

from wwpdb.utils.session.WebRequest import InputRequest
from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.apps.ann_tasks_v2.webapp.AnnTasksWebAppWorker import AnnTasksWebAppWorker
from wwpdb.apps.ann_tasks_v2.webapp.ReviewDataWebAppWorker import ReviewDataWebAppWorker
from wwpdb.apps.ann_tasks_v2.webapp.StatusUpdateWebAppWorker import StatusUpdateWebAppWorker
from wwpdb.apps.ann_tasks_v2.webapp.ValidationTasksWebAppWorker import ValidationTasksWebAppWorker


class AnnTasksWebApp(object):
    """Handle request and response object processing for miscellaneous annotation tasks."""

    def __init__(self, parameterDict=None, verbose=False, log=sys.stderr, siteId="WWPDB_DEV"):
        """
        Create an instance of the appropriate worker class to manage input task web request.

         :param `parameterDict`: dictionary storing parameter information from the web request.
             Storage model for GET and POST parameter data is a dictionary of lists.
         :param `verbose`:  boolean flag to activate verbose logging.
         :param `log`:      stream for logging.
         :param `siteId`:      site identifier.

        """
        if parameterDict is None:
            parameterDict = {}
        self.__verbose = verbose
        self.__lfh = log
        self.__siteId = siteId
        #
        self.__debug = True
        #
        self.__cI = ConfigInfo(self.__siteId)
        self.__topPath = self.__cI.get("SITE_WEB_APPS_TOP_PATH")
        self.__topSessionPath = self.__cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH")
        #
        if isinstance(parameterDict, dict):
            self.__myParameterDict = parameterDict
        else:
            self.__myParameterDict = {}

        self.__reqObj = InputRequest(self.__myParameterDict, verbose=self.__verbose, log=self.__lfh)
        #
        self.__reqObj.setValue("TopSessionPath", self.__topSessionPath)
        self.__reqObj.setValue("TopPath", self.__topPath)
        self.__reqObj.setValue("WWPDB_SITE_ID", self.__siteId)
        os.environ["WWPDB_SITE_ID"] = self.__siteId
        #
        self.__reqObj.setDefaultReturnFormat(return_format="html")
        self.__requestPath = self.__reqObj.getValue("request_path")

    def doOp(self):
        """Execute request and package results in response dictionary.

        :Returns:
             A dictionary containing response data for the input request.
             Minimally, the content of this dictionary will include the
             keys: CONTENT_TYPE and REQUEST_STRING.
        """
        if self.__debug:
            self.__dumpRequest()
        if self.__requestPath.startswith("/service/review"):
            stw = ReviewDataWebAppWorker(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        elif self.__requestPath.startswith("/service/status"):
            stw = StatusUpdateWebAppWorker(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        elif self.__requestPath.startswith("/service/validation_task"):
            stw = ValidationTasksWebAppWorker(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        elif self.__requestPath.startswith("/service/ann_task"):
            stw = AnnTasksWebAppWorker(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        else:
            stw = AnnTasksWebAppWorker(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)

        rC = stw.doOp()

        #
        # Package return according to the request return_format -
        #
        # if self.__debug:
        #    self.__dumpResponse(rC)

        return rC.get()

    # def __dumpResponse(self, rC):
    #     """Utility method to format the contents of the response object.

    #     :Returns: None
    #     """
    #     self.__lfh.write("+-----------------------------------------------------------------------------------------\n\n")
    #     self.__lfh.write("+%s.%s completed request  %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self.__requestPath))
    #     if rC is not None:
    #         self.__lfh.write("%s" % ("".join(rC.dump())))
    #     else:
    #         self.__lfh.write("+%s.%s response content object empty.\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name))
    #     self.__lfh.flush()

    def __dumpRequest(self):
        """Utility method to format the contents of the internal parameter dictionary
        containing data from the input web request.

        :Returns: None

        """
        self.__lfh.write("\n\n\n+------------------------------ NEW REQUEST - NEW REQUEST - NEW REQUEST ---------------------------------------------------------\n")
        self.__lfh.write("+%s.%s starting a new request:  %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self.__requestPath))
        self.__reqObj.printIt(self.__lfh)
        self.__lfh.flush()
