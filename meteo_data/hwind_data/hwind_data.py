import numpy as np
import sys
import math
from scipy.interpolate import griddata
from enum import Enum

from meteo_data.hwind_data.hwind_file import HwindFile
from utilities.utilities import haversine


class PWRelationship(Enum):
    Dvorak = 0
    Knaffzehr = 1
    SpecifiedPC = 2
    Background = 3


class HwindData:
    def __init__(self, meteo_file_path):
        with open(meteo_file_path) as meteo_input_file:
            #Skip first line
            meteo_input_file.readline()

            self.hwind_multiplier = float(meteo_input_file.readline())

            pw_relationship_string = meteo_input_file.readline().rstrip('\n')

            if pw_relationship_string == "dvorak":
                self.pressure_wind_relationship = PWRelationship.Dvorak
            elif pw_relationship_string == "knaffzehr":
                self.pressure_wind_relationship = PWRelationship.Knaffzehr
            elif pw_relationship_string == "specifiedPc":
                self.pressure_wind_relationship = PWRelationship.SpecifiedPC
            elif pw_relationship_string == "background":
                self.pressure_wind_relationship = PWRelationship.Background
            else:
                print("Undefined pressure-wind relationship type: {}. Exiting!".format(pw_relationship_string))
                sys.exit()

            #Assuming here that hwind files are in the same folder as meteo input file
            meteo_input_root = meteo_file_path[0:meteo_file_path.rfind('/') + 1]

            self.hwind_files = []
            for line in meteo_input_file:
                hwind_string = line.split()

                self.hwind_files.append(
                    HwindFile(float(hwind_string[1]), float(hwind_string[2]), meteo_input_root + hwind_string[3]))

            if len(self.hwind_files) < 2:
                print("Insufficient number of files for temporal interpolation. Exiting!")
                sys.exit()

            #Sort time ascending
            self.hwind_files.sort(key=lambda hwind_file: hwind_file.time)

            for hwind_file in self.hwind_files:
                hwind_file.parse_data()

            #Visualize parsed data to check for consistency
            #for hwind_file in self.hwind_files:
            #    hwind_file.plot_data()

    def get_wind_data(self, input, time, grid_coord_spherical):
        interpolate = False

        #check if there is hwind file with same timestamp
        iter = 0
        for hwind_file in self.hwind_files:
            if hwind_file.time == time:
                break
            iter += 1

        if iter < len(self.hwind_files):
            #No interpolation
            curr_ramp = self.hwind_files[iter].ramp

            curr_storm_lon = self.hwind_files[iter].storm_center_lon
            curr_storm_lat = self.hwind_files[iter].storm_center_lat

            vmax = self.hwind_files[iter].vmax
            rmax = self.hwind_files[iter].rmax

            p_central = self.hwind_files[iter].pressure_central

            vx_interp = griddata(self.hwind_files[iter].spherical_grid_point_coordinates, self.hwind_files[iter].vx,
                                 grid_coord_spherical, fill_value=0.0)

            vy_interp = griddata(self.hwind_files[iter].spherical_grid_point_coordinates, self.hwind_files[iter].vy,
                                 grid_coord_spherical, fill_value=0.0)

            vx_interp = vx_interp * curr_ramp * self.hwind_multiplier
            vy_interp = vy_interp * curr_ramp * self.hwind_multiplier
        else:
            interpolate = True

        if interpolate:
            iter = 0
            for hwind_file in self.hwind_files:
                if hwind_file.time >= time:
                    break
                iter += 1

            if iter != 0 and iter < len(self.hwind_files):
                #Interpolation weight
                time_range = self.hwind_files[iter].time - self.hwind_files[iter - 1].time
                intep_w = (time - self.hwind_files[iter - 1].time) / time_range

                #Interpolate ramp
                d_ramp = self.hwind_files[iter].ramp - self.hwind_files[iter - 1].ramp

                curr_ramp = self.hwind_files[iter - 1].ramp + intep_w * d_ramp

                #Find new storm eye
                d_lon = self.hwind_files[iter].storm_center_lon - self.hwind_files[iter - 1].storm_center_lon
                d_lat = self.hwind_files[iter].storm_center_lat - self.hwind_files[iter - 1].storm_center_lat

                curr_storm_lon = self.hwind_files[iter - 1].storm_center_lon + intep_w * d_lon
                curr_storm_lat = self.hwind_files[iter - 1].storm_center_lat + intep_w * d_lat

                #Interpolate vmax, rmax
                d_vmax = self.hwind_files[iter].vmax - self.hwind_files[iter - 1].vmax
                d_rmax = self.hwind_files[iter].rmax - self.hwind_files[iter - 1].rmax

                vmax = self.hwind_files[iter - 1].vmax + intep_w * d_vmax
                rmax = self.hwind_files[iter - 1].rmax + intep_w * d_rmax

                #Interpolate pressure central
                d_p_central = self.hwind_files[iter].pressure_central - self.hwind_files[iter - 1].pressure_central

                p_central = self.hwind_files[iter - 1].pressure_central + intep_w * d_p_central

                #Move in storm to new storm eye
                sp_grid_pt_coord_in = np.copy(self.hwind_files[iter - 1].spherical_grid_point_coordinates)

                d_lon_in = intep_w * d_lon
                d_lat_in = intep_w * d_lat

                sp_grid_pt_coord_in[:, 0] = sp_grid_pt_coord_in[:, 0] + d_lon_in
                sp_grid_pt_coord_in[:, 1] = sp_grid_pt_coord_in[:, 1] + d_lat_in

                #Move ex storm to new storm eye
                sp_grid_pt_coord_ex = np.copy(self.hwind_files[iter].spherical_grid_point_coordinates)

                d_lon_ex = curr_storm_lon - self.hwind_files[iter].storm_center_lon
                d_lat_ex = curr_storm_lat - self.hwind_files[iter].storm_center_lat

                sp_grid_pt_coord_ex[:, 0] = sp_grid_pt_coord_ex[:, 0] + d_lon_ex
                sp_grid_pt_coord_ex[:, 1] = sp_grid_pt_coord_ex[:, 1] + d_lat_ex

                #Intepolate in storm
                vx_interp_in = griddata(sp_grid_pt_coord_in, self.hwind_files[iter - 1].vx, grid_coord_spherical,
                                        fill_value=0.0)

                vy_interp_in = griddata(sp_grid_pt_coord_in, self.hwind_files[iter - 1].vy, grid_coord_spherical,
                                        fill_value=0.0)

                #Intepolate ex storm
                vx_interp_ex = griddata(sp_grid_pt_coord_ex, self.hwind_files[iter].vx, grid_coord_spherical,
                                        fill_value=0.0)

                vy_interp_ex = griddata(sp_grid_pt_coord_ex, self.hwind_files[iter].vy, grid_coord_spherical,
                                        fill_value=0.0)

                #Combine interpolations
                vx_interp = (1 - intep_w) * vx_interp_in + intep_w * vx_interp_ex
                vy_interp = (1 - intep_w) * vy_interp_in + intep_w * vy_interp_ex

                #Apply factors
                vx_interp = vx_interp * curr_ramp * self.hwind_multiplier
                vy_interp = vy_interp * curr_ramp * self.hwind_multiplier
            else:
                print("Existing hwind files are not in time range that contains t={}. Exiting!".format(time))
                sys.exit()

        #Compute pressure field for Dvorak and Knaffzehr cases
        if self.pressure_wind_relationship == PWRelationship.Dvorak:
            p_central = 1015.0 - (vmax / 3.92)**(1.0 / 0.644)
        elif self.pressure_wind_relationship == PWRelationship.Knaffzehr:
            p_central = 1010.0 - (vmax / 2.3)**(1.0 / 0.76)

        #Use central pressure and max wind speed to estimate the Holland B value
        rho_air = input.rho_air  #kg/m^3

        B = vmax**2 * rho_air * math.e / ((1013.0 - p_central) * 100.0)  #with conversion from milibars to Pa
        B = max(min(B, 2.5), 1.0)  # limit B to range [1.0,2.5]

        p = []

        for grid_point in grid_coord_spherical:
            if self.pressure_wind_relationship != PWRelationship.Background:
                distance = haversine(grid_point[0], grid_point[1], curr_storm_lon, curr_storm_lat)

                pressure = p_central + (1013.0 - p_central) * math.exp(-(rmax / distance)**B)
            else:
                pressure = 1013.0

            p.append(pressure)

        #Ramping pressure
        p = 1013.0 - (1013.0 - np.asarray(p)) * curr_ramp

        p = p * 100.0  #convert from milibars to Pa

        return np.column_stack((vx_interp, vy_interp, p))
