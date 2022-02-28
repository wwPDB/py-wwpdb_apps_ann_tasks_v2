import sys
import os
import platform

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)

# We do this here - as unittest loads all at once - need to insure common

try:
    from unittest.mock import Mock, MagicMock
except ImportError:
    from mock import Mock, MagicMock

configInfo = {
    "SITE_REFDATA_PROJ_NAME_CC": "ligand-dict-v3",
    "SITE_WEB_APPS_TOP_SESSIONS_PATH": TESTOUTPUT,
    # "REFERENCE_PATH": os.path.join(HERE, "data"),
}

configInfoMockConfig = {
    "return_value": configInfo,
}

configMock = MagicMock(**configInfoMockConfig)


def getSiteIdReplace(defaultSiteId=None):  # pylint: disable=unused-argument
    return "WWPDB_DEPLOY"


# Returns a dictionary by default - which has a get operator
sys.modules["wwpdb.utils.config.ConfigInfo"] = Mock(ConfigInfo=configMock, getSiteId=getSiteIdReplace)


# ConfigInfoAppCommon
class ConfigInfoAppReplace(object):
    def __init__(self, siteId=None):
        pass

    def get_site_cc_dict_path(self):
        return os.path.join(TESTOUTPUT, "cc-dict")

    def get_cc_index(self):
        return os.path.join(self.get_site_cc_dict_path(), "chemcomp-index.pic")

    def get_site_refdata_top_cvs_sb_path(self):
        return os.path.join(HERE, "data", "components")

    def get_site_cc_cvs_path(self):
        return os.path.join(self.get_site_refdata_top_cvs_sb_path(), "ligand-dict-v3")

    def get_cc_dict(self):
        return os.path.join(self.get_site_cc_dict_path(), "Components-all-v3.cif")

    def get_cc_path_list(self):
        return os.path.join(self.get_site_cc_dict_path(), "PATHLIST-v3")

    def get_cc_id_list(self):
        return os.path.join(self.get_site_cc_dict_path(), "IDLIST-v3")

    def get_cc_dict_serial(self):
        return os.path.join(self.get_site_cc_dict_path(), "Components-all-v3.sdb")

    def get_cc_dict_idx(self):
        return os.path.join(self.get_site_cc_dict_path(), "Components-all-v3-r4.idx")

    def get_cc_db(self):
        return os.path.join(self.get_site_cc_dict_path(), "chemcomp_v3.db")

    def get_cc_parent_index(self):
        return os.path.join(self.get_site_cc_dict_path(), "chemcomp-parent-index.pic")

    def get_site_prdcc_cvs_path(self):
        return os.path.join(self.get_site_refdata_top_cvs_sb_path(), "prdcc")

    def get_site_prd_dict_path(self):
        return os.path.join(self.get_site_refdata_top_cvs_sb_path(), "prd-dict")

    def get_prd_dict_file(self):
        return os.path.join(self.get_site_prd_dict_path(), "Prd-all-v3.cif")

    def get_prd_dict_serial(self):
        return os.path.join(self.get_site_prd_dict_path(), "Prd-all-v3.sdb")

    def get_prd_cc_file(self):
        return os.path.join(self.get_site_prd_dict_path(), "Prdcc-all-v3.cif")

    def get_prd_cc_serial(self):
        return os.path.join(self.get_site_prd_dict_path(), "Prdcc-all-v3.sdb")

    def get_prd_summary_cif(self):
        return os.path.join(self.get_site_prd_dict_path(), "prd_summary.cif")

    def get_prd_summary_sdb(self):
        return os.path.join(self.get_site_prd_dict_path(), "prd_summary.sdb")

    def get_prd_family_mapping(self):
        return os.path.join(self.get_site_prd_dict_path(), "PrdFamilyIDMapping.lst")


sys.modules["wwpdb.utils.config.ConfigInfoApp"] = Mock(ConfigInfoAppCommon=ConfigInfoAppReplace)
