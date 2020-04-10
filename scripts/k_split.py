#!bin/usr/env python3

import os
import sys
import json
import math
import random

current_dir = os.path.dirname(os.path.realpath(__file__))

RANDOM = "random"
SPLIT = 'split'

SEED = 'seed'
SPLITS = 'splits'
DATASET = 'dataset'
DATAFILE = 'data'
PERCENT_TRAIN = 'percent_train'
FALSE_TRIP_RATIO = 'false_triples_ratio'
TYPE_SPLIT = 'type_split'

TRAIN = 'train.txt'
TEST =  'test.txt'

ENTITY_1 = 0
ENTITY_2 = 2
RELATION = 1

# Get command line arguments
# datafile contains all data to be split
def main():

    # Read arguments
    config_path = parse_args(sys.argv)

    # Load data from arguments
    config, data, entity_list, set_of_data= load_data(config_path)

    #Set the Seed
    seed = config[SEED]
    random.seed(seed)


    # Create splits directory
    dataset_dir = os.path.join(os.path.dirname(current_dir), config[DATASET])
    raw_splits_dir = os.path.join(os.path.dirname(current_dir), DATAFILE)
    if os.path.isdir(raw_splits_dir) is False:
        os.mkdir(raw_splits_dir)
    sub_dir = os.path.join(raw_splits_dir, config[DATASET])
    #Todo: Should delete splits directory if exists?
    isdir = os.path.isdir(sub_dir)
    if isdir is False:
        os.mkdir(sub_dir)

    # Generate and write each split
    create_splits(data, entity_list, set_of_data, sub_dir, config)


def parse_args(args):
    if(len(args) != 2 or ({'h','help'} & {arg.lower().strip().replace('-', '') for arg in args})):
        print("Usage: python3 gen_splits.py <path_to_config_file>")
        sys.exit(1)

    config_file = args[1]
    return config_file

def load_data(config_file):
    config_fd = open(config_file, 'r')

    config = json.load(config_fd)
    data = []
    entities = set()
    set_of_data = set()

    data_fd =  open(config[DATAFILE], 'r')

    # Read input file into a list of lines and a set of all entities seen
    for line in data_fd:
        data.append(line.strip('\n').split('\t'))
        set_of_data.add(tuple(line.strip('\n').split('\t')))
        entities.add(line.strip('\n').split('\t')[ENTITY_2])
    entity_list = list(entities)

    data_fd.close()
    config_fd.close()

    return config, data, entity_list, set_of_data

def create_splits(data, entity_list, set_of_data, sub_dir, config):
    if config[TYPE_SPLIT] == RANDOM:
        random_splits(data, entity_list, set_of_data, sub_dir, config)
    else:
        print("Split Type not Supported")
        sys.exit(1)

def random_splits(data, entity_list, set_of_data, sub_dir, config):
    split_num = config[SPLITS]
    percent_train = config[PERCENT_TRAIN]
    percent_test = round(1 - percent_train, 2)
    train_bound = math.floor(percent_train * len(data))
    false_triple_ratio =  config[FALSE_TRIP_RATIO]
    permanent_set_of_data = set_of_data.copy()
    for i in range(0, split_num):

    # Lists used to store output
        train = ''
        test = ''
        # Shuffle data to generate random split
        random.shuffle(data)

        #reset set of data for checking negative triples
        set_of_data = permanent_set_of_data

        #Generate split paths
        train_path, test_path = create_split_path(sub_dir, i)

        #Create train split
        for line in range(0,  len(data)):
            choose_split  = random.random()
            if(choose_split >= percent_test):
                train += (data[line][ENTITY_1] + '\t' + data[line][RELATION] + '\t' + data[line][ENTITY_2] + '\t' + '1' + '\n')
                #Generate Negative Triples
                train += generate_negatives(data, line, entity_list, set_of_data, false_triple_ratio)
            else:
                test += (data[line][ENTITY_1] + '\t' + data[line][RELATION] + '\t' + data[line][ENTITY_2] + '\t' + '1' + '\n')
                #Generate Negative Triples
                test += generate_negatives(data, line, entity_list, set_of_data, false_triple_ratio)

        write_out(train, train_path)
        write_out(test, test_path)

def generate_negatives(data, line, entity_list, set_of_data, false_triple_ratio):
    negatives = ''

    #Pick random entities for false triples, while avoiding duplicates
    for _ in range(0, false_triple_ratio):
        negative_entity = random.choices(entity_list)
        #If entity is already in a false triple keep choosing
        while (data[line][ENTITY_1], data[line][RELATION], negative_entity[0]) in set_of_data:
            negative_entity = random.choices(entity_list)
        #Append entity to the list and continue
        set_of_data.add((data[line][ENTITY_1], data[line][RELATION], negative_entity[0]))
        negatives += (data[line][ENTITY_1] + '\t' + data[line][RELATION] + '\t'+ negative_entity[0] + '\t' + '0' + '\n')
    return negatives

def write_out(data, path):
    path_fd = open(path, 'w+')
    path_fd.write(data)
    path_fd.close()

def create_split_path(sub_dir, split_num):
    #Create split directory
    split_dir  = os.path.join(sub_dir, str(split_num))
    isdir = os.path.isdir(split_dir)
    if isdir is False:
        os.mkdir(split_dir)

    #Generate all sub paths for the split
    train_file = TRAIN
    test_file = TEST
    train_path = os.path.join(split_dir, train_file)
    test_path = os.path.join(split_dir, test_file)
    return train_path, test_path

if __name__ == "__main__":
    main()
