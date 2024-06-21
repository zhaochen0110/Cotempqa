import argparse
import os
import itertools
import json
import jsonlines
import datetime
import string
from collections import Counter
import re

default_template = 'Answer the question based on the context:\n{fact}\nQuestion: {question} Only return the answer.\n'

few_shot_template = '''Answer the question based on the context:\nValdis Dombrovskis holds the position of Vice-President of the European Commission in December 1, 2019.\nValdis Dombrovskis holds the position of European Commissioner for Internal Market and Services from July 16, 2016 to October 12, 2020.\nValdis Dombrovskis holds the position of European Commissioner for Trade in August 26, 2020.\nValdis Dombrovskis holds the position of European Commissioner for An Economy that Works for People in December 1, 2019.\nValdis Dombrovskis holds the position of Prime Minister of Latvia from March 12, 2009 to January 22, 2014.\nValdis Dombrovskis holds the position of Minister of Finance from November 7, 2002 to March 9, 2004.\nQuestion: While Valdis Dombrovskis was holding the position of European Commissioner for Trade, which position did Valdis Dombrovskis during the identical time period?\nOnly return the answer.
European Commissioner for Internal Market and Services
Answer the question based on the context:\nKamari Maxine Clarke works for Yale University from 1999 to 2012.\nKamari Maxine Clarke attended Yale Law School in 2003.\nKamari Maxine Clarke works for Carleton University from 2015 to 2019.\nKamari Maxine Clarke works for University of Pennsylvania from 2012 to 2015.\nKamari Maxine Clarke attended University of California, Santa Cruz in 1997.\nQuestion: While Kamari Maxine Clarke attended Yale Law School, which employer did Kamari Maxine Clarke work for during the identical time period?\nOnly return the answer.
Yale University
Answer the question based on the context:\nSarah Kendzior attended Sarah Lawrence College from 1996 to 2000.\nJoanna Frueh attended Sarah Lawrence College in 1970.\nCarolyn Kizer attended Sarah Lawrence College in 1945.\nSue W. Kelly attended Sarah Lawrence College in 1985.\nJoseph Campbell works for Sarah Lawrence College from 1934 to 1972.\nRahm Emanuel attended Sarah Lawrence College in 1981.\nLaura Curran attended Sarah Lawrence College in 1989.\nMaria Goeppert Mayer works for Sarah Lawrence College from 1941 to 1942.\nTheodora Mead Abel works for Sarah Lawrence College from 1929 to 1933.\nGenevieve Taggard works for Sarah Lawrence College from 1935 to 1946.\nJewel Plummer Cobb works for Sarah Lawrence College from 1960 to 1969.\nGerda Lerner works for Sarah Lawrence College in 1968.\nQuestion: While Maria Goeppert Mayer was working for Sarah Lawrence College, who also worked for Sarah Lawrence College simultaneously?\nOnly return the answer.
Genevieve Taggard and Joseph Campbell
Answer the question based on the context:\nJoan Morales plays for Sevilla FC Puerto Rico in 2011.\nJoan Morales plays for Puerto Rico national football team in 2010.\nJoan Morales plays for Bayamón FC in 2010.\nZhang Jian plays for Wuhan Yangtze River F.C. in 2015.\nZhang Jian plays for Chongqing Liangjiang Athletic F.C. from 2006 to 2011.\nZhang Jian plays for Hebei F.C. in 2013.\nZhang Jian plays for Beijing Guoan F.C. from 2012 to 2014.\nZhang Jian plays for Dalian Transcendence F.C. in 2016.\nQuestion: While Joan Morales was playing for Bayamón FC, which team did Zhang Jian play for during the same time period?\nOnly return the answer.
Chongqing Liangjiang Athletic F.C
Answer the question based on the context:\nRussell Keat works for University of Nevada, Reno from 1969 to 1970.\nRussell Keat works for University of Edinburgh from 1994 to 2006.\nRussell Keat attended Merton College in 1967.\nRussell Keat attended Linacre College in 1969.\nRussell Keat works for University of Lancaster from 1970 to 1994.\nWatkins Moorman Abbitt holds the position of United States representative from February 17, 1948 to January 3, 1973.\nWatkins Moorman Abbitt attended primary school in 1925.\nWatkins Moorman Abbitt attended University of Richmond in 1931.\nWatkins Moorman Abbitt holds the position of county attorney from 1932 to 1948.\nQuestion: While Russell Keat attended Merton College, which position did Watkins Moorman Abbitt hold during the identical time period?\nOnly return the answer.
United States representative
Answer the question based on the context:\n{fact}\nQuestion: {question}\nOnly return the answer.\n'''

