#============================================================
# import from pjslib
from pjslib.general import get_upper_folder_path
from pjslib.general import accepts
from pjslib.logger import oanda_logger
#================================================
import os
import requests
import collections
import re
import numpy as np
from read_parameters import ReadParameters




class ReadForexData:
    """read the up-to-date forex data via oanda API"""
    def __init__(self, parameters_dict):
        self.mode = parameters_dict['mode']
        self.instruments_list = ['EUR_USD', 'USD_JPY', 'USD_CAD', 'GBP_USD', 'USD_CHF','AUD_USD']
        self.granularity = parameters_dict['granularity']
        self.candle_format = parameters_dict['candle_format']
        self.date_range = parameters_dict['date_range']
        self.url = "https://api-fxtrade.oanda.com/v1/candles?" \
                   "instrument=#instrument&" \
                   "count={date_range}&" \
                   "candleFormat={candle_format}&" \
                   "granularity={granularity}&" \
                   "dailyAlignment=0&" \
                   "alignmentTimezone=America%2FNew_York".format(date_range = self.date_range,
                                                                 candle_format = self.candle_format,
                                                                 granularity = self.granularity)
        # set the data output path
        parent_folder = os.path.join(get_upper_folder_path(2), 'data')
        data_folder = os.path.join(parent_folder, 'oanda')
        if self.mode == 'testing':
            self.file_path = os.path.join(data_folder, 'oanda_forex_testing_data.txt')
        elif self.mode == 'trading':
            self.file_path = os.path.join(data_folder, 'oanda_forex_trading_data.txt')
        self.forex_data_dict = collections.defaultdict(lambda :[])

    def write_forex_dict_to_file(self):
        path = self.file_path
        #self.forex_data_dict : {'EUR_USD':[('AUD_USD', '2014-9-9', 0.77157, 0.772, 0.767955, 0.76851, 0.76, 0.11, 0.14), ...]}
        with open (path, 'w', encoding = 'utf-8') as f:
            for instrument, days_feature_list in self.forex_data_dict.items():
                for day_features in days_feature_list:
                    day_features = [str(x) for x in day_features]
                    feature_str = ','.join(day_features)
                    f.write(feature_str)
                    f.write('\n')


    def format_forex_data_file_into_new_feature(self):
        # TODO
        pass

    def read_onanda_data(self):
        def compute_std(day, day_forex_list, feature, i, instrument):
            variance_list = []
            for j in range(day):
                feature_value = day_forex_list[i-j][feature]
                if feature == 'openMid':
                    if instrument == 'USD_JPY':
                        feature_value *= 10
                    else:
                        feature_value *= 1000
                elif feature == 'volume':
                    feature_value /= 1000
                variance_list.append(feature_value)
            std = np.std(variance_list)
            std = float("{:3.1f}".format(std))
            oanda_logger.info("instrument: {}, feature :{}, variance: {}".format(instrument, feature, std))
            return std

        '''read oanda data via online api to dict with several features'''
        ignore_date_num = 7
        for instrument in self.instruments_list:
            url = self.url.replace("#instrument", instrument)
            response = requests.get(url)
            response_status_code = response.status_code
            print("response_status_code: ", response_status_code)
            day_forex_list = dict(response.json())['candles']

            for i, day_forex_dict in enumerate(day_forex_list):
                if i < ignore_date_num or i > len(day_forex_list) - 1 - ignore_date_num: # -1-7
                    continue
                time = day_forex_dict['time']
                time = re.findall(r'([0-9]+-[0-9]+-[0-9]+)', time)[0]
                time_list = time.split('-')
                # switch year with day, day with month
                time_list[0], time_list[2] = time_list[2], time_list[0]
                time_list[0], time_list[1] = time_list[1], time_list[0]
                time = '/'.join(time_list)
                ## getting features
                # openMid
                openMid = day_forex_dict['openMid']
                openMid_1_day_ago = day_forex_list[i - 1]['openMid']
                openMid_1_day_percent = float("{:2.2f}".format(100*((openMid - openMid_1_day_ago)/ openMid)))
                openMid_3_day_std = compute_std(3, day_forex_list, 'openMid', i, instrument)
                openMid_7_day_std = compute_std(7, day_forex_list, 'openMid', i, instrument)
                # highMid
                highMid = day_forex_dict['highMid']
                highMid_1_day_ago = day_forex_list[i - 1]['highMid']
                highMid_1_day_percent = float("{:2.2f}".format(100*((highMid - highMid_1_day_ago) / highMid)))
                # lowMid
                lowMid = day_forex_dict['lowMid']
                lowMid_1_day_ago = day_forex_list[i - 1]['lowMid']
                lowMid_percent = float("{:2.2f}".format(100*((lowMid - lowMid_1_day_ago)/ lowMid)))
                # closeMid
                closeMid = day_forex_dict['closeMid']
                closeMid_1_day_ago = day_forex_list[i - 1]['closeMid']
                closeMid_1_day_later = day_forex_list[i + 1]['closeMid']
                closeMid_3_day_later = day_forex_list[i + 3]['closeMid']
                closeMid_7_day_later = day_forex_list[i + 7]['closeMid']
                closeMid_1_day_percent = float("{:2.2f}".format(100*((closeMid - closeMid_1_day_ago)/ closeMid)))
                # volume
                volume = day_forex_dict['volume']
                volume_1_day_ago = day_forex_list[i - 1]['volume']
                volume_1_day_percent = float("{:2.2f}".format(100*((volume - volume_1_day_ago)/ volume)))
                volume_3_day_std = compute_std(3, day_forex_list, 'volume', i, instrument)
                volume_7_day_std = compute_std(7, day_forex_list, 'volume', i, instrument)
                # profit
                profit_1_day = float("{:2.3f}".format(100*((closeMid_1_day_later - closeMid) / closeMid)))
                profit_3_day = float("{:2.3f}".format(100*((closeMid_3_day_later - closeMid) / closeMid)))
                profit_7_day = float("{:2.3f}".format(100*((closeMid_7_day_later - closeMid) / closeMid)))
                # custom feature
                real_body_percent = float("{:2.2f}".format(abs((openMid - closeMid) / (highMid - lowMid))))
                upper_shadow_percent = float("{:2.2f}".format(abs((highMid - openMid) / (highMid - lowMid))))
                lower_shadow_percent = float("{:2.2f}".format(abs((closeMid - lowMid) / (highMid - lowMid))))
                # 1,AA,1/14/2011,$16.71,$16.71,$15.64,$15.97,242963398,-4.42849,1.380223028,239655616,$16.19,$15.79,
                # -2.47066,19,0.187852
                day_forex_tuple = ('_', instrument, time, openMid_1_day_percent, highMid_1_day_percent, lowMid_percent,
                                   closeMid_1_day_percent, volume, volume_1_day_percent, openMid_3_day_std,
                                   openMid_7_day_std, volume_3_day_std, volume_7_day_std,
                                   real_body_percent, upper_shadow_percent, lower_shadow_percent, profit_1_day,
                                   profit_3_day, profit_7_day)
                self.forex_data_dict[instrument].append(day_forex_tuple)


