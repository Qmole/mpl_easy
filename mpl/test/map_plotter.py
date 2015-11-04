# -*- coding: utf-8 -*-
import sys
import random
import yaml
import matplotlib as mpl
import numpy as np
from datetime import datetime
from rounding import get_round_str
sys.path.append("/pj1/cmf/python/graphs")
import plotter

class ValueCalculator(object):
    def __init__(self, data, calc_type):
        self.data = data
        self.calc_type = calc_type

    def calc_value(self):
        if self.calc_type == "sum":
            return self.get_sum_of_data()
        elif self.calc_type == "avg":
            return self.get_average_of_data()
        elif self.calc_type == "max":
            return self.get_maximum()
        elif self.calc_type == "min":
            return self.get_minimum()
        else: #self.calc_type == 'nan':
            return self.get_average_of_data()
    
    def get_sum_of_data(self, decimal=1):
        values_without_nan = self.filter_nan_data(self.data)
        if not values_without_nan:
            return 0
        sum_of_data = np.nansum(values_without_nan)
        #if isinstance(sum_of_data, float):
        #    return get_round_str(sum_of_data, decimal)
        return sum_of_data
        
    def get_average_of_data(self):
        values_without_nan = self.filter_nan_data(self.data)
        if not values_without_nan:
            return '0'
        average_of_data = np.nanmean(values_without_nan)
        return average_of_data
        #return get_round_str(average_of_data, 1)  
    
    def get_maximum(self):
        values_without_nan = self.filter_nan_data(self.data)
        # index, max_value = max(enumerate(values), key=operator.itemgetter(1))
        if not values_without_nan:
            return 0
        max_value = np.nanmax(values_without_nan)
        #return get_round_str(max_value, 1)  
        return max_value
        
    def get_minimum(self):
        values_without_nan = self.filter_nan_data(self.data)
        if not values_without_nan:
            return 0
        min_value = np.nanmin(values_without_nan)
        return get_round_str(min_value, 1)  
        
    def filter_nan_data(self, data):
        nan_list = [np.nan, "nan", "no", "X"]
        values_without_nan = [i for i in data if i not in nan_list]
        # change the value with * to integer, and string "0" to integer 0.
        int_values_without_nan = [int(re.sub('[*]','',i)) if isinstance(i,str) else i for i in values_without_nan]
        return int_values_without_nan  


class MapPlotter(object):
    def __init__(self, data, extra_data, start_date, end_date):
        self.data = data
        self.start_date = start_date
        self.end_date = end_date               
        self.stations = extra_data['stations'].split(',')    
        self.index_name = extra_data['index_name']

        with open('../config/extreme.yaml', 'r') as f:
            self.config = yaml.load(f)
            
        self.unit = self._read_unit()
         
    def set_title(self, title):
        self.title = title    
  
    def _get_values(self, info):
        info = [value[1] for value in info]
        calc_type = self._read_calc_type()
        val_calc =  ValueCalculator(info, calc_type)
        val = val_calc.calc_value()

        if np.isnan(float(val)):
            return 0
        return val

    def _read_calc_type(self):
        return self.config['index_name'][self.index_name]['calc_type']
  
    def _read_unit(self):
        return self.config['index_name'][self.index_name]['unit']
  
    def gen_output_files(self):
        pic_html = ''
        plot_element = plotter.Plotter(length=6.5, width=5) 
        
        plot_element.set_x_label(u'日期')
        
        start_date_str = datetime.strftime(self.start_date, '%Y%m%d')
        end_date_str = datetime.strftime(self.end_date, '%Y%m%d')
        title_str = self.title + u' 月全島平面圖' + '\n' + start_date_str + ' ~ ' + end_date_str
        if self.unit != '':
            title_str += u' (單位:' + self.unit + u')'
            
        plot_element.set_title(title_str, fontsize=13) 

        plot_element.set_bottom_blank_width(0.12)
        plot_element.set_legend(False)
        
        plot_element.set_shapefile('/pj1/cmf/config/TWN_MAP/', 'TWN_COUNTY', color="#DDDDDD")
        plot_element.set_shapefile('/pj1/cmf/config/TWN_MAP/', 'TWN_adm0', color="#111111")
        plot_element.read_station_position('../config/', 'SStationXY_dmos_108.dat')
        plot_element.read_station_value_position('../config/', 'station_text.yaml')
        
        values = {stn: self._get_values(self.data[stn]) for stn in self.data }
        
        plot_element.add_map(values, self.stations, 25.8, 21.5, 122.5, 119.5, color="blue")
        
        filename = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S') + str(random.randint(0,1000000))
        plot_element.save_file('/pj1/cmf/www/htdocs/tmp/' + filename +'.png', dpi=150)  
        pic_html += '<img src="../../tmp/' + filename + '.png"  id="map_img"><br><br> '       
        return pic_html