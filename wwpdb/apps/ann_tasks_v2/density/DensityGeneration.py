import os
from wwpdb.utils.dp.DensityWrapper import DensityWrapper


class DensityConversionInSession:
    def __init__(self, reqObj=None):
        self.__reqObj = reqObj
        session_id = self.__reqObj.getSessionId()
        session_path = self.__reqObj.getSessionPath()
        self.__session_directory = os.path.join(session_path, session_id)
        self.__density_wrapper = DensityWrapper()

    def em_volume_conversion(self, in_map, out_map):
        return self.__density_wrapper.convert_em_volume(in_em_volume=in_map, out_binary_volume=out_map, working_dir=self.__session_directory)

    # Commented out until DensityWrapper updated to calling args match
    # def xray_density_conversion(self, coord_file, in_2fofc_map, in_fofc_map, out_binary_cif):
    #     return self.__density_wrapper.convert_xray_density_map(
    #         coord_file=coord_file, in_2fofc_map=in_2fofc_map, in_fofc_map=in_fofc_map, out_binary_cif=out_binary_cif, working_dir=self.__session_directory
    #     )
