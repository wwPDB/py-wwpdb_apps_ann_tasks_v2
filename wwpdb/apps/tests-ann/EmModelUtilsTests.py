##
# File:    EmModelUtilsTests.py
# Author:  jdw
# Date:    24-July-2015
# Version: 0.001
#
# Updates:
#    18-Aug-2015 - jdw add support for  map type and partition alignment in em_map category update.
#
##
"""
Tests for model update using map header data  -

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import unittest
import traceback
import time

if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from commonsetup import HERE  # noqa:  F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import HERE  # noqa: F401 pylint: disable=relative-beyond-top-level

from wwpdb.apps.ann_tasks_v2.em3d.EmModelUtils import EmModelUtils


@unittest.skip("Until tests ported")
class EmModelUtilsTests(unittest.TestCase):
    def setUp(self):
        self.__lfh = sys.stderr
        self.__verbose = True
        # example files --
        self.__pathEmModelFile = "./tests/D_1000000020_model_P1.cif.V1"
        self.__pathEmVolumeFile = "./tests/D_1000000020_em-volume_P1.map.V1"
        self.__pathEmHeaderFile = "./tests/D_1000000020_mapfix-header-report_P1.json"
        self.__entryId = "D_1000000020"

    def tearDown(self):
        pass

    def testUpdateModel(self):
        """Test case -  model file update with map header data"""
        startTime = time.time()
        self.__lfh.write("\nStarting %s %s at %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        try:
            emmu = EmModelUtils(verbose=self.__verbose, log=self.__lfh)
            mD = emmu.setMapHeaderFilePath(self.__pathEmHeaderFile)
            status = emmu.setModelFilePath(self.__pathEmModelFile)
            pth, fn = os.path.split(self.__pathEmVolumeFile)
            emmu.setMapFileName(fn)
            emmu.setEntryId(self.__entryId)
            emmu.setMapType("primary map")
            self.__lfh.write("+%s.%s read %s with em_map category status %r\n" % (self.__class__.__name__, sys._getframe().f_code.co_name, self.__pathEmModelFile, status))
            self.__lfh.write("+%s.%s map header contents\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
            for k, v in mD.items():
                self.__lfh.write(" map key %s  %r\n" % (k, v))
            for k in sorted(mD["output_header_long"].keys()):
                v = mD["output_header_long"][k]
                self.__lfh.write("'%s': %r,\n" % (k, v))
            #
            emmu.updateModelFromHeader(entryId=self.__entryId, outModelFilePath="t-out.cif", mapType="primary map", partition="1")
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=sys.stdout)
            self.fail()

        endTime = time.time()
        self.__lfh.write(
            "\nCompleted %s %s at %s (%.2f seconds)\n"
            % (self.__class__.__name__, sys._getframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - startTime)
        )


def suiteUpdateModelTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(EmModelUtilsTests("testUpdateModel"))
    return suiteSelect


if __name__ == "__main__":
    if True:
        mySuite = suiteUpdateModelTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
