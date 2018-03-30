from enum import Enum
import yaml
import sys


class MeshType(Enum):
    ADCIRC = 0
    Meta = 1


class MeteoDataType(Enum):
    NONE = 0
    HWIND = 1


class InputFile:
    def __init__(self, input_file_path):
        with open(input_file_path) as input_file:
            input = yaml.load(input_file)

        self.dt = float(input["timestepping"]["dt"])
        self.end_time = float(input["timestepping"]["end_time"])

        self.g = float(input["gravity"])
        self.rho_air = float(input["density_air"])
        self.rho_water = float(input["density_water"])

        if input["mesh"]["format"] == "Adcirc":
            self.mesh_type = MeshType.ADCIRC
        elif input["mesh"]["format"] == "Meta":
            self.mesh_type = MeshType.Meta
        else:
            print("Undefined mesh type: {}. Exiting!".format(input["mesh"]["format"]))
            sys.exit()

        self.mesh_file_path = input["mesh"]["file_name"]

        if input["problem"]["meteo_forcing"]["type"] == "None":
            print("No meteo forcing. Exiting!")
            sys.exit()
        elif input["problem"]["meteo_forcing"]["type"] == "HWIND":
            self.meteo_data_type = MeteoDataType.HWIND
        else:
            print("Undefined meteo forcing type: {}. Exiting!".format(input["problem"]["meteo_forcing"]["type"]))
            sys.exit()

        self.raw_meteo_input_file = input["problem"]["meteo_forcing"]["raw_input_file"]
        self.meteo_input_file = input["problem"]["meteo_forcing"]["input_file"]
        self.meteo_input_frequency = float(input["problem"]["meteo_forcing"]["frequency"])
