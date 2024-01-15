import json
import csv
import random
from tqdm import tqdm
import argparse

def read_qid_names(filepath):   
    name_dict = {}
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            key, value = line.strip().split('\t')
            name_dict[key] = value
    return name_dict

def time_transfer(time):
    # print(time)
    if time[1]==0:
        return str(time[0])
    elif time[2]==0:
        return '{0}, {1}'.format(months_dict[time[1]],time[0])
    else:
        return '{0} {1}, {2}'.format(months_dict[time[1]],time[2],time[0])
    
def complete_time(time):
    year, month, day = time
    return (year, month if month is not None else 0, day if day is not None else 0)

def transfer_time_to_int(time):
    # print(time)
    st,et = time
    if st==et:
        et='None'
    st = eval(st) if st != 'None' else (None, None, None)
    et = eval(et) if et != 'None' else (None, None, None)
    if st != (None, None, None) and et != (None, None, None):
        return (complete_time(st),complete_time(et))
    elif st != (None, None, None):
        return (complete_time(st))
    else:
        return (complete_time(et))
    
def read_jsonl(in_file):
    questions = []
    with open(in_file) as fin:
        for line in fin:
            question_item = json.loads(line)
            questions.append(question_item)
    return questions

def read_query_templates(filepath):
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return {row["Wikidata ID"]: row["Template"] for row in reader}
    
def transfer_lst_qid(lst, name_dict):
    # import pdb; pdb.set_trace()
    qid_name_lst = []
    for item in lst:
        qid_name = name_dict[item]
        qid_name_lst.append(qid_name)
    return qid_name_lst

def fact_combine(subjects, fact_dict):
    fact_lst = []
    for subject in subjects:
        fact = fact_dict[subject]
        fact_lst += fact
    return fact_lst

def time_judgement(question_time, compare_time):
    # 说明他是一个段时间
    # import pdb; pdb.set_trace()
    if len(compare_time) == 2:
        start1, end1 = question_time
        start2, end2 = compare_time
        if start1 <= start2 < end1 and start1 < end2 <= end1:
            return True
        elif start2 <= start1 < end2 and start2 < end1 <= end2:
            return True
        elif start1 < start2 and end1 < end2 and start2 < end1:
            return True
        elif start2 < start1 and end2 < end1 and start1 < end2:
            return True
        else:
            return False

    # import pdb; pdb.set_trace()
    # 说明他是一个点时间

    if len(compare_time) == 3:
        
        if question_time[0] <= compare_time <= question_time[1]:
            return True
        else:
            return False
    
    if len(question_time) == 3:
        if compare_time[0] <= question_time <= compare_time[1]:
            return True
        else:
            return False
        
def read_generate_templates(filepath):
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return {row["Relation"]: row["Templates"] for row in reader}
    
