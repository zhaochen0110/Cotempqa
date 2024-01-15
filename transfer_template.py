import json
import random
import os

expression_list = ["during the same time span?", "within the same time interval?", "during the same time period?", "at the same time?", "during the identical time period?", "concurrently?", "simultaneously?"]


# items = []
def random_generate(input_file, output_file1):
    items = []
    with open(input_file, 'r') as fin:
        for line in fin:
            item = json.loads(line)
            item["query"] = item["query"] + random.choice(expression_list)
            items.append(item)

    with open(output_file1, 'w') as f:
        for data in items:
            # data['fact'] = data['fact']
            json_data = json.dumps(data)
            f.write(json_data + '\n')

    print(f"save in {output_file1}") 

def template_generate(input_file, output_file, expression=expression_list[0]):
    items = []
    with open(input_file, 'r') as fin:
        for line in fin:
            item = json.loads(line)
            item["query"] = item["query"] + expression
            items.append(item)

    with open(output_file, 'w') as f:
        for data in items:
            json_data = json.dumps(data)
            f.write(json_data + '\n')

    print(f"save in {output_file}") 

# random generate
for file_name in ['S1_R1_O2.json','S1_R2_O2.json','S2_R1_O1.json','S2_R1_O2.json','S2_R2_O2.json']:
    input_file = 'data_without_temporal_expression/' + file_name
    output_file1 = 'result/' + file_name
    # output_file2 = 'inital2expand/inital/' + file_name
    random_generate(input_file, output_file1)


