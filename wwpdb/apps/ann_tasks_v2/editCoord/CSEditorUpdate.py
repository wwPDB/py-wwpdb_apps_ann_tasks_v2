##
# File:  CSEditorUpdate.py
# Date:  04-Aug-2015
# Update:
##
"""
Update chemical shift cif file

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

from wwpdb.api.facade.ConfigInfo    import ConfigInfo
from pdbx.writer.PdbxWriter         import PdbxWriter
from pdbx.reader.PdbxContainers     import *

class CSEditorUpdate(object):
    """
     The CSEditorUpdate class updates chemical shift cif file.

    """
    def __init__(self,reqObj=None,verbose=False,log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        #
        self.__setup()

    def __setup(self):
        self.__siteId=self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__cI=ConfigInfo(self.__siteId)
        self.__sObj=self.__reqObj.getSessionObj()
        self.__sessionId=self.__sObj.getId()
        self.__sessionPath=self.__sObj.getPath()
        self.__entryId=self.__reqObj.getValue("entryid")
        self.__entryFile=self.__reqObj.getValue("entrycsfilename")
        #

    def run(self):
        """  Run update
        """
        map = {}
        #
        pickleFile = os.path.join(self.__sessionPath, self.__entryId + '_cs_pickle.db')
        if os.access(pickleFile, os.F_OK):
            fb = open(pickleFile, 'rb')
            map = pickle.load(fb)
            fb.close()
        #
        dir = self.__reqObj.getDictionary()
        for key,value in dir.items():
            if key.startswith('RangeNum') or key.startswith('RangeCID'):
                if value and value[0]:
                    map[key] = value[0]
                #
            #
        #
        if not map:
            return 'No option selected.'
        #
        self.__writeSelectInfo(map)
        text = self.__runUpdateScript()
        if text:
            return text
        #
        return 'OK'

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
        filename = os.path.join(self.__sessionPath, self.__entryId + '_cs_select.cif')
        f = file(filename, 'w')
        pdbxW = PdbxWriter(f)
        pdbxW.write(myDataList)
        f.close()

    def __runUpdateScript(self):
        script = os.path.join(self.__sessionPath, self.__entryId + '_cs_update.csh')
        f = file(script, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('#\n')
        f.write('setenv RCSBROOT   ' + self.__cI.get('SITE_ANNOT_TOOLS_PATH') + '\n')
        f.write('setenv COMP_PATH  ' + self.__cI.get('SITE_CC_CVS_PATH') + '\n')
        f.write('setenv BINPATH  ${RCSBROOT}/bin\n')
        f.write('#\n')
        f.write('${BINPATH}/edit_chemical_shift -input ' + self.__entryFile + \
                ' -assign ' + self.__entryId + '_cs_select.cif ' + \
                ' -output ' + self.__entryFile + \
                ' -log ' + self.__entryId + '_cs_update.log\n')
        f.write('#\n')
        f.close()
        cmd = 'cd ' + self.__sessionPath + '; chmod 755 ' + self.__entryId + '_cs_update.csh; ' \
            + './' + self.__entryId + '_cs_update.csh >& cs_update_log'
        os.system(cmd)
        #
        return self.__readLogFile('_cs_update.log', 'Update failed!')

    def __readLogFile(self, extension, default_message):
        filename = os.path.join(self.__sessionPath, self.__entryId + extension)
        if os.access(filename, os.F_OK):
            f = file(filename, 'r')
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
