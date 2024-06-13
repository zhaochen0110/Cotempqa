import argparse
import os
import itertools
import json
import jsonlines
import datetime
import string
from collections import Counter
import re

def normalize_answer(s):
    """
    Normalize the text by converting to lowercase, removing punctuation, and fixing whitespace.
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
    """
    return prediction == ground_truth

def f1_score(prediction, ground_truth):
    """
    Compute the F1 score, precision, and recall between the prediction and ground truth.
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
extract_template = {
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
search_dict = {
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
reverse_search = [
    (' the position of ', 'P39'),
    (' a member of ', 'P102'),
    (' the chair of ', 'P488'),
    (' the head of ', 'P6'),
    (' owned by ', 'P127'),
    ('attend', 'P69'),
    ('work', 'P108'),
    ('play', 'P54')
]

def main(all_data, mode):
    """
    Main function to evaluate the performance of predictions against the ground truth.
    """
    em_total = 0
    f1_total = 0
    p_total = 0
    r_total = 0
    count = 0
    
    for data in all_data:
        golds = data['gold']
        golds = [ans.lower() for ans in golds]

        is_subject = 'S1_R1_O2' not in data['triple_element']

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
            for p in reverse_search:
                if is_match:
                    break
                if p[0] in fact:
                    fact = fact.replace(" was ", " is ").replace(' held ', ' holds ').replace(' worked ', ' works ').replace(' played ', ' plays ')
                    relation = p[1]
                    for template in extract_template[relation]:
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate co-temporal reasoning in LLMs.")
    parser.add_argument("--data_path", type=str, required=True, help="Path to the dataset.")
    parser.add_argument("--mode", type=str, required=True, choices=["cot", "nocot"], help="Evaluation mode.")
    args = parser.parse_args()

    with jsonlines.open(args.data_path) as reader:
        all_data = [obj for obj in reader]

    results = main(all_data, args.mode)
    print(json.dumps(results, indent=4))
