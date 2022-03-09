##
# File:  EmMapAutoFixVers.py
# Date:  17-Jun-2019  E Peisach
#
# Update:
##
"""
Updates versions numbers of components in em_map category

"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"


import sys
import logging
from mmcif.io.IoAdapterCore import IoAdapterCore
from wwpdb.io.locator.PathInfo import PathInfo

logger = logging.getLogger()


class EmMapAutoFixVers(object):
    def __init__(self, sessionPath, siteId=None, verbose=True, log=sys.stderr):  # pylint: disable=unused-argument
        self.__verbose = verbose
        self.__lfh = log
        # self.__siteId = siteId
        # self.__sessionPath = sessionPath
        self.__pI = PathInfo(sessionPath=sessionPath, verbose=self.__verbose, log=self.__lfh)

    def autoFixEmMapVersions(self, datasetid, modelin, modelout, location="archive"):
        """For a given depositions id, takes the em_map category from modelin.  It will scan datasetid in location
        for version numbers corresponding to the filenames and update version number.  If any changes, will write
        modelout.

        Assumptions: October 2019
        o em_map filenames do not contain milestones

        Returns True if model file updated
        Returns False if no changes made and modelout not written
        """

        logger.info("Starting fixing versions of em_map")

        # Parse model file
        ioobj = IoAdapterCore()
        c0 = ioobj.readFile(inputFilePath=modelin)
        if len(c0) == 0:
            logger.error("Could not read %s", modelin)
            return False

        block0 = c0[0]

        # Is there an em_map category?
        tobj = block0.getObj("em_map")
        if not tobj:
            logger.info("No em_map category - done")
            return False

        updated = False
        for row in range(tobj.getRowCount()):
            fname = tobj.getValue("file", row)

            (d_id, ct_type, ct_format, partno, _verno) = self.__pI.parseFileName(fname)
            if not d_id:
                logger.error("Could not parse filename in em_map category %s", fname)
                continue

            newname = self.__pI.getFileName(datasetid, contentType=ct_type, formatType=ct_format, partNumber=partno, fileSource=location, versionId="latest")
            if newname != fname:
                logger.debug("Updating fname from %s to %s", fname, newname)
                updated = True
                tobj.setValue(value=newname, attributeName="file", rowIndex=row)

        if updated:
            logger.info("Model file updated")

            # Write model
            ret = ioobj.writeFile(outputFilePath=modelout, containerList=c0)
            logger.info("Writing file returns %s %s", ret, modelout)
            return True

        return False


if __name__ == "__main__":
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    pI = PathInfo(sessionPath="/tmp")

    dep = "D_800037"
    modellocation = "session"
    modin = "/tmp/D_800037/D_800037_model_P1.cif.V17"
    modout = "/tmp/D_800037/D_800037_model_P1.cif.V18"
    ema = EmMapAutoFixVers(sessionPath="/tmp/D_800037")
    ema.autoFixEmMapVersions(datasetid=dep, modelin=modin, modelout=modout, location="session")