def create_unoverlap_fact_object(interval_newdata_templates,point_newdata_templates,time_low_limit,time_high_limit,time,object_count,relation,object_already_used,name_dict,subject): 
    if random.randint(0,1)==0:
        s_year=random.randint(time_low_limit,time_high_limit)
        e_year=random.randint(s_year,time_high_limit)
        if random.randint(0,2)!=0:
            s_month=random.randint(1,12)
            if s_year == e_year:
                e_month=random.randint(s_month,12)
            else:
                e_month=random.randint(1,12)
            if random.randint(0,1)==0:
                s_day=random.randint(1,28)
                e_day=random.randint(s_day,28)
            else:
                s_day=0
                e_day=0
        else:
            s_month=0
            s_day=0
            e_month=0
            e_day=0
        s_date=(s_year,s_month,s_day)                          
        e_date=(e_year,e_month,e_day)
        if len(time)==3:
            if e_date>s_date and ((e_date<time and e_date[0]!=time[0]) or (s_date>time and s_date[0]!=time[0])):
                while True:
                    data_object=random.choice(object_count[relation])
                    if data_object not in object_already_used:
                        st=time_transfer(s_date)
                        et=time_transfer(e_date)
                        new_data=interval_newdata_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", data_object).replace('<st>',st).replace('<et>',et)
                        return (new_data,data_object)
        else:
            if e_date>s_date and ((e_date<time[0] and e_date[0]!=time[0][0]) or (s_date>time[1] and s_date[0]!=time[1][0])):
                while True:
                    data_object=random.choice(object_count[relation])
                    if data_object not in object_already_used:
                        st=time_transfer(s_date)
                        et=time_transfer(e_date)
                        new_data=interval_newdata_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", data_object).replace('<st>',st).replace('<et>',et)
                        return (new_data,data_object)
    else:
        s_year=random.randint(time_low_limit,time_high_limit)
        if random.randint(0,2)!=0:
            s_month=random.randint(1,12)
            if random.randint(0,1)==0:
                s_day=random.randint(1,28)
            else:
                s_day=0
        else:
            s_month=0
            s_day=0
        s_date=(s_year,s_month,s_day)
        if len(time)==3 and s_date!=time:
            if s_date[0]!=time[0] or (time[1]!=0 and s_date[1]!=0 and time[1]!=s_date[1]) or (time[1]!=0 and s_date[1]!=0 and time[2]!=0 and s_date[2]!=0):
                while True:
                    data_object=random.choice(object_count[relation])
                    if data_object not in object_already_used:
                        st=time_transfer(s_date)
                        new_data=point_newdata_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", data_object).replace('<st>',st)
                        return (new_data,data_object)
        elif len(time)==2:
            if s_date<time[0]:
                if s_date[0]!=time[0][0] or (time[0][1]!=0 and s_date[1]!=0 and time[0][1]!=s_date[1]) or (time[0][1]!=0 and s_date[1]!=0 and time[0][2]!=0 and s_date[2]!=0):
                    while True:
                        data_object=random.choice(object_count[relation])
                        if data_object not in object_already_used:
                            st=time_transfer(s_date)
                            new_data=point_newdata_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", data_object).replace('<st>',st)
                            return (new_data,data_object)
            elif s_date>time[1]:
                if s_date[0]!=time[1][0] or (time[1][1]!=0 and s_date[1]!=0 and time[1][1]!=s_date[1]) or (time[1][1]!=0 and s_date[1]!=0 and time[1][2]!=0 and s_date[2]!=0):
                    while True:
                        data_object=random.choice(object_count[relation])
                        if data_object not in object_already_used:
                            st=time_transfer(s_date)
                            new_data=point_newdata_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", data_object).replace('<st>',st)
                            return (new_data,data_object)
    return None

def create_unoverlap_fact_subject(interval_newdata_templates,point_newdata_templates,time_low_limit,time_high_limit,time,subject_count,relation,subject_already_used,name_dict,object_): 
    if random.randint(0,1)==0:
        s_year=random.randint(time_low_limit,time_high_limit)
        e_year=random.randint(s_year,time_high_limit)
        if random.randint(0,2)!=0:
            s_month=random.randint(1,12)
            if s_year == e_year:
                e_month=random.randint(s_month,12)
            else:
                e_month=random.randint(1,12)
            if random.randint(0,1)==0:
                s_day=random.randint(1,28)
                e_day=random.randint(s_day,28)
            else:
                s_day=0
                e_day=0
        else:
            s_month=0
            s_day=0
            e_month=0
            e_day=0
        s_date=(s_year,s_month,s_day)                          
        e_date=(e_year,e_month,e_day)
        if len(time)==3:
            if e_date>s_date and ((e_date<time and e_date[0]!=time[0]) or (s_date>time and s_date[0]!=time[0])):
                while True:
                    data_subject=random.choice(subject_count[relation])
                    if data_subject not in subject_already_used:
                        st=time_transfer(s_date)
                        et=time_transfer(e_date)
                        new_data=interval_newdata_templates[relation].replace("<subject1>", name_dict[data_subject]).replace("<object1>", name_dict[object_]).replace('<st>',st).replace('<et>',et)
                        return (new_data,data_subject)
        else:
            if e_date>s_date and ((e_date<time[0] and e_date[0]!=time[0][0]) or (s_date>time[1] and s_date[0]!=time[1][0])):
                while True:
                    data_subject=random.choice(subject_count[relation])
                    if data_subject not in subject_already_used:
                        st=time_transfer(s_date)
                        et=time_transfer(e_date)
                        new_data=interval_newdata_templates[relation].replace("<subject1>", name_dict[data_subject]).replace("<object1>", name_dict[object_]).replace('<st>',st).replace('<et>',et)
                        return (new_data,data_subject)
    else:
        s_year=random.randint(time_low_limit,time_high_limit)
        if random.randint(0,2)!=0:
            s_month=random.randint(1,12)
            if random.randint(0,1)==0:
                s_day=random.randint(1,28)
            else:
                s_day=0
        else:
            s_month=0
            s_day=0
        s_date=(s_year,s_month,s_day)
        if len(time)==3 and s_date!=time:
            if s_date[0]!=time[0] or (time[1]!=0 and s_date[1]!=0 and time[1]!=s_date[1]) or (time[1]!=0 and s_date[1]!=0 and time[2]!=0 and s_date[2]!=0):
                while True:
                    data_subject=random.choice(subject_count[relation])
                    if data_subject not in subject_already_used:
                        st=time_transfer(s_date)
                        new_data=point_newdata_templates[relation].replace("<subject1>", name_dict[data_subject]).replace("<object1>", name_dict[object_]).replace('<st>',st)
                        return (new_data,data_subject)
        elif len(time)==2:
            if s_date<time[0]:
                if s_date[0]!=time[0][0] or (time[0][1]!=0 and s_date[1]!=0 and time[0][1]!=s_date[1]) or (time[0][1]!=0 and s_date[1]!=0 and time[0][2]!=0 and s_date[2]!=0):
                    while True:
                        data_subject=random.choice(subject_count[relation])
                        if data_subject not in subject_already_used:
                            st=time_transfer(s_date)
                            new_data=point_newdata_templates[relation].replace("<subject1>", name_dict[data_subject]).replace("<object1>", name_dict[object_]).replace('<st>',st)
                            return (new_data,data_subject)
            elif s_date>time[1]:
                if s_date[0]!=time[1][0] or (time[1][1]!=0 and s_date[1]!=0 and time[1][1]!=s_date[1]) or (time[1][1]!=0 and s_date[1]!=0 and time[1][2]!=0 and s_date[2]!=0):
                    while True:
                        data_subject=random.choice(subject_count[relation])
                        if data_subject not in subject_already_used:
                            st=time_transfer(s_date)
                            new_data=point_newdata_templates[relation].replace("<subject1>", name_dict[data_subject]).replace("<object1>", name_dict[object_]).replace('<st>',st)
                            return (new_data,data_subject)
    return None

