##
# File:   NmrRemedationUtils.py
# Date:   20-Dec-2022
#
#
"""
Handle remediation of legacy CS data to make NMR 3.1 compliant for validation

"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisacht@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import logging
import sys

from wwpdb.utils.nmr.CifToNmrStar import CifToNmrStar
from mmcif.io.IoAdapterPy import IoAdapterPy

logger = logging.getLogger()


def remediate_cs_file(infile, outfile):
    """Produces an NMR* formatted from input CIF.  Correcting missing section headers that are required"""
    ctns = CifToNmrStar()
    return ctns.convert(cifPath=infile, strPath=outfile)


def starToPdbx(starPath=None, pdbxPath=None):
    """Converts NMR* to mmCIF"""
    if starPath is None or pdbxPath is None:
        return False
    #
    try:
        myIo = IoAdapterPy(False, sys.stderr)
        containerList = myIo.readFile(starPath)
        if containerList is not None and len(containerList) > 1:
            logger.debug("Input container list is  %r", ([(c.getName(), c.getType()) for c in containerList]))
            for c in containerList:
                c.setType("data")
            # myIo.writeFile(pdbxPath, containerList=containerList[1:])
            myIo.writeFile(pdbxPath, containerList=containerList)
            return True
    except Exception as _e:  # noqa: F841
        logger.exception("starToPdx - failed with exception")

    return False
