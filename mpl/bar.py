
from plotbase import PlotBase

class Bar(PlotBase):
    def __init__(self, Plotter, twinx):
        PlotBase.__init__(self, Plotter, twinx)
    
    def date_plotting(self, x_values, y_values, width, name, color, alpha, twinx):
        if twinx:
            return self.ax2.bar(x_values, y_values, width, label=name, color=color, alpha=alpha)
        else:
            return self.ax.bar(x_values, y_values, width, label=name, color=color, alpha=alpha)
      