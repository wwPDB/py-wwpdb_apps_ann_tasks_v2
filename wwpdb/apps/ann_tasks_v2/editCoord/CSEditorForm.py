##
# File:  CSEditorForm.py
# Date:  04-Agu-2015
# Update:
##
"""
Manage the generating chemical shift editor form

"""
__docformat__ = "restructuredtext en"
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import sys,os.path,os,traceback

from wwpdb.utils.config.ConfigInfo    import ConfigInfo

class CSEditorForm(object):
    """
     The CSEditorForm class generates chemical shift editor form.

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
        pickleFile = os.path.join(self.__sessionPath, self.__entryId + '_cs_pickle.db')
        if os.access(pickleFile, os.F_OK):
            os.remove(pickleFile)
        #

    def get(self):
        """  Get chemical shift editor form
        """
        myD = {}
        #
        coordFile = os.path.join(self.__sessionPath, self.__entryFile)
        if not os.access(coordFile, os.F_OK):
            myD['htmlcontent'] = 'No chemical shift file uploaded'
            return myD
        #
        self.__runScript()
        #
        myD['htmlcontent'] = self.__getHtmlcontent()
        return myD

    def __runScript(self):
        script = os.path.join(self.__sessionPath, self.__entryId + '_cs_script.csh')
        f = file(script, 'w')
        f.write('#!/bin/tcsh -f\n')
        f.write('#\n')
        f.write('setenv RCSBROOT   ' + self.__cI.get('SITE_ANNOT_TOOLS_PATH') + '\n')
        f.write('setenv COMP_PATH  ' + self.__cI.get('SITE_CC_CVS_PATH') + '\n')
        f.write('setenv BINPATH  ${RCSBROOT}/bin\n')
        f.write('#\n')
        f.write('${BINPATH}/depict_chemical_shift -input ' + self.__entryFile + \
                ' -output ' + self.__entryId + '_cs_html.txt ' + \
                ' -log ' + self.__entryId + '_cs_summary.log\n')
        f.write('#\n')
        f.close()
        cmd = 'cd ' + self.__sessionPath + '; chmod 755 ' + self.__entryId + '_cs_script.csh; ' \
            + ' ./' + self.__entryId + '_cs_script.csh >& cs_summary_log'
        os.system(cmd)

    def __getHtmlcontent(self):
        content = 'No result found!'
        filename = os.path.join(self.__sessionPath, self.__entryId + '_cs_html.txt')
        if os.access(filename, os.F_OK):
            f = file(filename, 'r')
            content = f.read()
            f.close()
        #
        return content
