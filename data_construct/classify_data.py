import argparse
import os
import itertools
import json
import jsonlines
import datetime
import string
from collections import Counter
import re

# Extract templates for different properties
EXTRACT_TEMPLATES = {
    'P39': [
        r"(.+?) holds the position of (.+?) from (.+?) to (.+?)\.",
        r"(.+?) holds the position of (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\."
    ],
    'P102': [
        r"(.+?) is a member of the (.+?) from (.+?) to (.+?)\.",
        r"(.+?) is a member of the (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\."
    ],
    'P69': [
        r"(.+?) attended (.+?) from (.+?) to (.+?)\.",
        r"(.+?) attended (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\."
    ],
    'P108': [
        r"(.+?) works for (.+?) from (.+?) to (.+?)\.",
        r"(.+?) works for (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\."
    ],
    'P54': [
        r"(.+?) plays for (.+?) from (.+?) to (.+?)\.",
        r"(.+?) plays for (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\."
    ],
    'P488': [
        r"(.+?) is the chair of (.+?) from (.+?) to (.+?)\.",
        r"(.+?) is the chair of (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\."
    ],
    'P6': [
        r"(.+?) is the head of (.+?) from (.+?) to (.+?)\.",
        r"(.+?) is the head of (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\."
    ],
    'P127': [
        r"(.+?) is owned by (.+?) from (.+?) to (.+?)\.",
        r"(.+?) is owned by (.+?) in ((?:\d{4}|January|February|March|April|May|June|July|August|September|October|November|December).*?)\."
    ]
}

# Search terms for different properties
RELATION_SEARCH_TERMS = {
    'P39': ' the position of ',
    'P102': ' a member of ',
    'P69': 'attend',
    'P108': 'work',
    'P54': 'play',
    'P488': ' the chair of ',
    'P6': ' the head of ',
    'P127': ' owned by '
}

# Reverse mapping of search terms to properties
REVERSE_RELATION_SEARCH = [
    (' the position of ', 'P39'),
    (' a member of ', 'P102'),
    (' the chair of ', 'P488'),
    (' the head of ', 'P6'),
    (' owned by ', 'P127'),
    ('attend', 'P69'),
    ('work', 'P108'),
    ('play', 'P54')
]

