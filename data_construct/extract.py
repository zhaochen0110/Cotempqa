import csv
from collections import defaultdict
import json
from collections import Counter
import random
from tqdm import tqdm
import argparse
from data_construct.structured_to_query import *
from data_construct.classify_data import * 

## transfer the time into int tuple 
def complete_time(time):
    year, month, day = time
    return (year, month if month is not None else 0, day if day is not None else 0)

## define the order   
def custom_sort(item):
    order = {"dot_to_dot_equal": 0, "dot_to_interval_during": 1, "interval_to_interval_equal": 2, "interval_to_interval_during": 3, 'interval_to_interval_overlap': 4}
    level = order[item[2]]
    return level

## judge weather cotemporal from three dimensions: 
# 1. point-time & point time
# 2. point-time & interval time
# 3. interval-time & interval time
# key (which can distinguish a event)
# S -> False when have at least two variable(s,r,o) and one of them is variable (s)
# key(S1_R1_O2) -> (object, start time, end time)
# key(S2_R1_O1) -> (subject, start_time, end_time)
# key(S1_R2_O2) -> (relation, object, start_time, end_time)
# key(S2_R1_O2) and key(S2_R2_O2) -> (relation, object, start_time, end_time) + (subject1, subject2)
def judge_imply(key1, key2,subject1=None,subject2=None,S=True):
    if S:
        if len(key1)==3: # key(S1_R1_O2) or key(S2_R1_O1)
            R_S_1, start1, end1 = key1
            R_S_2, start2, end2 = key2

            # import pdb; pdb.set_trace()
            if start1 == end1:
                end1 = 'None'
            if start2 == end2:
                end2 = 'None'
        else: # key(S1_R2_O2)
            relation1, object_1, start1, end1 = key1
            relation2, object_2, start2, end2 = key2

            R_S_1 = (relation1, object_1)
            R_S_2 = (relation2, object_2)

            if relation1 != relation2:
                    
                if start1 == end1:
                    end1 = 'None'
                if start2 == end2:
                    end2 = 'None'
    else: # key(S2_R1_O2) and key(S2_R2_O2)
        relation1, object_1, start1, end1 = key1
        relation2, object_2, start2, end2 = key2

        R_S_1 = (subject1, relation1, object_1)
        R_S_2 = (subject2, relation2, object_2)


        if start1 == end1:
            end1 = 'None'
        if start2 == end2:
            end2 = 'None'


    # transfer None into tuple
    start1 = eval(start1) if start1 != 'None' else (None, None, None)
    end1 = eval(end1) if end1 != 'None' else (None, None, None)
    start2 = eval(start2) if start2 != 'None' else (None, None, None)
    end2 = eval(end2) if end2 != 'None' else (None, None, None)

    # judge weather is a point-time
    point_time1 = start1 if end1 == (None, None, None) else end1 if start1 == (None, None, None) else None
    point_time2 = start2 if end2 == (None, None, None) else end2 if start2 == (None, None, None) else None
    
    # if these two events are both point-time
    if point_time1 is not None and point_time2 is not None:
        if complete_time(point_time1) == complete_time(point_time2) and complete_time(point_time1)[1]!=0 and complete_time(point_time1)[2]!=0: #eg. time1 (2014, 1, 1) time2 (2014, 1, 1) -> equal
            return ((complete_time(point_time1), R_S_1), R_S_2, "dot_to_dot_equal") 
        elif complete_time(point_time1)[0]!=complete_time(point_time2)[0]: # year1 != year2
            return None # None -> not cotemporal
        elif complete_time(point_time1)[0]==complete_time(point_time2)[0] and complete_time(point_time1)[1]!=complete_time(point_time2)[1] and 0 not in [complete_time(point_time1)[1],complete_time(point_time2)[1]]: # month1 != month2
            return None
        elif complete_time(point_time1)[0]==complete_time(point_time2)[0] and complete_time(point_time1)[1]==complete_time(point_time2)[1] and complete_time(point_time1)[2]!=complete_time(point_time2)[2] and 0 not in [complete_time(point_time2)[2],complete_time(point_time1)[2]]: # day1 != day2
            return None
        else:
            return 'flag' # flag -> ambiguous cotemporal expression (eg. (2014, 0, 0) & (2014, 6, 1))

    # point-time & interval-time
    if point_time1 is not None and point_time2 is None:
        point_time1 = complete_time(point_time1)
        start2 = complete_time(start2)
        end2 = complete_time(end2)
        if start2<point_time1<end2:
            if point_time1[0] not in [start2[0],end2[0]]:  # start_year2 < start_year1 < end_year2
                return ((point_time1,R_S_1),R_S_2,"dot_to_interval_during")
            elif point_time1[0] == start2[0] and start2[1]==0: # eg. [(2014, 0, 0), (...)] & (2014, 6, 1)
                return 'flag'
            elif point_time1[0] == end2[0] and point_time1[1]==0: #eg. (2014, 0, 0) & [(...), (2014, 6, 1)]
                return 'flag'
            elif point_time1[0] == start2[0] and point_time1[1] == start2[1] and start2[2] == 0: #eg. [(2014, 6, 0), (...)] & (2014, 6, 1)
                return 'flag'
            elif point_time1[0] == end2[0] and point_time1[1] == end2[1] and point_time1[2] == 0: #eg. (2014, 6, 0) & [(...), (2014, 6, 1)]
                return 'flag'
            return ((point_time1,R_S_1),R_S_2,"dot_to_interval_during")
        elif point_time1[0] not in [start2[0],end2[0]]: # year1 < start_year2 or year1 > end_year2
            return None
        elif point_time1[0] == start2[0] and point_time1[1]!=start2[1] and point_time1[1]!=0 and start2[1]!=0: # eg. [(2014, 6, 0), (...)] & (2014, 5, 1)
            return None
        elif point_time1[0] == start2[0] and point_time1[1]==start2[1] and point_time1[2]!=start2[2] and point_time1[2]!=0 and start2[2]!=0: # eg. [(2014, 6, 5), (...)] & (2014, 6, 1)
            return None
        elif point_time1[0] == end2[0] and point_time1[1]!=end2[1] and point_time1[1]!=0 and end2[1]!=0: #eg. (2014, 7, 0) & [(...), (2014, 6, 1)]
            return None
        elif point_time1[0] == end2[0] and point_time1[1]==end2[1] and point_time1[2]!=end2[2] and point_time1[2]!=0 and end2[2]!=0: #eg. (2014, 6, 5) & [(...), (2014, 6, 1)]
            return None
        else:
            return 'flag'


    if point_time2 is not None and point_time1 is None: # the same as (point-time & interval-time) above
        point_time2=complete_time(point_time2)
        start1 = complete_time(start1)
        end1 = complete_time(end1)
        if start1<point_time2<end1:
            if point_time2[0] not in [start1[0],end1[0]]:
                return ((point_time2,R_S_1),R_S_2,"dot_to_interval_during")
            elif point_time2[0] == start1[0] and point_time2[1]==start1[1]==0:
                return 'flag'
            elif point_time2[0] == end1[0] and point_time2[1]==end1[1]==0:
                return 'flag'
            elif point_time2[0] == start1[0] and point_time2[1]!=start1[1] and ((point_time2[1]==0 and start1[1]!=0) or (point_time2[1]!=0 and start1[1]==0)):
                return 'flag'
            elif point_time2[0] == end1[0] and point_time2[1]!=end1[1] and ((point_time2[1]==0 and end1[1]!=0) or (point_time2[1]!=0 and end1[1]==0)):
                return 'flag'
            return ((point_time2,R_S_1),R_S_2,"dot_to_interval_during")
        elif point_time2[0] not in [start1[0],end1[0]]:
            return None
        elif point_time2[0] == start1[0] and point_time2[1]!=start1[1] and point_time2[1]!=0 and start1[1]!=0:
            return None
        elif point_time2[0] == start1[0] and point_time2[1]==start1[1] and point_time2[2]!=start1[2] and point_time2[2]!=0 and start1[2]!=0:
            return None
        elif point_time2[0] == end1[0] and point_time2[1]!=end1[1] and point_time2[1]!=0 and end1[1]!=0:
            return None
        elif point_time2[0] == end1[0] and point_time2[1]==end1[1] and point_time2[2]!=end1[2] and point_time2[2]!=0 and end1[2]!=0:
            return None
        else:
            return 'flag'        

    start1 = complete_time(start1, is_start=True)
    end1 = complete_time(end1, is_start=False)
    start2 = complete_time(start2, is_start=True)
    end2 = complete_time(end2, is_start=False)

    # import pdb; pdb.set_trace()

    if point_time1 is None and point_time2 is None:
        # s2 s1 e1 e2
        if (start1 ==  end2) or (start2 ==  end1):
            return 'flag'
        if start1[0] ==  end2[0] and ((start1[1] == 0 and end2[1] != 0) or (start1[1] != 0 and end2[1] == 0)):
            return 'flag'
        if start2[0] == end1[0] and ((start2[1] == 0 and end1[1] != 0) or (start2[1] != 0 and end1[1] == 0)):
            return 'flag'
        if start1[0] ==  end2[0] and start1[1]==end2[1] and ((start1[2]==0 and end2[2]!=0) or (start1[2]!=0 and end2[2]==0)):
            return 'flag'
        if start2[0] == end1[0] and start2[1]==end1[1] and ((start2[2]==0 and end1[2]!=0) or (start2[2]!=0 and end1[2]==0)):
            return 'flag'
        if start1==start2 and end1==end2:
            return (((start1, end1), R_S_1), R_S_2, "interval_to_interval_equal")
        
        if (start2 < start1 and start1< end1 and end1<= end2) or (start2 <= start1 and start1 < end1 and end1 < end2):
            return (((start1, end1), R_S_1), R_S_2, "interval_to_interval_during")
        
        # s1 s2 e2 e1
        if (start1 <= start2 and start2 < end2 and end2 < end1) or (start1 < start2 and start2 < end2 and end2 <= end1):
            return (((start2, end2), R_S_2), R_S_1, "interval_to_interval_during")
 
        # s1 s2 e1 e2
        if start1 < start2 and start2 < end1 and end1 < end2:
            return (((start2, end1), R_S_1), R_S_2, 'interval_to_interval_overlap')
        
        # s1 e2 e1 s2    
        if start2 < start1 and start1 < end2 and end2 < end1:
            return (((start1, end2), R_S_1), R_S_2, 'interval_to_interval_overlap')
        
        if start1<end1<start2<end2:
            return None
        
        if start2<end2<start1<end1:
            return None
        return 'flag'
        

