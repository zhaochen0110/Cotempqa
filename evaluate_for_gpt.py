import argparse, os
import itertools
import json, jsonlines, datetime, string
from collections import Counter
import re
import argparse

def read_qid_names(filepath):
    name_dict = {}
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            key, value = line.strip().split('\t')
            name_dict[key] = value
    return name_dict

def normalize_answer(s):
    # TODO: should we keep those counter removal? 
    def remove_counter(text):
        return text.replace("年", "").replace("歳", "").replace("人", "").replace("년", "")

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        # import pdb; pdb.set_trace()
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_counter(remove_punc(lower(s))))

def f1_score(prediction, ground_truth):
    common = Counter(prediction) & Counter(ground_truth)
    # print(prediction,ground_truth)
    num_same = sum(common.values())
    if num_same == 0:
        return (0,0,0)
    precision = 1.0 * num_same / len(prediction)
    recall = 1.0 * num_same / len(ground_truth)
    f1 = (2 * precision * recall) / (precision + recall)
    return (f1,precision,recall)

def exact_match_score(prediction, ground_truth):
    return prediction == ground_truth

def main(file_path):
    extract_template={
    'P39':["(.+?) holds the position of (.+?) from (.+?) to (.+?)\.",'(.+?) holds the position of (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\.'],
    'P102':["(.+?) is a member of the (.+?) from (.+?) to (.+?)\.",'(.+?) is a member of the (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\.'],
    'P69':["(.+?) attended (.+?) from (.+?) to (.+?)\.",'(.+?) attended (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\.'],
    'P108':["(.+?) works for (.+?) from (.+?) to (.+?)\.",'(.+?) works for (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\.'],
    'P54':["(.+?) plays for (.+?) from (.+?) to (.+?)\.",'(.+?) plays for (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\.'],
    'P488':["(.+?) is the chair of (.+?) from (.+?) to (.+?)\.",'(.+?) is the chair of (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\.'],
    'P6':["(.+?) is the head of (.+?) from (.+?) to (.+?)\.",'(.+?) is the head of (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\.'],
    'P127':["(.+?) is owned by (.+?) from (.+?) to (.+?)\.","(.+?) is owned by (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\."]
    }
    reverse_search = [(' the position of ', 'P39'),(' a member of ', 'P102'),(' the chair of ', 'P488'),(' the head of ', 'P6'),(' owned by ', 'P127'),(' attended ', 'P69'), (' works ', 'P108'),(' plays ', 'P54')]
    
    count = 0
    em_total = 0
    f1_total = 0
    r_total = 0
    p_total = 0
    cnt = set()
    with open(file_path,'r',encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            facts = data['fact']
            id = data['id']

            question = data['question']
            question=question.lower()
            if question in cnt:
                continue
            cnt.add(question)

            entity = data['entity']
            if 'S1_R1_O2' in id or 'S1_R2_O2' in id:
                entity_name = name_dict_all[entity].lower()
            elif 'S2_R1_O1' in id:
                entity_name = name_dict_v5[entity].lower()
            elif 'S2_R1_O2' in id or 'S2_R2_O2' in id:
                entity_name = name_dict_v3[entity[0]].lower()
                if 'which ' in question:
                    question_with_condition = question.split('which ')[0]
                elif 'who ' in question:
                    question_with_condition =  question.split('who ')[0]
                else:
                    print(question)
                if entity_name not in question_with_condition:
                    # print('error')
                    entity_name = name_dict_v3[entity[1]].lower()
                    if entity_name not in question_with_condition:
                        print(name_dict_v3[entity[0]].lower())
                        print(name_dict_v3[entity[1]].lower())
                        print(question)
                      
            if 'S2_R1_O1' in id:
                is_subject = True
            else:
                is_subject = False
            golds = data['text_answers']
            golds = [ans.lower() for ans in golds]
            prediction = data['ans']
            prediction = prediction.lower()
            if 'therefore' in prediction:
                prediction = prediction.split('therefore')[1]
            elif 'answer' in prediction:
                prediction = prediction.split('answer')[1]  

            prediction = prediction.lower()
            alternative_answers = []
            for fact in facts:
                is_match = False
                for p in reverse_search:
                    if is_match:
                        break
                    if " was " in fact:
                        fact = fact.replace(" was ", " is ")
                    if ' held ' in fact:
                        fact = fact.replace(' held ',' holds ')
                    if ' worked ' in fact:
                        fact = fact.replace(' worked ',' works ')
                    if ' played ' in fact:
                        fact = fact.replace(' played ',' plays ')  
                    if p[0] in fact:
                        # print(p[1])                  
                        relation = p[1]
                        template = extract_template[relation][0]
                        match = re.match(template,fact)
                        if match:
                            is_match = True
                            subject = match.group(1)
                            extract_content = match.group(2)
                            start_time = match.group(3)
                            end_time = match.group(4)
                        if not is_match:
                            template = extract_template[relation][1]
                            match = re.match(template,fact)
                            if match:
                                is_match = True
                                subject = match.group(1)
                                extract_content = match.group(2)
                                start_time = match.group(3) 
                        if is_match:
                            if is_subject:
                                alternative_answers.append(subject.lower())
                            else:
                                alternative_answers.append(extract_content.lower())
                
            predict = []
            alternative_answers = alternative_answers+golds
            alternative_answers = list(set(alternative_answers))
            alternative_answers = sorted(alternative_answers, key=len, reverse=True)
            shot = False
            flag = False

            for ans in alternative_answers:
                if ans in prediction and ans in question and not flag:
                    prediction = prediction.replace(ans,'')
                    flag =True
                    continue
                if ans in prediction and ans not in question:
                    predict.append(ans)
                    prediction = prediction.replace(ans,'')
                    shot = True 
                elif ans in prediction and ans in question and flag: 
                    predict.append(ans)
                    prediction = prediction.replace(ans,'')
                    shot = True 
                    
            if not shot:
                predict = [prediction]

            predict = list(set(predict))
            predict = [normalize_answer(i) for i in predict]
            predict.sort()
            golds = list(set(golds))
            golds = [normalize_answer(j) for j in golds]
            golds.sort()
            
            em_total += exact_match_score(predict,golds)
            f1,p,r = f1_score(predict,golds)
            f1_total += f1 
            p_total += p
            r_total += r
            count+=1
    print({'em': round(em_total*100/count,1), 'f1': round(f1_total*100/count,1),'p':round(p_total*100/count,1),'r':round(r_total*100/count,1),'avg':round((em_total+f1_total)*50/count,1)},end=' ')
    print('number:{0}'.format(count))
    return(em_total,f1_total,count)

if __name__ == '__main__':
    name_dict_v3 = read_qid_names('qid\\ailab_data_v3.txt')
    name_dict_v4 = read_qid_names('qid\\ailab_data_v4.txt')
    name_dict_v5 = read_qid_names('qid\\ailab_data_v5.txt')
    name_dict_all = read_qid_names('qid\\ailab_data_all.txt')
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path',
                        type=str,
                        default='S1_R1_O2.json',
                        help='The path to the json file')
    args = parser.parse_args()
    input_path = args.input_path
    main(input_path)