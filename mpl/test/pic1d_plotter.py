# -*- coding: utf-8 -*-
import sys
import random
import numpy as np
import yaml
from datetime import datetime
sys.path.append("/pj1/cmf/python/graphs")
import plotter
import Station

class Pic1dPlotter(object):
    def __init__(self, data, extra_data, start_date, end_date, value_type, graph_type, show_values):
        self.data = data
        self.start_date = start_date
        self.end_date = end_date   
        self.time_unit = extra_data['time_unit']
        if self.time_unit == 'month':
            self.time_unit_chn = u'月'
        elif self.time_unit == 'day':
            self.time_unit_chn = u'日'
        else:
            self.time_unit_chn = u'年'
        self.title = ''
        self.value_type = value_type
        self.graph_type = graph_type

        stn_info = Station.CWBStationInfo 
        self.stn_names = {stn['id']: {'chn_name':stn['chName'], 'code6':stn['realId'][-1][0] } for stn in stn_info}
        self.ordered_stations = extra_data['stations'].split(',')
        
        self.unit = self._get_unit(extra_data['index_name'])
        if self.unit == u'天':
            self.digit = 0
        else:
            self.digit = 1

        self.show_values = (show_values == 'true')
      
    def set_title(self, title):
        self.title = title    
   
    def _get_unit(self, index_name):
        with open('../config/extreme.yaml', 'r') as f:
            config = yaml.load(f)
        
        return config['index_name'][index_name]['unit']    
   
    def plot(self, plot_element, x_values, y_values, legend_text):
        
        if self.graph_type == 'line':
            plot_element.add_date_lines(x_values, y_values, legend_text, has_dot=True)
            if self.show_values:
                plot_element.annotate_values(x_values, y_values, fontsize=10, digit=self.digit)
        elif self.graph_type == 'bar':
            plot_element.add_date_bars(x_values, y_values, legend_text, has_baseline=True,
                alpha=0.6, first_last_left_blank=False, plus_minus_seperate_color=True)     
   
    def get_values(self, stn):
        modified_stn = stn[:5] + '0'
        y_values = [0 if np.isnan(float(i[1])) else float(i[1]) for i in self.data[modified_stn]]
        x_values = [i[0] for i in self.data[modified_stn]]    
        return x_values, y_values
   
    def single_station_plotting(self, stn, plot_element, type='single'):    
        # format the date, for example, 10Jan2015 will become datetime(2015, 1, 10)
        x_values, y_values = self.get_values(stn)

        stn_chname = self.stn_names[stn[:5]]['chn_name'].decode('utf-8')
        plot_element.set_title(stn_chname + u'站 ' + self.title + self.time_unit_chn + u'時序圖') 
        
        self._general_setting(plot_element, len(x_values), y_values)
        if self.unit != '':
            plot_element.add_text(0, 1.03, '('.encode('utf-8') + self.unit + ')'.encode('utf-8') )
        self.plot(plot_element, x_values, y_values, u'日數')
        

    def all_stations_plotting(self, stns, plot_element):    
        stn_number = len(stns)
        #all_y_values = []
        
        plot_element.set_title(str(stn_number) + u'站 ' + self.title + self.time_unit_chn + u'時序圖') 
        if self.unit != '':
            plot_element.add_text(0, 1.03, '('.encode('utf-8') + self.unit + ')'.encode('utf-8') )
        for stn in stns:
            x_values, y_values = self.get_values(stn)

            stn_chname = self.stn_names[stn[:5]]['chn_name'].decode('utf-8')

            #all_y_values.extend(y_values)
            self.plot(plot_element, x_values, y_values, stn_chname)
               
        #first_modified_stn = stns[0][:5] + '0'            
        #self._general_setting(plot_element, len(self.data[first_modified_stn]), all_y_values)      
      
    def _general_setting(self, plot_element, time_length, y_values):    
        plot_element.set_x_label(u'日期')
        major_interval, minor_interval = plot_element.get_suitable_interval(time_length)
        if self.time_unit in ['month']:
            plot_element.set_time_formatter('%b%Y', major_interval, minor_interval, 'month')
        elif self.time_unit == 'day':
            plot_element.set_time_formatter('%b%Y', major_interval, minor_interval, 'day')
        elif self.time_unit == 'year':
            plot_element.set_time_formatter('%Y', major_interval, minor_interval, 'year')
        plot_element.set_bottom_blank_width(0.15)
        plot_element.set_legend(True, 12)    
    
        max_value = np.nanmax(y_values) 
        min_value = np.nanmin(y_values)
        # if self.value_type in ['raw']:
            # min_value =  0
        # else:
            # min_value -= 1
        
        if max_value == 0:
            plot_element.ax.set_ylim(min_value, 5)
        else:
            plot_element.ax.set_ylim(min_value-4, max_value+4)           
        
    def gen_output_files(self):
        pic_html = ''
        
        for stn in self.ordered_stations:
            plot_element = plotter.Plotter() 
            self.single_station_plotting(stn, plot_element)     
            filename = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S') + str(random.randint(0,1000000))
            plot_element.save_file('/pj1/cmf/www/htdocs/tmp/' + filename +'.png')  
            pic_html += '<img src="../../tmp/' + filename + '.png" width="90%" id="index'  + '"><br><br> '  

        if self.graph_type == 'line':
            all_in_one_pic_plot_element = plotter.Plotter()
            self.all_stations_plotting(self.ordered_stations, all_in_one_pic_plot_element)    
           
            filename = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S') + str(random.randint(0,1000000))
            all_in_one_pic_plot_element.save_file('/pj1/cmf/www/htdocs/tmp/' + filename +'.png')  
            all_in_one_pic_html = '<img src="../../tmp/' + filename + '.png" width="90%" id="index'  + '"><br><br> '          
            
            return all_in_one_pic_html + pic_html 
        return pic_html