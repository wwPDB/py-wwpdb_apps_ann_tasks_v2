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
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.001"

import sys, unittest, traceback
import time, os, os.path, shutil
from wwpdb.apps.ann_tasks_v2.io.PisaReader import PisaAssemblyReader

class PisaReaderTests(unittest.TestCase):
    def setUp(self):
        self.__lfh=sys.stdout
        self.__pisaAssembliesFilePath='./data/pisa-assemblies.xml'
        #self.__pisaAssembliesFilePath='./data/3rij-assemblies.xml'
        self.__pisaInterfacesFilePath='./data/pisa-interfaces.xml'        
        self.__pisaAssembliesFilePath='./data/3rer_assembly-report_P1.xml'
    def tearDown(self):
        pass
    
    def testPisaAssemblyReader(self): 
        """Test PISA assembly file reader -
        """
        try:
            rC=PisaAssemblyReader(verbose=True,log=self.__lfh)
            rC.read(self.__pisaAssembliesFilePath)
            rC.dump("pisa-assemblies.dump")
            nA=rC.getAssemblySetCount()
            self.__lfh.write("Number of assembly sets %d\n" % nA)
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

           
def suitePisaTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PisaReaderTests("testPisaAssemblyReader"))    
    return suiteSelect    
    
if __name__ == '__main__':
    #
    mySuite=suitePisaTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
