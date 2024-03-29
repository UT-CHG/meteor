import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt

from input_file import InputFile
from input_file import MeshType
from input_file import MeteoDataType

from mesh.ADCIRC_mesh.adcirc_mesh import AdcirMesh
from mesh.Meta_mesh.meta_mesh import MetaMesh

from meteo_data.hwind_data.hwind_data import HwindData
from meteo_data.owiwind_data.owiwind_data import OWIwindData

if len(sys.argv) < 2:
    print("Not enough input variables. Please provide fort.15 file path! Exiting!")
    sys.exit()

input = InputFile(sys.argv[1])

if input.mesh_type == MeshType.ADCIRC:
    mesh = AdcirMesh(input.mesh_file_path)
elif input.mesh_type == MeshType.Meta:
    mesh = MetaMesh(input.mesh_file_path)

if input.meteo_data_type == MeteoDataType.HWIND:
    meteo_data = HwindData(input.raw_meteo_input_file)
elif input.meteo_data_type == MeteoDataType.OWIWIND:
    meteo_data = OWIwindData(input.raw_meteo_input_file)

#Construct grid data from mesh in spherical coordinates
#Here I assume that I read in mesh in lon/lat coordinates
#That is either true or projected cartesian x/y coordinates need to be projected back to lon/lat
grid_coord_spherical = np.zeros((mesh.num_nodes, 2))

for node in range(0, mesh.num_nodes):
    grid_coord_spherical[node][0] = mesh.nodes[node].c1
    grid_coord_spherical[node][1] = mesh.nodes[node].c2

current_time = input.start_time
while current_time <= input.end_time:
    wind_data = meteo_data.get_wind_data(input, current_time, grid_coord_spherical)

    #Garratt's formula is used to compute wind stress from the wind velocity.
    wind_speed = np.hypot(wind_data[:, 0], wind_data[:, 1])
    C_d = 0.001 * (0.75 + 0.067 * wind_speed)

    wind_stress_x = input.rho_air * np.multiply(C_d, np.multiply(wind_speed, wind_data[:, 0]))
    wind_stress_y = input.rho_air * np.multiply(C_d, np.multiply(wind_speed, wind_data[:, 1]))

    #Output file
    current_step = int(math.ceil((current_time - input.start_time).total_seconds() / input.dt))
    output_file_name = input.meteo_input_file[:-6] + '_' + str(current_step) + ".meteo"
    output_file = open(output_file_name, "w")

    for node_id in range(0, mesh.num_nodes):
        output_file.write(str(node_id) + ' ')
        output_file.write(str(wind_stress_x[node_id]) + ' ')
        output_file.write(str(wind_stress_y[node_id]) + ' ')
        output_file.write(str(wind_data[node_id, 2]) + '\n')

    output_file.close()

    current_time += dt.timedelta(seconds=input.meteo_input_frequency)