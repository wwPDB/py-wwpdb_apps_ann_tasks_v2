# File:  UpdateRelated.py
# Date:  16-Feb-2020 E. Peisach
#
# Update:
#
##
"""
Resolve pdbx_database_related that point at other deposition s
"""

import sys
import os
import tempfile
import logging
from mmcif.io.IoAdapterCore import IoAdapterCore
from wwpdb.apps.ann_tasks_v2.related.DaInternalDb import DaInternalDb

logger = logging.getLogger(__name__)


class UpdateRelated(object):
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        # self.__verbose = verbose
        # self.__lfh = log
        self.__siteId = siteId
        self.__ioObj = IoAdapterCore()

    def updateRelatedEntries(self, fPathIn, fPathOut, logPath):
        """Updates pdbx_database_related in fPathIn.  If updates made, fPathOut written.
        Returns True if changes made, or else False.
        logPath might be updated with details
        """

        logger.info("Starting with update %s to %s", fPathIn, fPathOut)
        ret = False
        with open(logPath, "w") as logf:
            cin = self.__getContainerList(fPathIn)
            if cin is None:
                logf.write("Could not load %s\n" % fPathIn)
                return False

            block0 = cin[0]
            ret = self.__updateRelatedCategory(block0, logf)
            if ret:
                self.__writeContainerList(fPathOut, cin)
                logger.info("Updated file %s written", fPathOut)

            logf.write("Done\n")

        return ret

    def __updateRelatedCategory(self, block, logf):
        """Updates the databloc pdbx_database_related if needbe.
        return True if updated
        """
        ret = False
        cobj = block.getObj("pdbx_database_related")
        if cobj:
            # Category exists
            for row in range(cobj.getRowCount()):
                db_name = cobj.getValue("db_name", row)
                db_id = cobj.getValue("db_id", row)
                if db_id is not None:
                    db_id = db_id.strip()
                if db_name in ["PDB", "BMRB", "EMDB"] and db_id[:2] == "D_":
                    dbids = self.__getRelatedIds(db_id)
                    if dbids is None:
                        logf.write("Failed to retrieve database_2 info for %s\n" % db_id)
                        continue
                    if db_name in dbids:
                        update = dbids[db_name]
                        cobj.setValue(update, "db_id", row)
                        logf.write("Updating %s %s to %s\n" % (db_name, db_id, update))
                        ret = True
                    else:
                        logf.write("database_2 info for %s does not contain %s id\n" % (db_id, db_name))

        return ret

    def __getRelatedIds(self, depid):
        """Returns a dictionary of data from database_2 as found in da_internal for depid
        If depid is not present in da_internal, return None
        """

        dai = DaInternalDb(siteId=self.__siteId)
        data = dai.getDatabase2(depid)
        if len(data) > 0:
            return data
        return None

    def __getOutDir(self, fPath):
        """Attempts to find a writeable place for log file during read"""
        for dp in [os.path.dirname(fPath), ".", tempfile.gettempdir()]:
            if os.access(dp, os.W_OK):
                return dp

    def __getContainerList(self, fPath):
        outDirPath = self.__getOutDir(fPath)
        try:
            return self.__ioObj.readFile(fPath, outDirPath=outDirPath)
        except Exception as _e:  # noqa: F841
            logger.exception("Failed to parse %s", fPath)
            return None

    def __writeContainerList(self, fPath, containerList):
        try:
            return self.__ioObj.writeFile(fPath, containerList)
        except Exception as e:
            logger.error("Failed to write out %s error: %s", fPath, str(e))
            return False


if __name__ == "__main__":
    ur = UpdateRelated()
    status = ur.updateRelatedEntries("D_800012_model_P1.cif.V27", "out", "logout.log")
