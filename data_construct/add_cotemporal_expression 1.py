import json
import random
import os

# List of temporal expressions to append to the queries
temporal_expressions = [
    "during the same time span?", 
    "within the same time interval?", 
    "during the same time period?", 
    "at the same time?", 
    "during the identical time period?", 
    "concurrently?", 
    "simultaneously?"
]

def random_generate(input_file, output_file):
    """
    Randomly appends a temporal expression from the list to each query in the input file and saves the modified items to the output file.
    
    Parameters:
    input_file (str): Path to the input JSON lines file.
    output_file (str): Path to the output file where modified items will be saved.
    """
    items = []
    with open(input_file, 'r') as fin:
        for line in fin:
            item = json.loads(line)
            item["question"] += random.choice(temporal_expressions)
            items.append(item)
    
    cnt = 0
    with open(output_file, 'w') as fout:
        for data in items:
            if 'S1_R1_O2' in data['id']:
                triple_element = 'S1_R1_O2'
            elif 'S2_R1_O1' in data['id']:
                triple_element = 'S2_R1_O1'
            elif 'S1_R2_O2' in data['id']:
                triple_element = 'S1_R2_O2'
            elif 'S2_R1_O2' in data['id']:
                triple_element = 'S2_R1_O2'
            elif 'S2_R2_O2' in data['id']:
                triple_element = 'S2_R2_O2'
            new_data = {
                'index': cnt,
                "triple_element": triple_element,
                'question': data['question'],
                'facts': data['facts'],
                'answer': data['answer'] 
            }
            json_data = json.dumps(new_data)
            fout.write(json_data + '\n')
            cnt+=1

    print(f"Saved modified data to {output_file}")

def template_generate(input_file, output_file, expression=temporal_expressions[0]):
    """
    Appends a specific temporal expression to each query in the input file and saves the modified items to the output file.
    
    Parameters:
    input_file (str): Path to the input JSON lines file.
    output_file (str): Path to the output file where modified items will be saved.
    expression (str): Temporal expression to append to each query. Defaults to the first expression in the list.
    """
    items = []
    with open(input_file, 'r') as fin:
        for line in fin:
            item = json.loads(line)
            item["question"] += expression
            items.append(item)

    cnt = 0
    with open(output_file, 'w') as fout:
        for data in items:
            if 'S1_R1_O2' in data['id']:
                triple_element = 'S1_R1_O2'
            elif 'S2_R1_O1' in data['id']:
                triple_element = 'S2_R1_O1'
            elif 'S1_R2_O2' in data['id']:
                triple_element = 'S1_R2_O2'
            elif 'S2_R1_O2' in data['id']:
                triple_element = 'S2_R1_O2'
            elif 'S2_R2_O2' in data['id']:
                triple_element = 'S2_R2_O2'
            new_data = {
                'index': cnt,
                "triple_element": triple_element,
                'question': data['question'],
                'facts': data['facts'],
                'answer': data['answer'] 
            }
            json_data = json.dumps(new_data)
            fout.write(json_data + '\n')
            cnt+=1

    print(f"Saved modified data to {output_file}")

if __name__ == '__main__':
    input_directory = 'output_data/'
    output_directory = 'co-temporal-dataset/'
    file_names = ['equal.json', 'during.json', 'overlap.json', 'mix.json']
    
    for file_name in file_names:
        input_file = os.path.join(input_directory, file_name)
        output_file = os.path.join(output_directory, file_name)
        random_generate(input_file, output_file)