def main(data_level,output_path):
    query_templates = {
        'S1_R1_O2':'templates/level_4.csv',
        'S2_R1_O1':'templates/level_5.csv',
        'S1_R2_O2':'templates/level_6.csv',
        'S2_R1_O2':'templates/level_7.csv',
        'S2_R2_O2':'templates/level_8.csv'
                       }
    equal = []
    during = []
    overlap = []
    mix = []
    # result_dict = defaultdict(lambda: defaultdict(list))
    data_file = f'raw_data/ailab_data_{data_level}.tsv'
    for mission_name in ['S1_R1_O2', 'S2_R1_O1', 'S1_R2_O2', 'S2_R1_O2', 'S2_R2_O2']:
        same_S_ST_ET = defaultdict(list)
        point_templates_path = 'generate_point_templates//'+mission_name+'.csv'
        interval_templates_path = 'generate_interval_templates//'+mission_name+'.csv'
        rawdata_path = f'raw_data/ailab_data_{data_level}.tsv'
        qid_path = f'qid/ailab_data_{data_level}.txt'
        subject_path = f'facts/ailab_{data_level}_subject_fact.json'
        object_path = f'facts/ailab_{data_level}_object_fact.json'
        question_templates = read_query_templates(query_templates[mission_name])
        name_dict = read_qid_names(qid_path)
        point_templates = read_generate_templates(point_templates_path)
        interval_templates = read_generate_templates(interval_templates_path)
        store_time = {}
        is_subject = True #判断问题的主体是否是subject，对于S2-R1_O1，其主体是object
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
        with open(question_fact_path, 'r') as f:  #获得任务主体相关的事实
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
            with open(DA_path, 'r') as f:  #我们这里将获取数据扩充所需要用到的对象，原则是首先获得不同的关系对应有哪些subject或者object
                for l in f:
                    item = json.loads(l.strip())
                    name = item.get("name", "")
                    data = item.get("data_list", [])
                    relation = data[0][0]
                    if relation in relation_limit:
                        if relation not in DA_object:
                            DA_object[relation]=[]
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
                                DA_object[relation]=[]
                            if name not in DA_object[relation]:
                                DA_object[relation].append(name)

        with open(rawdata_path, 'r', newline='', encoding='utf-8') as infile:  #使用对应的原始数据
            tsv_reader = csv.reader(infile, delimiter='\t')
            for row in tsv_reader:
                relation, subject, object_, start_time, end_time = row
                key = (relation, subject,object_)  # 注意这里，我们用relation, subject, object作为键
                store_time[key]=(start_time,end_time)

        if mission_name=='S1_R1_O2':
            with open(data_file, 'r', newline='', encoding='utf-8') as infile:
                tsv_reader = csv.reader(infile, delimiter='\t')
                for row in tsv_reader:
                    relation, subject, object_, start_time, end_time = row
                    key = (relation, subject)  # 注意这里，我们用relation, subject, object作为键
                    same_S_ST_ET[key].append((object_, start_time, end_time))

            filtered_subjects = {object_: data_list for object_, data_list in same_S_ST_ET.items() if object_[0] in ['P54','P39', 'P102', 'P108', 'P127']}
        
        elif mission_name=='S2_R1_O1':
            with open(data_file, 'r', newline='', encoding='utf-8') as infile:
                tsv_reader = csv.reader(infile, delimiter='\t')
                for row in tsv_reader:
                    relation, subject, object_, start_time, end_time = row
                    key = (relation, object_)  # 注意这里，我们用relation, subject, object作为键
                    same_S_ST_ET[key].append((subject, start_time, end_time))
            filtered_subjects = {object_: data_list for object_, data_list in same_S_ST_ET.items() if object_[0] in ["P54", "P39", "P108", "P102", "P69", "P488", "P6", "P127"]}
        
        elif mission_name in ['S1_R2_O2','S2_R1_O2','S2_R2_O2']:
            if mission_name=='S1_R2_O2':
                with open(data_file, 'r', newline='', encoding='utf-8') as infile:
                    tsv_reader = csv.reader(infile, delimiter='\t')
                    for row in tsv_reader:
                        relation, subject, object_, start_time, end_time = row
                        key = subject # 注意这里，我们用relation, subject, object作为键
                        same_S_ST_ET[key].append((relation, object_, start_time, end_time))
            else:           
                with open(data_file, 'r', newline='', encoding='utf-8') as infile:
                    tsv_reader = csv.reader(infile, delimiter='\t')
                    for row in tsv_reader:
                        relation, subject, object_, start_time, end_time = row
                        key = subject # 注意这里，我们用relation, subject, object作为键
                        same_S_ST_ET[key].append((relation, object_, start_time, end_time))
            # filtered_subjects = {object_: data_list for object_, data_list in same_S_ST_ET.items() if 4 < len(data_list) < 13}
            filtered_subjects = {object_: data_list for object_, data_list in same_S_ST_ET.items() if 4< len(data_list) < 13}
        
        if mission_name in ['S2_R1_O1','S1_R2_O2','S1_R1_O2']:

            for key, value_list in tqdm(filtered_subjects.items()):
                # import pdb; pdb.set_trace()
                min_time_units = []
                flag=0
                for i in range(len(value_list)):         
                    # 要求找到value_list所有最小时间单元情况下，不同object的构成情况都要考虑
                    for j in range(i+1, len(value_list)):
                        key1 = value_list[i]
                        key2 = value_list[j]
                        min_time_unit=None
                        # import pdb; pdb.set_trace() 
                        if mission_name=='S1_R2_O2':
                            relation1, object_1, start1, end1 = key1
                            relation2, object_2, start2, end2 = key2
                            relation_pair_str = relation1 + '-' + relation2
                            if relation_pair_str in ['P39-P102', 'P39-P108', 'P102-P39', 'P69-P108', 'P108-P69', 'P69-P39', 'P108-P39', 'P102-P108', 'P69-P102', 'P102-P69', 'P54-P69', 'P54-P286', 'P39-P6']:
                                min_time_unit = judge_imply(key1, key2)
                        else:
                            min_time_unit = judge_imply(key1, key2)

                        if min_time_unit=='flag':
                            flag='flag'

                        if min_time_unit:
                            min_time_units.append(min_time_unit)

                    if flag=='flag':
                        min_time_units=[]
                        break

                if min_time_units != []:
                    if mission_name in ['S1_R1_O2','S2_R1_O1']:
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
                    data = data_generate(mission_name, question_templates, current_data, store_time, point_templates, interval_templates, name_dict, fact_dict, DA_object, time_search, is_subject)
                    if data != []:
                        for k in data:
                            new_data = classify_data(k)
                            if new_data['class'] == 'equal':
                                equal.append(new_data)
                            elif new_data['class'] == 'during':
                                during.append(new_data)
                            elif new_data['class'] == 'overlap':
                                overlap.append(new_data)
                            elif new_data['class'] == 'mix':
                                mix.append(new_data)
                    # output_list.append(data)
                    # json_data = json.dumps(current_data)
                    # json_file.write(json_data + '\n')

        else:
            for i, (key1, value_list1) in enumerate(tqdm(filtered_subjects.items())):
                for j, (key2, value_list2) in enumerate(filtered_subjects.items()):
                    if j <= i:  # 跳过重复的和自身的比较
                        continue
                    min_time_units = []
                    flag=0
                    for data1 in value_list1:
                        for data2 in value_list2:
                            subject1 = key1
                            subject2 = key2
                            relation1, object1, start1, end1 = data1
                            relation2, object2, start2, end2 = data2
                            if mission_name == 'S2_R1_O2':
                                if relation1 == relation2 and object1 != object2 and subject1 != subject2:  # 确保关系相同但对象不同
                                    min_time_unit = judge_imply(data1, data2, subject1, subject2,False)
                                    # if min_time_unit == 'uncertain':
                                    #     flag = 'uncertain'
                                    if min_time_unit=='flag':
                                        flag='flag'
                                    if min_time_unit:
                                        min_time_units.append(min_time_unit)
                            else:
                                relation_pair_str = relation1 + '-' + relation2
                                if relation_pair_str in ['P39-P102', 'P39-P108', 'P102-P39', 'P69-P108', 'P108-P69', 'P69-P39', 'P108-P39', 'P102-P108', 'P69-P102', 'P102-P69', 'P54-P69', 'P54-P286', 'P39-P6']:
                                    if object1 != object2:  # 确保关系相同但对象不同
                                        min_time_unit = judge_imply(data1, data2, subject1, subject2,False)
                                        if min_time_unit=='flag':
                                            flag='flag'
                                        if min_time_unit:
                                            min_time_units.append(min_time_unit)

                        if flag == 'flag':
                            min_time_units = []
                            break

                    if min_time_units != []:
                        if mission_name == 'S2_R1_O2':
                            subject = (key1, key2)  # Split the key into relation and subject
                        else:
                            subject = (key1, key2, relation1, relation2)  # Split the key into relation and subject
                        # Initialize the dictionary for this particular relation and subject
                        current_data = {
                            "entity_pair": subject,
                            "query": min_time_units
                        }
                        data = data_generate(mission_name, question_templates, current_data, store_time, point_templates, interval_templates, name_dict, fact_dict, DA_object, time_search, is_subject)
                        if data!=[]:
                            for k in data:
                                new_data = classify_data(k)
                                if new_data['class'] == 'equal':
                                    equal.append(new_data)
                                elif new_data['class'] == 'during':
                                    during.append(new_data)
                                elif new_data['class'] == 'overlap':
                                    overlap.append(new_data)
                                elif new_data['class'] == 'mix':
                                    mix.append(new_data)
    num = min(len(equal), 1000)
    equal = random.sample(equal, num)
    with open('test/equal.json', 'w', encoding='utf-8') as f:
        for data in equal:
            json_data = json.dumps(data)
            f.write(json_data+'\n')
    num = min(len(during), 1000)
    during = random.sample(during, num)
    with open('test/during.json', 'w', encoding='utf-8') as f:
        for data in during:
            json_data = json.dumps(data)
            f.write(json_data+'\n')
    num = min(len(overlap), 1000)
    overlap = random.sample(overlap, num)
    with open('test/overlap.json', 'w', encoding='utf-8') as f:
        for data in overlap:
            json_data = json.dumps(data)
            f.write(json_data+'\n')
    num = min(len(mix), 1000)
    mix = random.sample(mix, num)
    with open('test/mix.json', 'w', encoding='utf-8') as f:
        for data in mix:
            json_data = json.dumps(data)
            f.write(json_data+'\n')

if __name__=='__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--mission_name', type=str, metavar='N',
                   default='S1_R1_O2.json', help='which kind structured data to generate') 
    parser.add_argument('--data_level',
                type=str,
                default='v3',
                help='the amount of the raw data') 
    parser.add_argument('--output_path',
                type=str,
                default='data_without_temporal_expression',
                help='where to store the data')  
    args = parser.parse_args()
    main(args.data_level,args.output_path)