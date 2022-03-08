##
# File:  Related.py
# Date:  17-Feb-2020 E. Peisach
#
# Update:
#
##
"""
Manage the update of pdbx_database_related if they appear to be deposition ids

"""


import logging
import sys
import os.path
from wwpdb.apps.ann_tasks_v2.related.UpdateRelated import UpdateRelated
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils
from wwpdb.io.file.DataFile import DataFile

logger = logging.getLogger(__name__)


class Related(SessionWebDownloadUtils):
    """
    The Related class encapsulates the update of pdbx_database_releated

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        super(Related, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__reqObj = reqObj
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #

    def run(self, entryId, inpFile, updateInput=True):
        """Run the related update"""
        logger.info("About to update %s %s %s", entryId, inpFile, updateInput)
        try:
            inpPath = os.path.join(self.__sessionPath, inpFile)
            logPath = os.path.join(self.__sessionPath, entryId + "-related-updated.log")
            retPath = os.path.join(self.__sessionPath, entryId + "_model-updated_related.cif")
            #
            ur = UpdateRelated(siteId=self.__siteId)
            updated = ur.updateRelatedEntries(inpPath, retPath, logPath)

            if updated:
                self.addDownloadPath(retPath)
                if updateInput:
                    df = DataFile(retPath)
                    df.copy(inpPath)

            self.addDownloadPath(logPath)

            logger.info("Completed with updated status %s", updated)

            return True
        except Exception as e:
            logger.traceback("Failed to updated related %s", str(e))
            return False
