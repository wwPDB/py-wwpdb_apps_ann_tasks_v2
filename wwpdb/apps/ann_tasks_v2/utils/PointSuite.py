##
# File:  PointSuite.py
# Date:  13-Agu-2024  Zukang Feng
#
# Update:
##
"""
Manage utility to run the programs defined in the suite.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys
import traceback

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

try:
    from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapter
except ImportError:
    from mmcif.io.IoAdapterPy import IoAdapterPy as IoAdapter
#


class PointSuite(object):
    """ PointSuite class encapsulates running the programs defined in the suite.
    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self.__reqObj = reqObj
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()

    def importMats(self, inputMatFilePath, logPath):
        """ Run PointSuite's "importmats" program
        """
        exportList = [os.path.join(self.__sessionPath, "import.biomt"), os.path.join(self.__sessionPath, "import.cif"),
                      os.path.join(self.__sessionPath, "import.matrix")]
        #
        allFileList = [os.path.join(self.__sessionPath, "import.biomt"), os.path.join(self.__sessionPath, "import.cif"),
                       os.path.join(self.__sessionPath, "import.matrix"), logPath]
        #
        for filePath in allFileList:
            if os.access(filePath, os.F_OK):
                os.remove(filePath)
            #
        #
        dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        dp.imp(inputMatFilePath)
        dp.op("pointsuite-importmats")
        dp.expList(dstPathList=exportList)
        dp.expLog(dstPath=logPath, appendMode=False)
        dp.cleanup()
        #
        num_of_matrices = 0
        matricesCifPath = os.path.join(self.__sessionPath, "import.cif")
        if os.access(matricesCifPath, os.F_OK):
            #
            # The "import.cif" file output from PointSuite software does not have "data_" line in the beginning of the file.
            # The following section adds the "data_" line in order for mmCIF parser to read file correctly.
            #
            ifh = open(matricesCifPath, "r")
            data = ifh.read()
            ifh.close()
            #
            tmpMatricesCifPath = os.path.join(self.__sessionPath, "tmp-import.cif")
            ofh = open(tmpMatricesCifPath, "w")
            ofh.write("data_matrices\n#\n%s\n" % data)
            ofh.close()
            #
            try:
                ioObj = IoAdapter()
                cifContainerList = ioObj.readFile(tmpMatricesCifPath)
                catObj = cifContainerList[0].getObj("pdbx_struct_oper_list")
                if catObj:
                    num_of_matrices = len(catObj.getRowList())
                #
            except:  # noqa: E722 pylint: disable=bare-except
                traceback.print_exc(file=self.__lfh)
                num_of_matrices = 0
            #
        #
        return num_of_matrices

    def findFrame(self, modelCifPath, biomtFilePath, logPath):
        """ Run PointSuite's "findframe" program
        """
        frameCifPath = os.path.join(self.__sessionPath, "findframe.cif")
        #
        for filePath in (frameCifPath, logPath):
            if os.access(filePath, os.F_OK):
                os.remove(filePath)
            #
        #
        dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        dp.imp(modelCifPath)
        dp.addInput(name="biomt", value=biomtFilePath)
        dp.op("pointsuite-findframe")
        dp.exp(frameCifPath)
        dp.expLog(dstPath=logPath, appendMode=False)
        dp.cleanup()

    def makeAssembly(self, modelCifPath, transmtFilePath, logPath):
        """ Run PointSuite's "makeassembly" program
        """
        assemblyCifPath = os.path.join(self.__sessionPath, "assembly.cif")
        #
        for filePath in (assemblyCifPath, logPath):
            if os.access(filePath, os.F_OK):
                os.remove(filePath)
            #
        #
        dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        dp.imp(modelCifPath)
        dp.addInput(name="transmt", value=transmtFilePath)
        dp.op("pointsuite-makeassembly")
        dp.exp(assemblyCifPath)
        dp.expLog(dstPath=logPath, appendMode=False)
        dp.cleanup()

    def mergeAssemblyInfo(self, inModelCifPath, assemblyCifPath, outModelCifPath, logPath):
        """ Run annotation-pack's "MergePointSuiteResult" program
        """
        modifiedAssemblyCifPath = os.path.join(self.__sessionPath, "assembly-with-data-block.cif")
        #
        for filePath in (outModelCifPath, modifiedAssemblyCifPath, logPath):
            if os.access(filePath, os.F_OK):
                os.remove(filePath)
            #
        #
        # The "assembly.cif" file output from PointSuite software does not have "data_" line in the beginning of the file.
        # The following section adds the "data_" line in order for mmCIF parser to read file correctly.
        #
        ifh = open(assemblyCifPath, "r")
        data = ifh.read()
        ifh.close()
        #
        ofh = open(modifiedAssemblyCifPath, "w")
        ofh.write("data_assembly\n#\n%s\n" % data)
        ofh.close()
        #
        dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        dp.imp(inModelCifPath)
        dp.addInput(name="support", value=modifiedAssemblyCifPath)
        dp.op("annot-merge-pointsuite-info")
        dp.exp(outModelCifPath)
        dp.expLog(dstPath=logPath, appendMode=False)
        dp.cleanup()
