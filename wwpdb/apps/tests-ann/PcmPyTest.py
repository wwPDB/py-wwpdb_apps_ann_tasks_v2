import os
import pytest
import tempfile

from wwpdb.utils.config.ConfigInfoData import ConfigInfoData
from wwpdb.apps.ann_tasks_v2.pcm.PcmCCDEditorForm import PcmCCDEditorForm


MOCK_SESSIONS_PATH = tempfile.mkdtemp()

@pytest.fixture
def mock_config(monkeypatch):
    mc = {
        "SITE_REFDATA_PROJ_NAME_PRDCC": "",
        "SITE_WEB_APPS_SESSIONS_PATH": MOCK_SESSIONS_PATH,
        "SITE_WEB_APPS_TOP_SESSIONS_PATH": MOCK_SESSIONS_PATH,
        "SITE_REFDATA_PROJ_NAME_CC": "",
        "SITE_CC_DICT_PATH": "",
        "SITE_REFDATA_TOP_CVS_SB_PATH": "",
        "PDBX_DICTIONARY_NAME_DICT": {"DEPOSIT": ""},
        "REFERENCE_PATH": "",
        "SITE_PDBX_DICT_PATH": "",
        "SITE_PACKAGES_PATH": "",
        "SITE_LOCAL_APPS_PATH": "",
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
        os.makedirs(self._session, exist_ok=True)

    def getPath(self):
        return self._session


def test_run_binary(mock_config):
    mock_req = MockReqObj({"display_identifier": "1cbs", "entryid": "1cbs", "entryfilename": "1cbs.cif", "WWPDB_SITE_ID": "WWPDB"})
    pcm_form = PcmCCDEditorForm(reqObj=mock_req, verbose=False)
    open(os.path.join(mock_req.session.getPath(), "1cbs.cif"), "w").close()

    assert pcm_form.run() == True
    assert os.path.exists(os.path.join(mock_req.session.getPath(), "1cbs_ccd_no_pcm_ann.csv"))
    assert os.path.exists(os.path.join(mock_req.session.getPath(), "1cbs_ccd_no_pcm_ann.log"))


def test_get_html_form(mock_config):
    mock_req = MockReqObj({"display_identifier": "1cbs", "entryid": "1cbs", "entryfilename": "1cbs.cif", "WWPDB_SITE_ID": "WWPDB"})
    pcm_form = PcmCCDEditorForm(reqObj=mock_req, verbose=False)

    with open(os.path.join(mock_req.session.getPath(), "1cbs_ccd_no_pcm_ann.csv"), "w") as fp:
        fp.write("Comp_id,Modified_residue_id,Type,Category,Position,Polypeptide_position,Comp_id_linking_atom,Modified_residue_id_linking_atom,First_instance_model_db_code\n")
        fp.write("MLU,missing,missing,missing,missing,missing,.,.,1PN3\n")
        fp.write("OMZ,missing,missing,missing,missing,missing,.,.,1PN3\n")
        fp.write("GHP,missing,missing,missing,missing,missing,.,.,1PN3\n")
        fp.write("BGC,GHP,missing,missing,missing,missing,C1,O4,1PN3\n")
        fp.write("OMY,missing,missing,missing,missing,missing,.,.,1PN3\n")
        fp.write("3FG,missing,missing,missing,missing,missing,.,.,1PN3")

    html_form = pcm_form.getCCDForm()["htmlcontent"]
    assert "MLU" in html_form
    assert "OMZ" in html_form
    assert "GHP" in html_form
    assert "BGC" in html_form
    assert "OMY" in html_form
    assert "3FG" in html_form