few_shot_cot_template = '''Answer the question based on the context:\nValdis Dombrovskis holds the position of Vice-President of the European Commission in December 1, 2019.\nValdis Dombrovskis holds the position of European Commissioner for Internal Market and Services from July 16, 2016 to October 12, 2020.\nValdis Dombrovskis holds the position of European Commissioner for Trade in August 26, 2020.\nValdis Dombrovskis holds the position of European Commissioner for An Economy that Works for People in December 1, 2019.\nValdis Dombrovskis holds the position of Prime Minister of Latvia from March 12, 2009 to January 22, 2014.\nValdis Dombrovskis holds the position of Minister of Finance from November 7, 2002 to March 9, 2004.\nQuestion: While Valdis Dombrovskis was holding the position of European Commissioner for Trade, which position did Valdis Dombrovskis during the identical time period?\nLet's think step by step.
Answer:\nAccording to the context, Valdis Dombrovskis became the European Commissioner for Trade on August 26, 2020.\nHe also holds the position of European Commissioner for Internal Market and Services from July 16, 2016 to October 12, 2020.\nThis period overlaps his tenure as European Commissioner for Trade.\n Therefore the answer is European Commissioner for Internal Market and Services.
Answer the question based on the context:\nKamari Maxine Clarke works for Yale University from 1999 to 2012.\nKamari Maxine Clarke attended Yale Law School in 2003.\nKamari Maxine Clarke works for Carleton University from 2015 to 2019.\nKamari Maxine Clarke works for University of Pennsylvania from 2012 to 2015.\nKamari Maxine Clarke attended University of California, Santa Cruz in 1997.\nQuestion: While Kamari Maxine Clarke attended Yale Law School, which employer did Kamari Maxine Clarke work for during the identical time period?\nLet's think step by step.
Answer:\nAccording to the context, Kamari Maxine Clarke attended Yale Law School in 2003.\nHe also works for Yale University from 1999 to 2012.\nThis period overlaps his experience in Yale Law School.\nTherefore the answer is Yale University.
Answer the question based on the context:\nSarah Kendzior attended Sarah Lawrence College from 1996 to 2000.\nJoanna Frueh attended Sarah Lawrence College in 1970.\nCarolyn Kizer attended Sarah Lawrence College in 1945.\nSue W. Kelly attended Sarah Lawrence College in 1985.\nJoseph Campbell works for Sarah Lawrence College from 1934 to 1972.\nRahm Emanuel attended Sarah Lawrence College in 1981.\nLaura Curran attended Sarah Lawrence College in 1989.\nMaria Goeppert Mayer works for Sarah Lawrence College from 1941 to 1942.\nTheodora Mead Abel works for Sarah Lawrence College from 1929 to 1933.\nGenevieve Taggard works for Sarah Lawrence College from 1935 to 1946.\nJewel Plummer Cobb works for Sarah Lawrence College from 1960 to 1969.\nGerda Lerner works for Sarah Lawrence College in 1968.\nQuestion: While Maria Goeppert Mayer was working for Sarah Lawrence College, who also worked for Sarah Lawrence College simultaneously?\nLet's think step by step.
Answer:\nAccording to the context, Maria Goeppert Mayer works for Sarah Lawrence College from 1941 to 1942.\nAnd Joseph Campbell works for Sarah Lawrence College from 1934 to 1972.\nThis period overlaps Maria Goeppert Mayer's experience in Sarah Lawrence College.\nTherefore the answer is Joseph Campbell.
Answer the question based on the context:\nJoan Morales plays for Sevilla FC Puerto Rico in 2011.\nJoan Morales plays for Puerto Rico national football team in 2010.\nJoan Morales plays for Bayamón FC in 2010.\nZhang Jian plays for Wuhan Yangtze River F.C. in 2015.\nZhang Jian plays for Chongqing Liangjiang Athletic F.C. from 2006 to 2011.\nZhang Jian plays for Hebei F.C. in 2013.\nZhang Jian plays for Beijing Guoan F.C. from 2012 to 2014.\nZhang Jian plays for Dalian Transcendence F.C. in 2016.\nQuestion: While Joan Morales was playing for Bayamón FC, which team did Zhang Jian play for during the same time period?\nLet's think step by step.
Answer:\nAccording to the context, Joan Morales plays for Bayamón FC in 2010.\nAnd Zhang Jian plays for Chongqing Liangjiang Athletic F.C. from 2006 to 2011.\nThis period overlaps Joan Morales's experience in Bayamón FC.\nTherefore the answer is Chongqing Liangjiang Athletic F.C.
Answer the question based on the context:\nRussell Keat works for University of Nevada, Reno from 1969 to 1970.\nRussell Keat works for University of Edinburgh from 1994 to 2006.\nRussell Keat attended Merton College in 1967.\nRussell Keat attended Linacre College in 1969.\nRussell Keat works for University of Lancaster from 1970 to 1994.\nWatkins Moorman Abbitt holds the position of United States representative from February 17, 1948 to January 3, 1973.\nWatkins Moorman Abbitt attended primary school in 1925.\nWatkins Moorman Abbitt attended University of Richmond in 1931.\nWatkins Moorman Abbitt holds the position of county attorney from 1932 to 1948.\nQuestion: While Russell Keat attended Merton College, which position did Watkins Moorman Abbitt hold during the identical time period?\nLet's think step by step.
Answer:\nAccording to the context, Russell Keat attended Merton College in 1967.\nAnd Watkins Moorman Abbitt holds the position of United States representative from February 17, 1948 to January 3, 1973.\nThis period overlaps Russell Keat's experience in Merton College.\nTherefore the answer is United States representative.
Answer the question based on the context:\n{fact}\nQuestion: {question}\n Let's think step by step.\nAnswer:\nAccording to the context,'''

