import csv
from collections import defaultdict
import json
from collections import Counter
import random
from tqdm import tqdm
import argparse
from structured_to_query import *
from classify_data import *

def complete_time(time):
    """
    Complete the time tuple by filling missing month and day with 0.

    Args:
    time (tuple): A tuple containing year, month, and day.

    Returns:
    tuple: A tuple with year, month, and day where missing values are replaced with 0.
    """
    year, month, day = time
    return (year, month if month is not None else 0, day if day is not None else 0)

def custom_sort(item):
    """
    Define the order of temporal relations.

    Args:
    item (tuple): A tuple containing temporal relation data.

    Returns:
    int: An integer representing the order of the temporal relation.
    """
    order = {
        "dot_to_dot_equal": 0, 
        "dot_to_interval_during": 1, 
        "interval_to_interval_equal": 2, 
        "interval_to_interval_during": 3, 
        "interval_to_interval_overlap": 4
    }
    level = order[item[2]]
    return level

def judge_imply(key1, key2, subject1=None, subject2=None, S=True):
    """
    Judge whether two keys imply a co-temporal relationship.

    Args:
    key1, key2 (tuple): Keys representing temporal data.
    subject1, subject2 (str, optional): Subjects involved in the temporal relationship.
    S (bool, optional): Indicates the structure of the keys.

    Returns:
    tuple or None: A tuple representing the co-temporal relationship or None if no relationship.
    """
    if S:
        if len(key1) == 3:  # Key format: (S1_R1_O2) or (S2_R1_O1)
            R_S_1, start1, end1 = key1
            R_S_2, start2, end2 = key2

            if start1 == end1:
                end1 = 'None'
            if start2 == end2:
                end2 = 'None'
        else:  # Key format: (S1_R2_O2)
            relation1, object_1, start1, end1 = key1
            relation2, object_2, start2, end2 = key2

            R_S_1 = (relation1, object_1)
            R_S_2 = (relation2, object_2)

            if relation1 != relation2:
                if start1 == end1:
                    end1 = 'None'
                if start2 == end2:
                    end2 = 'None'
    else:  # Key format: (S2_R1_O2) and (S2_R2_O2)
        relation1, object_1, start1, end1 = key1
        relation2, object_2, start2, end2 = key2

        R_S_1 = (subject1, relation1, object_1)
        R_S_2 = (subject2, relation2, object_2)

        if start1 == end1:
            end1 = 'None'
        if start2 == end2:
            end2 = 'None'

    # Convert 'None' to tuple (None, None, None)
    start1 = eval(start1) if start1 != 'None' else (None, None, None)
    end1 = eval(end1) if end1 != 'None' else (None, None, None)
    start2 = eval(start2) if start2 != 'None' else (None, None, None)
    end2 = eval(end2) if end2 != 'None' else (None, None, None)

    # Determine if the time is a point-time
    point_time1 = start1 if end1 == (None, None, None) else end1 if start1 == (None, None, None) else None
    point_time2 = start2 if end2 == (None, None, None) else end2 if start2 == (None, None, None) else None

    # Check if both events are point-time
    if point_time1 is not None and point_time2 is not None:
        if complete_time(point_time1) == complete_time(point_time2) and complete_time(point_time1)[1] != 0 and complete_time(point_time1)[2] != 0:
            # Example: time1 (2014, 1, 1) and time2 (2014, 1, 1) -> equal
            return ((complete_time(point_time1), R_S_1), R_S_2, "dot_to_dot_equal")
        elif complete_time(point_time1)[0] != complete_time(point_time2)[0]:  # Different years
            return None  # Not co-temporal
        elif complete_time(point_time1)[0] == complete_time(point_time2)[0] and complete_time(point_time1)[1] != complete_time(point_time2)[1] and 0 not in [complete_time(point_time1)[1], complete_time(point_time2)[1]]:
            # Different months
            return None
        elif complete_time(point_time1)[0] == complete_time(point_time2)[0] and complete_time(point_time1)[1] == complete_time(point_time2)[1] and complete_time(point_time1)[2] != complete_time(point_time2)[2] and 0 not in [complete_time(point_time2)[2], complete_time(point_time1)[2]]:
            # Different days
            return None
        else:
            return 'flag'  # Ambiguous co-temporal expression (e.g., (2014, 0, 0) & (2014, 6, 1))

    # Point-time & interval-time
    if point_time1 is not None and point_time2 is None:
        point_time1 = complete_time(point_time1)
        start2 = complete_time(start2)
        end2 = complete_time(end2)
        if start2 < point_time1 < end2:
            if point_time1[0] not in [start2[0], end2[0]]:
                return ((point_time1, R_S_1), R_S_2, "dot_to_interval_during")
            elif point_time1[0] == start2[0] and start2[1] == 0:
                return 'flag'
            elif point_time1[0] == end2[0] and point_time1[1] == 0:
                return 'flag'
            elif point_time1[0] == start2[0] and point_time1[1] == start2[1] and start2[2] == 0:
                return 'flag'
            elif point_time1[0] == end2[0] and point_time1[1] == end2[1] and point_time1[2] == 0:
                return 'flag'
            return ((point_time1, R_S_1), R_S_2, "dot_to_interval_during")
        elif point_time1[0] not in [start2[0], end2[0]]:
            return None
        elif point_time1[0] == start2[0] and point_time1[1] != start2[1] and point_time1[1] != 0 and start2[1] != 0:
            return None
        elif point_time1[0] == start2[0] and point_time1[1] == start2[1] and point_time1[2] != start2[2] and point_time1[2] != 0 and start2[2] != 0:
            return None
        elif point_time1[0] == end2[0] and point_time1[1] != end2[1] and point_time1[1] != 0 and end2[1] != 0:
            return None
        elif point_time1[0] == end2[0] and point_time1[1] == end2[1] and point_time1[2] != end2[2] and point_time1[2] != 0 and end2[2] != 0:
            return None
        else:
            return 'flag'

    if point_time2 is not None and point_time1 is None:  # Same logic as above but reversed
        point_time2 = complete_time(point_time2)
        start1 = complete_time(start1)
        end1 = complete_time(end1)
        if start1 < point_time2 < end1:
            if point_time2[0] not in [start1[0], end1[0]]:
                return ((point_time2, R_S_1), R_S_2, "dot_to_interval_during")
            elif point_time2[0] == start1[0] and point_time2[1] == start1[1] == 0:
                return 'flag'
            elif point_time2[0] == end1[0] and point_time2[1] == end1[1] == 0:
                return 'flag'
            elif point_time2[0] == start1[0] and point_time2[1] != start1[1] and ((point_time2[1] == 0 and start1[1] != 0) or (point_time2[1] != 0 and start1[1] == 0)):
                return 'flag'
            elif point_time2[0] == end1[0] and point_time2[1] != end1[1] and ((point_time2[1] == 0 and end1[1] != 0) or (point_time2[1] != 0 and end1[1] == 0)):
                return 'flag'
            return ((point_time2, R_S_1), R_S_2, "dot_to_interval_during")
        elif point_time2[0] not in [start1[0], end1[0]]:
            return None
        elif point_time2[0] == start1[0] and point_time2[1] != start1[1] and point_time2[1] != 0 and start1[1] != 0:
            return None
        elif point_time2[0] == start1[0] and point_time2[1] == start1[1] and point_time2[2] != start1[2] and point_time2[2] != 0 and start1[2] != 0:
            return None
        elif point_time2[0] == end1[0] and point_time2[1] != end1[1] and point_time2[1] != 0 and end1[1] != 0:
            return None
        elif point_time2[0] == end1[0] and point_time2[1] == end1[1] and point_time2[2] != end1[2] and point_time2[2] != 0 and end1[2] != 0:
            return None
        else:
            return 'flag'

    start1 = complete_time(start1)
    end1 = complete_time(end1)
    start2 = complete_time(start2)
    end2 = complete_time(end2)

    # If neither is a point-time, compare intervals
    if point_time1 is None and point_time2 is None:
        if (start1 == end2) or (start2 == end1):
            return 'flag'
        if start1[0] == end2[0] and ((start1[1] == 0 and end2[1] != 0) or (start1[1] != 0 and end2[1] == 0)):
            return 'flag'
        if start2[0] == end1[0] and ((start2[1] == 0 and end1[1] != 0) or (start2[1] != 0 and end1[1] == 0)):
            return 'flag'
        if start1[0] == end2[0] and start1[1] == end2[1] and ((start1[2] == 0 and end2[2] != 0) or (start1[2] != 0 and end2[2] == 0)):
            return 'flag'
        if start2[0] == end1[0] and start2[1] == end1[1] and ((start2[2] == 0 and end1[2] != 0) or (start2[2] != 0 and end1[2] == 0)):
            return 'flag'
        if start1 == start2 and end1 == end2:
            return (((start1, end1), R_S_1), R_S_2, "interval_to_interval_equal")
        if (start2 < start1 < end1 <= end2) or (start2 <= start1 < end1 < end2):
            return (((start1, end1), R_S_1), R_S_2, "interval_to_interval_during")
        if (start1 <= start2 < end2 < end1) or (start1 < start2 < end2 <= end1):
            return (((start2, end2), R_S_2), R_S_1, "interval_to_interval_during")
        if start1 < start2 < end1 < end2:
            return (((start2, end1), R_S_1), R_S_2, 'interval_to_interval_overlap')
        if start2 < start1 < end2 < end1:
            return (((start1, end2), R_S_1), R_S_2, 'interval_to_interval_overlap')
        if start1 < end1 < start2 < end2:
            return None
        if start2 < end2 < start1 < end1:
            return None
        return 'flag'

