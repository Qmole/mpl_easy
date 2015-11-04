#!/usr/bin/env python
# -*- coding:utf-8 -*-
from datetime import datetime
from itertools import groupby
import operator
import numpy as np
import re
import sys
import yaml
#from collections import namedtuple
from decimal import Decimal
from process_data import ProcessData
from rounding import get_round_str
import Station
from table_generator import TableGen

        
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
        elif self.calc_type == 'nan':
            return ''        
    
    def get_sum_of_data(self, decimal=1):
        values_without_nan = self.filter_nan_data(self.data)
        if not values_without_nan:
            return '0'
        sum_of_data = np.nansum(values_without_nan)
        if isinstance(sum_of_data, float):
            return get_round_str(sum_of_data, decimal)  
        return sum_of_data
        
    def get_average_of_data(self):
        values_without_nan = self.filter_nan_data(self.data)
        if not values_without_nan:
            return '0'
        average_of_data = np.nanmean(values_without_nan)
        return get_round_str(average_of_data, 1)  
    
    def get_maximum(self):
        values_without_nan = self.filter_nan_data(self.data)
        # index, max_value = max(enumerate(values), key=operator.itemgetter(1))
        if not values_without_nan:
            return '0'
        max_value = np.nanmax(values_without_nan)
        return get_round_str(max_value, 1)  

    def get_minimum(self):
        values_without_nan = self.filter_nan_data(self.data)
        if not values_without_nan:
            return '0'
        min_value = np.nanmin(values_without_nan)
        return get_round_str(min_value, 1)  
        
    def filter_nan_data(self, data):
        nan_list = [np.nan, "nan", "no", "X"]
        values_without_nan = [i for i in data if i not in nan_list]
        # change the value with * to integer, and string "0" to integer 0.
        int_values_without_nan = [float(re.sub('[*]','',i)) if isinstance(i,str) else i for i in values_without_nan]
        return int_values_without_nan               
            