few_shot_math_template = '''Answer the question based on the context:\nValdis Dombrovskis holds the position of Vice-President of the European Commission in December 1, 2019.\nValdis Dombrovskis holds the position of European Commissioner for Internal Market and Services from July 16, 2016 to October 12, 2020.\nValdis Dombrovskis holds the position of European Commissioner for Trade in August 26, 2020.\nValdis Dombrovskis holds the position of European Commissioner for An Economy that Works for People in December 1, 2019.\nValdis Dombrovskis holds the position of Prime Minister of Latvia from March 12, 2009 to January 22, 2014.\nValdis Dombrovskis holds the position of Minister of Finance from November 7, 2002 to March 9, 2004.\nQuestion: While Valdis Dombrovskis was holding the position of European Commissioner for Trade, which position did Valdis Dombrovskis during the identical time period?
Answer:\nAccording to the context, Valdis Dombrovskis became the European Commissioner for Trade on August 26, 2020. The datetime can be formed (2020,8,26).\nThe content provided and related to the question can be structured as:\n(Vice-President of the European Commission, (2019, 12, 1)).\n(European Commissioner for Internal Market and Services, (2016, 6, 16), (2020, 10, 12)).\n(European Commissioner for An Economy, (2019, 12, 1)).\n(Prime Minister of Latvia, (2009, 3, 12),(2014, 1, 22)).\n(Minister of Finance, (2002, 11, 7),(2004, 3, 9)).\nGiven the (2020,8,26), compared with all contents related, we find that \[[(2016, 6, 16)-(2020, 10, 12)] \cap (2020, 8, 26) \\neq \emptyset\].\nTherefore the answer is European Commissioner for Internal Market and Services.
Answer the question based on the context:\nKamari Maxine Clarke works for Yale University from 1999 to 2012.\nKamari Maxine Clarke attended Yale Law School in 2003.\nKamari Maxine Clarke works for Carleton University from 2015 to 2019.\nKamari Maxine Clarke works for University of Pennsylvania from 2012 to 2015.\nKamari Maxine Clarke attended University of California, Santa Cruz in 1997.\nQuestion: While Kamari Maxine Clarke attended Yale Law School, which employer did Kamari Maxine Clarke work for during the identical time period?
Answer:\nAccording to the context, Kamari Maxine Clarke attended Yale Law School in 2003. The datetime can be formed as (2003, None, None).\nThe content provided and related to the question can be structured as:\n(Yale University, (1999, None, None), (2012, None, None)).\n(Carleton University, (2015, None, None), (2019, None, None)).\n(University of Pennsylvania, (2012, None, None), (2015, None, None)).\nGiven the (2003, None, None), compared with all contents related, we find that \[\left[(1999, \\text{None}, \\text{None}) - (2012, \\text{None}, \\text{None})\\right] \cap (2003, \\text{None}, \\text{None}) \\neq \emptyset\].\nTherefore the answer is Yale University.
Answer the question based on the context:\nSarah Kendzior attended Sarah Lawrence College from 1996 to 2000.\nJoanna Frueh attended Sarah Lawrence College in 1970.\nCarolyn Kizer attended Sarah Lawrence College in 1945.\nSue W. Kelly attended Sarah Lawrence College in 1985.\nJoseph Campbell works for Sarah Lawrence College from 1934 to 1972.\nRahm Emanuel attended Sarah Lawrence College in 1981.\nLaura Curran attended Sarah Lawrence College in 1989.\nMaria Goeppert Mayer works for Sarah Lawrence College from 1941 to 1942.\nTheodora Mead Abel works for Sarah Lawrence College from 1929 to 1933.\nGenevieve Taggard works for Sarah Lawrence College from 1935 to 1946.\nJewel Plummer Cobb works for Sarah Lawrence College from 1960 to 1969.\nGerda Lerner works for Sarah Lawrence College in 1968.\nQuestion: While Maria Goeppert Mayer was working for Sarah Lawrence College, who also worked for Sarah Lawrence College simultaneously?
Answer:\nAccording to the context, Maria Goeppert Mayer worked at Sarah Lawrence College from 1941 to 1942. The datetime can be formed as ((1941, None, None),(1942, None, None)).\nThe content provided and related to the question can be structured as:\n(Joseph Campbell, (1934, None, None), (1972, None, None)).\n(Theodora Mead Abel, (1929, None, None), (1933, None, None)).\n(Genevieve Taggard, (1935, None, None), (1946, None, None)).\n(Jewel Plummer Cobb, (1960, None, None), (1969, None, None)).\n(Gerda Lerner, (1968, None, None)).\nGiven the ((1941, None, None),(1942, None, None)), compared with all contents related, we find that \[\left[(1935, \\text{None}, \\text{None}) - (1946, \\text{None}, \\text{None})\\right] \cap [\left(1941, \\text{None}, \\text{None}) - (1942, \\text{None}, \\text{None}\\right)] \\neq \emptyset\] and \[\left[(1934, \\text{None}, \\text{None}) - (1972, \\text{None}, \\text{None})\\right] \cap [\left(1941, \\text{None}, \\text{None}) - (1942, \\text{None}, \\text{None}\\right)] \\neq \emptyset\].\nTherefore the answer is Genevieve Taggard and Joseph Campbell.
Answer the question based on the context:\nJoan Morales plays for Sevilla FC Puerto Rico in 2011.\nJoan Morales plays for Puerto Rico national football team in 2010.\nJoan Morales plays for Bayamón FC in 2010.\nZhang Jian plays for Wuhan Yangtze River F.C. in 2015.\nZhang Jian plays for Chongqing Liangjiang Athletic F.C. from 2006 to 2011.\nZhang Jian plays for Hebei F.C. in 2013.\nZhang Jian plays for Beijing Guoan F.C. from 2012 to 2014.\nZhang Jian plays for Dalian Transcendence F.C. in 2016.\nQuestion: While Joan Morales was playing for Bayamón FC, which team did Zhang Jian play for during the same time period?
Answer:\nAccording to the context, Joan Morales played for Bayamón FC in 2010. The datetime can be formed as (2010, None, None).\nThe content provided and related to the question can be structured as:\n(Wuhan Yangtze River F.C., (2015, None, None)).\n(Chongqing Liangjiang Athletic F.C., (2006, None, None), (2011, None, None)).\n(Hebei F.C., (2013, None, None)).\n(Beijing Guoan F.C., (2012, None, None), (2014, None, None)).\n(Dalian Transcendence F.C., (2016, None, None)).\nGiven the (2010, None, None), compared with all contents related, we find that \[\left[(2006, \\text{None}, \\text{None}) - (2011, \\text{None}, \\text{None})\\right] \cap (2010, \\text{None}, \\text{None}) \\neq \emptyset\].\nTherefore the answer is Chongqing Liangjiang Athletic F.C.
Answer the question based on the context:\nRussell Keat works for University of Nevada, Reno from 1969 to 1970.\nRussell Keat works for University of Edinburgh from 1994 to 2006.\nRussell Keat attended Merton College in 1967.\nRussell Keat attended Linacre College in 1969.\nRussell Keat works for University of Lancaster from 1970 to 1994.\nWatkins Moorman Abbitt holds the position of United States representative from February 17, 1948 to January 3, 1973.\nWatkins Moorman Abbitt attended primary school in 1925.\nWatkins Moorman Abbitt attended University of Richmond in 1931.\nWatkins Moorman Abbitt holds the position of county attorney from 1932 to 1948.\nQuestion: While Russell Keat attended Merton College, which position did Watkins Moorman Abbitt hold during the identical time period?
Answer:\nAccording to the context, Russell Keat attended Merton College in 1967. The datetime can be formed as (1967, None, None).\nThe content provided and related to the question can be structured as:\n(United States representative, (1948, 2, 17), (1973, 1, 3)).\n(county attorney, (1932, None, None), (1948, None, None)).\nGiven the (1967, None, None), compared with all contents related, we find that \[\left[(1948, \\text{2}, \\text{17}) - (1973, \\text{1}, \\text{3})\\right] \cap (1967, \\text{None}, \\text{None}) \\neq \emptyset\].\nTherefore the answer is United States representative.
Answer the question based on the context:\n{fact}\nQuestion:{question}\nAnswer:\nAccording to the context,'''

