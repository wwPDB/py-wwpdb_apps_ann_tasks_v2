##
# File:  CoordEditorUpdate.py
# Date:  11-Oct-2013
# Update:
##
"""
Update coordinate cif file

"""
__docformat__ = "restructuredtext en"
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

import sys,os.path,os,traceback
import logging

from mmcif.io.PdbxWriter         import PdbxWriter
from mmcif.api.PdbxContainers     import DataContainer
from mmcif.api.DataCategory import DataCategory
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

logger = logging.getLogger(__name__)

class CoordEditorUpdate(object):
    """
     The CoordEditorUpdate class updates coordinate cif file.

    """
    def __init__(self,reqObj=None,verbose=False,log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        #
        self.__setup()

    def __setup(self):
        self.__siteId=self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj=self.__reqObj.getSessionObj()
        self.__sessionId=self.__sObj.getId()
        self.__sessionPath=self.__sObj.getPath()
        self.__entryId=self.__reqObj.getValue("entryid")
        self.__entryFile=self.__reqObj.getValue("entryfilename")
        #

    def run(self):
        """  Run update
        """
        map = {}
        #
        pickleFile = os.path.join(self.__sessionPath, self.__entryId + '_coord_pickle.db')
        if os.access(pickleFile, os.F_OK):
            fb = open(pickleFile, 'rb')
            map = pickle.load(fb)
            fb.close()
        #
        dir = self.__reqObj.getDictionary()
        for key,value in dir.items():
            if key.startswith('chainId') or key.startswith('chainNum') or \
               key.startswith('chainRangeNum'):
                if value and value[0]:
                    map[key] = value[0]
                #
            #
        #
        if not map:
            return 'No option selected.'
        #
        text = self.__checkUniqueNumbering(map)
        if text:
            return text
        #
        text = self.__runUpdateScript()
        if text:
            return text
        #
        #return 'Entry ' + self.__entryId + ' updated.'
        return 'OK'

    def __checkUniqueNumbering(self, map):
        self.__writeSelectInfo(map)
        return self.__runCheckScript()

    def __writeSelectInfo(self, map):
        category = DataCategory('update_info')
        category.appendAttribute('key')
        category.appendAttribute('value')
        row = 0
        for key,v in map.items():
            category.setValue(key, 'key', row)
            category.setValue(v, 'value', row)
            row += 1
        #
        container = DataContainer('XXXX')
        container.append(category)
        #
        myDataList = []
        myDataList.append(container)
        #
        filename = os.path.join(self.__sessionPath, self.__entryId + '_select.cif')
        f = open(filename, 'w')
        pdbxW = PdbxWriter(f)
        pdbxW.write(myDataList)
        f.close()

    def __runCheckScript(self):
        """
        """
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(os.path.join(self.__sessionPath, self.__entryId + "_index.cif"))
            dp.addInput(name="select", value=os.path.join(self.__sessionPath, self.__entryId + "_select.cif"))
            dp.op("annot-check-select-number")
            dp.expLog(dstPath=os.path.join(self.__sessionPath, self.__entryId + "_check.log"), appendMode=False)
            dp.cleanup()
            #
            return self.__readLogFile('_check.log', 'Run numbering checking failed')
        except:
            traceback.print_exc(file=self.__lfh)
            error = 'error:' + traceback.format_exc()
            return error
        #

    def __runUpdateScript(self):
        """
        """
        try:
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            dp.imp(os.path.join(self.__sessionPath, self.__entryFile))
            dp.addInput(name="assign", value=os.path.join(self.__sessionPath, self.__entryId + "_select.cif"))
            dp.op("annot-update-molecule")
            dp.exp(os.path.join(self.__sessionPath, self.__entryFile))
            dp.expLog(dstPath=os.path.join(self.__sessionPath, self.__entryId + "_update.log"), appendMode=False)
            dp.cleanup()
            #
            return self.__readLogFile('_update.log', 'Update failed!')
        except:
            traceback.print_exc(file=self.__lfh)
            error = 'error:' + traceback.format_exc()
            return error
        #

    def __readLogFile(self, extension, default_message):
        filename = os.path.join(self.__sessionPath, self.__entryId + extension)
        if os.access(filename, os.F_OK):
            f = open(filename, 'r')
            content = f.read()
            f.close()
            #
            if content.find('Finished!') == -1:
                return default_message + '\n\n' + content
            #
            error = ''
            list = content.split('\n')
            for line in list:
                if not line:
                    continue
                #
                if line == 'Finished!':
                    continue
                #
                error += line + '\n'
            #
            return error
        else:
            return default_message
        #
