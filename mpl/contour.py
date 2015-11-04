import sys
import matplotlib as mpl
from plotbase import PlotBase

class Contour(PlotBase):
    def __init__(self, Plotter):
        PlotBase.__init__(self, Plotter)

    def contour_plotting(self, x_values, y_values, z_values, levels, cm):
        cs = self.ax.contourf(x_values, y_values, z_values,  levels=levels, cmap=cm, extend="both")
        #cmap=self.plt.cm.bone,
        return cs