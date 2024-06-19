import json
import csv
import random
from tqdm import tqdm
import argparse

# Dictionary to map month numbers to month names
MONTHS_DICT = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 
    6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 
    11: 'November', 12: 'December'
}

# Dictionary to map relations to search terms
SEARCH_TERMS = {
    'P39': 'the position of', 'P102': 'member of', 'P108': 'work', 
    'P69': 'attend', 'P6': 'the head of', 'P286': 'head coach', 
    'P54': 'play', 'P488': 'the chair of', 'P127': 'own'
}

def read_qid_names(filepath):
    """
    Read QID names from a file and return a dictionary.
    
    Args:
    filepath (str): Path to the file containing QID names.
    
    Returns:
    dict: Dictionary with QID as keys and names as values.
    """  
    name_dict = {}
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                key, value = line.strip().split('\t')
                name_dict[key] = value
            except Exception as e:
                continue
    return name_dict

def convert_time(time):
    """
    Convert a time tuple to a formatted string.
    
    Args:
    time (tuple): A tuple containing year, month, and day.
    
    Returns:
    str: A formatted string representing the time.
    """
    if time[1] == 0:
        return str(time[0])
    elif time[2] == 0:
        return f'{MONTHS_DICT[time[1]]}, {time[0]}'
    else:
        return f'{MONTHS_DICT[time[1]]} {time[2]}, {time[0]}'

def complete_time(time):
    """
    Complete the time tuple by filling missing month and day with 0.
    
    Args:
    time (tuple): A tuple containing year, month, and day.
    
    Returns:
    tuple: A completed time tuple.
    """
    year, month, day = time
    return (year, month if month is not None else 0, day if day is not None else 0)

def transfer_time_to_int(time):
    """
    Convert time strings to integer tuples.
    
    Args:
    time (tuple): A tuple containing start and end time as strings.
    
    Returns:
    tuple: A tuple containing start and end time as integer tuples.
    """
    start_time, end_time = time
    if start_time == end_time:
        end_time = 'None'
    start_time = eval(start_time) if start_time != 'None' else (None, None, None)
    end_time = eval(end_time) if end_time != 'None' else (None, None, None)
    if start_time != (None, None, None) and end_time != (None, None, None):
        return (complete_time(start_time), complete_time(end_time))
    elif start_time != (None, None, None):
        return (complete_time(start_time))
    else:
        return (complete_time(end_time))

def read_jsonl(file_path):
    """
    Read JSON lines from a file and return a list of questions.
    
    Args:
    file_path (str): Path to the JSONL file.
    
    Returns:
    list: List of questions.
    """
    questions = []
    with open(file_path) as file:
        for line in file:
            question_item = json.loads(line)
            questions.append(question_item)
    return questions

def read_query_templates(filepath):
    """
    Read query templates from a CSV file and return a dictionary.
    
    Args:
    filepath (str): Path to the CSV file.
    
    Returns:
    dict: Dictionary with Wikidata ID as keys and templates as values.
    """
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return {row["Wikidata ID"]: row["Template"] for row in reader}

def transfer_lst_qid(lst, name_dict):
    """
    Convert a list of QIDs to their corresponding names.
    
    Args:
    lst (list): List of QIDs.
    name_dict (dict): Dictionary with QID as keys and names as values.
    
    Returns:
    list: List of names corresponding to the QIDs.
    """
    qid_name_lst = [name_dict[item] for item in lst]
    return qid_name_lst

def fact_combine(subjects, fact_dict):
    """
    Combine facts from multiple subjects into a single list.
    
    Args:
    subjects (list): List of subjects.
    fact_dict (dict): Dictionary with subjects as keys and lists of facts as values.
    
    Returns:
    list: Combined list of facts from all subjects.
    """
    fact_lst = []
    for subject in subjects:
        fact_lst.extend(fact_dict[subject])
    return fact_lst

