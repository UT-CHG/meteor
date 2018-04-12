import sys
import numpy as np
import matplotlib.pyplot as plt
import re
import datetime as dt

from utilities.utilities import haversine


class HwindFile:
    def __init__(self, pressure_central, ramp, file_path):
        self.pressure_central = pressure_central
        self.ramp = ramp
        self.file_path = file_path

        time_data = re.search(r'(?P<time>[0-9]{4}_[0-9]{4}_[0-9]{4})', self.file_path)

        if (time_data == None):
            print("Unable to extract time data for hwind file: {}. Exiting!".format(self.file_path))
            sys.exit()

        self.time = dt.datetime.strptime(time_data.group('time'), '%Y_%m%d_%H%M')

    def parse_data(self):
        with open(self.file_path) as hwind_file:
            #Skip first line
            hwind_file.readline()

            #DX=DY= 6.02280 KILOMETERS.
            dx_dy = re.search(r'DX=DY=(?P<dx_dy>[\s0-9.Ee]+)', hwind_file.readline())
            self.dx_dy = float(dx_dy.group('dx_dy'))

            #STORM CENTER LOCALE IS(LON) EAST LONGITUDE and (LAT) NORTH LATITUDE ... STORM CENTER IS AT (X,Y)=(0,0)
            storm_center = re.search(
                r'STORM CENTER LOCALE IS (?P<lon>[\s\-0-9.Ee]+) EAST LONGITUDE and (?P<lat>[\s\-0-9.Ee]+) NORTH LATITUDE',
                hwind_file.readline())
            self.storm_center_lon = float(storm_center.group('lon'))
            self.storm_center_lat = float(storm_center.group('lat'))

            #Skip next line
            hwind_file.readline()

            #Read in grid x_coordinates
            n_x_coordinates = int(hwind_file.readline())

            x_coordinates = []

            parsed_coordinates = 0
            while parsed_coordinates < n_x_coordinates:
                x_coord_string = hwind_file.readline().split()

                for x_coord in x_coord_string:
                    x_coordinates.append(float(x_coord))

                parsed_coordinates += len(x_coord_string)

            #Skip next line
            hwind_file.readline()

            #Read in grid y_coordinates
            n_y_coordinates = int(hwind_file.readline())

            y_coordinates = []

            parsed_coordinates = 0
            while parsed_coordinates < n_y_coordinates:
                y_coord_string = hwind_file.readline().split()

                for y_coord in y_coord_string:
                    y_coordinates.append(float(y_coord))

                parsed_coordinates += len(y_coord_string)

            #Skip next line
            hwind_file.readline()

            #Read in grid lon_coordinates
            n_lon_coordinates = int(hwind_file.readline())

            lon_coordinates = []

            parsed_coordinates = 0
            while parsed_coordinates < n_lon_coordinates:
                lon_coord_string = hwind_file.readline().split()

                for lon_coord in lon_coord_string:
                    lon_coordinates.append(float(lon_coord))

                parsed_coordinates += len(lon_coord_string)

            #Skip next line
            hwind_file.readline()

            #Read in grid lat_coordinates
            n_lat_coordinates = int(hwind_file.readline())

            lat_coordinates = []

            parsed_coordinates = 0
            while parsed_coordinates < n_lat_coordinates:
                lat_coord_string = hwind_file.readline().split()

                for lat_coord in lat_coord_string:
                    lat_coordinates.append(float(lat_coord))

                parsed_coordinates += len(lat_coord_string)

            lat_coordinates = np.asarray(lat_coordinates)

            #Store coordinates in arrays
            self.cartesian_coordinates = np.column_stack((x_coordinates, y_coordinates))
            self.spherical_coordinates = np.column_stack((lon_coordinates, lat_coordinates))

            #Store grid point coordinates (all combinations)
            x_grid, y_grid = np.meshgrid(self.cartesian_coordinates[:, 0], self.cartesian_coordinates[:, 1])
            self.cartesian_grid_point_coordinates = np.column_stack((x_grid.flatten(), y_grid.flatten()))

            lon_grid, lat_grid = np.meshgrid(self.spherical_coordinates[:, 0], self.spherical_coordinates[:, 1])
            self.spherical_grid_point_coordinates = np.column_stack((lon_grid.flatten(), lat_grid.flatten()))

            #Skip next line
            hwind_file.readline()

            #Read in grid velocity data
            n_grid_string = hwind_file.readline().split()

            nx_grid = int(n_grid_string[0])
            ny_grid = int(n_grid_string[1])

            vx = []
            vy = []

            for i in range(0, ny_grid):
                temp_vx = []
                temp_vy = []

                parsed_velocities = 0
                while parsed_velocities < nx_grid:
                    velocities = re.finditer(r'\((?P<u>[\s\-0-9.Ee]+),(?P<v>[\s\-0-9.Ee]+)\)', hwind_file.readline())

                    for velocity in velocities:
                        temp_vx.append(float(velocity.group('u')))
                        temp_vy.append(float(velocity.group('v')))
                        parsed_velocities += 1

                vx.append(temp_vx)
                vy.append(temp_vy)

            #Store velocities
            self.vx = np.asarray(vx).flatten()
            self.vy = np.asarray(vy).flatten()

            #find vmax and rmax
            speed = np.hypot(np.asarray(vx), np.asarray(vy))
            max_index = np.unravel_index(np.argmax(speed, axis=None), speed.shape)

            self.vmax = speed[max_index]

            lon_max = lon_grid[max_index]
            lat_max = lat_grid[max_index]

            self.rmax = haversine(self.storm_center_lon, self.storm_center_lat, lon_max, lat_max)

    def plot_data(self):
        nx = len(self.cartesian_coordinates[:, 0])
        ny = len(self.cartesian_coordinates[:, 1])

        speed = np.hypot(self.vx, self.vy).reshape((nx, ny))

        plt.streamplot(self.cartesian_coordinates[:, 0], self.cartesian_coordinates[:, 1], self.vx.reshape((nx, ny)),
                       self.vy.reshape((nx, ny)), color=speed, density=2)

        plt.colorbar()

        x_min = min(self.cartesian_coordinates[:, 0])
        x_max = max(self.cartesian_coordinates[:, 0])
        y_min = min(self.cartesian_coordinates[:, 1])
        y_max = max(self.cartesian_coordinates[:, 1])

        plt.axis([x_min, x_max, y_min, y_max])
        plt.axes().set_aspect('equal')
        plt.grid()
        plt.show()
