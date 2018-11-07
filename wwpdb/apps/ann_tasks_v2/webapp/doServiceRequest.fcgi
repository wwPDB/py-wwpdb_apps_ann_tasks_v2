#!/opt/wwpdb/bin/python 
#
# File:     doServiceRequest.fcgi
# Created:  22-Feb-2014
#
# Updated:
#   04-Mar-2014 jdw Take the last parameter of the request  -- do not concatenate for now --
#    5-Jul-2014 jdw add support for attachments and compression 
#
##
"""
This top-level responder for requests to /services/.... for annotation, review, 
and status update tasks

This version depends on FCGID or FASTCGI and WebOb.

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import sys,os,traceback

from wwpdb.utils.rcsb.fcgi  import WSGIServer
from webob import Request, Response

from wwpdb.apps.ann_tasks_v2.webapp.AnnTasksWebApp import AnnTasksWebApp


class MyRequestApp(object):
    """  Handle server interaction using FASTCGI/WSGI and WebOb Request
         and Response objects.
    """
    def __init__(self,textString="default init",verbose=False,log=sys.stderr):
        """ 
        """
        self.__text=textString
        self.__verbose=verbose
        self.__debug=False
        self.__lfh=log
        self.__myParameterDict={}
        self.__siteId=None        
        #
        
    def __dumpEnv(self,request):
        outL=[]
        #outL.append('<pre align="left">')
        outL.append("\n------------------doServiceRequest(__dumpEnv())------------------------------\n")
        outL.append("Web server request data content:\n")                
        outL.append("Text initialization:   %s\n" % self.__text)        
        try:
            outL.append("Host:         %s\n" % request.host)
            outL.append("Path:         %s\n" % request.path)
            outL.append("Method:       %s\n" % request.method)        
            outL.append("Query string: %s\n" % request.query_string)
            outL.append("Parameter List:\n")
            for name,value in request.params.items():
                outL.append("Request parameter:    %s:  %r\n" % (name,value))
        except:
            traceback.print_exc(file=self.__lfh)            

        outL.append("\n------------------------------------------------\n\n")
        #outL.append("</pre>")
        return outL

    def __call__(self, environment, responseApplication):
        """          Request callable entry point

        """
        myRequest  = Request(environment)
        #
        self.__myParameterDict={}   
        try:
            if environment.has_key('WWPDB_SITE_ID'):
                self.__siteId=environment['WWPDB_SITE_ID']
                if (self.__debug):
                    self.__lfh.write("+MyRequestApp.__call__() - WWPDB_SITE_ID:  %s\n" % self.__siteId)
            #
            if (self.__debug):
                for name,value in environment.items():
                    self.__lfh.write("+MyRequestApp.__call__() - request environment:    %s:  %r\n" % (name,value))
            
            for name,value in myRequest.params.items():
                if (not self.__myParameterDict.has_key(name)):
                    self.__myParameterDict[name]=[]
                # change overwrite be
                #self.__myParameterDict[name].append(value)
                self.__myParameterDict[name]=[value]
                #
            self.__myParameterDict['request_path']=[myRequest.path.lower()]
            if environment.has_key('HTTP_HOST'):            
                self.__myParameterDict['request_host']=[environment['HTTP_HOST']]
            else:
                self.__myParameterDict['request_host']=['']
            for ky in ['SITE_DA_INTERNAL_DB_USER','SITE_DA_INTERNAL_DB_PASSWORD','SITE_DA_INTERNAL_DB_SOCKET']:
                if environment.has_key(ky):
                    self.__myParameterDict[ky] = [environment[ky]]
                else:
                    self.__myParameterDict[ky] = ''                    
        except:
            self.__lfh.write("+MyRequestApp.__call__() - Exception processing in request setup\n")            
            traceback.print_exc(file=self.__lfh)

        if (self.__debug):
            self.__lfh.write("+MyRequestApp.__call__() - contents of request data\n")
            self.__lfh.write("%s" % ("\n".join(self.__dumpEnv(request=myRequest))))
            for k,v in self.__myParameterDict.items():
                self.__lfh.write("+MyRequestApp.__call__() - parameter dict:    %s:  %r\n" % (k,v))                
            
        ###
        ### At this point we have everything needed from the request !
        ###
        myResponse = Response()
        ##
        ## Default return type and status
        ##
        myResponse.status       = '200 OK'
        myResponse.content_type = 'text/html'       
        ###
        ###  Application specific functionality called here --
        ###
        seqT= AnnTasksWebApp(parameterDict=self.__myParameterDict,verbose=self.__verbose, log=self.__lfh,siteId=self.__siteId)
        rspD=seqT.doOp()
        myResponse.content_type=rspD['CONTENT_TYPE']
        myResponse.body=rspD['RETURN_STRING']
        if rspD.has_key('ENCODING'):
            myResponse.content_encoding=rspD['ENCODING']
        if rspD.has_key('DISPOSITION'):
            myResponse.content_disposition=rspD['DISPOSITION']

        if (self.__debug):
            self.__lfh.write("+MyRequestApp.__call__() - Response content_type %r \n" % rspD['CONTENT_TYPE'])
            self.__lfh.write("+MyRequestApp.__call__() - Response body  %r \n" % rspD['RETURN_STRING'])                
        
        ####
        ###
        return myResponse(environment,responseApplication)
##
WSGIServer(MyRequestApp(textString="doServiceRequest()",verbose=True,log=sys.stderr)).run()
#