def get_prompts(all_inputs, template):
    """
    Generate prompts from the input data using the provided template.
    
    Parameters:
    all_inputs (list): List of input data dictionaries.
    template (str): Template string for formatting the prompts.
    
    Returns:
    list: List of formatted prompts.
    """
    all_outputs = []
    for input in all_inputs:
        fact_str = "\n".join(input['facts'])
        output = template.format(
            fact=fact_str,
            question=input['question']
        )
        all_outputs.append(output)
    return all_outputs

def chatgpt(out_f, prompt, item_data, index, api_list):
    """
    Interact with the OpenAI ChatGPT API to get a response for the given prompt.
    
    Parameters:
    out_f (file object): File object to write the output.
    prompt (str): Prompt to send to the API.
    item_data (dict): Input data dictionary.
    index (int): Index to select the API key from the list.
    api_list (list): List of OpenAI API keys.
    """
    cnt = 0
    key_index = index % len(api_list)
    while cnt < 5:
        try:
            openai.api_key = api_list[key_index]
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
            )
            answer = response.choices[0].message.content
            item_data['ans'] = answer
            json_data = json.dumps(item_data)
            out_f.write(json_data + '\n')
            out_f.flush()
            break
        except Exception as e:
            print(e)
            cnt += 1
            continue

def normalize_answer(s):
    """
    Normalize the text by converting to lowercase, removing punctuation, and fixing whitespace.
    
    Parameters:
    s (str): Input string to normalize.
    
    Returns:
    str: Normalized string.
    """
    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_punc(lower(s)))

