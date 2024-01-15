import csv
from collections import defaultdict
import json
from collections import Counter
import random
from tqdm import tqdm
import argparse

# # 时间节点的确认没有向前回溯

# # 读取源TSV文件
# # 下面的时间

# # 将时间转换为可比较的元组，None 被转换为极小或极大值以便于比较

def complete_time(time, is_start=True):

    year, month, day = time
    if is_start:
        return (year, month if month is not None else 0, day if day is not None else 0)
    else:
        return (year, month if month is not None else 0, day if day is not None else 0)

## 定义排序    
def custom_sort(item):
    order = {"dot_to_dot_equal": 0, "dot_to_interval_during": 1, "interval_to_interval_equal": 2, "interval_to_interval_during": 3, 'interval_to_interval_overlap': 4}
    level = order[item[2]]
    return level

def judge_imply(key1, key2,subject1=None,subject2=None,S=True):
    if S:
        if len(key1)==3:
            R_S_1, start1, end1 = key1
            R_S_2, start2, end2 = key2

            # import pdb; pdb.set_trace()
            if start1 == end1:
                end1 = 'None'
            if start2 == end2:
                end2 = 'None'
        else:
            relation1, object_1, start1, end1 = key1
            relation2, object_2, start2, end2 = key2

            R_S_1 = (relation1, object_1)
            R_S_2 = (relation2, object_2)

            if relation1 != relation2:
                    
                if start1 == end1:
                    end1 = 'None'
                if start2 == end2:
                    end2 = 'None'
    else:
        relation1, object_1, start1, end1 = key1
        relation2, object_2, start2, end2 = key2

        R_S_1 = (subject1, relation1, object_1)
        R_S_2 = (subject2, relation2, object_2)


        if start1 == end1:
            end1 = 'None'
        if start2 == end2:
            end2 = 'None'


    # 这步将模型转换为(None, None, None)的格式，如果有其中为0的情况
    start1 = eval(start1) if start1 != 'None' else (None, None, None)
    end1 = eval(end1) if end1 != 'None' else (None, None, None)
    start2 = eval(start2) if start2 != 'None' else (None, None, None)
    end2 = eval(end2) if end2 != 'None' else (None, None, None)

    # 判断是否为点时间
    point_time1 = start1 if end1 == (None, None, None) else end1 if start1 == (None, None, None) else None
    point_time2 = start2 if end2 == (None, None, None) else end2 if start2 == (None, None, None) else None
    
    # 如果其中有一个是点时间，就是纯粹的点时间(None, None, None)这三个都不是None
    # 两个都是点时间的情况
    if point_time1 is not None and point_time2 is not None:
        if complete_time(point_time1, is_start=False) == complete_time(point_time2, is_start=False) and complete_time(point_time1, is_start=False)[1]!=0 and complete_time(point_time1, is_start=False)[2]!=0:
            return ((complete_time(point_time1), R_S_1), R_S_2, "dot_to_dot_equal") 
        elif complete_time(point_time1,is_start=False)[0]!=complete_time(point_time2, is_start=False)[0]:
            return None
        elif complete_time(point_time1,is_start=False)[0]==complete_time(point_time2, is_start=False)[0] and complete_time(point_time1,is_start=False)[1]!=complete_time(point_time2,is_start=False)[1] and 0 not in [complete_time(point_time1,is_start=False)[1],complete_time(point_time2,is_start=False)[1]]:
            return None
        elif complete_time(point_time1,is_start=False)[0]==complete_time(point_time2, is_start=False)[0] and complete_time(point_time1,is_start=False)[1]==complete_time(point_time2, is_start=False)[1] and complete_time(point_time1,is_start=False)[2]!=complete_time(point_time2,is_start=False)[2] and 0 not in [complete_time(point_time2,is_start=False)[2],complete_time(point_time1,is_start=False)[2]]:
            return None
        else:
            return 'flag'

    # 其中一个是点时间的情况
    if point_time1 is not None and point_time2 is None:
        # 限制极端情况的判断，当比较的时间一个是只有年份，另外一个是段时间，删去由于1976,0,0这种模棱两可的情况
        point_time1 = complete_time(point_time1,is_start=True)
        start2 = complete_time(start2,is_start=True)
        end2 = complete_time(end2,is_start=False)
        if start2<point_time1<end2:
            if point_time1[0] not in [start2[0],end2[0]]:
                return ((point_time1,R_S_1),R_S_2,"dot_to_interval_during")
            elif point_time1[0] == start2[0] and point_time1[1]==start2[1]==0:
                return 'flag'
            elif point_time1[0] == end2[0] and point_time1[1]==end2[1]==0:
                return 'flag'
            elif point_time1[0] == start2[0] and point_time1[1]!=start2[1] and ((point_time1[1]==0 and start2[1]!=0) or (point_time1[1]!=0 and start2[1]==0)):
                return 'flag'
            elif point_time1[0] == end2[0] and point_time1[1]!=end2[1] and ((point_time1[1]==0 and end2[1]!=0) or (point_time1[1]!=0 and end2[1]==0)):
                return 'flag'
            return ((point_time1,R_S_1),R_S_2,"dot_to_interval_during")
        elif point_time1[0] not in [start2[0],end2[0]]:
            return None
        elif point_time1[0] == start2[0] and point_time1[1]!=start2[1] and point_time1[1]!=0 and start2[1]!=0:
            return None
        elif point_time1[0] == start2[0] and point_time1[1]==start2[1] and point_time1[2]!=start2[2] and point_time1[2]!=0 and start2[2]!=0:
            return None
        elif point_time1[0] == end2[0] and point_time1[1]!=end2[1] and point_time1[1]!=0 and end2[1]!=0:
            return None
        elif point_time1[0] == end2[0] and point_time1[1]==end2[1] and point_time1[2]!=end2[2] and point_time1[2]!=0 and end2[2]!=0:
            return None
        else:
            return 'flag'

        # if complete_time(point_time1, is_start=True)[1] == 0 and complete_time(start2, is_start=True)[1] != 0 and complete_time(point_time1, is_start=True)[0] in [complete_time(start2, is_start=True)[0], complete_time(end2, is_start=True)[0]]:
        #     return 'flag'

        # if complete_time(point_time1, is_start=True) == complete_time(start2, is_start=True) or complete_time(point_time1, is_start=False) == complete_time(end2, is_start=False):
        #     return ((complete_time(point_time1), R_S_1), R_S_2, "dot_to_interval_easy")
        # elif complete_time(start2, is_start=True) < complete_time(point_time1, is_start=False) < complete_time(end2, is_start=False):
        #     return ((complete_time(point_time1), R_S_1), R_S_2, "dot_to_interval_hard")
        # else:
        #     return None


    if point_time2 is not None and point_time1 is None:
        point_time2=complete_time(point_time2, is_start=True)
        start1 = complete_time(start1,is_start=True)
        end1 = complete_time(end1,is_start=False)
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
        # if complete_time(point_time2, is_start=True)[1] == 0 and complete_time(start1, is_start=True)[1] != 0 and complete_time(point_time2, is_start=True)[0] in [complete_time(start1, is_start=True)[0], complete_time(end1, is_start=True)[0]]:
        #     return 'flag'
        
        # if complete_time(point_time2, is_start=True) == complete_time(start1, is_start=True) or complete_time(point_time2, is_start=False) == complete_time(end1, is_start=False):
        #     return ((complete_time(point_time2), R_S_2), R_S_1, "dot_to_interval_easy")
        # elif complete_time(start1, is_start=True) < complete_time(point_time2, is_start=False) < complete_time(end1, is_start=False):
        #     return ((complete_time(point_time2), R_S_2), R_S_1, "dot_to_interval_hard")
        # else:
        #     return None
        
    # import pdb; pdb.set_trace()
    # Both are time ranges
    start1 = complete_time(start1, is_start=True)
    end1 = complete_time(end1, is_start=False)
    start2 = complete_time(start2, is_start=True)
    end2 = complete_time(end2, is_start=False)

    # import pdb; pdb.set_trace()

    if point_time1 is None and point_time2 is None:
        # s2 s1 e1 e2
        if start1 ==  end2:
            return 'flag'
        if start2 ==  end1:
            return 'flag'
        if start1[1] == 0 and end2[1] != 0 and  start1[0] ==  end2[0]:
            return 'flag'
        if start2[1] == 0 and end1[1] != 0 and start2[0] ==  end1[0]:
            return 'flag'
        if start1[1] != 0 and end2[1] == 0 and  start1[0] ==  end2[0]:
            return 'flag'
        if start2[1] != 0 and end1[1] == 0 and start2[0] ==  end1[0]:
            return 'flag'
        if start1[0] ==  end2[0] and start1[1]==end2[1] and ((start1[2]==0 and end2[2]!=0) or (start1[2]!=0 and end2[2]==0)):
            return 'flag'
        if start2[0] == end1[0] and start2[1]==end1[1] and ((start2[2]==0 and end1[2]!=0) or (start2[2]!=0 and end1[2]==0)):
            return 'flag'
        if start1==start2 and end1==end2:
            return (((start1, end1), R_S_1), R_S_2, "interval_to_interval_equal")
        
        if start2 < start1 and start1< end1 and end1<= end2:
            return (((start1, end1), R_S_1), R_S_2, "interval_to_interval_during")
        
        if start2 <= start1 and start1 < end1 and end1 < end2:
            return (((start1, end1), R_S_1), R_S_2, "interval_to_interval_during")        
        
        # s1 s2 e2 e1
        if start1 <= start2 and start2 < end2 and end2 < end1:
            return (((start2, end2), R_S_2), R_S_1, "interval_to_interval_during")

        if start1 < start2 and start2 < end2 and end2 <= end1:
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
        

