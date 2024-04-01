import json
import pandas as pd
import argparse
from config import *
import os
from vllm import LLM, SamplingParams

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
Answer the question based on the context:\n{fact}\nQuestion: {question} Only return the answer.\n'''

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
    all_outputs = []
    for input in all_inputs:
        fact_str = ""
        for i in input['facts']:
            fact_str += i + '\n'
        output = template.format(
            fact = fact_str,
            question = input['question']
        )
        all_outputs.append(output)
    return all_outputs

def evaluate_cotemporal(model_name, data_path, mode, output_dir, evaluate_result_dir):
    all_data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            all_data.append(data)
            
    llm = LLM(model=model_name, tensor_parallel_size=4)
    sampling_params = SamplingParams(temperature=0, max_tokens=300)
    
    if mode == 'few_shot':
        all_prompts = get_prompts(all_data, few_shot_template)
    elif mode == 'few_shot_cot':
        all_prompts = get_prompts(all_data, few_shot_cot_template)
    elif mode == 'few_shot_math_cot':
        all_prompts = get_prompts(all_data, few_shot_math_template)
        
    print(len(all_prompts))
    all_outputs = llm.generate(all_prompts, sampling_params)
    all_outputs = [output.outputs[0].text for output in all_outputs]
    
    output_data = []
    for prompt, input, output in zip(all_prompts, all_data, all_outputs):
        prompt = 'Answer the question based on the context:' + prompt.split('Answer the question based on the context:')[-1]
        output_data.append({'input': prompt, 'prediction': output, 'gold': input['answer'], 'triple_element': input['triple_element'], 'question': input['question'], 'facts': input['facts']})
    
    filename = data_path.split("/")[-1]
    output_path =  output_dir + '/' + mode + '_' + filename
    
    with open(output_path, 'w', encoding = 'utf-8') as f:
        for data in output_data:
            json_data = json.dumps(data)
            f.write(json_data + '\n')
            
    result = main(output_data, mode)
    evaluate_result_path = evaluate_result_dir+'/'+mode+'_'+filename
    with open(evaluate_result_path, 'w', encoding='utf-8') as f:
        json_data = json.dumps(result)
        f.write(json_data + '\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Co-temporal datasets")
    parser.add_argument("model_name", type=str, help="Path to the model")
    parser.add_argument("data_path", type=str, help="Path to the dataset file")
    parser.add_argument("mode", type=str, help="use which way to evaluate the co-temporal ability of llms")
    parser.add_argument("output_dir", type=str, help="Path to save the outputs")
    parser.add_argument("evaluate_output", type=str, help="Path to save the evaluate result")
    
    args = parser.parse_args()

    evaluate_cotemporal(args.model_name, args.data_path, args.mode, args.output_dir, args.evaluate_output)