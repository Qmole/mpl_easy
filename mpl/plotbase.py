class PlotBase(object):
    def __init__(self, Plotter, twinx=False):
        self.plt = Plotter.plt
        self.fig = Plotter.fig
        self.ax = Plotter.ax
        if twinx:
            self.ax2 = Plotter.ax2