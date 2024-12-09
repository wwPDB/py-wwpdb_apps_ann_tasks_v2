##
# File: CSValidationReportStyle.py
# Date: 7-Dec-2024
#
# Updates:
#
##
"""
Report style details for NMR Chemical Shift Validation.

"""
from __future__ import absolute_import

__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zukang.feng@rcsb.org"
__license__ = "Apache 2.0"

from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class CSValidationReportStyle(PdbxCategoryStyleBase):
    _styleId = "NMR_CHEMICAL_SHIFT_VALIDATION_REPORT_V1"
    _categoryInfo = [
        ("pdbx_nmr_chemical_shift_validation_statistics", "table"),
        ("pdbx_nmr_chemical_shift_not_found_list", "table")
    ]
    _cDict = {
        "pdbx_nmr_chemical_shift_validation_statistics": [
            ("_pdbx_nmr_chemical_shift_validation_statistics.Total number of shifts", "%s", "str", ""),
            ("_pdbx_nmr_chemical_shift_validation_statistics.Number of shifts mapped to atoms", "%s", "str", ""),
            ("_pdbx_nmr_chemical_shift_validation_statistics.Number of unparsed shifts", "%s", "str", ""),
            ("_pdbx_nmr_chemical_shift_validation_statistics.Number of shifts with mapping errors", "%s", "str", ""),
            ("_pdbx_nmr_chemical_shift_validation_statistics.Number of shifts with mapping warnings", "%s", "str", ""),
            ("_pdbx_nmr_chemical_shift_validation_statistics.Number of shifts outliers (ShiftChecker)", "%s", "str", "")
        ],
        "pdbx_nmr_chemical_shift_not_found_list": [
            ("_pdbx_nmr_chemical_shift_not_found_list.Chain", "%s", "str", ""),
            ("_pdbx_nmr_chemical_shift_not_found_list.Res", "%s", "str", ""),
            ("_pdbx_nmr_chemical_shift_not_found_list.Type", "%s", "str", ""),
            ("_pdbx_nmr_chemical_shift_not_found_list.Atom", "%s", "str", "")
        ]
    }

    _excludeList = []
    _suppressList = []
    #

    def __init__(self):
        super(CSValidationReportStyle, self).__init__(
            styleId=CSValidationReportStyle._styleId,
            catFormatL=CSValidationReportStyle._categoryInfo,
            catItemD=CSValidationReportStyle._cDict,
            excludeList=CSValidationReportStyle._excludeList,
            suppressList=CSValidationReportStyle._suppressList,
        )