def exact_match_score(prediction, ground_truth):
    """
    Compute the exact match score between the prediction and ground truth.
    
    Parameters:
    prediction (str): Predicted answer string.
    ground_truth (str): Ground truth answer string.
    
    Returns:
    bool: True if prediction matches ground_truth exactly, else False.
    """
    return prediction == ground_truth

def f1_score(prediction, ground_truth):
    """
    Compute the F1 score, precision, and recall between the prediction and ground truth.
    
    Parameters:
    prediction (str): Predicted answer string.
    ground_truth (str): Ground truth answer string.
    
    Returns:
    tuple: F1 score, precision, and recall.
    """
    common = Counter(prediction) & Counter(ground_truth)
    num_same = sum(common.values())
    if num_same == 0:
        return (0, 0, 0)
    precision = 1.0 * num_same / len(prediction)
    recall = 1.0 * num_same / len(ground_truth)
    f1 = (2 * precision * recall) / (precision + recall)
    return (f1, precision, recall)

# Templates for extracting information from text based on properties
EXTRACT_TEMPLATES = {
    'P39': ["(.+?) holds the position of (.+?) from (.+?) to (.+?)\\.", "(.+?) holds the position of (.+?) in (.+?)\\.", "(.+?) holds the position of (.+?) from (.+?)", "(.+?) holds the position of (.+?) in (.+?)\\.", "(.+?) holds the position of (.+?)\\."],
    'P102': ["(.+?) is a member of the (.+?) from (.+?) to (.+?)\\.", "(.+?) is a member of the (.+?) in (.+?)\\.", "(.+?) is a member of the (.+?) from (.+?)", "(.+?) is a member of the (.+?)\\."],
    'P69': ["(.+?) attended (.+?) from (.+?) to (.+?)\\.", "(.+?) attended (.+?) in (.+?)\\.", "(.+?) attended (.+?) from (.+?)", "(.+?) attended (.+?)\\."],
    'P108': ["(.+?) works for (.+?) from (.+?) to (.+?)\\.", "(.+?) works for (.+?) in (.+?)\\.", "(.+?) works for (.+?) from (.+?)", "(.+?) works for (.+?)\\."],
    'P54': ["(.+?) plays for (.+?) from (.+?) to (.+?)\\.", "(.+?) plays for (.+?) in (.+?)\\.", "(.+?) plays for (.+?) from (.+?)", "(.+?) plays for (.+?)\\."],
    'P488': ["(.+?) is the chair of (.+?) from (.+?) to (.+?)\\.", "(.+?) is the chair of (.+?) in (.+?)\\.", "(.+?) is the chair of (.+?) from (.+?)", "(.+?) is the chair of (.+?)\\."],
    'P6': ["(.+?) is the head of (.+?) from (.+?) to (.+?)\\.", "(.+?) is the head of (.+?) in (.+?)\\.", "(.+?) is the head of (.+?) from (.+?)", "(.+?) is the head of (.+?)\\."],
    'P127': ["(.+?) is owned by (.+?) from (.+?) to (.+?)\\.", "(.+?) is owned by (.+?) in (.+?)\\.", "(.+?) is owned by (.+?) from (.+?)", "(.+?) is owned by (.+?)\\."]
}

