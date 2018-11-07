##
# File:  PdbxEntryInfo.py
# Date:  12-June-2014
#
# Updates:
##
"""
Extract and package PDBx general entry info 

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.01"

import os, sys, time, types, string, shutil, traceback


from wwpdb.api.facade.ConfigInfo              import ConfigInfo
from pdbx_v2.pdbx.PdbxIo                      import PdbxEntryInfoIo
from wwpdb.utils.rcsb.PathInfo                import PathInfo


class PdbxEntryInfo(object):
    """Get essential entry info from PDBx model file ... 

    """
    def __init__(self,reqObj,verbose=False,log=sys.stderr):
        """Get essential entry info from PDBx model file ... 

         :param `verbose`:  boolean flag to activate verbose logging.
         :param `log`:      stream for logging.
          
        """
        self.__verbose=verbose
        self.__lfh=log
        self.__debug=False
        #
        self.__reqObj=reqObj
        # 
        self.__sObj=self.__reqObj.newSessionObj()
        self.__sessionPath=self.__sObj.getPath()
        self.__sessionRelativePath=self.__sObj.getRelativePath()        
        self.__sessionId  =self.__sObj.getId()        
        #
        self.__siteId=self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__cI=ConfigInfo(self.__siteId)
        
        #
        self.__idCode=None
        self.__filePath=None
        self.__fileFormat='pdbx'
        #

    def setFilePath(self,idCode=None,fileSource='session',versionId="none"):
        if idCode is not None:
            self.__idCode=str(idCode).upper()
        else:
            return False

        if self.__verbose:
            self.__lfh.write("\n+PdbxEntryInfo.setFilePath() site %s idCode %s session path %s\n" % (self.__siteId,idCode,self.__sessionPath))

        pI=PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        self.__filePath=pI.getModelPdbxFilePath(dataSetId=idCode,wfInstanceId=None,fileSource=fileSource,versionId=versionId,mileStone=None)
        self.__fileFormat='pdbx'

        if self.__verbose:
            self.__lfh.write("\n\n+PdbxEntryInfo.setFilePath() pdbx file path %s\n" % (self.__filePath))
        if (not os.access(self.__filePath,os.R_OK)):
            return False
        #
        return True

    def getFilePath(self):
        return self.__filePath


    def doReport(self,contentType='info'):
        """ Return data object to support the input content type - 
        """
        #
        oD={}
        oD['dataDict']={}        
        filePath   = self.__filePath
        fileFormat = self.__fileFormat
        blockId    = self.__idCode
        #
        if self.__verbose:
            self.__lfh.write("\n\n+PdbxEntryInfo.doReport()  - starting for content type %s \n" % contentType)
            self.__lfh.write("+PdbxEntryInfo.doReport()  format %s file path  %s\n" % (fileFormat,filePath))
            self.__lfh.flush()
        #
        #
        # Path context --
        oD['idCode']=self.__idCode
        oD['filePath']=filePath
        oD['sessionId']=self.__sessionId
        oD['requestHost'] = self.__reqObj.getValue("request_host")                
        #
        try:
            if contentType == 'info':
                pdbxI=PdbxEntryInfoIo(verbose=self.__verbose,log=self.__lfh)
                pdbxI.setFilePath(filePath,idCode=None)
                pdbxI.get()
                oD['blockId']=pdbxI.getCurrentContainerId()
                oD['struct_title']=pdbxI.getStructTitle()
                oD['pdb_id']=pdbxI.getDbCode(dbId='PDB')
                mL=pdbxI.getExperimentalMethods()
                oD['experimental_methods']=','.join(mL)
                statusCode,authReleaseCode,initialDepositionDate,holdCoordinatesDate,coordinatesDate=pdbxI.getStatusDetails()
                oD['status_code']=statusCode
                oD['auth_release_code']=authReleaseCode
                oD['deposit_date']=initialDepositionDate
                oD['hold_coord_date']=holdCoordinatesDate
                oD['coord_date']=coordinatesDate

            elif contentType == 'all':
                if (self.__verbose):
                    self.__lfh.write("+PdbxEntryInfo.doReport() - category name list %r \n" % pdbxR.getStyleCategoryNameList() )
                for catName in pdbxR.getCurrentStyleNameList():
                    oD['dataDict'][catName]=pdbxR.getCategory(catName=catName)
                if (self.__verbose):
                    self.__lfh.write("+PdbxEntryInfo.doReport() - data object built\n")
        except:
            if (self.__verbose):
                traceback.print_exc(file=self.__lfh)
                self.__lfh.write("+PdbxEntryInfo.doReport() - report preparation failed for:  %s\n" % filePath)
                self.__lfh.flush()                            

        return oD

if __name__ == '__main__':
    pass
