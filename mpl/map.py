
from plotbase import PlotBase

class Map(PlotBase):
    def __init__(self, Plotter):
        PlotBase.__init__(self, Plotter)
    
    def plotting(self, values):
        return self.ax.bar(values)
      