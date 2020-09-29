##
# File: PdbxXrayExpReportCategoryStyle.py
# Date: 1-Jan-2014
#
# Updates:
#   5-Mar-2018  jdw Py2-Py3 and refactor for Python Packaging
#
##
"""
Report style details for PDBx X-ray experimental validation data categories.

"""
from __future__ import absolute_import
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



from mmcif_utils.style.PdbxCategoryStyleBase import PdbxCategoryStyleBase


class PdbxXrayExpReportCategoryStyle(PdbxCategoryStyleBase):
    _styleId = "PDBX_DCC_REPORT_V1"
    _categoryInfo = [
        ('pdbx_density', 'table'),
        ('pdbx_density_corr', 'table'),
        ('pdbx_dcc_software', 'table'),
        ('pdbx_dcc_sf', 'table'),
        ('pdbx_rscc_mapman_overall', 'table'),
        ('pdbx_rscc_mapman', 'table'),
    ]
    _cDict = {
        'pdbx_rscc_mapman': [
            ('_pdbx_rscc_mapman.model_id', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.pdb_id', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.auth_asym_id', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.auth_comp_id', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.auth_seq_id', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.label_alt_id', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.label_ins_code', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.correlation', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.real_space_R', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.real_space_Zscore', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.Biso_mean', '%s', 'str', ''),
            ('_pdbx_rscc_mapman.occupancy_mean', '%s', 'str', '')
        ],
        'pdbx_rscc_mapman_overall': [
            ('_pdbx_rscc_mapman_overall.correlation', '%s', 'str', ''),
            ('_pdbx_rscc_mapman_overall.correlation_sigma', '%s', 'str', ''),
            ('_pdbx_rscc_mapman_overall.real_space_R', '%s', 'str', ''),
            ('_pdbx_rscc_mapman_overall.real_space_R_sigma', '%s', 'str', '')
        ],
        'pdbx_density': [
            ('_pdbx_density.error', '%s', 'str', ''),
        ],
        'pdbx_density_corr': [
            ('_pdbx_density_corr.ordinal', '%s', 'str', ''),
            ('_pdbx_density_corr.program', '%s', 'str', ''),
            ('_pdbx_density_corr.ls_d_res_high', '%s', 'str', ''),
            ('_pdbx_density_corr.ls_d_res_low', '%s', 'str', ''),
            ('_pdbx_density_corr.ls_R_factor_R_all', '%s', 'str', ''),
            ('_pdbx_density_corr.ls_R_factor_R_work', '%s', 'str', ''),
            ('_pdbx_density_corr.ls_R_factor_R_free', '%s', 'str', ''),
            ('_pdbx_density_corr.ls_number_reflns_obs', '%s', 'str', ''),
            ('_pdbx_density_corr.ls_percent_reflns_obs', '%s', 'str', ''),
            ('_pdbx_density_corr.ls_number_reflns_R_free', '%s', 'str', ''),
            ('_pdbx_density_corr.correlation_coeff_Fo_to_Fc', '%s', 'str', ''),
            ('_pdbx_density_corr.real_space_R', '%s', 'str', ''),
            ('_pdbx_density_corr.correlation', '%s', 'str', ''),
            ('_pdbx_density_corr.details', '%s', 'str', '')
        ],
        'pdbx_dcc_software': [
            ('_pdbx_dcc_software.ordinal', '%s', 'str', ''),
            ('_pdbx_dcc_software.name', '%s', 'str', ''),
            ('_pdbx_dcc_software.version', '%s', 'str', ''),
            ('_pdbx_dcc_software.description', '%s', 'str', '')
        ],
        'pdbx_dcc_sf': [
            ('_pdbx_dcc_sf.id', '%s', 'str', ''),
            ('_pdbx_dcc_sf.section_id', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_obs', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_R_work', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_R_free', '%s', 'str', ''),
            ('_pdbx_dcc_sf.percent_reflns_R_free', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_friedel_pair_F', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_F_plus', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_F_minus', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_F_all', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_friedel_pair_I', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_I_plus', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_I_minus', '%s', 'str', ''),
            ('_pdbx_dcc_sf.number_reflns_I_all', '%s', 'str', '')
        ]
    }

    _excludeList = []
    _suppressList = []
    #

    def __init__(self):
        super(PdbxXrayExpReportCategoryStyle, self).__init__(styleId=PdbxXrayExpReportCategoryStyle._styleId,
                                                             catFormatL=PdbxXrayExpReportCategoryStyle._categoryInfo,
                                                             catItemD=PdbxXrayExpReportCategoryStyle._cDict,
                                                             excludeList=PdbxXrayExpReportCategoryStyle._excludeList,
                                                             suppressList=PdbxXrayExpReportCategoryStyle._suppressList)
