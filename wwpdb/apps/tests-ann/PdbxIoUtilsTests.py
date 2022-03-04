##
# File:    PdbxIoUtilsTests.py
# Date:    09-Nov-2018
#
# Updates:
#
##
"""
Test cases for extracting assembly info

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import sys
import unittest
import os.path

if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from commonsetup import HERE  # noqa:  F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import HERE  # noqa: F401 pylint: disable=relative-beyond-top-level

from wwpdb.apps.ann_tasks_v2.io.PdbxIoUtils import ModelFileIo, PdbxFileIo

TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


class PdbxIoUtilsTests(unittest.TestCase):
    def setUp(self):
        #
        self.__verbose = True
        self.__lfh = sys.stdout
        # Old examples -
        self.__pathExamples = os.path.abspath(os.path.join(HERE, "tests"))
        #
        self.__examFileList = ["3rer.cif"]

    def tearDown(self):
        pass

    def testAssemblyAcesss(self):
        """Test access patterns for assembly info"""
        for f in self.__examFileList:
            fN = os.path.join(self.__pathExamples, f)
            c0 = PdbxFileIo(verbose=self.__verbose, log=self.__lfh).getContainer(fN)
            sdf = ModelFileIo(dataContainer=c0, verbose=self.__verbose, log=self.__lfh)
            assemL, assemGenL, assemOpL = sdf.getAssemblyDetails()
            # Test examples have assemblies
            self.assertIsNotNone(assemL)
            self.assertIsNotNone(assemGenL)
            self.assertIsNotNone(assemOpL)

            # For public files, missing
            assemL = sdf.getDepositorAssemblyDetails()
            self.assertEqual(assemL, [])
            assemOper = sdf.getDepositorStructOperList()
            self.assertEqual(assemOper, [])
            assemEvidence = sdf.getDepositorAssemblyEvidence()
            self.assertEqual(assemEvidence, [])
            assemClassification = sdf.getDepositorAssemblyClassification()
            self.assertEqual(assemClassification, [])

            # Returns list with contents even when empty
            assemRcsbL = sdf.getDepositorAssemblyDetailsRcsb()
            self.assertNotEqual(assemRcsbL, [])

            #
            ed = sdf.getPolymerEntityChainDict()
            self.assertNotEqual(ed, {})

            polyEntityList = sdf.getEntityPolyList()
            self.assertNotEqual(polyEntityList, [])


if __name__ == "__main__":
    unittest.main()
