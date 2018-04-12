from enum import Enum
import yaml
import sys
import datetime as dt


class MeshType(Enum):
    ADCIRC = 0
    Meta = 1


class MeteoDataType(Enum):
    NONE = 0
    HWIND = 1
    OWIWIND = 2


class InputFile:
    def __init__(self, input_file_path):
        with open(input_file_path) as input_file:
            input = yaml.load(input_file)

        self.start_time = dt.datetime.strptime(input["timestepping"]["start_time"], '%d-%m-%Y %H:%M')
        self.end_time = dt.datetime.strptime(input["timestepping"]["end_time"], '%d-%m-%Y %H:%M')
        self.dt = float(input["timestepping"]["dt"])
        self.run_time = (self.end_time - self.start_time).total_seconds()

        self.g = float(input["problem"]["gravity"])
        self.rho_air = float(input["problem"]["density_air"])
        self.rho_water = float(input["problem"]["density_water"])

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
        elif input["problem"]["meteo_forcing"]["type"] == "OWIWIND":
            self.meteo_data_type = MeteoDataType.OWIWIND
        else:
            print("Undefined meteo forcing type: {}. Exiting!".format(input["problem"]["meteo_forcing"]["type"]))
            sys.exit()

        self.raw_meteo_input_file = input["problem"]["meteo_forcing"]["raw_input_file"]
        self.meteo_input_file = input["problem"]["meteo_forcing"]["input_file"]
        self.meteo_input_frequency = float(input["problem"]["meteo_forcing"]["frequency"])
