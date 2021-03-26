import os
from wwpdb.utils.dp.DensityWrapper import DensityWrapper


class DensityConversionInSession:

    def __init__(self, reqObj=None):
        self.__reqObj = reqObj
        session_id = self.__reqObj.getSessionId()
        session_path = self.__reqObj.getSessionPath()
        self.session_directory = os.path.join(session_path, session_id)
        self.density_wrapper = DensityWrapper()

    def em_volume_conversion(self, in_map, out_map):
        return self.density_wrapper.convert_em_volume(in_em_volume=in_map,
                                                      out_binary_volume=out_map,
                                                      working_dir=self.session_directory)

    def xray_density_conversion(self, coord_file, in_2fofc_map, in_fofc_map, out_binary_cif):
        return self.density_wrapper.convert_xray_density_map(coord_file=coord_file,
                                                             in_2fofc_map=in_2fofc_map,
                                                             in_fofc_map=in_fofc_map,
                                                             out_binary_cif=out_binary_cif,
                                                             working_dir=self.session_directory)
