import matplotlib as mpl
import numpy as np
from plotbase import PlotBase

class FillBetween(PlotBase):
    def __init__(self, Plotter):
        PlotBase.__init__(self, Plotter)
    
    def date_plotting(self, x_values, y_values, compare_values, name, above_color, below_color, alpha=0.4):
        x_values = np.array([mpl.dates.date2num(i) for i in x_values])
        y_values = np.array(y_values)
        compare_values = np.array(compare_values)

        self.ax.fill_between(x_values, y_values, compare_values, where=compare_values<=y_values, facecolor=above_color, alpha=alpha, interpolate=True)
        self.ax.fill_between(x_values, y_values, compare_values, where=compare_values>=y_values, facecolor=below_color, alpha=alpha, interpolate=True)       
        #return list(y_values)