def time_judgement(question_time, compare_time):
    """
    Determine if two time intervals overlap.
    
    Args:
    question_time (tuple): Time interval of the question.
    compare_time (tuple): Time interval to compare with.
    
    Returns:
    bool: True if the time intervals overlap, False otherwise.
    """
    if len(compare_time) == 2:
        start1, end1 = question_time
        start2, end2 = compare_time
        return (
            (start1 <= start2 < end1 and start1 < end2 <= end1) or
            (start2 <= start1 < end2 and start2 < end1 <= end2) or
            (start1 < start2 and end1 < end2 and start2 < end1) or
            (start2 < start1 and end2 < end1 and start1 < end2)
        )
    if len(compare_time) == 3:
        return question_time[0] <= compare_time <= question_time[1]
    if len(question_time) == 3:
        return compare_time[0] <= question_time <= compare_time[1]

def read_generate_templates(filepath):
    """
    Read generate templates from a CSV file and return a dictionary.
    
    Args:
    filepath (str): Path to the CSV file.
    
    Returns:
    dict: Dictionary with relations as keys and templates as values.
    """
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return {row["Relation"]: row["Templates"] for row in reader}

def create_unoverlap_fact_object(interval_templates, point_templates, low_limit, high_limit, time, object_count, relation, used_objects, name_dict, subject):
    """
    Create a non-overlapping fact for an object.
    
    Args:
    interval_templates (dict): Dictionary of interval templates.
    point_templates (dict): Dictionary of point templates.
    low_limit (int): Lower limit of the time range.
    high_limit (int): Upper limit of the time range.
    time (tuple): Current time interval.
    object_count (dict): Dictionary with relations as keys and lists of objects as values.
    relation (str): Relation type.
    used_objects (set): Set of already used objects.
    name_dict (dict): Dictionary with QID as keys and names as values.
    subject (str): Subject of the fact.
    
    Returns:
    tuple: New fact and the used object.
    """
    if random.randint(0, 1) == 0:
        s_year = random.randint(low_limit, high_limit)
        e_year = random.randint(s_year, high_limit)
        if random.randint(0, 2) != 0:
            s_month = random.randint(1, 12)
            e_month = random.randint(s_month, 12) if s_year == e_year else random.randint(1, 12)
            s_day = random.randint(1, 28) if random.randint(0, 1) == 0 else 0
            e_day = random.randint(s_day, 28) if s_day != 0 else 0
        else:
            s_month = s_day = e_month = e_day = 0
        s_date = (s_year, s_month, s_day)
        e_date = (e_year, e_month, e_day)
        if len(time) == 3 and (e_date > s_date and ((e_date < time and e_date[0] != time[0]) or (s_date > time and s_date[0] != time[0]))):
            while True:
                data_object = random.choice(object_count[relation])
                if data_object not in used_objects:
                    st = convert_time(s_date)
                    et = convert_time(e_date)
                    new_data = interval_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", data_object).replace('<st>', st).replace('<et>', et)
                    return new_data, data_object
        elif len(time) == 2 and (e_date > s_date and ((e_date < time[0] and e_date[0] != time[0][0]) or (s_date > time[1] and s_date[0] != time[1][0]))):
            while True:
                data_object = random.choice(object_count[relation])
                if data_object not in used_objects:
                    st = convert_time(s_date)
                    et = convert_time(e_date)
                    new_data = interval_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", data_object).replace('<st>', st).replace('<et>', et)
                    return new_data, data_object
    else:
        s_year = random.randint(low_limit, high_limit)
        s_month = random.randint(1, 12) if random.randint(0, 2) != 0 else 0
        s_day = random.randint(1, 28) if s_month != 0 and random.randint(0, 1) == 0 else 0
        s_date = (s_year, s_month, s_day)
        if len(time) == 3 and s_date != time and (s_date[0] != time[0] or (time[1] != 0 and s_date[1] != 0 and time[1] != s_date[1]) or (time[2] != 0 and s_date[2] != 0)):
            while True:
                data_object = random.choice(object_count[relation])
                if data_object not in used_objects:
                    st = convert_time(s_date)
                    new_data = point_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", data_object).replace('<st>', st)
                    return new_data, data_object
        elif len(time) == 2 and ((s_date < time[0] and (s_date[0] != time[0][0] or (time[0][1] != 0 and s_date[1] != 0 and time[0][1] != s_date[1]) or (time[0][2] != 0 and s_date[2] != 0))) or 
                                  (s_date > time[1] and (s_date[0] != time[1][0] or (time[1][1] != 0 and s_date[1] != 0 and time[1][1] != s_date[1]) or (time[1][2] != 0 and s_date[2] != 0)))):
            while True:
                data_object = random.choice(object_count[relation])
                if data_object not in used_objects:
                    st = convert_time(s_date)
                    new_data = point_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", data_object).replace('<st>', st)
                    return new_data, data_object
    return None

