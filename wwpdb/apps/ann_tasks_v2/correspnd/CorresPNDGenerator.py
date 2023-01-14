##
# File:  CorresPNDGenerator.py
# Date:  09-Oct-2013
# Updates:
##
"""
Parse submitted form and generate correspondence

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2012 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys

#


class CorresPNDGenerator(object):
    """Class responsible for parsing submitted form and generating correspondence"""

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        # self.__verbose = verbose
        # self.__lfh = log
        self.__reqObj = reqObj
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #
        # self.__corres_content = str(self.__reqObj.getValue("full_text"))
        self.__corres_content = self.__encodeUtf8ToCif(self.__reqObj.getValue("full_text"))
        #
        # self.__parseForm()

    def get(self):
        if self.__corres_content:
            entryId = self.__reqObj.getValue("entryid")
            filename = os.path.join(self.__sessionPath, entryId + "_correspondence-to-depositor_P1.txt")
            f = open(filename, "w")
            f.write(self.__corres_content + "\n")
            f.close()
            return "Generated"
        #
        return "No item selected"

    def __encodeUtf8ToCif(self, p_content):
        """Encoding unicode/utf-8 content into cif friendly ascii
        Have to replace any ';' that begin a newline with a ' ;' in order to preserve ; matching required for multiline items
        """
        if sys.version_info[0] < 3:
            return p_content.encode("ascii", "xmlcharrefreplace").replace("\n;", "\n ;").replace("\\xa0", " ")
        else:
            # Coming in as string already - no need to encode to bytes, however, we would like the xml character replacement
            return p_content.encode("ascii", "xmlcharrefreplace").decode("ascii").replace("\n;", "\n ;").replace("\\xa0", " ")

    # def __parseForm(self):
    #     number = int(str(self.__reqObj.getValue("number_question")))
    #     count = 0
    #     for i in range(number):
    #         title = str(self.__reqObj.getValue("question_" + str(i)))
    #         if not title:
    #             continue
    #         #
    #         text = str(self.__reqObj.getValue("text_" + str(i)))
    #         if not text:
    #             continue
    #         #
    #         count += 1
    #         self.__corres_content += "\n" + str(count) + ". "
    #         if not title.startswith("Free text question"):
    #             self.__corres_content += title + "\n\n"
    #         #
    #         self.__corres_content += text + "\n\n"
    #     #
