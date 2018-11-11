##
# File:    PdbxExpIoUtilsTests.py
# Date:    30-Apr-2014
#
# Updates:
#
##
"""
Test cases for IO and edit operation of reflection data files ...

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import unittest
import traceback
import time
import os
import os.path
import logging

from wwpdb.apps.ann_tasks_v2.expIoUtils.PdbxExpIoUtils import PdbxExpFileIo, PdbxExpIoUtils

import platform
import os
HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, 'test-output', platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)

# Create logger
logger = logging.getLogger()
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] [%(module)s.%(funcName)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


class PdbxExpIoUtilsTests(unittest.TestCase):
    def setUp(self):
        #
        self.__verbose = True
        self.__lfh = sys.stdout
        self.__pathExamplesRel = "./tests"
        mockTopPath = os.path.join(TOPDIR, 'wwpdb', 'mock-data')
        
        self.__pathExamples = os.path.join(mockTopPath, 'SF')
        self.__pathModelExamples = os.path.join(mockTopPath, 'MODELS')
        self.__examSFFileList = ['3oqp-sf.cif']

        self.__examFileRegex = os.path.join(HERE, 'tests', 'regex-input.cif')

        self.__examPairFileList = [('4pdr.cif', '4pdr-sf.cif')]

    def tearDown(self):
        pass

    @staticmethod
    def __insertCommentsM(fn):
        """
        """
        import re
        import mmap
        pattern = r'''\ndata_'''
        replacement = r'''\n#END\ndata_'''
        reObj = re.compile(pattern, re.MULTILINE | re.DOTALL)

        f = open(fn, 'a+b')
        m = mmap.mmap(f.fileno(), 0, access = mmap.ACCESS_WRITE)
        reObj.sub(replacement, m)
        m.append('\n#END OF REFLECTIONS\n')
        # Flush changes made to the inmemory copy of the file back to disk
        m.flush()
        m.close()
        f.close()

    @staticmethod
    def __insertComments(inpFn, outFn):
        """  Insert end of block/file comments in the input file -- 
        """
        import re
        #
        pattern = r"[\r\n]+data_"
        replacement = r"\n#END\ndata_"
        reObj = re.compile(pattern, re.MULTILINE | re.DOTALL | re.VERBOSE)
        # Flush changes made to the in-memory copy of the file back to disk
        ofh = open(outFn, 'w')
        ofh.write(reObj.sub(replacement, open(inpFn, 'r').read()) + '\n#END OF REFLECTIONS\n')
        ofh.close()
        return True

    def testInsertComments(self):
        """ Read and write operations --
        """
        startTime = time.time()
        self.__lfh.write(
            "\n\n========================================================================================================\n")
        self.__lfh.write("Starting %s %s at %s\n" % (self.__class__.__name__,
                                                     sys._getframe().f_code.co_name,
                                                     time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        try:
            fnInp = self.__examFileRegex
            fnOut = os.path.join(TESTOUTPUT, "test-regex-sf.cif")
            self.__insertComments(fnInp, fnOut)
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

        endTime = time.time()
        self.__lfh.write("\nCompleted %s %s at %s (%.2f seconds)\n" % (self.__class__.__name__,
                                                                       sys._getframe().f_code.co_name,
                                                                       time.strftime("%Y %m %d %H:%M:%S",
                                                                                     time.localtime()),
                                                                       endTime - startTime))

    def testReadWriteSF(self):
        """ Read and write reflection data files adding comment terminators  ----
        """
        startTime = time.time()
        self.__lfh.write(
            "\n\n========================================================================================================\n")
        self.__lfh.write("Starting %s %s at %s\n" % (self.__class__.__name__,
                                                     sys._getframe().f_code.co_name,
                                                     time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        try:
            pIo = PdbxExpFileIo(verbose=self.__verbose, log=self.__lfh)
            for ii, f in enumerate(self.__examSFFileList):
                fnInp = os.path.join(self.__pathExamples, f + '.gz')
                fnOut = os.path.join(TESTOUTPUT, "test-%d-sf.cif" % ii)
                fnCmt = os.path.join(TESTOUTPUT, "test-%d-sf-comments.cif" % ii)
                containerList = pIo.getContainerList(fnInp)
                for container in containerList:
                    self.__lfh.write("In file %s Found data set %s\n" % (fnInp, container.getName()))
                    catNameList = container.getObjNameList()
                    for catName in catNameList:
                        catObj = container.getObj(catName)
                        nRows = catObj.getRowCount()
                        self.__lfh.write(" +++ category %s row count %d\n" % (catName, nRows))
                pIo.writeContainerList(fnOut, containerList)
                self.__insertComments(fnOut, fnCmt)

        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

        endTime = time.time()
        self.__lfh.write("\nCompleted %s %s at %s (%.2f seconds)\n" % (self.__class__.__name__,
                                                                       sys._getframe().f_code.co_name,
                                                                       time.strftime("%Y %m %d %H:%M:%S",
                                                                                     time.localtime()),
                                                                       endTime - startTime))

    def testReadExpItems(self):
        """ Read selected items from model and reflection data files -- 

            This is an illustration of the available accessor methods -- 
        """
        startTime = time.time()
        self.__lfh.write(
            "\n\n========================================================================================================\n")
        self.__lfh.write("Starting %s %s at %s\n" % (self.__class__.__name__,
                                                     sys._getframe().f_code.co_name,
                                                     time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        try:
            # get model data --
            pIo = PdbxExpFileIo(verbose=self.__verbose, log=self.__lfh)
            for ii, (mFn, sfFn) in enumerate(self.__examPairFileList):
                fnInp = os.path.join(self.__pathModelExamples, mFn)
                containerList = pIo.getContainerList(fnInp)
                for container in containerList:
                    self.__lfh.write("In file %s found data set %s\n" % (fnInp, container.getName()))
                    catNameList = container.getObjNameList()
                    for catName in sorted(catNameList):
                        catObj = container.getObj(catName)
                        nRows = catObj.getRowCount()
                        self.__lfh.write(" +++ category %s row count %d\n" % (catName, nRows))
                    pE = PdbxExpIoUtils(dataContainer=container, verbose=self.__verbose, log=self.__lfh)
                    cName = pE.getContainerName()
                    entryId = pE.getEntryId()
                    pdbId = pE.getDbCode(dbId='PDB')
                    diffrnSourceIdList = pE.getDiffrnSourceIds()
                    diffrnIdList = pE.getDiffrnIds()

                    self.__lfh.write(
                        " +++ container name %r  entryId %r pdbId %r Source diffrnIdList %r diffrnIdList %r\n" %
                        (cName, entryId, pdbId, diffrnSourceIdList, diffrnIdList))
                    #
                    #
                    muD = pE.getDiffrnRadiationWavelengthList()
                    self.__lfh.write(" +++ muD %r\n" % muD)
                    #
                    for diffrnId in diffrnIdList:
                        mu = pE.getDiffrnSourceWavelength(diffrnId=diffrnId)
                        muListS = pE.getDiffrnSourceWavelengthList(diffrnId=diffrnId)
                        muList = pE.getDiffrnSourceWavelengthListAsList(diffrnId=diffrnId)
                        # muList = [(str(ii+1),str(mu).strip()) for ii,mu  in enumerate(muListS.split(','))]
                        self.__lfh.write(" +++ diffrnId %r  wavelength     %r\n" % (diffrnId, mu))
                        self.__lfh.write(" +++ diffrnId %r  wavelengthList %r\n" % (diffrnId, muListS))
                        self.__lfh.write(" +++ diffrnId %r  diffrn radiation wavelength list %r\n" % (diffrnId, muList))

                # pIo.writeContainerList(fnOut,containerList)
                # self.__insertComments(fnOut,fnCmt)

        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

        endTime = time.time()
        self.__lfh.write("\nCompleted %s %s at %s (%.2f seconds)\n" % (self.__class__.__name__,
                                                                       sys._getframe().f_code.co_name,
                                                                       time.strftime("%Y %m %d %H:%M:%S",
                                                                                     time.localtime()),
                                                                       endTime - startTime))

    def testUpdateExpItems(self):
        """ update selected items from model and reflection data files -- 

            This is an illustration of the available accessor methods -- 
        """
        startTime = time.time()
        self.__lfh.write(
            "\n\n========================================================================================================\n")
        self.__lfh.write("Starting %s %s at %s\n" % (self.__class__.__name__,
                                                     sys._getframe().f_code.co_name,
                                                     time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        try:

            pIo = PdbxExpFileIo(verbose=self.__verbose, log=self.__lfh)
            for ii, (mFn, sfFn) in enumerate(self.__examPairFileList):
                # First get the get model data --
                #
                modelPath = os.path.join(self.__pathModelExamples, mFn)
                mIo = PdbxExpFileIo(verbose=self.__verbose, log=self.__lfh)
                mcList = mIo.getContainerList(modelPath)
                if len(mcList) < 1:
                    continue
                #
                #  Read relevant data items in the first container -- 
                #
                mE = PdbxExpIoUtils(dataContainer=mcList[0], verbose=self.__verbose, log=self.__lfh)
                entryId = mE.getEntryId()
                pdbId = mE.getDbCode(dbId='PDB')
                modelDiffrnSourceIdList = mE.getDiffrnSourceIds()
                modelWavelengthD = {}
                for diffrnId in modelDiffrnSourceIdList:
                    modelWavelengthD[diffrnId] = mE.getDiffrnSourceWavelengthListAsList(diffrnId=diffrnId)
                #
                # ------
                #
                sfPath = os.path.join(self.__pathExamples, sfFn)
                sfIo = PdbxExpFileIo(verbose=self.__verbose, log=self.__lfh)
                containerList = sfIo.getContainerList(sfPath)
                if len(containerList) < 1:
                    continue
                # 
                # ---- simple updates ----
                sfIo.updateContainerNames(idCode=pdbId, containerList=containerList)
                sfIo.updateEntryIds(idCode=pdbId, containerList=containerList)
                #
                for container in containerList:
                    self.__lfh.write("In file %s found data set %s\n" % (sfPath, container.getName()))
                    #
                    # Read selected items from this container --
                    pE = PdbxExpIoUtils(dataContainer=container, verbose=self.__verbose, log=self.__lfh)
                    curContainerName = mE.getContainerName()
                    diffrnIdList = pE.getDiffrnIds()
                    curMuList = pE.getDiffrnRadiationWavelengthList()
                    # 
                    # Try to assign the diffrn_id for the current reflection data section ...
                    #
                    if len(diffrnIdList) > 1:
                        self.__lfh.write("+ERROR multiple diffrn_id codes %r in reflection data section %r\n" % (
                        diffrnIdList, curContainerName))
                        continue
                    #
                    if len(diffrnIdList) < 1:
                        dId = '1'
                    else:
                        dId = diffrnIdList[0]
                    #
                    if dId in modelWavelengthD:
                        muList = modelWavelengthD[dId]
                        muD = {}
                        for muId, mu, wt in muList:
                            muD[muId] = (muId, mu, wt)
                    else:
                        muList = []
                        muD = {}
                        # no data -- move on  
                        continue
                    #
                    # Limited substitution - 
                    #
                    updMuList = []
                    for muId, mu, wt in curMuList:
                        if ((mu in [None, '', '.', '?', '1.0', '1.00', '1.000', '1.0000']) and (muId in muD)):
                            (tmuId, tmu, twt) = muD[muId]
                            updMuList.append((muId, tmu, twt))
                        else:
                            updMuList.append((muId, mu, wt))
                            #
                    self.__lfh.write(" +++ updating wavelength setting in container %r updMuList %r\n" % (
                    curContainerName, updMuList))
                    ok = sfIo.updateRadiationWavelength(updMuList, container)
                #
                sfOutPath = sfFn + '-out'
                sfIo.writeContainerList(sfOutPath, containerList)
                fnCmt = sfFn + '-out-comment'
                self.__insertComments(sfOutPath, fnCmt)
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

        endTime = time.time()
        self.__lfh.write("\nCompleted %s %s at %s (%.2f seconds)\n" % (self.__class__.__name__,
                                                                       sys._getframe().f_code.co_name,
                                                                       time.strftime("%Y %m %d %H:%M:%S",
                                                                                     time.localtime()),
                                                                       endTime - startTime))


def suiteUpdateExpItemsTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PdbxExpIoUtilsTests("testUpdateExpItems"))
    return suiteSelect


def suiteReadExpItemsTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PdbxExpIoUtilsTests("testReadExpItems"))
    return suiteSelect


def suiteReadWriteTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PdbxExpIoUtilsTests("testReadWriteSF"))
    return suiteSelect


def suiteRegexTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PdbxExpIoUtilsTests("testInsertComments"))
    return suiteSelect


if __name__ == '__main__':

    if (True):
        mySuite = suiteReadWriteTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteRegexTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteReadExpItemsTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

    mySuite = suiteUpdateExpItemsTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
