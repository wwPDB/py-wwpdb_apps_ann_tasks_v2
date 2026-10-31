##
# File:    PisaReaderTests.py
# Author:  jdw
# Date:    16-April-2012
#
# Update:
#          5-July-2012 jdw add empty test case
##
"""
Test cases for the PISA XML parser.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.001"

import sys
import unittest
import traceback
import os
import os.path

if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from commonsetup import HERE, TESTOUTPUT  # noqa:  F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import HERE, TESTOUTPUT  # noqa: F401 pylint: disable=relative-beyond-top-level

from wwpdb.apps.ann_tasks_v2.io.PisaReader import PisaAssemblyReader


class PisaReaderTests(unittest.TestCase):
    def setUp(self):
        self.__lfh = sys.stdout
        self.__pisaAssembliesFilePath = os.path.join(HERE, "tests", "pisa-assemblies.xml")
        # self.__pisaInterfacesFilePath = os.path.join(HERE, "tests", "pisa-interfaces.xml")
        self.__pisaAssembliesFilePath = os.path.join(HERE, "tests", "3rer_assembly-report_P1.xml")

    def tearDown(self):
        pass

    def testPisaAssemblyReader(self):
        """Test PISA assembly file reader -"""
        try:
            rC = PisaAssemblyReader(verbose=True, log=self.__lfh)
            rC.read(self.__pisaAssembliesFilePath)
            rC.dump(os.path.join(TESTOUTPUT, "pisa-assemblies.dump"))
            nA = rC.getAssemblySetCount()
            self.__lfh.write("Number of assembly sets %d\n" % nA)
            self.assertEqual(nA, 3)
        except:  # noqa: E722  pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            self.fail()


def suitePisaTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PisaReaderTests("testPisaAssemblyReader"))
    return suiteSelect


if __name__ == "__main__":
    #
    mySuite = suitePisaTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