# Dictionary for month names and their numerical equivalents
MONTHS_DICT = {
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

# Reverse mapping of month names to numbers
REVERSE_MONTHS_DICT = {v: k for k, v in MONTHS_DICT.items()}

def convert_time(time_str):
    """
    Convert a time string to a tuple (year, month, day).

    Args:
    time_str (str): A string representing the time.

    Returns:
    tuple: A tuple containing year, month, and day.
    """
    if ', ' in time_str:
        year = int(time_str.split(', ')[1])
        month_day = time_str.split(', ')[0]
        if ' ' in month_day:
            month, day = month_day.split(' ')
            month = REVERSE_MONTHS_DICT[month]
            day = int(day)
        else:
            month = REVERSE_MONTHS_DICT[month_day]
            day = 0
    else:
        year = int(time_str)
        month = 0
        day = 0
    return (year, month, day)

def time_relation(time1, time2):
    """
    Classify the relationship between two time periods.
    
    Return values:
    'equal' - if time periods are exactly equal
    'during' - if one time period is within the other
    'overlap' - if time periods overlap
    """
    if len(time1) == 1 and len(time2) == 1:  # point-time == point-time
        return 'equal'
    elif (len(time1) == 1 and len(time2) == 2) or (len(time1) == 2 and len(time2) == 1):  # point-time is a subset of interval-time
        return 'during'
    else:  # interval-time & interval-time
        start1, end1 = time1
        start2, end2 = time2
        if start1 == start2 and end1 == end2:
            return 'equal'
        
        # time1 is a subset of time2
        if (start2 < start1 < end1 <= end2) or (start2 <= start1 < end1 < end2):
            return 'during'    
        
        # time2 is a subset of time1
        if (start1 <= start2 < end2 < end1) or (start1 < start2 < end2 <= end1):
            return 'during'

        # Overlap cases
        if start1 < start2 < end1 < end2:
            return 'overlap'
        
        if start2 < start1 < end2 < end1:
            return 'overlap'

def classify_data(data):
    """
    Classify data into four classes: equal, during, overlap, mix.

    Args:
    data (dict): A dictionary containing the data to be classified.

    Returns:
    dict or None: A dictionary with classified data or None if the classification fails.
    """
    is_subject = data['is_subject']
    entity_id = data['id']
    
    if 'P488' in entity_id:
        return None
    if 'P69' not in entity_id and 'P6' in entity_id:
        return None
    
    level = data['level']
    answers = data['answer']
    
    # If only one answer, use the level to determine the class
    if len(answers) == 1:
        if 'during' in level:
            class_label = 'during'
        elif 'equal' in level:
            class_label = 'equal'
        elif 'overlap' in level:
            class_label = 'overlap'
        else:
            print('Classification error')
            return None
        
        return {
            'id': entity_id,
            'question': data['query'],
            'class': class_label,
            'is_subject': is_subject,
            'facts': data['fact'],
            'answer': data['answer']
        }

    facts = data['fact']
    query = data['query']
    alt_answers_with_time = {}
    
    # Extract all possible answers from facts and timestamps
    for fact in facts:
        is_match = False
        for search_term, prop in REVERSE_RELATION_SEARCH:
            if search_term in fact:
                fact = fact.replace(" was ", " is ").replace(' held ', ' holds ').replace(' worked ', ' works ').replace(' played ', ' plays ')
                for template in EXTRACT_TEMPLATES[prop]:
                    match = re.match(template, fact)
                    if match:
                        is_match = True
                        subject = match.group(1)
                        content = match.group(2)
                        start_time = match.group(3)
                        end_time = match.group(4) if len(match.groups()) > 3 else ''
                        times = [convert_time(start_time)]
                        if end_time:
                            times.append(convert_time(end_time))
                        if is_subject:
                            alt_answers_with_time[subject] = times
                        else:
                            alt_answers_with_time[content] = times
                        break
            if is_match:
                break

    sorted_answers = sorted(alt_answers_with_time.items(), key=lambda x: len(x[0]), reverse=True)
    condition_time = False
    for ans in sorted_answers:
        if ans[0] in query and ans[0] not in answers:
            condition_time = ans[1]
            break
    if not condition_time:
        return None

    answer_time_counts = {ans[0]: ans[1] for ans in sorted_answers if ans[0] in answers}

    cnt_equal = 0
    cnt_during = 0
    cnt_overlap = 0
    
    # Determine the class based on the relationships
    for ans, times in answer_time_counts.items():
        result = time_relation(condition_time, times)
        if result == 'equal':
            if cnt_during == 0 and cnt_overlap == 0:
                cnt_equal += 1
            else:
                return {
                    'id': data['id'],
                    'question': data['query'],
                    'class': 'mix',
                    'is_subject': is_subject,
                    'facts': data['fact'],
                    'answer': data['answer']
                }
        elif result == 'during':
            if cnt_equal == 0 and cnt_overlap == 0:
                cnt_during += 1
            else:
                return {
                    'id': data['id'],
                    'question': data['query'],
                    'class': 'mix',
                    'is_subject': is_subject,
                    'facts': data['fact'],
                    'answer': data['answer']
                }
        elif result == 'overlap':
            if cnt_equal == 0 and cnt_during == 0:
                cnt_overlap += 1
            else:
                return {
                    'id': data['id'],
                    'question': data['query'],
                    'class': 'mix',
                    'is_subject': is_subject,
                    'facts': data['fact'],
                    'answer': data['answer']
                }

    if cnt_equal != 0:
        return {
            'id': data['id'],
            'question': data['query'],
            'class': 'equal',
            'is_subject': is_subject,
            'facts': data['fact'],
            'answer': data['answer']
        }
    elif cnt_during != 0:
        return {
            'id': data['id'],
            'question': data['query'],
            'class': 'during',
            'is_subject': is_subject,
            'facts': data['fact'],
            'answer': data['answer']
        }
    elif cnt_overlap != 0:
        return {
            'id': data['id'],
            'question': data['query'],
            'class': 'overlap',
            'is_subject': is_subject,
            'facts': data['fact'],
            'answer': data['answer']
        }