def main(rawdata_path, qid_path, subject_path, object_path, output_path):
    """
    Main function to process data and classify temporal relationships.

    Args:
    rawdata_path (str): Path to the raw data.
    qid_path (str): Path to the QID names.
    subject_path (str): Path to the subject facts.
    object_path (str): Path to the object facts.
    output_path (str): Path to store the output data.
    """
    query_templates = {
        'S1_R1_O2': 'templates/S1_R1_O2.csv',
        'S2_R1_O1': 'templates/S2_R1_O1.csv',
        'S1_R2_O2': 'templates/S1_R2_O2.csv',
        'S2_R1_O2': 'templates/S2_R1_O2.csv',
        'S2_R2_O2': 'templates/S2_R2_O2.csv'
    }

    for mission_name in ['S1_R1_O2', 'S2_R1_O1', 'S1_R2_O2', 'S2_R1_O2', 'S2_R2_O2']:
        constructed_data = []
        same_S_ST_ET = defaultdict(list)
        point_templates_path = 'point_templates/' + mission_name + '.csv'
        interval_templates_path = 'interval_templates/' + mission_name + '.csv'
        question_templates = read_query_templates(query_templates[mission_name])
        name_dict = read_qid_names(qid_path)
        point_templates = read_generate_templates(point_templates_path)
        interval_templates = read_generate_templates(interval_templates_path)
        store_time = {}
        is_subject = True 
        if 'S2_R1_O1' in mission_name:
            is_subject = False
        if is_subject:
            question_fact_path = subject_path
            DA_path = object_path
        else:
            question_fact_path = object_path
            DA_path = subject_path

        fact_dict = {}
        time_search = {}
        with open(question_fact_path, 'r') as f:  # Load facts related to the mission entity
            for l in f:
                item = json.loads(l.strip())
                entity = item.get("entity", "")
                facts = item.get("facts", [])
                data_list = item['data_list']
                fact_dict[entity] = facts
                time_search[entity] = data_list

        DA_object = {}
        
        if 'S1_R1_O2' in mission_name:
            relation_limit = ['P39', 'P102', 'P108', 'P127']
        elif 'S2_R1_O1' in mission_name:
            relation_limit = ['P39', 'P102', 'P108', 'P127', 'P54', 'P6', 'P488', 'P69']
        elif 'S1_R2_O2' in mission_name:
            relation_limit = ['P39', 'P102', 'P108','P6',"P69",'P286','P54']
        elif 'S2_R1_O2' in mission_name:
            relation_limit = ['P39', 'P102', 'P108', 'P127','P6',"P69",'P488','P54','P286']
        elif 'S2_R2_O2' in mission_name:
            relation_limit = ['P39', 'P102', 'P108', 'P127','P6',"P69",'P488','P54','P286']

        if is_subject:
            with open(DA_path, 'r') as f:  # Load object data
                for l in f:
                    item = json.loads(l.strip())
                    name = item.get("name", "")
                    data = item.get("data_list", [])
                    relation = data[0][0]
                    if relation in relation_limit:
                        if relation not in DA_object:
                            DA_object[relation] = []
                        if name not in DA_object[relation]:
                            DA_object[relation].append(name)
        else:
            with open(DA_path, 'r') as f:
                for l in f:
                    item = json.loads(l.strip())
                    name = item.get("entity", "")
                    data_list = item['data_list']
                    for data in data_list:
                        relation = data[0]
                        if relation in relation_limit:
                            if relation not in DA_object:
                                DA_object[relation] = []
                            if name not in DA_object[relation]:
                                DA_object[relation].append(name)

        with open(rawdata_path, 'r', newline='', encoding='utf-8') as infile:  # Load raw data
            tsv_reader = csv.reader(infile, delimiter='\t')
            for row in tsv_reader:
                relation, subject, object_, start_time, end_time = row
                key = (relation, subject, object_)  # Use (relation, subject, object) as key
                store_time[key] = (start_time, end_time)

        if mission_name == 'S1_R1_O2':
            with open(rawdata_path, 'r', newline='', encoding='utf-8') as infile:
                tsv_reader = csv.reader(infile, delimiter='\t')
                for row in tsv_reader:
                    relation, subject, object_, start_time, end_time = row
                    key = (relation, subject)  # Use (relation, subject) as key
                    same_S_ST_ET[key].append((object_, start_time, end_time))

            filtered_subjects = {object_: data_list for object_, data_list in same_S_ST_ET.items() if object_[0] in ['P54', 'P39', 'P102', 'P108', 'P127']}

        elif mission_name == 'S2_R1_O1':
            with open(rawdata_path, 'r', newline='', encoding='utf-8') as infile:
                tsv_reader = csv.reader(infile, delimiter='\t')
                for row in tsv_reader:
                    relation, subject, object_, start_time, end_time = row
                    key = (relation, object_)  
                    same_S_ST_ET[key].append((subject, start_time, end_time))

            filtered_subjects = {object_: data_list for object_, data_list in same_S_ST_ET.items() if object_[0] in ["P54", "P39", "P108", "P102", "P69", "P488", "P6", "P127"]}

        elif mission_name in ['S1_R2_O2', 'S2_R1_O2', 'S2_R2_O2']:
            with open(rawdata_path, 'r', newline='', encoding='utf-8') as infile:
                tsv_reader = csv.reader(infile, delimiter='\t')
                for row in tsv_reader:
                    relation, subject, object_, start_time, end_time = row
                    key = subject 
                    same_S_ST_ET[key].append((relation, object_, start_time, end_time))

            filtered_subjects = {object_: data_list for object_, data_list in same_S_ST_ET.items() if 4 < len(data_list) < 13}
            if mission_name != 'S1_R2_O2':
                filtered_subjects = random.sample(filtered_subjects.items(), 4000)
                filtered_subjects = {item[0]: item[1] for item in filtered_subjects}

        if mission_name in ['S2_R1_O1', 'S1_R2_O2', 'S1_R1_O2']:
            exit_flag = False
            for key, value_list in tqdm(filtered_subjects.items()):
                min_time_units = []
                flag = 0
                if exit_flag:
                    break
                for i in range(len(value_list)):         
                    for j in range(i + 1, len(value_list)):
                        key1 = value_list[i]
                        key2 = value_list[j]
                        min_time_unit = None
                        if mission_name == 'S1_R2_O2':
                            relation1, object_1, start1, end1 = key1
                            relation2, object_2, start2, end2 = key2
                            relation_pair_str = relation1 + '-' + relation2
                            if relation_pair_str in ['P39-P102', 'P39-P108', 'P102-P39', 'P69-P108', 'P108-P69', 'P69-P39', 'P108-P39', 'P102-P108', 'P69-P102', 'P102-P69', 'P54-P69', 'P54-P286', 'P39-P6']:
                                min_time_unit = judge_imply(key1, key2)
                        else:
                            min_time_unit = judge_imply(key1, key2)

                        if min_time_unit == 'flag':
                            flag = 'flag'

                        if min_time_unit:
                            min_time_units.append(min_time_unit)

                    if flag == 'flag':
                        min_time_units = []
                        break

                if min_time_units:
                    if mission_name in ['S1_R1_O2', 'S2_R1_O1']:
                        relation, subject = key
                        current_data = {
                            "entity": subject,
                            "relation": relation,
                            "query": min_time_units
                        }                 
                    else:
                        subject = key
                        current_data = {
                            "entity": subject,
                            "query": min_time_units
                        }
                    constructed_data.append(current_data)
        else:
            exit_flag = False
            for i, (key1, value_list1) in enumerate(tqdm(filtered_subjects.items())):
                if exit_flag:
                    break
                for j, (key2, value_list2) in enumerate(filtered_subjects.items()):
                    if exit_flag:
                        break
                    if j <= i:  # Skip duplicate and self-comparisons
                        continue
                    min_time_units = []
                    flag = 0
                    for data1 in value_list1:
                        for data2 in value_list2:
                            subject1 = key1
                            subject2 = key2
                            relation1, object1, start1, end1 = data1
                            relation2, object2, start2, end2 = data2
                            if mission_name == 'S2_R1_O2':
                                if relation1 == relation2 and object1 != object2 and subject1 != subject2:  # Ensure same relation but different objects
                                    min_time_unit = judge_imply(data1, data2, subject1, subject2, False)
                                    if min_time_unit == 'flag':
                                        flag = 'flag'
                                    if min_time_unit:
                                        min_time_units.append(min_time_unit)
                            else:
                                relation_pair_str = relation1 + '-' + relation2
                                if relation_pair_str in ['P39-P102', 'P39-P108', 'P102-P39', 'P69-P108', 'P108-P69', 'P69-P39', 'P108-P39', 'P102-P108', 'P69-P102', 'P102-P69', 'P54-P69', 'P54-P286', 'P39-P6']:
                                    if object1 != object2:  # Ensure same relation but different objects
                                        min_time_unit = judge_imply(data1, data2, subject1, subject2, False)
                                        if min_time_unit == 'flag':
                                            flag = 'flag'
                                        if min_time_unit:
                                            min_time_units.append(min_time_unit)

                        if flag == 'flag':
                            min_time_units = []
                            break

                    if min_time_units:
                        if mission_name == 'S2_R1_O2':
                            subject = (key1, key2)
                            current_data = {
                                "entity_pair": subject,
                                "query": min_time_units
                            }
                        else:
                            subject = (key1, key2, relation1, relation2)
                            current_data = {
                                "entity_pair": subject,
                                "query": min_time_units
                            }
                        constructed_data.append(current_data)

        all_data = []
        for current_data in constructed_data:
            data = data_generate(mission_name, question_templates, current_data, store_time, point_templates, interval_templates, name_dict, fact_dict, DA_object, time_search, is_subject)
            if data:
                for k in data:
                    new_data = classify_data(k)
                    if new_data:
                        all_data.append(new_data)

        all_data = random.sample(all_data, 1000)
        for data in all_data:
            if data['class'] == 'equal':
                with open(output_path + '/equal.json', 'a', encoding='utf-8') as f:
                    json_data = json.dumps(data)
                    f.write(json_data + '\n')
            elif data['class'] == 'during':
                with open(output_path + '/during.json', 'a', encoding='utf-8') as f:
                    json_data = json.dumps(data)
                    f.write(json_data + '\n')
            elif data['class'] == 'overlap':
                with open(output_path + '/overlap.json', 'a', encoding='utf-8') as f:
                    json_data = json.dumps(data)
                    f.write(json_data + '\n')
            elif data['class'] == 'mix':
                with open(output_path + '/mix.json', 'a', encoding='utf-8') as f:
                    json_data = json.dumps(data)
                    f.write(json_data + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--rawdata_path', type=str, help='Path to raw data')
    parser.add_argument('--qid_path', type=str, help='Path to QID names')
    parser.add_argument('--subject_path', type=str, help='Path to subject facts')
    parser.add_argument('--object_path', type=str, help='Path to object facts')
    parser.add_argument('--output_path', type=str, default='data_without_temporal_expression', help='Output path to store the data')
    args = parser.parse_args()
    main(args.rawdata_path, args.qid_path, args.subject_path, args.object_path, args.output_path)
