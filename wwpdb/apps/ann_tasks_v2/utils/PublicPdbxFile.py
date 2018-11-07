##
# File:  PublicPdbxFile.py
# Date:  14-Oct-2013
#
# Update:
# 28-Feb -2014  jdw Add base class 
# 4-Jun-2014    jdw Added V4 dictionary argument --
##
"""
Generate public pdbx cif file.

"""
__docformat__ = "restructuredtext en"
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import sys,os.path,os,traceback

from wwpdb.api.facade.ConfigInfo    import ConfigInfo
from wwpdb.apps.ann_tasks_v2.utils.SessionWebDownloadUtils import SessionWebDownloadUtils

class PublicPdbxFile(SessionWebDownloadUtils):
    """ The PublicPdbxFile class encapsulates conversion internal pdbx cif to public pdbx cif file.
    """
    def __init__(self,reqObj=None,verbose=False,log=sys.stderr):
        super(PublicPdbxFile,self).__init__(reqObj=reqObj,verbose=verbose,log=log)
        self.__verbose=verbose
        self.__lfh=log
        self.__reqObj=reqObj
        self.__setup()
        
    def __setup(self):
        self.__siteId=self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__cI=ConfigInfo(self.__siteId)
        self.__sObj=self.__reqObj.getSessionObj()
        self.__sessionId=self.__sObj.getId()
        self.__sessionPath=self.__sObj.getPath()
        #

    def run(self,entryId,inpFile): 
        """  Run conversion.
        """
        try:
            inpPath=os.path.join(self.__sessionPath,inpFile)
            logPath=os.path.join(self.__sessionPath,entryId+"-public_cif.log")
            retPath=os.path.join(self.__sessionPath,entryId+"_model-review_P1.cif")
            #
            script = os.path.join(self.__sessionPath, entryId + '_pub_pdbx.csh')
            f = file(script, 'w')
            f.write('#!/bin/tcsh -f\n')
            f.write('#\n')
            f.write('setenv DICPATH ' + self.__cI.get('SITE_PDBX_DICT_PATH') + '\n')
            f.write('setenv BINPATH ' + self.__cI.get('SITE_PACKAGES_PATH') + '/dict/bin\n')
            f.write('#\n')
            f.write('set dict = "'   + self.__cI.get('SITE_PDBX_DICT_NAME')    + '.sdb"\n')
            f.write('set dictV4 = "' + self.__cI.get('SITE_PDBX_V4_DICT_NAME') + '.sdb"\n')        
            f.write('set exchprog = "cifexch2"\n')
            f.write('#\n')
            f.write('${BINPATH}/${exchprog} -dicSdb ${DICPATH}/${dict}  -pdbxDicSdb ${DICPATH}/${dictV4}  -reorder -strip -op in ' + \
                    '-pdbids -input ' + inpFile + ' -output ' + entryId + '_model-review_P1.cif\n') 
            f.write('#\n')
            f.close()
            cmd = 'cd ' + self.__sessionPath + '; chmod 755 ' + entryId + '_pub_pdbx.csh; ' \
                + './' + entryId + '_pub_pdbx.csh >& pub_pdbx_log'
            os.system(cmd)
            self.addDownloadPath(retPath)
            self.addDownloadPath(logPath)            
            #
            return True
        except:
            traceback.print_exc(file=self.__lfh)
            return False