def main(root,mission_name,data_level):
    same_S_ST_ET = defaultdict(list)
    result_dict = defaultdict(lambda: defaultdict(list))
    data_file = f'raw_data/ailab_data_{data_level}.tsv'
    if mission_name=='S1_R1_O2.json':
        with open(data_file, 'r', newline='', encoding='utf-8') as infile:
            tsv_reader = csv.reader(infile, delimiter='\t')
            for row in tsv_reader:
                relation, subject, object_, start_time, end_time = row
                key = (relation, subject)  # 注意这里，我们用relation, subject, object作为键
                same_S_ST_ET[key].append((object_, start_time, end_time))

        filtered_subjects = {object_: data_list for object_, data_list in same_S_ST_ET.items() if object_[0] in ['P54','P39', 'P102', 'P108', 'P127']}
    
    elif mission_name=='S2_R1_O1.json':
        with open(data_file, 'r', newline='', encoding='utf-8') as infile:
            tsv_reader = csv.reader(infile, delimiter='\t')
            for row in tsv_reader:
                relation, subject, object_, start_time, end_time = row
                key = (relation, object_)  # 注意这里，我们用relation, subject, object作为键
                same_S_ST_ET[key].append((subject, start_time, end_time))
        filtered_subjects = {object_: data_list for object_, data_list in same_S_ST_ET.items() if object_[0] in ["P54", "P39", "P108", "P102", "P69", "P488", "P6", "P127"]}
    
    elif mission_name in ['S1_R2_O2.json','S2_R1_O2.json','S2_R2_O2.json']:
        if mission_name=='S1_R2_O2.json':
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
    
    if mission_name in ['S2_R1_O1.json','S1_R2_O2.json','S1_R1_O2.json']:

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
                    if mission_name=='S1_R2_O2.json':
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
                result_dict[key] = min_time_units
        
        with open(root+'\\'+mission_name, 'w', encoding='utf-8') as json_file:
            for key, time_to_objects in result_dict.items():
                # print(key)
                # relation, subject = key  # Split the key into relation and subject
                # Initialize the dictionary for this particular relation and subject
                time_to_objects = sorted(time_to_objects, key=custom_sort)
                if mission_name in ['S1_R1_O2.json','S2_R1_O1.json']:
                    relation, subject = key
                    current_data = {
                    "entity": subject,
                    "relation": relation,
                    "query": time_to_objects
                    }
                else:
                    subject = key
                    current_data = {
                        "entity": subject,
                        "query": time_to_objects
                    }
                json_data = json.dumps(current_data)
                json_file.write(json_data + '\n')

    else:
        with open(root+'\\'+mission_name, 'w', encoding='utf-8') as json_file:
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
                            if mission_name == 'S2_R1_O2.json':
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
                        if mission_name == 'S2_R1_O2.json':
                            subject = (key1, key2)  # Split the key into relation and subject
                        else:
                            subject = (key1, key2, relation1, relation2)  # Split the key into relation and subject
                        # Initialize the dictionary for this particular relation and subject
                        current_data = {
                            "entity_pair": subject,
                            "query": min_time_units
                        }

                        json_data = json.dumps(current_data)
                        json_file.write(json_data + '\n')

if __name__=='__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--mission_name', type=str, metavar='N',
                   default='S1_R1_O2.json', help='which kind structured data to generate')
    parser.add_argument('--output_file', type=str, metavar='N',
                   default='structured_data', help='where to store the data') 
    parser.add_argument('--data_level',
                type=str,
                default='v3',
                help='the amount of the raw data')   
    args = parser.parse_args()
    main(args.output_file,args.mission_name,args.data_level)