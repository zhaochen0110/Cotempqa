import argparse, os
import itertools
import json, jsonlines, datetime, string
from collections import Counter
import re

def classified_data(file):
    equal = []
    overlap = []
    during = []
    mix = []
    mix_fs = []
    overlap_fs = []
    equal_fs = []
    during_fs = []
    equal_cot = []
    overlap_cot = []
    during_cot = []
    mix_cot = []
    cnt =0
    if 'equal' in file:
        origin_file = 'equal.json'
    elif 'overlap' in file:
        origin_file = 'overlap.json'
    elif 'during' in file:
        origin_file = 'during.json'
    elif 'mix' in file:
        origin_file = 'mix.json'

    q_cnt = set()
    origin_datas = []
    with open('classified_data\\'+origin_file,'r',encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            origin_datas.append(item)
    with open(file,'r',encoding='utf-8') as f:
        all_data = json.load(f)
    # print(file)
    for key in all_data.keys():
        cnt+=1
        data = all_data[key]
        origin_promote = data['origin_prompt']
        question = origin_promote.split('Question:')[-1]

        for origin_data in origin_datas:
            if origin_data['question'] in question:
                if 'S1_R1_O2' in origin_data['triple_element']:
                    data['is_subject'] = False
                else:
                    data['is_subject'] = True
                data['question'] = origin_data['question']
                data['facts'] = origin_data['facts']
                if question in q_cnt:
                    continue
                if 'fs_equal' in file:
                    equal_fs.append(data)
                elif 'fs_overlap' in file:
                    overlap_fs.append(data)
                elif 'fs_during' in file:
                    during_fs.append(data)
                elif 'fs_mix' in file:
                    mix_fs.append(data)
                elif 'fs_cot_equal' in file:
                    equal_cot.append(data)
                elif 'fs_cot_overlap' in file:
                    overlap_cot.append(data)
                elif 'fs_cot_during' in file:
                    during_cot.append(data)
                elif 'fs_cot_mix' in file:
                    mix_cot.append(data)
                elif 'equal' in file:
                    equal.append(data)
                elif 'overlap' in file:
                    overlap.append(data)
                elif 'during' in file:
                    during.append(data)
                elif 'mix' in file:
                    mix.append(data)
                q_cnt.add(question)
    for i in [equal,equal_fs,equal_cot,during,during_fs,during_cot,mix,mix_fs,mix_cot,overlap,overlap_fs,overlap_cot]:
        if i!=[]:
            return i
    
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

def exact_match_score(prediction, ground_truth):
    return prediction == ground_truth

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

extract_template={
'P39':["(.+?) holds the position of (.+?) from (.+?) to (.+?)\.","(.+?) holds the position of (.+?) in (.+?)\.","(.+?) holds the position of (.+?) from (.+?)","(.+?) holds the position of (.+?) in (.+?)\.","(.+?) holds the position of (.+?)\."],
'P102':["(.+?) is a member of the (.+?) from (.+?) to (.+?)\.","(.+?) is a member of the (.+?) in (.+?)\.","(.+?) is a member of the (.+?) from (.+?)","(.+?) is a member of the (.+?)\."],
'P69':["(.+?) attended (.+?) from (.+?) to (.+?)\.","(.+?) attended (.+?) in (.+?)\.","(.+?) attended (.+?) from (.+?)","(.+?) attended (.+?)\."],
'P108':["(.+?) works for (.+?) from (.+?) to (.+?)\.","(.+?) works for (.+?) in (.+?)\.","(.+?) works for (.+?) from (.+?)","(.+?) works for (.+?)\."],
'P54':["(.+?) plays for (.+?) from (.+?) to (.+?)\.","(.+?) plays for (.+?) in (.+?)\.","(.+?) plays for (.+?) from (.+?)","(.+?) plays for (.+?)\."],
'P488':["(.+?) is the chair of (.+?) from (.+?) to (.+?)\.","(.+?) is the chair of (.+?) in (.+?)\.","(.+?) is the chair of (.+?) from (.+?)","(.+?) is the chair of (.+?)\."],
'P6':["(.+?) is the head of (.+?) from (.+?) to (.+?)\.","(.+?) is the head of (.+?) in (.+?)\.","(.+?) is the head of (.+?) from (.+?)","(.+?) is the head of (.+?)\."],
'P127':["(.+?) is owned by (.+?) from (.+?) to (.+?)\.","(.+?) is owned by (.+?) in (.+?)\.","(.+?) is owned by (.+?) from (.+?)",'"(.+?) is owned by (.+?)\.']
}

search_dict = {
    'P39':' the position of ',
    'P102':' a member of ',
    'P69':'attend',
    'P108':'work',
    'P54':'play',
    'P488':' the chair of ',
    'P6':' the head of ',
    'P127':' owned by '
}

reverse_search = [(' the position of ', 'P39'),(' a member of ', 'P102'),(' the chair of ', 'P488'),(' the head of ', 'P6'),(' owned by ', 'P127'),('attend', 'P69'), ('work', 'P108'),('play', 'P54')]


def main(input_path):
    all_data = classified_data(input_path)
    em_total = 0
    f1_total = 0
    p_total = 0
    r_total = 0
    count = 0
    for data in all_data:
        golds = data['gold'] #对比大小写区别
        golds = [ans.lower() for ans in golds]
        
        is_subject = data['is_subject']
        
        prediction = data['prediction']
        prediction = prediction.lower()
        if 'cot' in input_path:
            if 'therefore the answer is' not in prediction:
                prediction = 'answer'
            else:
                prediction = prediction.split('therefore the answer is')[1]
                prediction = prediction.split('answer the question based on')[0]
        elif 'answer the question based on' in prediction:
            prediction=prediction.split('answer the question based on')[0]
        elif ' answer ' in prediction:
            prediction=prediction.split(' answer ')[1]
 
        facts = data['facts']
        question = data['question']
        question = question.lower()
        
        alternative_answers=[] #对比大小写区别

        for fact in facts:
            is_match = False
            for p in reverse_search:
                if is_match:
                    break
                if p[0] in fact:
                    if " was " in fact:
                        fact = fact.replace(" was ", " is ")
                    if ' held ' in fact:
                        fact = fact.replace(' held ',' holds ')
                    if ' worked ' in fact:
                        fact = fact.replace(' worked ',' works ')
                    if ' played ' in fact:
                        fact = fact.replace(' played ',' plays ')                    
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
                            alternative_answers.append(subject.lower()) #对比大小写区别
                        else:
                            alternative_answers.append(extract_content.lower()) #对比大小写区别
        
        alternative_answers = alternative_answers+golds
        alternative_answers = list(set(alternative_answers))
        alternative_answers = sorted(alternative_answers, key=len, reverse=True) 

        shot = False    
        flag = False
        predict = []
        for ans in alternative_answers:
            if ans in prediction and ans in question and not flag:
                prediction = prediction.replace(ans,'')
                flag = True
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
        
        # print(predict)
        predict = list(set(predict))
        predict = [normalize_answer(i) for i in predict] 
        predict.sort()
        golds = list(set(golds))
        golds = [normalize_answer(i) for i in golds]
        golds.sort()
        
        em_total += exact_match_score(predict,golds)
        f1,p,r = f1_score(predict,golds)
        f1_total += f1 
        p_total += p
        r_total+=r
        count+=1

    print(input_path,end=':')
    print({'em': round(em_total*100/count,1), 'f1': round(f1_total*100/count,1),'p':round(p_total*100/count,1),'r':round(r_total*100/count,1),'avg':round((em_total+f1_total)*50/count,1)},end=' ')
    print('number:{0}'.format(count)) 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path',
                        type=str,
                        default='S1_R1_O2.json',
                        help='The path to the json file')
    args = parser.parse_args()
    input_path = args.input_path
    main(input_path)