"""
Report style details for PDBx struct_conn category.

"""

from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class PdbxLinksReportCategoryStyle(PdbxCategoryStyleBase):
    _styleId = "PDBX_LINKS_REPORT_V1"
    _categoryInfo = [
        ("struct_conn", "table"),
    ]
    _cDict = {
        "struct_conn": [
            ("_struct_conn.id", "%s", "str", ""),
            ("_struct_conn.pdbx_leaving_atom_flag", "%s", "str", ""),
            ("_struct_conn.ptnr1_auth_asym_id", "%s", "str", ""),
            ("_struct_conn.ptnr1_auth_comp_id", "%s", "str", ""),
            ("_struct_conn.ptnr1_auth_seq_id", "%s", "str", ""),
            ("_struct_conn.ptnr1_symmetry", "%s", "str", ""),
            ("_struct_conn.pdbx_ptnr1_label_alt_id", "%s", "str", ""),
            ("_struct_conn.pdbx_ptnr1_PDB_ins_code", "%s", "str", ""),
            ("_struct_conn.ptnr2_auth_asym_id", "%s", "str", ""),
            ("_struct_conn.ptnr2_auth_comp_id", "%s", "str", ""),
            ("_struct_conn.ptnr2_auth_seq_id", "%s", "str", ""),
            ("_struct_conn.ptnr2_symmetry", "%s", "str", ""),
            ("_struct_conn.pdbx_ptnr2_label_alt_id", "%s", "str", ""),
            ("_struct_conn.pdbx_ptnr2_PDB_ins_code", "%s", "str", ""),
            ("_struct_conn.pdbx_dist_value", "%s", "str", ""),
        ],
    }
    _excludeList = []
    _suppressList = []
    #

    def __init__(self):
        super(PdbxLinksReportCategoryStyle, self).__init__(
            styleId=PdbxLinksReportCategoryStyle._styleId,
            catFormatL=PdbxLinksReportCategoryStyle._categoryInfo,
            catItemD=PdbxLinksReportCategoryStyle._cDict,
            excludeList=PdbxLinksReportCategoryStyle._excludeList,
            suppressList=PdbxLinksReportCategoryStyle._suppressList,
        )
