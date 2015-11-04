import sys
import matplotlib as mpl
from plotbase import PlotBase

class Line(PlotBase):
    def __init__(self, Plotter):
        PlotBase.__init__(self, Plotter)

    def date_plotting(self, x_values, y_values, name, has_dot, forced_selected_date, linestyle, linewidth, markersize, color, alpha):
        if has_dot:
            linestyle += 'o'
        return self.ax.plot_date(x_values, y_values, linestyle, linewidth=linewidth, markersize=markersize, color=color, alpha=alpha)