def create_unoverlap_fact_subject(interval_templates, point_templates, low_limit, high_limit, time, subject_count, relation, used_subjects, name_dict, object_):
    """
    Create a non-overlapping fact for a subject.
    
    Args:
    interval_templates (dict): Dictionary of interval templates.
    point_templates (dict): Dictionary of point templates.
    low_limit (int): Lower limit of the time range.
    high_limit (int): Upper limit of the time range.
    time (tuple): Current time interval.
    subject_count (dict): Dictionary with relations as keys and lists of subjects as values.
    relation (str): Relation type.
    used_subjects (set): Set of already used subjects.
    name_dict (dict): Dictionary with QID as keys and names as values.
    object_ (str): Object of the fact.
    
    Returns:
    tuple: New fact and the used subject.
    """
    if random.randint(0, 1) == 0:
        s_year = random.randint(low_limit, high_limit)
        e_year = random.randint(s_year, high_limit)
        if random.randint(0, 2) != 0:
            s_month = random.randint(1, 12)
            e_month = random.randint(s_month, 12) if s_year == e_year else random.randint(1, 12)
            s_day = random.randint(1, 28) if random.randint(0, 1) == 0 else 0
            e_day = random.randint(s_day, 28) if s_day != 0 else 0
        else:
            s_month = s_day = e_month = e_day = 0
        s_date = (s_year, s_month, s_day)
        e_date = (e_year, e_month, e_day)
        if len(time) == 3 and (e_date > s_date and ((e_date < time and e_date[0] != time[0]) or (s_date > time and s_date[0] != time[0]))):
            while True:
                data_subject = random.choice(subject_count[relation])
                if data_subject not in used_subjects:
                    st = convert_time(s_date)
                    et = convert_time(e_date)
                    new_data = interval_templates[relation].replace("<subject1>", name_dict[data_subject]).replace("<object1>", name_dict[object_]).replace('<st>', st).replace('<et>', et)
                    return new_data, data_subject
        elif len(time) == 2 and (e_date > s_date and ((e_date < time[0] and e_date[0] != time[0][0]) or (s_date > time[1] and s_date[0] != time[1][0]))):
            while True:
                data_subject = random.choice(subject_count[relation])
                if data_subject not in used_subjects:
                    st = convert_time(s_date)
                    et = convert_time(e_date)
                    new_data = interval_templates[relation].replace("<subject1>", name_dict[data_subject]).replace("<object1>", name_dict[object_]).replace('<st>', st).replace('<et>', et)
                    return new_data, data_subject
    else:
        s_year = random.randint(low_limit, high_limit)
        s_month = random.randint(1, 12) if random.randint(0, 2) != 0 else 0
        s_day = random.randint(1, 28) if s_month != 0 and random.randint(0, 1) == 0 else 0
        s_date = (s_year, s_month, s_day)
        if len(time) == 3 and s_date != time and (s_date[0] != time[0] or (time[1] != 0 and s_date[1] != 0 and time[1] != s_date[1]) or (time[2] != 0 and s_date[2] != 0)):
            while True:
                data_subject = random.choice(subject_count[relation])
                if data_subject not in used_subjects:
                    st = convert_time(s_date)
                    new_data = point_templates[relation].replace("<subject1>", name_dict[data_subject]).replace("<object1>", name_dict[object_]).replace('<st>', st)
                    return new_data, data_subject
        elif len(time) == 2 and ((s_date < time[0] and (s_date[0] != time[0][0] or (time[0][1] != 0 and s_date[1] != 0 and time[0][1] != s_date[1]) or (time[0][2] != 0 and s_date[2] != 0))) or 
                                  (s_date > time[1] and (s_date[0] != time[1][0] or (time[1][1] != 0 and s_date[1] != 0 and time[1][1] != s_date[1]) or (time[1][2] != 0 and s_date[2] != 0)))):
            while True:
                data_subject = random.choice(subject_count[relation])
                if data_subject not in used_subjects:
                    st = convert_time(s_date)
                    new_data = point_templates[relation].replace("<subject1>", name_dict[data_subject]).replace("<object1>", name_dict[object_]).replace('<st>', st)
                    return new_data, data_subject
    return None

