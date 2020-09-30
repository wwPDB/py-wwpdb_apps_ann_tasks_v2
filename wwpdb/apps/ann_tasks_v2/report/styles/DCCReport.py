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
            ('_pdbx_density.DCC_version', '%s', 'str', ''),
            ('_pdbx_density.error', '%s', 'str', ''),
            ('_pdbx_density.iso_B_value_type', '%s', 'str', ''),
            ('_pdbx_density.pdbtype', '%s', 'str', ''),
            ('_pdbx_density.unit_cell', '%s', 'str', ''),
            ('_pdbx_density.space_group_name_H-M', '%s', 'str', ''),
            ('_pdbx_density.space_group_pointless', '%s', 'str', ''),
            ('_pdbx_density.ls_d_res_high', '%s', 'str', ''),
            ('_pdbx_density.R_value_R_work', '%s', 'str', ''),
            ('_pdbx_density.R_value_R_free', '%s', 'str', ''),
            ('_pdbx_density.working_set_count', '%s', 'str', ''),
            ('_pdbx_density.free_set_count', '%s', 'str', ''),
            ('_pdbx_density.occupancy_min', '%s', 'str', ''),
            ('_pdbx_density.occupancy_max', '%s', 'str', ''),
            ('_pdbx_density.occupancy_mean', '%s', 'str', ''),
            ('_pdbx_density.Biso_min', '%s', 'str', ''),
            ('_pdbx_density.Biso_max', '%s', 'str', ''),
            ('_pdbx_density.Biso_mean', '%s', 'str', ''),
            ('_pdbx_density.B_wilson', '%s', 'str', ''),
            ('_pdbx_density.B_wilson_scale', '%s', 'str', ''),
            ('_pdbx_density.mean_I2_over_mean_I_square', '%s', 'str', ''),
            ('_pdbx_density.mean_F_square_over_mean_F2', '%s', 'str', ''),
            ('_pdbx_density.mean_E2_1_abs', '%s', 'str', ''),
            ('_pdbx_density.Padilla-Yeates_L_mean', '%s', 'str', ''),
            ('_pdbx_density.Padilla-Yeates_L2_mean', '%s', 'str', ''),
            ('_pdbx_density.Padilla-Yeates_L2_mean_pointless', '%s', 'str', ''),
            ('_pdbx_density.Z_score_L_test', '%s', 'str', ''),
            ('_pdbx_density.twin_type', '%s', 'str', ''),
            ('_pdbx_density.twin_operator_xtriage', '%s', 'str', ''),
            ('_pdbx_density.twin_fraction_xtriage', '%s', 'str', ''),
            ('_pdbx_density.twin_Rfactor', '%s', 'str', ''),
            ('_pdbx_density.I_over_sigI_resh', '%s', 'str', ''),
            ('_pdbx_density.I_over_sigI_diff', '%s', 'str', ''),
            ('_pdbx_density.I_over_sigI_mean', '%s', 'str', ''),
            ('_pdbx_density.ice_ring', '%s', 'str', ''),
            ('_pdbx_density.anisotropy', '%s', 'str', ''),
            ('_pdbx_density.Z-score', '%s', 'str', ''),
            ('_pdbx_density.prob_peak_value', '%s', 'str', ''),
            ('_pdbx_density.translational_pseudo_symmetry', '%s', 'str', ''),
            ('_pdbx_density.wavelength', '%s', 'str', ''),
            ('_pdbx_density.B_solvent', '%s', 'str', ''),
            ('_pdbx_density.K_solvent', '%s', 'str', ''),
            ('_pdbx_density.TLS_refinement_reported', '%s', 'str', ''),
            ('_pdbx_density.partial_B_value_correction_attempted', '%s', 'str', ''),
            ('_pdbx_density.partial_B_value_correction_success', '%s', 'str', ''),
            ('_pdbx_density.reflection_status_archived', '%s', 'str', ''),
            ('_pdbx_density.reflection_status_used', '%s', 'str', ''),
            ('_pdbx_density.reflns_twin', '%s', 'str', ''),
            ('_pdbx_density.twin_by_xtriage', '%s', 'str', ''),
            ('_pdbx_density.twin_operator', '%s', 'str', ''),
            ('_pdbx_density.twin_fraction', '%s', 'str', ''),
            ('_pdbx_density.tls_group_number', '%s', 'str', ''),
            ('_pdbx_density.ncs_group_number', '%s', 'str', ''),
            ('_pdbx_density.mtrix_number', '%s', 'str', ''),
            ('_pdbx_density.Matthew_coeff', '%s', 'str', ''),
            ('_pdbx_density.solvent_content', '%s', 'str', ''),
            ('_pdbx_density.Cruickshank_dpi_xyz', '%s', 'str', ''),
            ('_pdbx_density.dpi_free_R', '%s', 'str', ''),
            ('_pdbx_density.fom', '%s', 'str', '')
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