# Keywords for identifying properties in text
SEARCH_DICT = {
    'P39': ' the position of ',
    'P102': ' a member of ',
    'P69': 'attend',
    'P108': 'work',
    'P54': 'play',
    'P488': ' the chair of ',
    'P6': ' the head of ',
    'P127': ' owned by '
}

# Reverse lookup for properties based on keywords
REVERSE_SEARCH = [
    (' the position of ', 'P39'),
    (' a member of ', 'P102'),
    (' the chair of ', 'P488'),
    (' the head of ', 'P6'),
    (' owned by ', 'P127'),
    ('attend', 'P69'),
    ('work', 'P108'),
    ('play', 'P54')
]

def evaluate_model(all_data, mode):
    """
    Evaluate the performance of predictions against the ground truth.
    
    Parameters:
    all_data (list): List of data dictionaries with predictions and ground truth.
    mode (str): Evaluation mode (e.g., 'cot' for chain of thought).
    
    Returns:
    dict: Evaluation metrics including accuracy, F1 score, precision, recall, and average score.
    """
    em_total = 0
    f1_total = 0
    p_total = 0
    r_total = 0
    count = 0
    
    for data in all_data:
        golds = data['gold']
        golds = [ans.lower() for ans in golds]

        is_subject = 'S2_R1_O1' not in data['triple_element']

        prediction = data['prediction'].lower()
        if 'cot' in mode:
            if 'therefore the answer is' not in prediction:
                prediction = 'answer'
            else:
                prediction = prediction.split('therefore the answer is')[1].split('answer the question based on')[0]
        elif 'answer the question based on' in prediction:
            prediction = prediction.split('answer the question based on')[0]
        elif ' answer ' in prediction:
            prediction = prediction.split(' answer ')[1]

        facts = data['facts']
        question = data['question'].lower()

        alternative_answers = []

        for fact in facts:
            is_match = False
            for p in REVERSE_SEARCH:
                if is_match:
                    break
                if p[0] in fact:
                    fact = fact.replace(" was ", " is ").replace(' held ', ' holds ').replace(' worked ', ' works ').replace(' played ', ' plays ')
                    relation = p[1]
                    for template in EXTRACT_TEMPLATES[relation]:
                        match = re.match(template, fact)
                        if match:
                            is_match = True
                            subject = match.group(1)
                            extract_content = match.group(2)
                            if is_subject:
                                alternative_answers.append(subject.lower())
                            else:
                                alternative_answers.append(extract_content.lower())
                            break

        alternative_answers += golds
        alternative_answers = list(set(alternative_answers))
        alternative_answers.sort(key=len, reverse=True)

        shot = False
        flag = False
        predict = []

        for ans in alternative_answers:
            if ans in prediction and ans in question and not flag:
                prediction = prediction.replace(ans, '')
                flag = True
                continue
            if ans in prediction:
                predict.append(ans)
                prediction = prediction.replace(ans, '')
                shot = True

        if not shot:
            predict = [prediction]

        predict = list(set(predict))
        predict = [normalize_answer(i) for i in predict]
        predict.sort()
        golds = list(set(golds))
        golds = [normalize_answer(i) for i in golds]
        golds.sort()

        em_total += exact_match_score(predict, golds)
        f1, p, r = f1_score(predict, golds)
        f1_total += f1
        p_total += p
        r_total += r
        count += 1

    return {
        'acc': round(em_total * 100 / count, 1),
        'f1': round(f1_total * 100 / count, 1),
        'p': round(p_total * 100 / count, 1),
        'r': round(r_total * 100 / count, 1),
        'avg': round((em_total + f1_total) * 50 / count, 1)
    }

def evaluate_gpt(file_path):
    """
    Evaluate the performance of GPT-based predictions from a file.
    
    Parameters:
    file_path (str): Path to the file containing GPT predictions and ground truth.
    
    Returns:
    dict: Evaluation metrics including accuracy, F1 score, precision, recall, and average score.
    """
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
                for p in REVERSE_SEARCH:
                    if is_match:
                        break
                    fact = fact.replace(" was ", " is ").replace(' held ', ' holds ').replace(' worked ', ' works ').replace(' played ', ' plays ')
                    if p[0] in fact:
                        relation = p[1]
                        for template in EXTRACT_TEMPLATES[relation]:
                            match = re.match(template, fact)
                            if match:
                                is_match = True
                                subject = match.group(1)
                                extract_content = match.group(2)
                                if is_subject:
                                    alternative_answers.append(subject.lower())
                                else:
                                    alternative_answers.append(extract_content.lower())
                                break
                
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
    return {
        'acc': round(em_total * 100 / count, 1),
        'f1': round(f1_total * 100 / count, 1),
        'p': round(p_total * 100 / count, 1),
        'r': round(r_total * 100 / count, 1),
        'avg': round((em_total + f1_total) * 50 / count, 1)
    }