def data_generate(task, query_templates, line, store_time, point_templates, interval_templates, name_dict, fact_dict, DA_object, time_search, is_subject):
    """
    Generate data for a given task.
    
    Args:
    task (str): Task name.
    query_templates (dict): Dictionary of query templates.
    line (dict): Dictionary containing query information.
    store_time (dict): Dictionary containing start and end times.
    point_templates (dict): Dictionary of point templates.
    interval_templates (dict): Dictionary of interval templates.
    name_dict (dict): Dictionary with QID as keys and names as values.
    fact_dict (dict): Dictionary with entities as keys and facts as values.
    DA_object (dict): Dictionary of objects.
    time_search (dict): Dictionary containing time-related search data.
    is_subject (bool): Boolean indicating if the entity is a subject.
    
    Returns:
    list: List of generated data.
    """
    output_list = []
    
    if 'S1_R1_O2' in task or 'S2_R1_O1' in task:
        # Handle S1_R1_O2 and S2_R1_O1 tasks together as they have fixed subjects and relations
        sentence = line["query"]
        main_entity = line["entity"]
        relation = line["relation"]
        if 'S2_R1_O2' in task and (relation == 'P286' or len(fact_dict[main_entity]) > 17):
            return []

        already_query = []
        already_question = []
        
        for num in range(len(sentence)):
            answer_set = set()

            time_interval, vice_entity1 = sentence[num][0]
            vice_entity2 = sentence[num][1]
            level =  sentence[num][2]

            if sentence[num][0] not in already_query and (main_entity, vice_entity1) not in already_question:
                already_query.append(sentence[num][0])
                already_question.append((main_entity, vice_entity1))  
                answer_set.add(vice_entity2)

                for pass_query in sentence:
                    compare_object = pass_query[0][1]
                    compare_time = pass_query[0][0]
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

                if relation in query_templates and answer_set and len(answer_set) < 5:
                    facts = fact_dict[main_entity].copy()
                    times = 5000
                    ans_cnt = transfer_lst_qid(list(answer_set), name_dict)
                    if is_subject:
                        subject = main_entity
                        object_ = vice_entity1
                    else:
                        subject = vice_entity1
                        object_ = main_entity
                    time = transfer_time_to_int(store_time[(relation, subject, object_)])
                    object_already_used = set()
                    question = query_templates[relation].replace("<subject1>", name_dict[subject]).replace("<object1>", name_dict[object_])
                    random_number = random.randint(0, 100)
                    index = f"S1_R1_O2_{relation}_{main_entity}_{random_number}"
                    facts_length = len(facts)
                    time_high_limit = 0
                    time_low_limit = float('inf')
                    
                    if facts_length < 10:
                        data_list = time_search[main_entity]
                        for data in data_list:
                            object_already_used.add(name_dict[data[1]])
                            if data[2] != 'None':
                                time1 = eval(data[2])
                                time_high_limit = max(time_high_limit, time1[0])
                                time_low_limit = min(time_low_limit, time1[0])
                            if data[3] != 'None':
                                time1 = eval(data[3])
                                time_high_limit = max(time_high_limit, time1[0])
                                time_low_limit = min(time_low_limit, time1[0])

                        need_num = 10 - facts_length
                        while need_num > 0 and times > 0:
                            if is_subject:
                                generated = create_unoverlap_fact_object(interval_templates, point_templates, time_low_limit, time_high_limit, time, DA_object, relation, object_already_used, name_dict, main_entity)
                            else:
                                generated = create_unoverlap_fact_subject(interval_templates, point_templates, time_low_limit, time_high_limit, time, DA_object, relation, object_already_used, name_dict, main_entity)
                            if generated is not None:
                                new_fact, o2 = generated
                                object_already_used.add(o2)
                                facts.append(new_fact)
                                need_num -= 1   
                                facts_length += 1                  
                            times -= 1

                    if facts_length >= 10:  
                        random.shuffle(facts)   
                        output_list.append({
                            "id": index,
                            "level": level,
                            "entity": main_entity,
                            "relation": relation,
                            "time": time_interval,
                            "query": question,
                            "answer": ans_cnt,
                            "fact": facts,
                            "is_subject": not is_subject
                        })

    elif 'S1_R2_O2' in task:
        relation_pair = {}
        sentence = line["query"]
        main_entity = line["entity"]
        already_query = []
        already_question = []

        for num in range(len(sentence)):
            answer_set = set()

            time_interval, rel_obj1 = sentence[num][0]
            relation1, object1 = rel_obj1

            rel_obj2 = sentence[num][1]
            relation2, object2 = rel_obj2

            level = sentence[num][2]

            if sentence[num][0] not in already_query and (relation1, object1, relation2, main_entity) not in already_question:
                relation_pair_str = f"{relation1}-{relation2}"
                already_query.append(sentence[num][0])
                already_question.append((relation1, object1, relation2, main_entity))
                answer_set.add(object2)

                if relation_pair_str in ['P39-P102', 'P39-P108', 'P102-P39', 'P69-P108', 'P108-P69', 'P69-P39', 'P108-P39', 'P102-P108', 'P69-P102', 'P102-P69', 'P54-P69', 'P54-P286', 'P39-P6']:
                    if relation_pair_str not in relation_pair:
                        relation_pair[relation_pair_str] = 0
                    relation_pair[relation_pair_str] += 1    
                    
                    for pass_query in sentence:
                        compare_r_o1 = pass_query[0][1]
                        compare_r_o2 = pass_query[1]
                        compare_time = pass_query[0][0]

                        if compare_r_o1 == rel_obj1 and compare_r_o2[0] == relation2:
                            if len(time_interval) == 3:
                                if compare_time == time_interval:
                                    answer_set.add(compare_r_o2[1])
                            else:
                                if time_judgement(time_interval, compare_time):
                                    answer_set.add(compare_r_o2[1])
                                else:
                                    answer_set = set()
                                    break

                        if compare_r_o2 == rel_obj1 and compare_r_o1[0] == relation2:
                            if len(time_interval) == 3:
                                if compare_time == time_interval:
                                    answer_set.add(compare_r_o1[1])
                            else:
                                if time_judgement(time_interval, compare_time):
                                    answer_set.add(compare_r_o1[1])
                                else:
                                    answer_set = set()
                                    break

                    if answer_set and len(answer_set) < 5 and relation_pair_str in query_templates:
                        facts = fact_dict[main_entity].copy()
                        times = 10000
                        time = transfer_time_to_int(store_time[(relation1, main_entity, object1)])
                        ans_cnt = transfer_lst_qid(list(answer_set), name_dict)
                        object_already_used = set()
                        question = query_templates[relation_pair_str].replace("<subject1>", name_dict[main_entity]).replace("<object1>", name_dict[object1])
                        random_number = random.randint(0, 100)
                        index = f"S1_R2_O2_{relation_pair_str}_{main_entity}_{random_number}"
                        facts_length = len(facts)
                        time_high_limit = 0
                        time_low_limit = float('inf')
                        cnt_r1 = 0
                        cnt_r2 = 0
                        flag = False
                        for fact in facts:
                            if SEARCH_TERMS[relation1] in fact and SEARCH_TERMS[relation2] in fact:
                                flag = True
                                break
                            if SEARCH_TERMS[relation1] in fact:
                                cnt_r1 += 1
                            elif SEARCH_TERMS[relation2] in fact:
                                cnt_r2 += 1
                        if flag:
                            continue
                        
                        if cnt_r1 < 10 or cnt_r2 < 10:
                            data_list = time_search[main_entity]
                            for data in data_list:
                                object_already_used.add(name_dict[data[1]])
                                if data[2] != 'None':
                                    time1 = eval(data[2])
                                    time_high_limit = max(time_high_limit, time1[0])
                                    time_low_limit = min(time_low_limit, time1[0])
                                if data[3] != 'None':
                                    time1 = eval(data[3])
                                    time_high_limit = max(time_high_limit, time1[0])
                                    time_low_limit = min(time_low_limit, time1[0])

                            if cnt_r1 < 10:
                                need_r1 = 10 - cnt_r1
                                while need_r1 > 0 and times > 0:    
                                    generated = create_unoverlap_fact_object(interval_templates, point_templates, time_low_limit, time_high_limit, time, DA_object, relation1, object_already_used, name_dict, main_entity)
                                    if generated is not None:
                                        new_fact, o2 = generated
                                        object_already_used.add(o2)
                                        facts.append(new_fact)
                                        need_r1 -= 1 
                                        cnt_r1 += 1                    
                                    times -= 1
                            
                            if cnt_r2 < 10:
                                need_r2 = 10 - cnt_r2
                                while need_r2 > 0 and times > 0:
                                    generated = create_unoverlap_fact_object(interval_templates, point_templates, time_low_limit, time_high_limit, time, DA_object, relation2, object_already_used, name_dict, main_entity)
                                    if generated is not None:
                                        new_fact, o2 = generated
                                        object_already_used.add(o2)
                                        facts.append(new_fact)
                                        need_r2 -= 1 
                                        cnt_r2 += 1                    
                                    times -= 1                                    

                        if cnt_r1 >= 10 and cnt_r2 >= 10:  
                            random.shuffle(facts)   
                            output_list.append({
                                "id": index,
                                "level": level,
                                "entity": main_entity,
                                "relation": relation_pair_str,
                                "time": time_interval,
                                "query": question,
                                "answer": ans_cnt,
                                "fact": facts,
                                "is_subject": not is_subject
                            })

    elif 'S2_R1_O2' in task or 'S2_R2_O2' in task:
        sentence = line["query"]
        subject_pair = line["entity_pair"]
    
        already_query = []
        already_question = []

        for num in range(len(sentence)):
            answer_set = set()

            time_interval, fact1 = sentence[num][0]
            s1, r1, o1 = fact1
            fact2 = sentence[num][1]
            s2, r2, o2 = fact2
            level =  sentence[num][2]
            relation_pair = r1
            if 'S2_R2_O2' in task:
                relation_pair = f"{r1}-{r2}"
                query_condition = (s1, r1, o1, s2, r2)
            else:
                if r1 != r2:
                    continue
                else:
                    query_condition = (s1, r1, o1, s2)
            if sentence[num][0] not in already_query and query_condition not in already_question:
                already_query.append(sentence[num][0])
                already_question.append(query_condition)
                answer_set.add(o2)

                for pass_query in sentence:
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
                                if 'S2_R2_O2' in task and len(compare_time) == 3 and compare_time in [time_interval[0], time_interval[1]]:
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
                                if 'S2_R2_O2' in task and len(compare_time) == 3 and compare_time in [time_interval[0], time_interval[1]]:
                                    answer_set = set()
                                    break   
                            else:
                                answer_set = set()
                                break

                if answer_set and relation_pair in query_templates and len(answer_set) < 5 and s1 in fact_dict and s2 in fact_dict:
                    facts1 = fact_dict[s1].copy()
                    facts2 = fact_dict[s2].copy()
                    facts = facts1 + facts2
                    times = 2000
                    ans_cnt = transfer_lst_qid(list(answer_set), name_dict)
                    time = transfer_time_to_int(store_time[(r1, s1, o1)])
                    object_already_used = set()
                    question = query_templates[relation_pair].replace("<subject1>", name_dict[s1]).replace("<object1>", name_dict[o1]).replace("<subject2>", name_dict[s2])
                    random_number = random.randint(0, 100)
                    index = f"S2_R1_O2_{r1}_{s1}_{s2}_{random_number}" if 'S2_R1_O2' in task else f"S2_R2_O2_{r1}_{r2}_{s1}_{s2}_{random_number}"
                    facts_length = len(facts)
                    time_high_limit = 0
                    time_low_limit = float('inf')
                    cnt_s1_r1 = 0
                    cnt_s2_r = 0
                    flag = False
                    for fact in facts:
                        if (name_dict[s1] in fact and name_dict[s2] in fact and SEARCH_TERMS[r1] and r1 == r2) or (r1 != r2 and SEARCH_TERMS[r1] in fact and SEARCH_TERMS[r2] in fact):
                            flag = True
                        if name_dict[s1] in fact and SEARCH_TERMS[r1] in fact:
                            cnt_s1_r1 += 1
                        elif name_dict[s2] in fact and SEARCH_TERMS[r2] in fact:
                            cnt_s2_r += 1
                    if flag or len(facts) - (cnt_s1_r1 + cnt_s2_r) < 5:
                        continue
                    if cnt_s1_r1 == 0 or cnt_s2_r == 0:
                        print('***********************error*********************') 
                    
                    if cnt_s1_r1 < 10 or cnt_s2_r < 10:
                        data_list = time_search[s1] + time_search[s2]
                        for data in data_list:
                            object_already_used.add(name_dict[data[1]])
                            if data[2] != 'None':
                                time1 = eval(data[2])
                                time_high_limit = max(time_high_limit, time1[0])
                                time_low_limit = min(time_low_limit, time1[0])
                            if data[3] != 'None':
                                time1 = eval(data[3])
                                time_high_limit = max(time_high_limit, time1[0])
                                time_low_limit = min(time_low_limit, time1[0])
                                
                        if cnt_s1_r1 < 10:
                            need_s1_r1 = 10 - cnt_s1_r1
                            while need_s1_r1 > 0 and times > 0:
                                generated = create_unoverlap_fact_object(interval_templates, point_templates, time_low_limit, time_high_limit, time, DA_object, r1, object_already_used, name_dict, s1)
                                if generated is not None:
                                    new_fact, o2 = generated
                                    object_already_used.add(o2)
                                    facts.append(new_fact)
                                    need_s1_r1 -= 1
                                    cnt_s1_r1 += 1                     
                                times -= 1
                        
                        if cnt_s2_r < 10:
                            need_s2_r = 10 - cnt_s2_r
                            while need_s2_r > 0 and times > 0:
                                generated = create_unoverlap_fact_object(interval_templates, point_templates, time_low_limit, time_high_limit, time, DA_object, r2, object_already_used, name_dict, s2)
                                if generated is not None:
                                    new_fact, o2 = generated
                                    object_already_used.add(o2)
                                    facts.append(new_fact)
                                    need_s2_r -= 1
                                    cnt_s2_r += 1                     
                                times -= 1                               

                    if cnt_s1_r1 >= 10 and cnt_s2_r >= 10:   
                        random.shuffle(facts)  
                        output_list.append({
                            "id": index,
                            "level": level,
                            "entity": subject_pair,
                            "relation": relation_pair,
                            "time": time_interval,
                            "query": question,
                            "answer": ans_cnt,
                            "fact": facts,
                            "is_subject": not is_subject
                        })  
    return output_list
