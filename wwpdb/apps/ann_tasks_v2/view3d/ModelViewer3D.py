##
# File:  ModelViewer3D.py
# Date:  20-April-2012  J. Westbrook
#
# Update:
# 2-Dec-2013  Updated with to latest JMOL using signed applet --
#
##
"""
Utility methods model and map 3d visualization.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys


class ModelViewer3D(object):
    """
    ModelViewer3D class encapsulates depiction of coordinate models and maps.

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__modelPathRel = ""
        self.__mapPathRel = ""
        self.__setup()

    def __setup(self):
        pass

    def setModelRelativePath(self, modelPath):
        self.__modelPathRel = modelPath

    def setMapRelativePath(self, mapPath):
        self.__mapPathRel = mapPath

    def getLaunchJmolHtml(self):
        setupCmds = "background black; wireframe only; wireframe 0.15; labels off; slab 100; depth 40; slab on;"

        htmlL = []
        # htmlL.append('<applet name="jmolApplet0" id="jmolApplet0" code="JmolApplet" archive="JmolApplet0.jar" codebase="/applets/jmol" mayscript="true" height="90%" width="90%">')
        htmlL.append(
            '<applet name="jmolApplet0" id="jmolApplet0" code="JmolApplet" archive="JmolAppletSigned0.jar" codebase="/applets/jmol-latest/jsmol/java" mayscript="true" height="100%" width="100%">'  # noqa:E501
        )
        htmlL.append('<param name="progressbar" value="true">')
        htmlL.append('<param name="progresscolor" value="blue">')
        htmlL.append('<param name="boxbgcolor" value="white">')
        htmlL.append('<param name="boxfgcolor" value="black">')
        htmlL.append('<param name="boxmessage" value="Downloading JmolApplet ...">')

        htmlL.append('<param name="script" value="load %s; %s">' % (self.__modelPathRel, setupCmds))
        htmlL.append("</applet>")
        return str("".join(htmlL))

    def getLaunchJmolWithMapHtml(self):
        # setupCmds=" background black; wireframe only; wireframe 0.05; labels off; slab 100; depth 40; slab on; "
        # setupCmds=" background black; wireframe only; wireframe 0.05; labels off; slab 100; depth 40; slab on; "
        setupCmds = " background black; wireframe only; wireframe 0.05; labels off; slab 50; depth 20; slab on; "
        setupCmds += " isosurface surf_15 color [x3050F8] sigma 1.5 within 2.0 {*} '%s' mesh nofill; " % self.__mapPathRel

        htmlL = []
        # htmlL.append('<applet name="jmolApplet0" id="jmolApplet0" code="JmolApplet" archive="JmolApplet0.jar" codebase="/applets/jmol" mayscript="true" height="100%" width="100%">')
        htmlL.append(
            '<applet name="jmolApplet0" id="jmolApplet0" code="JmolApplet" archive="JmolAppletSigned0.jar" codebase="/applets/jmol-latest/jsmol/java" mayscript="true" height="100%" width="100%">'  # noqa: E501
        )
        htmlL.append('<param name="progressbar" value="true">')
        htmlL.append('<param name="progresscolor" value="blue">')
        htmlL.append('<param name="boxbgcolor" value="white">')
        htmlL.append('<param name="boxfgcolor" value="black">')
        htmlL.append('<param name="boxmessage" value="Downloading JmolApplet ...">')

        htmlL.append('<param name="script" value="load %s; %s">' % (self.__modelPathRel, setupCmds))
        htmlL.append("</applet>")
        tS = str("".join(htmlL))
        if self.__verbose:
            self.__lfh.write("ModelViewer3D.getLaunchJmolWithMapHtml() markup %s\n" % tS)
        return tS

    def getLaunchAstexHtml(self):
        astexScript = r"""
        background '0x000000';
        set symmetry off;
        molecule load mol '%s';
        display spheres off all;         display cylinders off all;         display sticks off all;
        display lines on all;
        color_by_atom;
        object display 'mol_schematic' on;
        """

        setupCmds = astexScript % self.__modelPathRel
        htmlL = []
        htmlL.append('<applet   id="astexviewer"    name="astexviewer" width="90%" height="90%" code="MoleculeViewerApplet.class" archive="/applets/astex/OpenAstexViewer.jar">')

        htmlL.append('<param name="script" value="%s">' % setupCmds)
        htmlL.append("</applet>")
        return str("".join(htmlL))

    def astexControls(self):
        oL = []
        oL.append('<form name="appletcontrols" onsubmit="return false">')
        oL.append('<input  name="avdisplaystyle" checked="checked"  onClick="av_wireframe(this)"  type="radio">Wireframe')
        oL.append('<input  name="avdisplaystyle"                    onClick="av_sticks(this)"     type="radio">Sticks')
        oL.append("</form>")
        return oL

    def launch2(self):
        htmlL = []
        htmlL.append('<script type="text/javascript">')
        htmlL.append('jmolApplet(300, "load %s");' % self.__modelPathRel)
        htmlL.append("</script>")
        return htmlL
