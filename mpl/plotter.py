# -*- coding: utf-8 -*-

import os, sys
import traceback
from datetime import datetime, timedelta
from calendar import monthrange
from collections import defaultdict
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from mpl_toolkits.basemap import Basemap
import yaml

from line import Line
from bar import Bar
from fill_between import FillBetween
from contour import Contour
from map import Map
#new_fig.subplots_adjust(hspace = .001, top=0.88, right=0.85


font = FontProperties(fname="/pj1/cmf/www/htdocs/font/MSJH.TTF") 

class Plotter(object):
    def __init__(self, length=5, width=12):
        plt.rc('axes', color_cycle=['b', 'k', 'r', 'g', 'y', 'm', 'c', '#33FF00', '#6AF142', '#F31254', '#555555', 'A70028', 'CECF46'])
        self.plt = plt   
        self.fig = self.plt.figure(figsize=(width, length))
        self.fig.subplots_adjust(left=0.05, right=0.85)
        self.ax = self.fig.add_subplot(111)
        self.has_legend = True 
        self.legend_fontsize=9
        self.legends, self.legend_namelist = [], []
        self.bar_count = 0
        self.max_value = []
        self.min_value = []
        self.shapefile = {}
        self.readpath = './'
        
        
    def _add_station_texts(self, position_info):
        ''' read the station code from file'''
        with open(self.station_value_positionfile, 'r') as f:
            cfg = yaml.load(f)
        # print position_info['stn']
        # print cfg['stations']
        for i, stn in enumerate(position_info['stn']):
            if stn in cfg['stations'].keys():
                yaml_stn = cfg['stations'][stn]
            else:
                yaml_stn = cfg['stations']['default']
            x_shift = float(yaml_stn['horizontal']) * 1000
            y_shift = float(yaml_stn['vertical']) * 1000
            plt.text(position_info['x'][i]+float(x_shift), position_info['y'][i]+float(y_shift),
                    position_info['value'][i], fontsize=9, color='red')                            
        
    def _get_first_date(self, y_values):
        for i, value in enumerate(y_values):
            if not np.isnan(value):
                return i
        return i

    def _get_last_date(self, y_values):
        y_values = y_values[::-1]
        for i, value in enumerate(y_values):
            if not np.isnan(value):
                return len(y_values) - i
        return 0
        
    def _get_space_value(self, max_val):

        if max_val < 1.5:
            return 2
        elif max_val < 10:
            return int(max_val) + 1
        elif max_val < 100:
            return (max_val / 12 + 1) * 12
        elif max_val < 1000:
            return (max_val / 24 + 1) * 24
        else:
            return (max_val / 48 + 1) * 48
            
    def _read_all_station(self):
        ''' read the station code from file'''
        try:
            f=open(self.station_positionfile, 'r')
            station_title = f.readline()
            station_data = f.readlines()
        except IOError:
            msg = ("station position file can't be found.\n")
            print msg
            sys.exit()

        return  {line.split()[0]: line.split() for line in station_data }            
            
    def _read_coordinate(self, m, values, selected_stations):
        '''read the coordinate of stations for plotting on map '''
        stations = self._read_all_station()
        #valid_stn_count = 0
        xlist, ylist, clist, stlist = [], [], [], []
        # all different stations
        for st in stations.keys():
            lon, lat = stations[st][1], stations[st][2]
            xpt,ypt = m(float(lon),float(lat))
            # -1 is because the last element is stationlist, not statistical value
            if st in selected_stations:
                #if all_datas[count]<100:   # effective station
                xlist.append(xpt)
                ylist.append(ypt)
                stlist.append(st)
                value = 'Nan' if np.isnan(float(values[st])) else int(float(values[st])+0.5)
                clist.append(str(value))
                #valid_stn_count+=1

        if ( (len(xlist)==0) or (len(ylist)==0) ):
            print 'No data could be plotted. Please enter right station number'
            sys.exit()

        return [xlist, ylist, clist, stlist]    

    def set_top_blank_width(self, width):
        self.fig.subplots_adjust(top=width)
        
    def set_bottom_blank_width(self, width):
        self.fig.subplots_adjust(bottom=width)

    def set_right_blank_width(self, width):
        self.fig.subplots_adjust(right=1-width)
        
    def get_colorbar_range(self, colorbar_max, colorbar_min, colorbar_interval):
        num = colorbar_min
        while num < colorbar_max:
            yield num
            num += colorbar_interval
        yield colorbar_max   
        
    def count_running_mean(self, y_values, mean_count):
        try:
            #print y_values
            y_values = [np.nan if i == 'Nan' else i for i in y_values]
            last_item_index = -(mean_count-1)
            nan_head_and_tail_fill_count = (mean_count -1) / 2
            running_mean_array = np.convolve(y_values, np.ones((mean_count))/ mean_count)[(mean_count-1):][:last_item_index]
            final_array = [np.nan] * nan_head_and_tail_fill_count + list(running_mean_array) + [np.nan] * nan_head_and_tail_fill_count
        except Exception as e:
            print traceback.format_exc()
            sys.exit()
        return final_array

    def add_text(self, x_pos, y_pos, text, xycoords='axes fraction', fontsize=12, color='k'):
        self.plt.annotate(text, xy=(x_pos, y_pos), xycoords=xycoords, fontsize=fontsize, color=color, fontproperties=font)
        
    def add_trend_line(self, x_values, y_values, valid_data_threshold=0.4, plot_whole=False, color='green', alpha=1):
        try:
            y_values = [np.nan if i == 'Nan' else i for i in y_values]
            valid_data_ratio = sum(not np.isnan(i) for i in y_values) / float(len(y_values))
            
            if  valid_data_ratio > valid_data_threshold:                
        
                valid_counts = [ i for i, value in enumerate(y_values) if not np.isnan(value)]            
                # valid (has valid value) list
                valid_y_values = [value for i, value in enumerate(y_values) if i in valid_counts]
                valid_x_values = [value for i, value in enumerate(x_values) if i in valid_counts]                

                x_value_series = range(len(x_values))
                valid_x_value_series = range(len(valid_x_values))
                z = np.polyfit(valid_x_value_series, valid_y_values, 1)
                p = np.poly1d(z)
                if plot_whole:  #plot whole length line
                    x_values_num = [mpl.dates.date2num(i) for i in x_values]
                    self.add_date_lines(x_values, p(x_value_series), 'trendline', color=color, alpha=alpha)
                else: 
                    start_date_order = self._get_first_date(y_values)
                    end_date_order = self._get_last_date(y_values)           
                    
                    trend_x_values = x_values[start_date_order:end_date_order]
                    trend_y_values = p(range(end_date_order-start_date_order))  #y_values[start_date_order:end_date_order+1]

                    self.add_date_lines(trend_x_values, trend_y_values, 'trendline', color=color, alpha=alpha, forced_selected_date=False)
            else:
                print '有效資料太少(<全部資料的' + str(valid_data_threshold) + '), 將不繪出趨勢線'
        except Exception as e:
            print traceback.format_exc() 
            sys.exit()
            
    def add_date_lines(self, x_values, y_values, name='', has_dot=False, forced_selected_date=True, linestyle='-'\
                       ,linewidth=2, markersize=3, color='', alpha=1):

        line = Line(self)
        now_color = self.ax._get_lines.color_cycle.next()

        if color != '':
            now_color = color
            
        self.now_color = now_color
        self.alpha = float(alpha)
        
        y_values = self.change_missing_value(y_values, [np.nan, 'nan', 'Nan'], np.nan)

        output_line, = line.date_plotting(x_values, y_values, name, has_dot, forced_selected_date, linestyle, linewidth, markersize, now_color, float(alpha))
        self._add_legends(output_line, name)
        if forced_selected_date:
            self.min_date = x_values[0]
            self.max_date = x_values[-1]

            self.set_xaxis_limit()

        valid_items =  [i for i in y_values if i != 0]          
        if len(valid_items) > 0:
           self.min_value.append(np.nanmin(valid_items))
           self.max_value.append(np.nanmax(valid_items))
              
    def add_date_bars(self, x_values, y_values, name='', width=0.5, has_baseline=True, baseline_pos=0, 
                     color='', alpha=0.5, total_bars=1, twinx=False, first_last_left_blank=False, 
                     plus_minus_seperate_color=False, above_color='red', below_color='blue'):
                     
        self.alpha = float(alpha)
        
        if twinx:
            self.ax2 = self.ax.twinx()
        self.bar_count += 1    
        if len(x_values) > 1:
            date_interval = mpl.dates.date2num(x_values[1]) - mpl.dates.date2num(x_values[0]) 
        else:
            date_interval = 1
            first_last_left_blank = True
            
        bar_width = width * date_interval / total_bars

        x_values = [mpl.dates.date2num(i)-(date_interval * width/2) + (self.bar_count-1) * bar_width for i in x_values]
        bar = Bar(self, twinx)

        y_values = self.change_missing_value(y_values, [np.nan, 'nan', 'Nan'], 0)

        after_last_date_number =  x_values[-1] + date_interval
        x_values.append(after_last_date_number)
        y_values.append(0)
        
        if first_last_left_blank:
            first_data_minus_one_period = x_values[0] - date_interval
            x_values.insert(0, first_data_minus_one_period)
            y_values.insert(0, 0)


        if  plus_minus_seperate_color: 
            plus_bars = [i if i>baseline_pos else 0  for i in y_values]
            minus_bars = [i if i<baseline_pos else 0 for i in y_values]
            self.set_legend(False)
            bar.date_plotting(x_values, plus_bars, bar_width, name, color=above_color, alpha=float(alpha), twinx=twinx)
            bar.date_plotting(x_values, minus_bars, bar_width, name, color=below_color, alpha=float(alpha), twinx=twinx)
            self.now_color = ''
        else:
            if color == '':
                bar_color = self.ax._get_lines.color_cycle.next()
            else:
                bar_color = color
            self.now_color = bar_color    
            bars = bar.date_plotting(x_values, y_values, bar_width, name, color=bar_color, alpha=alpha, twinx=twinx)
            self.set_legend(True)            
            self._add_legends(bars, name)
            self.fig.subplots_adjust(left=0.05, right=0.88)

        no_zero_values = [i for i in y_values if i != 0]
        if len(no_zero_values) > 0:
            if max(np.nanmin(no_zero_values) ,np.nanmax(no_zero_values)) < 10:
                ax2_min =  np.nanmin(no_zero_values) -0.5
                ax2_max =  np.nanmax(no_zero_values) + 0.5 
            else: 
                ax2_min =  np.nanmin(no_zero_values) * 0.95
                ax2_max =  np.nanmax(no_zero_values) * 1.05                
        else:
            ax2_min = -0.5
            ax2_max = 0.5
            self.add_text(0.40, 0.7, 'no index data found!')
            
        self.max_value.append(ax2_max)
        self.min_value.append(ax2_min)
        
        if has_baseline:
            now_ax = getattr(self, 'ax2' if twinx else 'ax')
            now_ax.plot(x_values, [baseline_pos]*len(x_values), 'k-')      

            self.min_date = mpl.dates.num2date(x_values[0])
            self.max_date = mpl.dates.num2date(x_values[-1])
         
            self.set_xaxis_limit()
 
        if twinx:
            self.set_yaxis_limit(ax2_max, ax2_min,axis=self.ax2, auto=False)

    def add_date_2d(self, x_values, y_values, z_values, dates_ticks=[], stns_ticks=[], cmap='', 
                        time_unit='month', interval="equal", value_type="raw",
                        colorbar_max=30, colorbar_min=0, colorbar_interval=2):                         
        levels = np.linspace(colorbar_min, colorbar_max, (colorbar_max-colorbar_min)+1)

        cont = Contour(self)
        plt.xticks(x_values[0], dates_ticks, fontsize=11)
        plt.yticks(zip(*y_values)[0], stns_ticks, fontproperties=font, fontsize=9)
        cmap = plt.get_cmap(cmap)
        #print z_values
        #print x_values
        #print y_values
        cs = cont.contour_plotting(x_values, y_values, z_values, levels, cmap)  

        cbar = self.fig.colorbar(cs)

        colorbar_range = list(self.get_colorbar_range(colorbar_max, colorbar_min, colorbar_interval))
        cbar.set_ticks(colorbar_range)
        cbar.set_ticklabels(map(str, colorbar_range))            
            
    def add_map(self, values, selected_stations, map_lat_max, map_lat_min, map_lon_max, map_lon_min, color="#000000", filled=True):    
        map = Map(self)
        
        self.fig.subplots_adjust(top=0.93)
        
        ulat, llat, ulon, llon =  map_lat_max, map_lat_min, map_lon_max, map_lon_min
        m = Basemap(projection='merc', llcrnrlat=llat,
                                       urcrnrlat=ulat,
                                       llcrnrlon=llon,
                                       urcrnrlon=ulon,
                                       resolution='i')
        
        #cm = mpl.cm.get_cmap(self.colorbar_type)

            # cdict = {'red': ((0., 0, 0), (0.4, 1, 1),(0.6, 1, 1),(1, 0.5, 0.5)),
                     # 'green': ((0., 0, 0),(0.4, 1, 1), (0.6, 1, 1), (1, 0, 0)),
                     # 'blue': ((0., 1, 1),(0.4, 1, 1), (0.6, 1, 1), (1, 0, 0))}
            # cm = mpl.colors.LinearSegmentedColormap('my_colormap', cdict, 256)

        if 'TWN_COUNTY' in self.shapefile:     
            m.readshapefile(self.shapefile['TWN_COUNTY']['path'], 'TWN_COUNTY',
                        color=self.shapefile['TWN_COUNTY']['color'])

        if 'TWN_adm0' in self.shapefile:                        
            m.readshapefile(self.shapefile['TWN_adm0']['path'], 'TWN_adm0',
                        color=self.shapefile['TWN_adm0']['color'])
                        
        m.fillcontinents(color="#FFFFFF", zorder=0)
        
        xlist, ylist, clist, stlist = self._read_coordinate(m, values, selected_stations)

        s = plt.scatter(xlist, ylist, s=14, marker='x', zorder=2, color=color)
        m.drawmapboundary(fill_color="#F0F8FF", zorder=5)
        if filled:
            levels = np.linspace(0, 40, 41)

            cont = Contour(self)
            cm = mpl.cm.get_cmap('YlGnBu')
            cmap = plt.get_cmap(cm)

            x_min, y_min = m(map_lon_min, map_lat_min+0.0000001)
            x_max, y_max = m(map_lon_max, map_lat_max)

            x2 = np.array(np.linspace(x_min, x_max, (map_lon_max-map_lon_min)*10+1))
            y2 = np.array(np.linspace(y_min, y_max, (map_lat_max-map_lat_min)*10+1))

            x3, y3 = np.meshgrid(x2, y2) 

            wait_to_fill_values = [True] * len(clist)
            #z_values = np.zeros((len(y2), len(x2)))
            z_values = np.random.randint(40, size=(len(y2), len(x2)))
            # 先判斷是否有在裡面 沒有的話畫空白值?
            # 也許不要contourf，用polygon
            # 內插的方法
            for i, x in enumerate(x2):
                for j, y in enumerate(y2):
                    for idx, value in enumerate(clist): #stlist
                        if wait_to_fill_values[idx] and x > xlist[idx] and y> ylist[idx]:
                            wait_to_fill_values[idx] = False
                            z_values[j][i] = float(value)
                            break
                            
            cs = cont.contour_plotting(x3, y3, z_values, levels, cmap)    
            cbar = self.fig.colorbar(cs)

            colorbar_range = list(self.get_colorbar_range(40, 0, 5))
            cbar.set_ticks(colorbar_range)
            #cbar.set_ticklabels(map(str, colorbar_range))     

        # add text 
        self._add_station_texts({'x':xlist, 'y':ylist, 'stn':stlist, 'value':clist})

        #m.drawcoastlines(linewidth=1)
        # m.drawparallels(N.arange(llat, ulat, self.axis_line_interval),
                        # linewidth=self.axis_line_width, labels=[1,0,1,0])
        # m.drawmeridians(N.arange(llon, ulon, self.axis_line_interval),
                        # linewidth=self.axis_line_width, labels=[1,0,0,1])
        #return [m,cm]
        
        
        #map.map_plotting(values)
        
        
            
    def add_date_fillbetween(self, x_values, y_values, compare_values, name='', above_color='red', below_color='blue'\
                       ,alpha=0.4, add_legends=True):
        y_values = self.change_missing_value(y_values, [np.nan, 'nan', 'Nan'], np.nan)

        between_line = FillBetween(self)
        between_line.date_plotting(x_values, y_values, compare_values, name, above_color=above_color, below_color=below_color, alpha=alpha)

        #force the x-axis length of the picture to be the same as the input x_values length
        showed_line, = plt.plot(x_values, [0]*len(y_values), color='black', alpha=0, linewidth=1)

        if not add_legends: 
            self.set_legend(False)
            self.fig.subplots_adjust(left=0.05, right=0.95)
            
    def _add_legends(self, item, name):
        self.legends.append(item)        
        self.legend_namelist.append(name)
        
    def annotate_values(self, x_values='', y_values='', fontsize=9, color='k', digit=1):
        for x, y in zip(x_values, y_values):
            y_text = ("{0:." + str(digit) + "f}").format(y)
            self.plt.annotate(y_text, xy=(mpl.dates.date2num(x), y), xycoords='data', fontsize=fontsize, color=color, weight='bold')
 
    def change_missing_value(self, value_list, old_missing_value, new_missing_value):
        if isinstance(old_missing_value, list):
            return [i if i not in old_missing_value else new_missing_value for i in value_list]
        else:
            return [i if i != old_missing_value else new_missing_value for i in value_list]       
 
    def check_length(self, x_values, y_values, standard, missing_value=np.nan):
        if standard == 'x_axis':
            while len(y_values) < len(x_values):
                y_values.append(missing_value)
        elif standard == 'y_axis':
            while len(x_values) < len(y_values):
                x_values.append(missing_value)        
        return (x_values, y_values)
        
    def gen_date_iter(self, start_date, end_date, period='day', interval=1):
        count = 0
        while start_date <= end_date and count<1000:
            yield start_date
            
            if period == 'day':
                start_date = start_date + timedelta(days=interval)
            elif period == 'month':
                last_day_of_this_month = monthrange(start_date.year, start_date.month)[1]
                last_date_of_this_month = datetime(start_date.year, start_date.month, last_day_of_this_month)
                start_date = last_date_of_this_month  + timedelta(days=1)
            elif period == 'year':
                start_date = datetime(start_date.year+1, 1, 1)            
            count += 1


    def get_line_color_and_alpha(self):
        return (self.now_color, self.alpha)                
            
    def get_suitable_interval(self, length):
        if length == 1:
            return (10, 1)
        if length <= 15:
            return (1, 1)
        if length <= 30:
            return (2, 1)
        elif length <= 60:
            return (5, 1)
        elif length < 100:
            return (8, 1)
        else:
            return (length/10, length/100)        
      
    def read_station_value_position(self, path, positionfile):
        self.station_value_positionfile = path + positionfile
        
    def read_station_position(self, path, stationfile):    
        self.station_positionfile = path + stationfile
        
    def set_shapefile(self, path, filename, color="#000000"):
        self.shapefile[filename] = {'path':path + filename, 'color':color}
        
        
    def set_title(self, title, fontsize=14):
        self.ax.set_title(title, fontproperties=font, fontsize=fontsize)
        
    def set_x_label(self, labels):
        self.ax.set_xlabel(labels, fontproperties=font)
        
    def set_y_label(self, labels):
        self.ax.set_ylabel(labels, fontproperties=font, rotation='horizontal', x=-2, y=1.05, ha='left')        
        
    def set_y_twin_label(self, labels):
        if hasattr(self, 'ax2'):
            self.ax2.set_ylabel(labels, fontproperties=font, rotation='horizontal', x=-1.25, y=1.1, ha='right')            
        
    def set_y_max(self):
        pass
        
    def set_y_min(self):
        pass
    
    def get_max_value(self):
        if len(self.max_value) > 0:            
            no_nan_values = [i for i in self.max_value if not np.isnan(i)]
            if len(no_nan_values) >0:
                return max(no_nan_values)
        return np.nan
        
    def get_min_value(self):
        if len(self.min_value) > 0:
            no_nan_values = [i for i in self.min_value if not np.isnan(i)]
            if len(no_nan_values)>0:
                return min(no_nan_values)                
        return np.nan
    
    def set_time_formatter(self, date_format, major_interval=5, minor_interval=1, period='day', weekday='MO'):
        if date_format != 'custom':    
            dateFmt = mpl.dates.DateFormatter(date_format)
            self.ax.xaxis.set_major_formatter(dateFmt)

        if period == 'day':
            self.ax.xaxis.set_major_locator(mpl.dates.DayLocator(interval=major_interval))
            self.ax.xaxis.set_minor_locator(mpl.dates.DayLocator(interval=minor_interval))
        elif period == 'week':
            weekday_showed = getattr(mpl.dates, weekday)
            self.ax.xaxis.set_major_locator(mpl.dates.WeekdayLocator(byweekday=weekday_showed, interval=major_interval))
            self.ax.xaxis.set_minor_locator(mpl.dates.WeekdayLocator(byweekday=weekday_showed, interval=minor_interval))            
        elif period == 'month':
            self.ax.xaxis.set_major_locator(mpl.dates.MonthLocator(interval=major_interval))
            self.ax.xaxis.set_minor_locator(mpl.dates.MonthLocator(interval=minor_interval))                        
        elif period == 'year':
            self.ax.xaxis.set_major_locator(mpl.dates.YearLocator(base=major_interval))        
            self.ax.xaxis.set_minor_locator(mpl.dates.YearLocator(base=minor_interval))              
        #set font
        if period in ['day', 'month']:
            for label in self.ax.xaxis.get_ticklabels():
                label.set_fontsize(8)
                label.set_weight("bold")

            self.fig.autofmt_xdate()
            
        #ticker
        self.ax.xaxis.set_tick_params(which='major', length=6)
        self.ax.xaxis.set_tick_params(which='minor', length=4)
        
    def set_xaxis_limit(self):
        min_val = mpl.dates.date2num(self.min_date)
        max_val = mpl.dates.date2num(self.max_date)
        self.ax.set_xlim(min_val, max_val)           
        
    def set_yaxis_limit(self, max_val, min_val, axis='', auto=True):
        #space_val = self._get_space_value(max_val)
        if auto:
            if max_val == 0:
                max_val = 0.5
            else:
                max_val = max_val + abs(max_val * 0.05)   # considering plus and minus values
            
            if min_val == 0:
                min_val = -0.5
            else:
                min_val = min_val - abs(min_val * 0.05)     
        else:
            if not np.isnan(max_val):
                max_val = np.nanmax([abs(max_val), abs(min_val)])
                max_val = self._get_space_value(max_val)
                
                if abs(abs(min_val) - abs(-max_val)) < 0.2:
                    min_val = -max_val - 1
                else:
                    min_val = -max_val                   
            else:
                max_val = 0.5
                min_val = -0.5
 
        axis.set_ylim(min_val, max_val)
        
    def set_legend(self, has_legend=True, legend_fontsize=9):
        self.has_legend = has_legend
        if has_legend:
            self.legend_fontsize=legend_fontsize
        else:
            self.fig.subplots_adjust(left=0.05, right=0.95)
            
    def set_grid(self):
        self.plt.grid(True)    
        
    def save_file(self, name='', loc="upper left", bbox=(1.03, 0.9), ncol=1, frameon=True, columnspacing=1, handletextpad=None, dpi=''): 
        if self.has_legend:
            self.ax.legend(self.legends, self.legend_namelist, loc=loc, bbox_to_anchor=bbox, prop=font, \
                           fontsize=self.legend_fontsize, ncol=ncol, frameon=frameon, columnspacing=columnspacing, handletextpad=handletextpad)
        if dpi != "":                   
            self.plt.savefig(name, dpi=dpi)
        else:
            self.plt.savefig(name)
                 