class TablePlotter(object):
    def __init__(self, data, extra_data, start_date, end_date, data_count):
        self.data = data
        self.start_date = start_date
        self.end_date = end_date
        self.time_unit = extra_data['time_unit']

        if self.time_unit == 'month':
            self.time_unit_chn = u'月'  
        elif self.time_unit == 'day':
            self.time_unit_chn = u'日'
        elif self.time_unit == 'year':
            self.time_unit_chn = u'年' 
        elif self.time_unit == 'custom':
            self.time_unit_chn = u'自訂'             
        self.data_count = data_count
        self.incomplete_symbol = '*'
        self.station_name = extra_data['stations']
        self.index_name = extra_data['index_name']
        self.value_selector = extra_data['value_selector']
        
        if extra_data.has_key('percentile'):
            self.percentile_data = extra_data['percentile']
            #print '<table><tr><td></td>1</tr><tr>2</tr></table>'
        
        if extra_data.has_key('climate_value'):
            self.climate_value = extra_data['climate_value']
        
        with open('../config/extreme.yaml', 'r') as f:
            self.config = yaml.load(f)
            
    def set_title(self, title):
        self.title = title          
        
    def gen_output_files(self):
        table = TableGen()
        html_for_percentile_data = '<br>'
        stations = self.station_name.split(",") 
        num_of_stations = len(stations)
        class_by_row = ''
        
        table_class = 'tables'
        INVALID_VALUE = []
        if self._read_var_type() == 'prcp':
           table_class = 'rain_color'
           self.param = 'Precp'
           
        if self._read_var_type() == 'temp':
           INVALID_VALUE = ['-99.5', '-99.6']
           self.param = 'T'
           
        if num_of_stations == 1 and self.time_unit == 'month': # for single station monthly data, first column is year
            all_values = self.get_single_station_data(stations)
            calc_title = self._read_calc_title()
            title = ["年\月", "1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月", calc_title.encode('utf-8'), "月/年"]
            column_avg = self._calc_column_avg(all_values, title="年際平均")
            html_for_table = table.list2table_general(all_values, twin_header=False,  first_header=title, 
                                                      align={'center':[0]}, filtered_data=INVALID_VALUE, 
                                                      param=self.param, foot=column_avg)
        elif self.time_unit == 'day':
            all_values, ordered_data = self.get_multiple_station_data(stations, num_of_stations)
            colors = self._read_color()
            if colors != '':
                class_by_row = self.set_text_color(colors, all_values)
            first_header_list, second_header_list = self.get_day_title(ordered_data) 
            column_avg = self._calc_column_avg(all_values)
            html_for_table = table.list2table_general(all_values, twin_header=True, first_header=first_header_list, second_header=second_header_list, \
                                                      align={'center':[0]}, custom_class=class_by_row, table_class=table_class, 
                                                      filtered_data=INVALID_VALUE, param=self.param, foot=column_avg)         
        else:
            # for multiple station and single station with yearly data, the first colum is station.
            all_values, ordered_data = self.get_multiple_station_data(stations, num_of_stations)
            first_header_list, second_header_list = self.get_multiple_station_title(ordered_data)
            column_avg = self._calc_column_avg(all_values)
            if self.time_unit == 'month':
                html_for_table = table.list2table_general(all_values, twin_header=True, first_header=first_header_list, second_header=second_header_list, \
                                                          align={'center':[0]}, table_class=table_class, filtered_data=INVALID_VALUE, param=self.param,
                                                          foot=column_avg)                                                                                   
            elif self.time_unit in ['year', 'custom']:
                html_for_table = table.list2table_general(all_values, first_header=first_header_list, align={'center':[0]}, \
                                                          table_class=table_class, filtered_data=INVALID_VALUE, param=self.param,
                                                          foot=column_avg)         
                                                          
            if hasattr(self, 'percentile_data'):
                self.percentile_name = self.index_name.split('percent')[1][:2]
                percentile_values, header_list = self.get_percentile_data(stations, all_values)

                html_for_percentile_data += '<div class="percentile_block"><a href="#" id="percentile_link">點此看第'+ self.percentile_name + '百分位原始值</a><span id="percentile_symbol">+</span><div class="percentile_table">'
                html_for_percentile_data += table.list2table_general(percentile_values, twin_header=False, first_header=header_list, \
                                                      align={'center':[0]}, table_class=table_class, filtered_data=INVALID_VALUE, param=self.param)                                                       
                html_for_percentile_data += '</div></div>'   
            
            if hasattr(self, 'climate_value'):
                print self.climate_value
                climate_values, header_list = self.get_climate_values(stations, self.climate_value)
                html_for_percentile_data += '<div class="climate_value_block"><a href="#" id="climate_value_link">點此看氣候值原始值</a><span id="climate_symbol">+</span><div class="climate_table">'
                html_for_percentile_data += table.list2table_general(climate_values, twin_header=False, first_header=header_list, \
                                                     align={'center':[0]}, table_class=table_class, filtered_data=INVALID_VALUE, param=self.param)                                                       
                html_for_percentile_data += '</div></div>'                  
            
        title = self.gen_title()
        description = '<br>附註：加星號(*)表示非完整資料'
        description += '<br>' + self.config['index_name'][self.index_name].get('description', '').encode('utf-8')
        description += '<br>'
        return title + html_for_table + html_for_percentile_data + description  #.decode('utf-8')
    
    def gen_title(self):
        title = self.title.replace('<', '&lt;')
        title = title.replace('>', '&gt;')
        
        self.unit = self._read_unit()
        text = title.encode('utf-8') + self.time_unit_chn.encode('utf-8')
        if self.value_selector.split('_')[0] == 'anomaly':
            text += '距平'
        text += '列表' 
        if self.unit != '':
            text += ' (單位:' + self.unit.encode('utf-8') 
            # if hasattr(self, 'climate_value') and self.time_unit == 'month':
                # text +=  ', 氣候值：' + str(self.climate_value)
            text += ')'            
        return '<span class="table_title_block">' + text + '</span><br><br>'.encode('utf-8')
        
    def get_single_station_data(self, stations):
        # only one station is stations[0]
        modified_station = stations[0][:5] + '0'
        
        date_and_value = self.data[modified_station]
        # sort data by datetime
        ordered_data = sorted(date_and_value, key=lambda x:x[0])
        ordered_value = ['X' if i is np.nan else i for i in list(zip(*ordered_data)[1])]
        if self.data_count != '':
            checked_ordered_value = self._check_value_is_complete(modified_station, date_and_value, self.data_count)        
        else:
            checked_ordered_value = ordered_value
  
        all_values = [[]]
        year_info = self.start_date.year
        num_of_value = (len(ordered_value))
        # 指定enumerate從1開始計數(idx)
        for idx, value in enumerate(checked_ordered_value, 1):
            # every twelve values in a row
            remainder = (idx) % 12
            year_diff = year_info - self.start_date.year
            all_values[year_diff].append(value)
            if remainder == 0:
                values = all_values[year_diff]

                incomplete_symbol_for_calc_value = self.incomplete_symbol if any(self.incomplete_symbol in str(i) for i in values) else ""
                # 計算每一列的計算值(依變數不同可能是累積值、平均值、最大/小值)
                row_value = checked_ordered_value[year_diff*12:(year_diff + 1)*12]
                #print row_value
                calc_type = self._read_calc_type()
                value_calculator = ValueCalculator(row_value, calc_type)
                
                if all([i == 'X' for i in row_value]):
                    all_values[year_diff].append('X')
                else:
                    all_values[year_diff].append(incomplete_symbol_for_calc_value + str(value_calculator.calc_value()))

                all_values[year_diff].insert(0, year_info)
                all_values[year_diff].append(year_info)
                
                is_the_last_value = (idx == num_of_value)
                if not is_the_last_value:
                    year_info += 1
                    all_values.append([])
        return all_values

    def _calc_column_avg(self, all_values, title="測站平均"):
        data_only_values = []
        for i, all_data in enumerate(all_values):
            data_only_values.append([])
            for single_value in all_data[1:-1]:
                if isinstance(single_value, str) and '*' in single_value:
                    single_value = single_value.replace('*', '')
                if single_value == 'X':
                    single_value = np.nan
                else:
                    single_value = float(single_value)
                data_only_values[i].append(single_value)

        columns_avg = [np.nanmean(z) for z in zip(*data_only_values)]

        result_avg = [title]
        result_avg.extend(columns_avg)
        result_avg.append(title)
        return result_avg
        
    def _fill_checked_value(self, is_complete, value, decimal=1):
        #資料若存在data_complete_list裡面時，出現nan就寫0 (是不是只有日數才合理)
        if isinstance(value, Decimal):
            value = float(value)
        if np.isnan(value):
            value = '0'  

        if not is_complete:
            if isinstance(value, float):
                return self.incomplete_symbol + get_round_str(value, decimal)
            else:
                return self.incomplete_symbol + str(value)
        if isinstance(value, float):
            return get_round_str(value, decimal)            
        return value
        
    def _check_value_is_complete(self, station, datetime_and_value, data_complete_list):
        """ data complete list裡面是真正有資料的東西"""
        checked_values = []
        if station in data_complete_list:
            for i in datetime_and_value:
                if data_complete_list[station].has_key(i[0]):
                    is_complete = data_complete_list[station][i[0]] # True or False
                    checked_value = self._fill_checked_value(is_complete, i[1])
                    checked_values.append(checked_value)
                else:
                    checked_values.append('X')
        else:
            # station 不在data_complete_list裡，表此測站完全無資料，全部補X
            return ['X'] * len(datetime_and_value)
        return checked_values
       
    def _is_cross_year(self, start_date, end_date):   
        new_start_date = datetime(end_date.year, start_date.month, start_date.day)
        
        return new_start_date > end_date
       
    def get_multiple_station_data(self, stations, num_of_stations):
        all_values = [[]]
        
        data_length = max(len(v) for k, v in self.data.items())
        for idx_stn, stn_id in enumerate(stations):
            date_and_value = self.data[stn_id[:5]+'0']
            
            # sort data by datetime
            ordered_data = sorted(date_and_value, key=lambda x:x[0])          
            ordered_value = [np.nan if i is np.nan else i for i in list(zip(*ordered_data)[1])]

            if len(ordered_value) == 1 and np.isnan(ordered_value[0]):
                ordered_value = [np.nan] * data_length
            
            # add incomplete symbol '*'
            if self.data_count != '':
                checked_ordered_value = self._check_value_is_complete(stn_id[:5]+'0', date_and_value, self.data_count)
            else:
                #print ordered_value
                checked_ordered_value = ordered_value #['X' if np.isnan(float(i)) else i for i in ordered_value]

            incomplete_symbol_for_calc_value = self.incomplete_symbol if any(self.incomplete_symbol in str(i) for i in checked_ordered_value) else ""

            all_values[idx_stn] = checked_ordered_value 
            
            if self._read_calc_type() != 'nan':
                if all([i == 'X' for i in checked_ordered_value]):
                    all_values[idx_stn].append('X')
                else:
                    if self.time_unit == 'year':
                        value_calculator = ValueCalculator(checked_ordered_value, "avg")
                        all_values[idx_stn].append(incomplete_symbol_for_calc_value + str(value_calculator.calc_value()))
                    elif self.time_unit == 'day':
                        value_calculator = ValueCalculator(checked_ordered_value, self._read_calc_type())
                        all_values[idx_stn].append(incomplete_symbol_for_calc_value + str(value_calculator.calc_value()))
                    else :
                        calc_type = self._read_calc_type()
                        value_calculator = ValueCalculator(checked_ordered_value, calc_type)
                        all_values[idx_stn].append(incomplete_symbol_for_calc_value + str(value_calculator.calc_value()))
            
            # get the chinese name of station
            stn_info = Station.CWBStationInfo 
            stn_names = {stn['id']: {'chn_name':stn['chName'], 'code6':stn['realId'][-1][0] } for stn in stn_info} 
            stn_chname = stn_names[stn_id[0:5]]['chn_name']
            # add chinese name to the first and last column
            
            all_values[idx_stn].insert(0, stn_chname)
            all_values[idx_stn].append(stn_chname)
            # print ordered_value
            is_the_last_station = (idx_stn == (num_of_stations - 1))
            if not is_the_last_station:
                all_values.append([])       

        return all_values, ordered_data

        
    def get_percentile_data(self, stations, all_values):     
        new_values = []
        stations = [station[:5]+'0'  for station in stations]     
        first_stn_data = self.percentile_data[stations[0]]
        month_list = sorted(first_stn_data.keys())        
        for idx, row_values in enumerate(all_values):
            new_row_value = [row_values[0]]
            stn_data = self.percentile_data[stations[idx]]
            
            for month in month_list:
                new_row_value.append('{0:.1f}'.format(stn_data[month]))
            new_row_value.append(row_values[0])
            new_values.append(new_row_value)
            
        if month_list[0] == 'year':
            month_list[0] = '年資料第' + self.percentile_name + '百分位'
        if month_list[0] == 'custom':
            start_date_str = datetime.strftime(self.start_date, '%m/%d')
            end_date_str = datetime.strftime(self.end_date, '%m/%d')
            month_list[0] = '自訂時間(' + start_date_str + '~' +  end_date_str + ')第' + self.percentile_name + '百分位'
        header_list = ['站名'] + month_list + ['站名']
        return new_values, header_list
        
    def get_climate_values(self, stations, climate_values):     
        new_values = []
        stations = [station[:5]+'0'  for station in stations]     
        stn_info = Station.CWBStationInfo 

        #first_stn_data = climate_values[stations[0]]
        #month_list = sorted(first_stn_data.keys())        
        month_list = range(1,13)
        for stn, stn_values in climate_values.items():
            new_row_value = [stn_info[stn[:5]]['chName']]            
            for month in month_list:
                new_row_value.append('{0:.1f}'.format(stn_values[month-1]))
            new_row_value.append(stn_info[stn[:5]]['chName'])
            new_values.append(new_row_value)
            
        if month_list[0] == 'year':
            month_list[0] = '年資料氣候值'
        if month_list[0] == 'custom':
            start_date_str = datetime.strftime(self.start_date, '%m/%d')
            end_date_str = datetime.strftime(self.end_date, '%m/%d')
            month_list[0] = '自訂時間(' + start_date_str + '~' +  end_date_str + ')氣候值'
        header_list = ['站名'] + month_list + ['站名']
        return new_values, header_list
        
             
    def get_day_title(self, ordered_data):
        all_year_list = [date.year for date in zip(*ordered_data)[0]]
        first_header_list = self._get_year_show_times(all_year_list)             
        second_header_list = [datetime.strftime(date,'%m/%d') for date in list(zip(*ordered_data)[0])]
        if self._read_calc_type() == 'nan':
            first_header_list.append("")
        else:
            first_header_list.append(self._read_calc_type())        
        return first_header_list, second_header_list        
        
    def get_multiple_station_title(self, ordered_data): 
        all_year_list = [date.year for date in zip(*ordered_data)[0]]
        first_header_list = self._get_year_show_times(all_year_list)
        if self._read_calc_type() == 'nan':
            first_header_list.append("")
        elif self.time_unit == 'year':
            first_header_list.append("平均值")
        else:
            calc_title = self._read_calc_title()
            first_header_list.append(calc_title.encode('utf-8'))
        second_header_list = [datetime.strftime(date,'%m') for date in list(zip(*ordered_data)[0])]
        return first_header_list, second_header_list
    
    def _get_year_show_times(self, all_year_list):
        return [ [len(list(group)), k] for k, group in groupby(all_year_list)]    

    def filter_nan_data(self, data):
        nan_list = [np.nan, "nan", "no", "X"]
        values_without_nan = [i for i in data if i not in nan_list]
        # change the value with * to integer, and string "0" to integer 0.
        int_values_without_nan = [int(re.sub('[*]','',i)) if isinstance(i,str) else i for i in values_without_nan]

        return int_values_without_nan

    def _read_unit(self):
        return self.config['index_name'][self.index_name]['unit']        
        
    def _read_var_type(self):
        return self.config['index_name'][self.index_name]['var_type']    
        
    def _read_calc_type(self):
        return self.config['index_name'][self.index_name]['calc_type']
    
    def _read_calc_title(self):
        return self.config['index_name'][self.index_name]['calc_type_chn_name']
        
    def _read_color(self):
        index = self.config['index_name'][self.index_name]
        if 'color_range' in index:
            color_range = index['color_range']
            color_index = index['color_index']
            return zip(color_range, color_index)        
        return ''
        
    def set_text_color(self, colors, all_values):
        all_rows = {}

        for i, row in enumerate(all_values):
            row_color = []
            row_color.extend(map(lambda x:self.check_color(x, colors), row[1:-1]))
            all_rows[i] = row_color
        return all_rows

    def check_color(self, num, colors):
        if num in ['X', 'nan'] or np.isnan(num):
            return 'dark'
        for criteria in colors:
            if float(num) > float(criteria[0]):
                return criteria[1]
        return colors[-1][1]                