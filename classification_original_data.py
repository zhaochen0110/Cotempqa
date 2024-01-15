import argparse, os
import itertools
import json, jsonlines, datetime, string
from collections import Counter
import re

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

months_dict = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

reverse_month = {value:key for key,value in months_dict.items()}

def time_transfer(st):
    if len(st.split(', '))==2:
        year = eval(st.split(', ')[1])
        month_day = st.split(', ')[0]
        if len(month_day.split(' '))==2:
            month,day = month_day.split(' ')
            month = reverse_month[month]
            day = eval(day)
        else:
            month=reverse_month[month_day]
            day = 0
    else:
        year = eval(st)
        month = 0
        day = 0
    return (year,month,day)

def time_judge(time1, time2):
    if len(time1) == 1 and len(time2) == 1:
        # print(time1,time2)
        return 1
    elif len(time1) == 1 and len(time2) == 2:
        return 2
    elif len(time1) == 2 and len(time2) == 1:
        return 2
    else:
        start1,end1 = time1
        start2,end2 = time2
        if start1==start2 and end1==end2:
            return 1
        
        if start2 < start1 and start1< end1 and end1<= end2:
            return 2
        
        if start2 <= start1 and start1 < end1 and end1 < end2:
            return 2       
        
        # s1 s2 e2 e1
        if start1 <= start2 and start2 < end2 and end2 < end1:
            return 2

        if start1 < start2 and start2 < end2 and end2 <= end1:
            return 2
               
        # s1 s2 e1 e2
        if start1 < start2 and start2 < end1 and end1 < end2:
            return 3
        
        # s1 e2 e1 s2    
        if start2 < start1 and start1 < end2 and end2 < end1:
            return 3
        
overlap_list=[]
mix_list=[]
during_list=[]
equal_list=[]
for file in ['S1_R1_O2.json','S1_R2_O2.json','S2_R1_O1.json','S2_R1_O2.json','S2_R2_O2.json']:
    is_subject = False
    if file == 'S2_R1_O1.json':
        is_subject = True
    output_list = []
    with open('result//'+file,'r',encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            id = data ['id']
            if 'P488' in id:
                continue
            if 'P69' not in id and 'P6' in id:
                continue
            level = data['level']
            answer = data['answer']
            if len(answer) == 1:
                if 'during' in level:
                    output_list.append({
                        'id':data['id'],
                        'question':data['query'],
                        'class':'during',
                        'is_subject':is_subject
                    })
                    during_list.append(data)
                elif 'equal' in level:
                    output_list.append({
                        'id':data['id'],
                        'question':data['query'],
                        'class':'equal',
                        'is_subject':is_subject
                    })
                    equal_list.append(data)
                elif 'overlap' in level:
                    output_list.append({
                        'id':data['id'],
                        'question':data['query'],
                        'class':'overlap',
                        'is_subject':is_subject
                    })
                    overlap_list.append(data)
                else:
                    print('classify error')
            else:
                facts = data['fact']
                question = data['query']
                alternative_answers_with_time = {}
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
                            start_time = ''
                            end_time = ''
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
                                if end_time != '':
                                    if is_subject:
                                        alternative_answers_with_time[subject] = [time_transfer(start_time),time_transfer(end_time)]
                                    else:
                                        alternative_answers_with_time[extract_content] = [time_transfer(start_time),time_transfer(end_time)]
                                else:
                                    if is_subject:
                                        alternative_answers_with_time[subject] = [time_transfer(start_time)]
                                    else:
                                        alternative_answers_with_time[extract_content] = [time_transfer(start_time)]     
                new = sorted(alternative_answers_with_time.items(),key = lambda x:len(x[0]),reverse=True)   
                for item in new:
                    if item[0] in  question:
                        condition_time = item[1]
                        break
                answer_time_cnt = {}

                for item in new:
                    if item[0] in answer:
                        answer_time_cnt[item[0]] = item[1]

                cnt_1 = 0
                cnt_2 = 0
                cnt_3 = 0
                is_mix = False
                for ans in answer_time_cnt.items():
                    if is_mix:
                        break
                    # print(condition_time,ans[1])
                    res = time_judge(condition_time,ans[1])
                    if res == 1:
                        if cnt_2==0 and cnt_3==0:
                            cnt_1 += 1
                        else:
                            output_list.append({
                                'id':data['id'],
                                'question':data['query'],
                                'class':'mix',
                                'is_subject':is_subject
                            })
                            mix_list.append(data)
                            is_mix = True
                    elif res == 2:
                        if cnt_1==0 and cnt_3==0:
                            cnt_2 += 1
                        else:
                            output_list.append({
                                'id':data['id'],
                                'question':data['query'],
                                'class':'mix',
                                'is_subject':is_subject
                            })
                            mix_list.append(data)
                            is_mix = True
                    else:
                        if cnt_1==0 and cnt_2==0:
                            cnt_3 += 1
                        else:
                            output_list.append({
                                'id':data['id'],
                                'question':data['query'],
                                'class':'mix',
                                'is_subject':is_subject
                            })
                            mix_list.append(data)
                            is_mix = True
                if not is_mix:
                    if cnt_1!=0:
                        output_list.append({
                            'id':data['id'],
                            'question':data['query'],
                            'class':'equal',
                            'is_subject':is_subject
                        })
                        equal_list.append(data)
                    elif cnt_2!=0:
                        output_list.append({
                            'id':data['id'],
                            'question':data['query'],
                            'class':'during',
                            'is_subject':is_subject
                        })
                        during_list.append(data)
                    elif cnt_3!=0:
                        output_list.append({
                            'id':data['id'],
                            'question':data['query'],
                            'class':'overlap',
                            'is_subject':is_subject
                        })
                        overlap_list.append(data)

for file in ['equal.json','overlap.json','during.json','mix.json']:
    if file == 'equal.json':
        output_list = equal_list
    elif file == 'overlap.json':
        output_list = overlap_list
    elif file == 'during.json':
        output_list = during_list
    elif file == 'mix.json':
        output_list = mix_list
    with open('classified_data\\'+file,'w',encoding='utf-8') as f:
        cnt = 0
        for data in output_list:
            if 'S1_R1_O2' in data['id']:
                triple_element = 'S1_R1_O2'
            elif 'S1_R2_O2' in data['id']:
                triple_element = 'S1_R2_O2'
            elif 'S2_R1_O1' in data['id']:
                triple_element = 'S2_R1_O1'
            elif 'S2_R1_O2' in data['id']:
                triple_element = 'S2_R1_O2'
            elif 'S2_R2_O2' in data['id']:
                triple_element = 'S2_R2_O2'
            json_data = {
                'index':cnt,
                'triple_element':triple_element,
                'question':data['query'],
                'facts':data['fact']
            }
            json_data=json.dumps(json_data)
            f.write(json_data + '\n')
            cnt+=1

