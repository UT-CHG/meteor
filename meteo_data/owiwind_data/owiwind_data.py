import sys
import re
import numpy as np
import datetime as dt
from scipy.interpolate import griddata

from meteo_data.owiwind_data.owiwind_snapshot import OWIwindSnapshot


class OWIwindData:
    def __init__(self, meteo_file_path):
        with open(meteo_file_path) as meteo_input_file:
            self.n_fields = int(meteo_input_file.readline().split()[0])
            self.n_skip = int(meteo_input_file.readline().split()[0])
            self.wind_multiplicator = float(meteo_input_file.readline().split()[0])

            self.parse_basin_data(meteo_file_path)

            if self.n_fields == 2:
                self.parse_regional_data(meteo_file_path)

    def parse_basin_data(self, meteo_file_path):
        with open(meteo_file_path + '1') as pressure_field_data:
            time_data = re.search(r'.+(?P<start>[0-9]{10})\s+(?P<end>[0-9]{10})', pressure_field_data.readline())

            start_year = int(time_data.group('start')[0:4])
            start_month = int(time_data.group('start')[4:6])
            start_day = int(time_data.group('start')[6:8])
            start_hour = int(time_data.group('start')[8:10])

            self.start_time = dt.datetime(start_year, start_month, start_day, start_hour)

            end_year = int(time_data.group('end')[0:4])
            end_month = int(time_data.group('end')[4:6])
            end_day = int(time_data.group('end')[6:8])
            end_hour = int(time_data.group('end')[8:10])

            self.end_time = dt.datetime(end_year, end_month, end_day, end_hour)

            self.owiwind_snapshots = []

            while True:
                snap_data = re.search(
                    r'iLat=(?P<n_lat>[\s0-9]+)iLong=(?P<n_lon>[\s0-9]+)DX=(?P<d_lon>[\s0-9.Ee]+)DY=(?P<d_lat>[\s0-9.Ee]+)SWLat=(?P<o_lat>[\s\-0-9.Ee]+)SWLon=(?P<o_lon>[\s\-0-9.Ee]+)DT=(?P<time>[\s0-9]+)',
                    pressure_field_data.readline())

                if snap_data == None:
                    break

                curr_year = int(snap_data.group('time')[0:4])
                curr_month = int(snap_data.group('time')[4:6])
                curr_day = int(snap_data.group('time')[6:8])
                curr_hour = int(snap_data.group('time')[8:10])
                curr_minute = int(snap_data.group('time')[10:12])

                curr_time = dt.datetime(curr_year, curr_month, curr_day, curr_hour, curr_minute)

                seconds_since_start = (curr_time - self.start_time).total_seconds()

                snapshot = OWIwindSnapshot(seconds_since_start, float(snap_data.group('o_lon')),
                                           float(snap_data.group('o_lat')), float(snap_data.group('d_lon')),
                                           float(snap_data.group('d_lat')), int(snap_data.group('n_lon')),
                                           int(snap_data.group('n_lat')))

                parsed_data_points = []

                while len(parsed_data_points) < int(snap_data.group('n_lon')) * int(snap_data.group('n_lat')):
                    parsed_data_points.extend(pressure_field_data.readline().split())

                p = np.asarray(parsed_data_points, float)

                snapshot.p = p

                self.owiwind_snapshots.append(snapshot)

        with open(meteo_file_path + '2') as velocity_field_data:
            time_data = re.search(r'.+(?P<start>[0-9]{10})\s+(?P<end>[0-9]{10})', velocity_field_data.readline())

            start_year = int(time_data.group('start')[0:4])
            start_month = int(time_data.group('start')[4:6])
            start_day = int(time_data.group('start')[6:8])
            start_hour = int(time_data.group('start')[8:10])

            start_time = dt.datetime(start_year, start_month, start_day, start_hour)

            end_year = int(time_data.group('end')[0:4])
            end_month = int(time_data.group('end')[4:6])
            end_day = int(time_data.group('end')[6:8])
            end_hour = int(time_data.group('end')[8:10])

            end_time = dt.datetime(end_year, end_month, end_day, end_hour)

            if self.start_time != start_time or self.end_time != end_time:
                print("Velocity and pressure files have inconsistent start/end times. Exiting!")
                sys.exit()

            for owiwind_snapshot in self.owiwind_snapshots:
                snap_data = re.search(
                    r'iLat=(?P<n_lat>[\s0-9]+)iLong=(?P<n_lon>[\s0-9]+)DX=(?P<d_lon>[\s0-9.Ee]+)DY=(?P<d_lat>[\s0-9.Ee]+)SWLat=(?P<o_lat>[\s\-0-9.Ee]+)SWLon=(?P<o_lon>[\s\-0-9.Ee]+)DT=(?P<time>[\s0-9]+)',
                    velocity_field_data.readline())

                #each existing pressure data set has to have a corresponding velocity data set
                if snap_data == None:
                    print("Velocity data was not found for time: {}. Exiting!".format(owiwind_snapshot.time))
                    sys.exit()

                curr_year = int(snap_data.group('time')[0:4])
                curr_month = int(snap_data.group('time')[4:6])
                curr_day = int(snap_data.group('time')[6:8])
                curr_hour = int(snap_data.group('time')[8:10])
                curr_minute = int(snap_data.group('time')[10:12])

                curr_time = dt.datetime(curr_year, curr_month, curr_day, curr_hour, curr_minute)

                seconds_since_start = (curr_time - self.start_time).total_seconds()

                #check if pressure and velocity snapshots are consistent
                if owiwind_snapshot.time != seconds_since_start or \
                   owiwind_snapshot.o_lon != float(snap_data.group('o_lon')) or \
                   owiwind_snapshot.o_lat != float(snap_data.group('o_lat')) or \
                   owiwind_snapshot.d_lon != float(snap_data.group('d_lon')) or \
                   owiwind_snapshot.d_lat != float(snap_data.group('d_lat')) or \
                   owiwind_snapshot.n_lon != int(snap_data.group('n_lon')) or \
                   owiwind_snapshot.n_lat != int(snap_data.group('n_lat')):
                    print("Velocity and pressure are inconsistent at time: {}. Exiting!".format(
                        int(snap_data.group('time'))))
                    sys.exit()

                parsed_data_points = []

                while len(parsed_data_points) < int(snap_data.group('n_lon')) * int(snap_data.group('n_lat')):
                    parsed_data_points.extend(velocity_field_data.readline().split())

                vx = np.asarray(parsed_data_points, float)

                owiwind_snapshot.vx = vx

                parsed_data_points = []

                while len(parsed_data_points) < int(snap_data.group('n_lon')) * int(snap_data.group('n_lat')):
                    parsed_data_points.extend(velocity_field_data.readline().split())

                vy = np.asarray(parsed_data_points, float)

                owiwind_snapshot.vy = vy

        #Generate grid data
        for owiwind_snapshot in self.owiwind_snapshots:
            lon_start = owiwind_snapshot.o_lon
            lon_step = owiwind_snapshot.d_lon
            lon_stop = lon_start + lon_step * owiwind_snapshot.n_lon

            lat_start = owiwind_snapshot.o_lat
            lat_step = owiwind_snapshot.d_lat
            lat_stop = lat_start + lat_step * owiwind_snapshot.n_lat

            #Store coordinates in arrays
            owiwind_snapshot.lon_coord = np.arange(lon_start, lon_stop, lon_step, float)
            owiwind_snapshot.lat_coord = np.arange(lat_start, lat_stop, lat_step, float)

            #Store grid point coordinates (all combinations)
            lon_grid, lat_grid = np.meshgrid(owiwind_snapshot.lon_coord, owiwind_snapshot.lat_coord)
            owiwind_snapshot.spherical_grid_point_coordinates = np.column_stack((lon_grid.flatten(),
                                                                                 lat_grid.flatten()))

        #Sort snapshots by time since start
        self.owiwind_snapshots.sort(key=lambda owiwind_snapshot: owiwind_snapshot.time)

        #Plot data
        #for owiwind_snapshot in self.owiwind_snapshots:
        #    owiwind_snapshot.plot_data()

    def parse_regional_data(self, meteo_file_path):
        #This needs to be implemented once we get hold of 223 and 224 files
        print(meteo_file_path + '3')
        print(meteo_file_path + '4')

    def get_wind_data(self, input, time, grid_coord_spherical):
        interpolate = False

        #check if there is owiwind snap with same timestamp
        iter = 0
        for owiwind_snapshot in self.owiwind_snapshots:
            if owiwind_snapshot.time == time:
                break
            iter += 1

        if iter < len(self.owiwind_snapshots):
            #No interpolation
            p_interp = griddata(self.owiwind_snapshots[iter].spherical_grid_point_coordinates,
                                self.owiwind_snapshots[iter].p, grid_coord_spherical, fill_value=1013.0)

            vx_interp = griddata(self.owiwind_snapshots[iter].spherical_grid_point_coordinates,
                                 self.owiwind_snapshots[iter].vx, grid_coord_spherical, fill_value=0.0)

            vy_interp = griddata(self.owiwind_snapshots[iter].spherical_grid_point_coordinates,
                                 self.owiwind_snapshots[iter].vy, grid_coord_spherical, fill_value=0.0)
        else:
            interpolate = True

        if interpolate:
            iter = 0
            for owiwind_snapshot in self.owiwind_snapshots:
                if owiwind_snapshot.time >= time:
                    break
                iter += 1

            if iter != 0 and iter < len(self.owiwind_snapshots):
                #Interpolation weight
                time_range = self.owiwind_snapshots[iter].time - self.owiwind_snapshots[iter - 1].time
                intep_w = (time - self.owiwind_snapshots[iter - 1].time) / time_range

                #Intepolate in storm
                p_interp_in = griddata(self.owiwind_snapshots[iter - 1].spherical_grid_point_coordinates,
                                       self.owiwind_snapshots[iter - 1].p, grid_coord_spherical, fill_value=1013.0)

                vx_interp_in = griddata(self.owiwind_snapshots[iter - 1].spherical_grid_point_coordinates,
                                        self.owiwind_snapshots[iter - 1].vx, grid_coord_spherical, fill_value=0.0)

                vy_interp_in = griddata(self.owiwind_snapshots[iter - 1].spherical_grid_point_coordinates,
                                        self.owiwind_snapshots[iter - 1].vy, grid_coord_spherical, fill_value=0.0)

                #Intepolate ex storm
                p_interp_ex = griddata(self.owiwind_snapshots[iter].spherical_grid_point_coordinates,
                                       self.owiwind_snapshots[iter].p, grid_coord_spherical, fill_value=1013.0)

                vx_interp_ex = griddata(self.owiwind_snapshots[iter].spherical_grid_point_coordinates,
                                        self.owiwind_snapshots[iter].vx, grid_coord_spherical, fill_value=0.0)

                vy_interp_ex = griddata(self.owiwind_snapshots[iter].spherical_grid_point_coordinates,
                                        self.owiwind_snapshots[iter].vy, grid_coord_spherical, fill_value=0.0)

                #Combine interpolations
                p_interp = (1 - intep_w) * p_interp_in + intep_w * p_interp_ex
                vx_interp = (1 - intep_w) * vx_interp_in + intep_w * vx_interp_ex
                vy_interp = (1 - intep_w) * vy_interp_in + intep_w * vy_interp_ex
            else:
                print("Existing owiwind snapshots are not in time range that contains t={}. Exiting!".format(time))
                sys.exit()

        #convert form millibars to Pa
        p_interp = p_interp * 100.0

        return np.column_stack((vx_interp, vy_interp, p_interp))
