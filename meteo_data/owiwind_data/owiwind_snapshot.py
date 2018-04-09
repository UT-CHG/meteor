import numpy as np
import matplotlib.pyplot as plt


class OWIwindSnapshot:
    def __init__(self, time, o_lon, o_lat, d_lon, d_lat, n_lon, n_lat):
        self.time = time
        self.o_lon = o_lon
        self.o_lat = o_lat
        self.d_lon = d_lon
        self.d_lat = d_lat
        self.n_lon = n_lon
        self.n_lat = n_lat

    def plot_data(self):
        nx = self.n_lon
        ny = self.n_lat

        speed = np.hypot(self.vx, self.vy).reshape((ny, nx))

        #this plots velocity field
        #plt.streamplot(self.lon_coord, self.lat_coord, self.vx.reshape((ny, nx)),
        #               self.vy.reshape((ny, nx)), color=speed, density=2)

        #this plots pressure field
        plt.pcolormesh(self.spherical_grid_point_coordinates[:, 0].reshape((ny, nx)),
                       self.spherical_grid_point_coordinates[:, 1].reshape((ny, nx)), self.p.reshape((ny, nx)))

        plt.colorbar()

        x_min = min(self.lon_coord)
        x_max = max(self.lon_coord)
        y_min = min(self.lat_coord)
        y_max = max(self.lat_coord)

        plt.axis([x_min, x_max, y_min, y_max])
        plt.axes().set_aspect('equal')
        plt.grid()
        plt.show()
