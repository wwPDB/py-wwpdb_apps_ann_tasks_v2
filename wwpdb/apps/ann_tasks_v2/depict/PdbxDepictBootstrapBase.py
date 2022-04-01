##
# File:  PdbxDepictBootstrapBase.py
# Date:  18-Feb-2013
#
# Updates:
#
# 17-Jul-2013 jdw  revised to encapsulate full page conent - w/ container-fluid
#
##
"""
Base class for HTML depictions containing common constructs using required
by BootStrap framework.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.02"

import os
import sys


class PdbxDepictBootstrapBase(object):
    """Base class for HTML depictions contain definitions of common constructs
    using HTML5 and Bootstrap CSS -

    """

    def __init__(self, includePath=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        """

        :param `verbose`:  boolean flag to activate verbose logging.
        :param `log`:      stream for logging.

        """
        self.__includePath = includePath
        # self.__verbose = verbose
        # self.__lfh = log
        # self.__debug = True
        #
        # Within the <head></head> section
        self.__includeHeadList = ["head_common_bs.html"]
        #
        # Just after <body>  -- Typically the definition of any top nav menu
        self.__includeTopList = ["page_header_minimum_menu_bs.html"]
        #
        #
        # Just before </body>
        self.__includeBottomList = ["page_footer_bs.html"]
        #
        self.__includeJavaScriptList = ["page_javascript_bs.html"]
        #
        self.__meta = r"""<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />"""

    #
    def appDocType(self):
        return "<!DOCTYPE html>"

    def appMetaTags(self):
        return self.__meta

    def appPageTop(self, title=None):
        """Return the application specific top of page boiler plate -"""
        oL = []
        oL.append("<!DOCTYPE html>")
        oL.append('<html lang="en"')
        oL.append("<head>")

        try:
            for fn in self.__includeHeadList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        #
        if title is not None:
            oL.append("<title>%s</title>" % title)

        #
        oL.append("</head>")
        #
        oL.append("<body>")
        try:
            for fn in self.__includeTopList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        oL.append('<div class="container-fluid"> <!-- start application container -->')
        oL.append("<!-- Application content begins here -->")

        return oL

    def appPageBottom(self):
        """Return the application specific bottom of page boiler plate -

        </div> <!-- end container -->
        <!--#include virtual="includes/page_footer.html"-->
        <!--#include virtual="includes/page_javascript_bs.html"-->
        </body>
        </html>

        """
        oL = []
        oL.append("</div> <!-- end application container -->")

        try:
            for fn in self.__includeBottomList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        try:
            for fn in self.__includeJavaScriptList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        oL.append("</body>")
        oL.append("</html>")
        return oL
