import os
import pytest
import tempfile
import debugpy

from wwpdb.utils.config.ConfigInfoData import ConfigInfoData
from wwpdb.apps.ann_tasks_v2.pcm.PcmCCDEditorForm import PcmCCDEditorForm


MOCK_SESSIONS_PATH = tempfile.mkdtemp()

@pytest.fixture
def mock_config(monkeypatch):
    mc = {
        "SITE_WEB_APPS_SESSIONS_PATH": MOCK_SESSIONS_PATH,
        "SITE_WEB_APPS_TOP_SESSIONS_PATH": MOCK_SESSIONS_PATH,
        "SITE_REFDATA_PROJ_NAME_CC": "",
        "SITE_REFDATA_PROJ_NAME_PRDCC": "",
        "PDBX_DICTIONARY_NAME_DICT": {"DEPOSIT": ""},
        "REFERENCE_PATH": "",
        "SITE_PDBX_DICT_PATH": "",
        # "CONTENT_TYPE_DICTIONARY": {'foo': (['json'], 'foo'), 'model': (['pdbx', 'pdb', 'pdbml', 'cifeps'], 'model')},
        # "FILE_FORMAT_EXTENSION_DICTIONARY": {'json': 'foo', 'pdbx': 'cif'}
    }

    monkeypatch.setattr(ConfigInfoData, "getConfigDictionary", lambda s: mc)


class MockReqObj:
    def __init__(self, values):
        self.values = values
        self.session = MockSessionObj()

    def getValue(self, key):
        return self.values.get(key)

    def getSessionObj(self):
        # Return a mock session object
        return self.session


class MockSessionObj:
    def __init__(self) -> None:
        self._session = os.path.join(MOCK_SESSIONS_PATH, "mock_session")
        os.mkdir(self._session)

    def getPath(self):
        return self._session


def test_read_csv(mock_config):
    mock_req = MockReqObj({"display_identifier": "1cbs", "entryid": "1cbs", "entryfilename": "1cbs.cif", "WWPDB_SITE_ID": "WWPDB"})
    pcm_form = PcmCCDEditorForm(reqObj=mock_req, verbose=False)
    open(os.path.join(mock_req.session.getPath(), "1cbs.cif"), "w").close()

    assert pcm_form.run() == True
    assert os.path.exists(os.path.join(mock_req.session.getPath(), "1cbs_ccd_no_pcm_ann.csv"))
    assert os.path.exists(os.path.join(mock_req.session.getPath(), "1cbs_ccd_no_pcm_ann.log"))