def data_generate(task, question_templates_path, data_level,output_path):
    structured_data_path = 'structured_data//'+task+'.json'
    output_file_path = output_path+'//'+task+'.json'
    point_templates_path = 'generate_point_templates//'+task+'.csv'
    interval_templates_path = 'generate_interval_templates//'+task+'.csv'
    rawdata_path = f'raw_data/ailab_data_{data_level}.tsv'
    qid_path = f'qid/ailab_data_{data_level}.txt'
    subject_path = f'facts/ailab_{data_level}_subject_fact.json'
    object_path = f'facts/ailab_{data_level}_object_fact.json'
    question_templates = read_query_templates(question_templates_path)
    name_dict = read_qid_names(qid_path)
    point_templates = read_generate_templates(point_templates_path)
    interval_templates = read_generate_templates(interval_templates_path)
    store_time = {}
    with open(rawdata_path, 'r', newline='', encoding='utf-8') as infile:  #使用对应的原始数据
        tsv_reader = csv.reader(infile, delimiter='\t')
        for row in tsv_reader:
            relation, subject, object_, start_time, end_time = row
            key = (relation, subject,object_)  # 注意这里，我们用relation, subject, object作为键
            store_time[key]=(start_time,end_time)
    
    is_subject = True #判断问题的主体是否是subject，对于S2-R1_O1，其主体是object
    if 'S2_R1_O1' in structured_data_path:
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
        for line in f:
            item = json.loads(line.strip())
            entity = item.get("entity", "")
            facts = item.get("facts", [])
            data_list = item['data_list']
            fact_dict[entity] = facts
            time_search[entity] = data_list
    
    DA_object = {}
    if 'S1_R1_O2' in structured_data_path:
        relation_limit = ['P39', 'P102', 'P108', 'P127']
    elif 'S2_R1_O1' in structured_data_path:
        relation_limit = ['P39', 'P102', 'P108', 'P127', 'P54', 'P6', 'P488', 'P69']
    elif 'S1_R2_O2' in structured_data_path:
        question_templates = {
                "P39-P102": "While <subject1> was holding the position of <object1>, which political party did <subject1> belong to ",
                "P39-P108": "While <subject1> was holding the position of <object1>, which employer did <subject1> work for ",
                "P102-P39": "While <subject1> was a member of <object1>, which position did <subject1> hold ",
                "P69-P108": "While <subject1> attended <object1>, which employer did <subject1> work for ",
                "P108-P69": "While <subject1> was working for <object1>, which school did <subject1> attend ",
                "P69-P39": "While <subject1> attended <object1>, which position did <subject1> hold ",
                "P108-P39": "While <subject1> was working for <object1>, which position did <subject1> hold ",
                "P102-P108": "While <subject1> was a member of <object1>, which employer did <subject1> work for ",
                "P69-P102": "While <subject1> attended <object1>, which political party did <subject1> belong to ",
                "P102-P69": "While <subject1> was a member of <object1>, which school did <subject1> attend ",
                "P54-P69": "While <subject1> was playing for <object1>, which school did <subject1> attend ",
                "P54-P286": "While <subject1> was a member of <object1>, who was the head coach of <subject1> ",
                "P39-P6": "While <subject1> was holding the position of <object1>, who was the head of the government of <subject2> "
        }
        relation_limit = ['P39', 'P102', 'P108','P6',"P69",'P286','P54']
    elif 'S2_R1_O2' in structured_data_path:
        relation_limit = ['P39', 'P102', 'P108', 'P127','P6',"P69",'P488','P54','P286']
    elif 'S2_R2_O2' in structured_data_path:
        relation_limit = ['P39', 'P102', 'P108', 'P127','P6',"P69",'P488','P54','P286']
    if is_subject:
        with open(DA_path, 'r') as f:  #我们这里将获取数据扩充所需要用到的对象，原则是首先获得不同的关系对应有哪些subject或者object
            for line in f:
                item = json.loads(line.strip())
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
            for line in f:
                item = json.loads(line.strip())
                name = item.get("entity", "")
                data_list = item['data_list']
                for data in data_list:
                    relation = data[0]
                    if relation in relation_limit:
                        if relation not in DA_object:
                            DA_object[relation]=[]
                        if name not in DA_object[relation]:
                            DA_object[relation].append(name)
    output_list = []
    lines = read_jsonl(structured_data_path)
    if 'S1_R1_O2' in structured_data_path or 'S2_R1_O1' in structured_data_path:
        # 对于S1_R1_O2 和 S2_R1_O1 我们一同处理,因为他们都有固定的主体以及关系
        for i, line in enumerate(lines):
            sentence = line["query"]
            main_entity = line["entity"]
            relation = line["relation"]
            if 'S2_R1_O2' in structured_data_path:
                if relation == 'P286' or len(fact_dict[object_]) > 17:
                    continue

            # 用来存储目前共时事件之前有没有提问过
            alredy_query = []
            # 用来存储目前的问题之前有没有提问过
            already_question = []
            
            for num in range(len(sentence)):
                answer_set = set()

                time_interval, vice_entity1 = sentence[num][0]
                vice_entity2 = sentence[num][1]
                level =  sentence[num][2]

                # 分两种情况：点时间直接判断，段时间分情况判断
                if sentence[num][0] not in alredy_query and (main_entity, vice_entity1) not in already_question:
                    alredy_query.append(sentence[num][0])
                    already_question.append((main_entity, vice_entity1))  
                    answer_set.add(vice_entity2)


                    for pass_query in sentence:
                        compare_object = pass_query[0][1]
                        
                        compare_time = pass_query[0][0]
                        # import pdb; pdb.set_trace()
                        if vice_entity1 == compare_object:
                            if len(time_interval) == 3:
                                if pass_query[0][0] == sentence[num][0][0]:
                                    answer_set.add(pass_query[1])
                            else:
                                if time_judgement(time_interval, compare_time):
                                    answer_set.add(pass_query[1])
                                else:
                                    answer_set = set()
                                    break

                        if vice_entity1 == pass_query[1]:
                            if len(time_interval) == 3:
                                if pass_query[0][0] == sentence[num][0][0]:
                                    answer_set.add(compare_object)
                            else:
                                if time_judgement(time_interval, compare_time):
                                    answer_set.add(compare_object)
                                else:
                                    answer_set = set()
                                    break

                    if relation in question_templates and answer_set != set() and len(answer_set)<5:
                        facts=fact_dict[main_entity].copy()
                        # inital_fact = fact_dict[subject].copy()
                        times=5000
                        ans_cnt = transfer_lst_qid(list(answer_set), name_dict)
                        if is_subject:
                            subject = main_entity
                            object_ = vice_entity1
                        else:
                            subject = vice_entity1
                            object_ = main_entity
                        time = transfer_time_to_int(store_time[(relation,subject,object_)])
                        object_already_used = set()
                        question = question_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", name_dict[object_])
                        random_number = random.randint(0, 100)
                        index = f"S1_R1_O2_{relation}_{main_entity}_{random_number}"
                        facts_length = len(facts)
                        time_high_limit=0
                        time_low_limit=float('inf')
                        if facts_length<10:
                            data_list=time_search[main_entity]     #已经用过了哪些对象
                            for data in data_list:
                                object_already_used.add(name_dict[data[1]])
                                if data[2]!='None':
                                    time1=eval(data[2])
                                    if time1[0]>time_high_limit:
                                        time_high_limit=time1[0]
                                    if time1[0]<time_low_limit:
                                        time_low_limit=time1[0]
                                if data[3]!='None':
                                    time1=eval(data[3])
                                    if time1[0]>time_high_limit:
                                        time_high_limit=time1[0]
                                    if time1[0]<time_low_limit:
                                        time_low_limit=time1[0]

                            need_num = 10-facts_length
                            while need_num>0 and times>0:
                                if is_subject:
                                    get_generate = create_unoverlap_fact_object(interval_templates,point_templates,time_low_limit,time_high_limit,time,DA_object,relation,object_already_used,name_dict,main_entity)
                                else:
                                    get_generate = create_unoverlap_fact_subject(interval_templates,point_templates,time_low_limit,time_high_limit,time,DA_object,relation,object_already_used,name_dict,main_entity)
                                if get_generate is not None:
                                    new_fact,o2 = get_generate
                                    object_already_used.add(o2)
                                    facts.append(new_fact)
                                    need_num-=1   
                                    facts_length+=1                  
                                times -= 1
    

                        if facts_length>=10:  
                            random.shuffle(facts)   
                            # random.shuffle(inital_fact)
                            output_list.append({
                                "id": index,
                                "level": level,
                                "entity": main_entity,
                                "relation": relation,
                                "time": time_interval,
                                "query": question,
                                "answer": ans_cnt,
                                "fact": facts
                            })     

    elif 'S1_R2_O2' in structured_data_path:
        relation_pair={}
        for i, line in enumerate(lines):
            sentence = line["query"]
            main_entity = line["entity"]
            alredy_query = []
            already_question = []

            for num in range(len(sentence)):
                answer_set = set()

                time_interval, relation1_object1_list = sentence[num][0]
                relation1 = relation1_object1_list[0]
                object1 = relation1_object1_list[1]

                relation2_object2_list = sentence[num][1]
                relation2 = relation2_object2_list[0]
                object2 = relation2_object2_list[1]

                level =  sentence[num][2]

                if sentence[num][0] not in alredy_query and (relation1, object1, relation2, main_entity) not in already_question:
                    relation_pair_str = relation1 + '-' + relation2
                    alredy_query.append(sentence[num][0])
                    already_question.append((relation1, object1, relation2, main_entity))
                    answer_set.add(object2)
                    
                    if relation_pair_str in ['P39-P102', 'P39-P108', 'P102-P39', 'P69-P108', 'P108-P69', 'P69-P39', 'P108-P39', 'P102-P108', 'P69-P102', 'P102-P69', 'P54-P69', 'P54-P286', 'P39-P6']:
                        if relation_pair_str not in relation_pair:
                            relation_pair[relation_pair_str] = 0
                        relation_pair[relation_pair_str] += 1    
                        
                        for pass_query in sentence:
                            # import pdb; pdb.set_trace()
                            compare_r_o1 = pass_query[0][1]
                            compare_r_o2 = pass_query[1]
                            compare_time = pass_query[0][0]

                            if compare_r_o1 == relation1_object1_list and compare_r_o2[0] == relation2:
                                if len(time_interval) == 3:
                                    if compare_time == time_interval:
                                        answer_set.add(compare_r_o2[1])
                                else:
                                    if time_judgement(time_interval, compare_time):
                                        answer_set.add(compare_r_o2[1])
                                    else:
                                        answer_set = set()
                                        break

                            if compare_r_o2 == relation1_object1_list and compare_r_o1[0] == relation2:
                                if len(time_interval) == 3:
                                    if compare_time == time_interval:
                                        answer_set.add(compare_r_o1[1])
                                else:
                                    if time_judgement(time_interval, compare_time):
                                        answer_set.add(compare_r_o1[1])
                                    else:
                                        answer_set = set()
                                        break

                        if answer_set != set() and len(answer_set)<5:
                            facts=fact_dict[main_entity].copy()
                            # inital_fact = fact_dict[subject].copy()
                            times=10000
                            time = transfer_time_to_int(store_time[(relation1,main_entity,object1)])
                            ans_cnt = transfer_lst_qid(list(answer_set), name_dict)
                            object_already_used = set()
                            question = question_templates[relation_pair_str].replace("<subject1>", name_dict[main_entity]).replace("<object1>", name_dict[object1])
                            random_number = random.randint(0, 100)
                            index = f"S1_R2_O2_{relation_pair_str}_{main_entity}_{random_number}"
                            facts_length = len(facts)
                            time_high_limit=0
                            time_low_limit=float('inf')
                            cnt_s1_r1=0
                            cnt_s1_r2=0
                            flag = False
                            for fact in facts:
                                if search[relation1] in fact and search[relation2] in fact:
                                    flag = True
                                    break
                                if search[relation1] in fact:
                                    cnt_s1_r1+=1
                                elif search[relation2] in fact:
                                    cnt_s1_r2+=1
                            if flag:
                                continue
                            
                            if cnt_s1_r1 < 10 or cnt_s1_r2<10:

                                data_list=time_search[subject]     #已经用过了哪些对象
                                for data in data_list:
                                    object_already_used.add(name_dict[data[1]])
                                    if data[2]!='None':
                                        time1=eval(data[2])
                                        if time1[0]>time_high_limit:
                                            time_high_limit=time1[0]
                                        if time1[0]<time_low_limit:
                                            time_low_limit=time1[0]
                                    if data[3]!='None':
                                        time1=eval(data[3])
                                        if time1[0]>time_high_limit:
                                            time_high_limit=time1[0]
                                        if time1[0]<time_low_limit:
                                            time_low_limit=time1[0]

                                if cnt_s1_r1 < 10:
                                    need_s1_r1 = 10-cnt_s1_r1
                                    while need_s1_r1>0 and times>0:    
                                        get_generate = create_unoverlap_fact_object(interval_templates,point_templates,time_low_limit,time_high_limit,time,DA_object,relation1,object_already_used,name_dict,subject)
                                        if get_generate is not None:
                                            new_fact,o2 = get_generate
                                            object_already_used.add(o2)
                                            facts.append(new_fact)
                                            need_s1_r1 -= 1 
                                            cnt_s1_r1 += 1                    
                                        times -= 1
                                
                                if cnt_s1_r2 < 10:
                                    need_s1_r2 = 10 - cnt_s1_r2
                                    while need_s1_r2>0 and times>0:
                                        get_generate = create_unoverlap_fact_object(interval_templates,point_templates,time_low_limit,time_high_limit,time,DA_object,relation2,object_already_used,name_dict,subject)
                                        if get_generate is not None:
                                            new_fact,o2 = get_generate
                                            object_already_used.add(o2)
                                            facts.append(new_fact)
                                            need_s1_r2 -= 1 
                                            cnt_s1_r2 += 1                    
                                        times -= 1                                    
    
                            # print(times)
                            if cnt_s1_r1 >= 10 and cnt_s1_r2 >= 10:  
                                random.shuffle(facts) 
                                # random.shuffle(inital_fact)  
                                output_list.append({
                                    "id": index,
                                    "level": level,
                                    "entity": subject,
                                    "relation": relation_pair_str,
                                    "time": time_interval,
                                    "query": question,
                                    "answer": ans_cnt,
                                    "fact": facts
                                })

    elif 'S2_R1_O2' in structured_data_path or 'S2_R2_O2' in structured_data_path:
        for i, line in enumerate(tqdm(lines)):
            sentence = line["query"]
            subject_pair = line["entity_pair"]
        
            alredy_query = []
            already_question = []

            for num in range(len(sentence)):
                answer_set = set()

                time_interval, fact1 = sentence[num][0]
                s1, r1, o1 = fact1
                fact2 = sentence[num][1]
                s2, r2, o2 = fact2
                level =  sentence[num][2]
                relation_pair = r1
                if 'S2_R2_O2' in structured_data_path:
                    relation_pair = r1 + "-" + r2
                    query_condition = (s1, r1, o1, s2, r2)
                else:
                    query_condition = (s1, r1, o1, s2)
                if sentence[num][0] not in alredy_query and query_condition not in already_question:
                    alredy_query.append(sentence[num][0])
                    already_question.append(query_condition)
                    answer_set.add(o2)

                    for pass_query in sentence:
                        # import pdb; pdb.set_trace()
                        compare_s1_r1_o1 = pass_query[0][1]
                        compare_s2_r_o2 = pass_query[1]
                        compare_time = pass_query[0][0]

                        if compare_s1_r1_o1 == fact1 and compare_s2_r_o2[0] == s2:
                            if len(time_interval) == 3:
                                if compare_time == time_interval:
                                    answer_set.add(compare_s2_r_o2[2])
                            else:
                                if time_judgement(time_interval, compare_time):
                                    answer_set.add(compare_s2_r_o2[2])
                                    if 'S2_R2_O2' in structured_data_path:
                                        if len(compare_time) == 3 and compare_time in [time_interval[0], time_interval[1]]:
                                            answer_set = set()
                                            break                            
                                else:
                                    answer_set = set()
                                    break

                        if compare_s2_r_o2 == fact1 and compare_s1_r1_o1[0] == s2:
                            if len(time_interval) == 3:
                                if compare_time == time_interval:
                                    answer_set.add(compare_s1_r1_o1[2])
                            else:
                                if time_judgement(time_interval, compare_time):
                                    answer_set.add(compare_s1_r1_o1[2])
                                    if 'S2_R2_O2' in structured_data_path:
                                        if len(compare_time) == 3 and compare_time in [time_interval[0], time_interval[1]]:
                                            answer_set = set()
                                            break   
                                else:
                                    answer_set = set()
                                    break
                    if answer_set != set() and relation_pair in question_templates and len(answer_set)<5:
                        facts1=fact_dict[s1].copy()
                        facts2=fact_dict[s2].copy()
                        facts = facts1+facts2
                        # inital_fact = facts.copy()
                        times=2000
                        ans_cnt = transfer_lst_qid(list(answer_set), name_dict)
                        time = transfer_time_to_int(store_time[(r1,s1,o1)])
                        # print(time)
                        object_already_used = set()
                        question = question_templates[relation_pair].replace("<subject1>", name_dict[s1]).replace("<object1>", name_dict[o1]).replace("<subject2>", name_dict[s2])
                        random_number = random.randint(0, 100)
                        if 'S2_R1_O2' in structured_data_path:
                            index = f"S2_R1_O2_{r1}_{s1}_{s2}_{random_number}"
                        else:
                            index = f"S2_R2_O2_{r1}_{r2}_{s1}_{s2}_{random_number}"
                        answer_length = len(answer_set)
                        facts_length = len(facts)
                        time_high_limit=0
                        time_low_limit=float('inf')
                        cnt_s1_r1 = 0
                        cnt_s2_r = 0
                        flag = False
                        for fact in facts:
                            if (name_dict[s1] in fact and name_dict[s2] in fact and search[r1] and r1==r2) or (r1!=r2 and search[r1] in fact and search[r2] in fact):
                                flag = True
                            if name_dict[s1] in fact and search[r1] in fact:
                                cnt_s1_r1 += 1
                            elif name_dict[s2] in fact and search[r2] in fact:
                                cnt_s2_r += 1
                        if flag or len(facts)-(cnt_s1_r1+cnt_s2_r)<5:
                            continue
                        if cnt_s1_r1==0 or cnt_s2_r==0:
                            print('***********************error*********************') 
                        
                        if cnt_s1_r1 < 10 or cnt_s2_r<10:

                            data_list=time_search[s1]+time_search[s2]     #已经用过了哪些对象
                            for data in data_list:
                                object_already_used.add(name_dict[data[1]])
                                if data[2]!='None':
                                    time1=eval(data[2])
                                    if time1[0]>time_high_limit:
                                        time_high_limit=time1[0]
                                    if time1[0]<time_low_limit:
                                        time_low_limit=time1[0]
                                if data[3]!='None':
                                    time1=eval(data[3])
                                    if time1[0]>time_high_limit:
                                        time_high_limit=time1[0]
                                    if time1[0]<time_low_limit:
                                        time_low_limit=time1[0]
                                    
                            if cnt_s1_r1 < 10:
                                need_s1_r1 = 10-cnt_s1_r1
                                while need_s1_r1>0 and times>0:
                                    get_generate = create_unoverlap_fact_object(interval_templates,point_templates,time_low_limit,time_high_limit,time,DA_object,r1,object_already_used,name_dict,s1)
                                    if get_generate is not None:
                                        new_fact,o2 = get_generate
                                        object_already_used.add(o2)
                                        facts.append(new_fact)
                                        need_s1_r1 -= 1
                                        cnt_s1_r1 += 1                     
                                    times -= 1
                            
                            if cnt_s2_r < 10:
                                need_s2_r = 10-cnt_s2_r
                                while need_s2_r>0 and times>0:
                                    get_generate = create_unoverlap_fact_object(interval_templates,point_templates,time_low_limit,time_high_limit,time,DA_object,r2,object_already_used,name_dict,s2)
                                    if get_generate is not None:
                                        new_fact,o2 = get_generate
                                        object_already_used.add(o2)
                                        facts.append(new_fact)
                                        need_s2_r -= 1
                                        cnt_s2_r += 1                     
                                    times -= 1                               


                        if cnt_s1_r1>=10 and cnt_s2_r>=10:   
                            random.shuffle(facts)  
                            # random.shuffle(inital_fact)
                            output_list.append({
                                "id": index,
                                "level": level,
                                "entity": subject_pair,
                                "relation": relation_pair,
                                "time": time_interval,
                                "query": question,
                                "answer": ans_cnt,
                                "fact": facts
                            })  
    
    c = {}
    relation_counts = {}
    data_list = []
    for json_data in output_list:
        data_list.append(json_data)
        relation_pair = json_data["relation"]
        if len(json_data['answer']) not in c:
            c[len(json_data['answer'])] = 0
        c[len(json_data['answer'])] += 1
        if relation_pair not in relation_counts:
            relation_counts[relation_pair] = 0
        relation_counts[relation_pair] += 1
    relation_counts = {key: value for key, value in relation_counts.items() if value >= 30}

    output_list=[]
    for key in relation_counts.keys():
        if relation_counts[key]<1000//len(relation_counts):
            for json_data in data_list:
                if json_data['relation']==key and json_data not in output_list:
                    output_list.append(json_data)
                    relation_counts[key]-=1

    relation_counts = {key: value for key, value in relation_counts.items() if value >= 10}
    random.shuffle(data_list)
    order = sorted(relation_counts.items(), key=lambda x: x[1])
    
    total=1000-len(output_list)
    for i in range(len(order)):
        num=total//(len(order)-i)
        cnt1=[]
        cnt2=[]
        cnt3=[]
        len1 = num*6.5//14
        len2 = num*6.5//14
        len3 = num-len1-len2
        for json_data in data_list:
            if json_data['relation'] == order[i][0] and json_data not in output_list:
                if len(json_data['answer'])>2:
                    if len3!=0:
                        relation_counts[order[i][0]]-=1
                        total-=1
                        num-=1
                        cnt3.append(json_data)
                        len3-=1
                    else:
                        cnt3=sorted(cnt3,key=lambda x:len(x.get('fact',[])))
                        if len(json_data['fact'])>len(cnt3[0]['fact']):
                            cnt3.pop(0)
                            cnt3.append(json_data)                   
                if len(json_data['answer'])==1:
                    if len1!=0:
                        relation_counts[order[i][0]]-=1
                        total-=1
                        num-=1
                        cnt1.append(json_data)
                        len1-=1
                    else:
                        cnt1=sorted(cnt1,key=lambda x:len(x.get('fact',[])))
                        if len(json_data['fact'])>len(cnt1[0]['fact']):
                            cnt1.pop(0)
                            cnt1.append(json_data)
                if len(json_data['answer'])==2:
                    if len2!=0:
                        relation_counts[order[i][0]]-=1
                        total-=1
                        num-=1
                        cnt2.append(json_data)
                        len2-=1
                    else:
                        cnt2=sorted(cnt2,key=lambda x:len(x.get('fact',[])))
                        if len(json_data['fact'])>len(cnt2[0]['fact']):
                            cnt2.pop(0)
                            cnt2.append(json_data)                  
            if relation_counts[order[i][0]]==0:
                break
        for item in cnt1+cnt2+cnt3:
            output_list.append(item)
    
    while len(output_list)<1000:
        for json_data in data_list:
            if json_data not in output_list:
                output_list.append(json_data)
                break   

    random.shuffle(output_list)
    print("Filtered data saved to:", output_file_path)
    relation_counts={}

    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        # output_list = random.sample(output_list, 1000)
        for json_data in output_list:
            relation_pair = json_data["relation"]
            json_data = json.dumps(json_data)
            output_file.write(json_data + '\n')

            if relation_pair not in relation_counts:
                relation_counts[relation_pair] = 0
            relation_counts[relation_pair] += 1

        print("关系统计结果:")
        for relation, count in relation_counts.items():
            print(f"{relation}: {count} 个")

months_dict = {1: 'January',2: 'February',3: 'March',4: 'April',5: 'May',6: 'June',7: 'July',8: 'August',9: 'September',10: 'October',11: 'November',12: 'December'}

search={'P39':'the position of',
        'P102':'member of',
        'P108':'work',
        'P69':'attend',
        'P6':'the head of',
        'P286':'head coach',
        'P54':'play',
        'P488':'the chair of',
        'P127':'own'}

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--task',
                    type=str,
                    default='S1_R1_O2',
                    help='the relation of the task')
    parser.add_argument('--question_templates',
                type=str,
                default='templates\level_4.csv',
                help='the template to generate the question')
    parser.add_argument('--data_level',
                type=str,
                default='v3',
                help='the amount of the raw data')
    parser.add_argument('--output_path',
                type=str,
                default='data_without_temporal_expression',
                help='where to store the data')
    args = parser.parse_args()
    task = args.task
    question_templates = args.question_templates
    data_level = args.data_level
    output_path = args.output_path
    data_generate(task,question_templates,data_level,output_path)