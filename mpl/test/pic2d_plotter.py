# -*- coding: utf-8 -*-
import sys
import random
import yaml
import matplotlib as mpl
import numpy as np
from datetime import datetime
sys.path.append("/pj1/cmf/python/graphs")
import Station
import plotter

class Pic2dPlotter(object):
    def __init__(self, data, extra_data, start_date, end_date, station_display, value_type, colorbar_info):
        self.data = data
        self.start_date = start_date
        self.end_date = end_date               
        self.station_display = station_display
        self.stations = self.get_station_order(extra_data['stations'].split(','))
        self.time_unit = extra_data['time_unit']
        if self.time_unit == 'month':
            self.time_unit_chn = u'月'
        elif self.time_unit == 'day':
            self.time_unit_chn = u'日'        
        else :
            self.time_unit_chn = u'年'        
        self.title = ''
        self.index_name = extra_data['index_name']
        
        self.value_type = value_type 
        self.colorbar_max = colorbar_info['colorbar_max']
        self.colorbar_min = colorbar_info['colorbar_min']
        self.colorbar_interval = colorbar_info['colorbar_interval']
        
    def get_station_order(self, unordered_stations):
        stn_info = Station.CWBStationInfo 
        stn_names = {stn['id']: {'chn_name':stn['chName'], 'code6':stn['realId'][-1][0] } for stn in stn_info}    
    
        station_group = Station.StationGroup['Station_27']

        reversed_stn_list =  [stn_names[stn]['code6'] for stn in station_group if stn_names[stn]['code6'] in unordered_stations]
        reversed_stn_list.reverse()
        self.stn_names = stn_names
        return reversed_stn_list
    
    def set_title(self, title):    
        self.title = title
        
    def _get_date_ticks(self, dates):
        dates_list = []
        interval = (len(dates) / 30) + 1
        dates = [date if i % interval == 0 else '' for i, date in enumerate(dates)]

        for i, now_date in enumerate(dates):
            try:
              if self.time_unit == 'year':
                  dates_list.append(datetime.strftime(now_date, '%Y'))
              elif self.time_unit == 'day':
                  if i % 5 == 0:
                      dates_list.append(datetime.strftime(now_date, '%m%d'))
                  else:
                      dates_list.append('')
                  
              elif i == 0 or now_date.month == 1:
                  dates_list.append(datetime.strftime(now_date, '%b\n%Y'))
              else:
                  dates_list.append(datetime.strftime(now_date, '%b'))
            except:
                  dates_list.append('')
        return dates_list        
    
    def _create_custom_map(self):    
        if self.value_type in ['raw']:
            cdict = {'red': ((0., 1, 1), (0.05, 1, 1), (0.3, 0, 0), (0.4, 0, 0), (0.5, 1, 1), (0.8, 1, 1),(1, 0.4, 1)),
                 'green': ((0., 1, 1),(0.05, 1, 1), (0.3, 0, 0), (0.4, 0.8, 1), (0.5, 1, 1), (0.8, 0, 0), (1, 0.2, 1)),
                 'blue': ((0., 1, 1), (0.05, 1, 1), (0.3, 1, 1), (0.4, 0, 0), (0.5, 0, 0), (0.8, 0, 0), (1, 0.4, 1))}
        else:
            cdict = {'red': ((0., 0, 0),  (0.5, 1, 1),  (1, 1, 1)),
                 'green': ((0., 0, 0),  (0.5, 1, 1),  (1, 0, 0)),
                 'blue': ((0., 1, 1),  (0.5, 1, 1),  (1, 0, 0))}                    
        return mpl.colors.LinearSegmentedColormap('my_colormap', cdict, 256)
        
    def _get_unit(self):
        with open('../config/extreme.yaml', 'r') as f:
            config = yaml.load(f)
        
        return config['index_name'][self.index_name]['unit']    
        
    def gen_output_files(self):
        #for count, index_data in enumerate(self.data):
        pic_html = ''
        #for stn in self.data:   
        plot_element = plotter.Plotter(length=5, width=10) 
        # format the date, for example, 10Jan2015 will become datetime(2015, 1, 10)
        
        if self.station_display == 'last3nums':
            stns_ticks = [stn[2:5] for stn in self.stations]
        elif self.station_display == 'chinese':
            stns_ticks = [self.stn_names[stn[:5]]['chn_name'].decode('utf-8') for stn in self.stations]
        
        stns_grid = np.array(xrange(len(self.data)))
        
        dates = [i[0] for i in self.data.items()[0][1]]
        dates_ticks = self._get_date_ticks(dates)
        dates_grid = np.array(xrange(len(self.data.items()[0][1])))

        x_values, y_values = np.meshgrid(dates_grid, stns_grid)

        stns = self.data.keys()
        z_values = [[ 0 if np.isnan(float(data[1])) else float(data[1]) for data in self.data[stn[:5]+'0'] ] 
                      for stn in self.stations] 
        
        plot_element.set_x_label(u'日期')

        self.unit = self._get_unit()
        title_text = self.title + self.time_unit_chn + u'二維時序圖'
        if self.unit != '':
            title_text += u' (單位:' + self.unit + u')'
        
        plot_element.set_title(title_text) 

        #major_interval, minor_interval = plot_element.get_suitable_interval(len(x_values))
        #plot_element.set_time_formatter('%b%Y', major_interval, minor_interval, 'month')
        plot_element.set_bottom_blank_width(0.15)
        plot_element.set_legend(False)
        
        mymap = self._create_custom_map()
        
        plot_element.add_date_2d(x_values, y_values, z_values, stns_ticks=stns_ticks, 
            dates_ticks=dates_ticks, cmap=mymap, time_unit=self.time_unit, value_type=self.value_type,
            colorbar_max=self.colorbar_max, colorbar_min=self.colorbar_min, colorbar_interval=self.colorbar_interval)

        filename = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S') + str(random.randint(0,1000000))
        plot_element.save_file('/pj1/cmf/www/htdocs/tmp/' + filename +'.png')  
        pic_html += '<img src="../../tmp/' + filename + '.png" id="img_2d"><br><br> '       
        return pic_html