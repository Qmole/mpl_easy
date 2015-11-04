# -*- coding: utf-8 -*-
import sys
import random
import numpy as np
from datetime import datetime
sys.path.append("/pj1/cmf/python/graphs")
import plotter

class BarPlotter(object):
    def __init__(self, data, start_date, end_date, time_unit, value_type):
        self.data = data
        self.start_date = start_date
        self.end_date = end_date   
        self.time_unit = time_unit
        self.time_unit_chn = u'月' if time_unit == 'month' else u'年'
        self.title = ''
        self.value_type = value_type
    
    def set_title(self, title):
        self.title = title    
        
    def gen_output_files(self):
        #for count, index_data in enumerate(self.data):
        pic_html = ''

        for stn in self.data:
            plot_element = plotter.Plotter() 
            # format the date, for example, 10Jan2015 will become datetime(2015, 1, 10)
            y_values = [0 if np.isnan(i[1]) else float(i[1]) for i in self.data[stn]]
            x_values = [i[0] for i in self.data[stn]]
            plot_element.set_x_label(u'日期')
            plot_element.set_title(stn + u'站 ' + self.title + u'日數 ' + self.time_unit_chn + u'柱狀圖') 
            
            major_interval, minor_interval = plot_element.get_suitable_interval(len(x_values))
            if self.time_unit == 'month':
                plot_element.set_time_formatter('%b%Y', major_interval, minor_interval, 'month')
            elif self.time_unit == 'year':
                plot_element.set_time_formatter('%Y', major_interval, minor_interval, 'year')
            plot_element.set_bottom_blank_width(0.15)
            plot_element.set_legend(True, 12)
            #plot_element.add_date_bars(x_values, y_values, u'日數', has_dot=True)
            plot_element.add_date_bars(x_values, y_values, u'日數', alpha=0.6, total_bars=data_length, 
            first_last_left_blank=False, plus_minus_seperate_color=plus_minus_seperate_color)
            
            max_value = np.nanmax(y_values) 
            min_value = np.nanmin(y_values)
            if self.value_type in ['raw']:
                min_value =  0
            else:
                min_value -= 1
            
            if max_value == 0:
                plot_element.ax.set_ylim(min_value, 5)
            else:
                plot_element.ax.set_ylim(min_value, max_value+4)

            filename = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S') + str(random.randint(0,1000000))
            plot_element.save_file('/pj1/cmf/www/htdocs/tmp/' + filename +'.png')  
            pic_html += '<img src="../../tmp/' + filename + '.png" width="90%" id="index'  + '"><br><br> '       
        return pic_html