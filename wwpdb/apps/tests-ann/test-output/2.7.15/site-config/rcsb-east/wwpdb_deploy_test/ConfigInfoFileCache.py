
import os
import sys
import json
import traceback

class ConfigInfoFileCache(object):
    _configD={'WWPDB_DEPLOY_TEST': {'SITE_NAME': 'RCSB', 'SITE_EXT_DICT_MAP_EMD_FILE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/resources_ro/emd/emd_map_v2.cif', 'VARTEST': 'Hello', 'SITE_PREFIX_LC': 'wwpdb_deploy_test', 'SITE_TEMPDEP_STORAGE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/data', 'DATA_DIR_NAME': 'data', 'RORESOURCE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/resources_ro', 'SITE_EM_DICT_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/resources_ro/emd', 'TEST_MOCKPATH_ENV': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15', 'SITE_REGISTRY_FILE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/resources_ro/actionData.xml', 'SITE_DEPOSIT_STORAGE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/data', 'TEST_FILE_ZLIB': 'TEST-FILE.DAT.Z', 'WWPDB_SITE_LOC': 'rcsb-east', 'TEST_FILE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/MISC', 'DEPLOY_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top', 'SITE_WORKFLOW_STORAGE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/data', 'DATA_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/data', 'DEPUI_RESOURCE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/resources_ro/depui', 'SITE_PREFIX': 'WWPDB_DEPLOY_TEST', 'SITE_DEP_DB_HOST_NAME': 'localhost', 'TEST_FILE_BZIP': 'TEST-FILE.DAT.bz2', 'SITE_ARCHIVE_STORAGE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/data', 'TEST_FILE': 'TEST-FILE.DAT', 'TEST_FILE_GZIP': 'TEST-FILE.DAT.gz', 'RESOURCE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/resources', 'SITE_ACCESS_INFO_FILE_PATH': '/Users/peisach/RCSB/OneDep/py-wwpdb_apps_ann_tasks_v2/wwpdb/apps/tests-ann/test-output/2.7.15/da_top/resources/site_access_info.json', 'TESTVAR1': '1', 'SITE_DEP_DB_DATABASE_NAME': 'status', 'TESTVAR2': '2'}}

    @classmethod
    def getConfigDictionary(cls, siteId):
        try:
            return cls._configD[siteId]
        except:
            return cls.getJsonConfigDictionary(siteId)

    @classmethod
    def getJsonConfigDictionary(cls, siteId):
        try:
            p = os.getenv("TOP_WWPDB_SITE_CONFIG_DIR")
            for l in ['rcsb-east','rcsb-west','pdbj','pdbe']:
                jsonPath = os.path.join(p,l,siteId.lower(),'ConfigInfoFileCache.json')
                if os.access(jsonPath, os.R_OK):
                    with open(jsonPath, "r") as infile:
                        cD = json.load(infile)
                    return cD[siteId]
        except:
            pass
            # traceback.print_exc(file=sys.stderr)

        return {}

    @classmethod
    def getJsonConfigDictionaryPrev(cls, siteId):
        try:
            id = os.getenv("WWPDB_SITE_ID")
            if siteId != id:
                p = os.getenv("TOP_WWPDB_SITE_CONFIG_DIR")
                l = str(os.getenv("WWPDB_SITE_LOC")).lower()
                jsonPath = os.path.join(p,l,siteId.lower(),'ConfigInfoFileCache.json')
                with open(jsonPath, "r") as infile:
                    cD = json.load(infile)
                return cD[siteId]
        except:
            pass
            # traceback.print_exc(file=sys.stderr)

        return {}

        