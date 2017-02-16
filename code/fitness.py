# import from pjslib
from pjslib.general import get_upper_folder_path
from pjslib.general import accepts
from pjslib.logger import logger1
#================================================
import os
import sys
import re
import collections
from ga import GeneticAlgorithm
import pprint



class AmericanStockFitness():
    def __init__(self, parameter_dict):
        self._next_price_str = parameter_dict['input']['next_price_str']
        pass

    # population_dict：{‘asd':((datetime_object1,EUR), (datetime_object2,USD), (datetime_object3,JPY),...)}
    def __call__(self, input_data_dict, solution):
        # predicted_stock_sequence is sorted by time, from past to future
        population_name = solution.name
        predicted_stock_sequence_tuple = solution.classification_result_list

        predicted_days_num = len(predicted_stock_sequence_tuple)
        average_sum = 0
        for date,stock in predicted_stock_sequence_tuple:
            features_tuple = input_data_dict[date][stock]
            features_dict = dict(features_tuple._asdict())
            average_sum += float(features_dict[self._next_price_str])
            #print('profit_percent: ', float(features_dict[self._next_price_str]))

        average = average_sum/predicted_days_num
        solution.fitness = average
        logger1.info("----------SOLUTION_INFO-----------------------")
        logger1.info("solution_name: {}, result:{}"
                     .format(population_name, average, pprint.pformat(solution.classification_result_list)))
        logger1.info("chromosome: {}"
                     .format(pprint.pformat(''.join([str(x) for x in solution.chromosome_bits]))))
        logger1.info("classification_result:\n{}"
                     .format(pprint.pformat(solution.classification_result_list)))
        logger1.info("feature_dict: {}"
                     .format(pprint.pformat(solution.feature_dict)))
        logger1.info("----------SOLUTION_INFO END-------------------")
        logger1.info("\n\n")
        # return tuple
        return (population_name, average)
















