import csv
import json

def read_qid_names(filepath):   
    name_dict = {}
    with open(filepath, 'r', encoding='utf-8') as file:
        try:
            for line in file:
                key, value = line.strip().split('\t')
                name_dict[key] = value
        except Exception as e:
            print("An error occurred:", e)
    return name_dict

def read_tsv(filepath):
    all_data = []
    with open(filepath, 'r', encoding='utf-8') as tsvfile:
        tsv_reader = csv.reader(tsvfile, delimiter='\t')
        for row in tsv_reader:
            all_data.append(row)
    return all_data

tsv_path = 'path_to_your_input_file.tsv'
qid_path = 'path_to_your_qid_name_file.txt'
subject_output_path = 'path_to_your_output_file.json'

all_data = read_tsv(tsv_path)
name_dict = read_qid_names(qid_path)

with open(subject_output_path, 'w', encoding='utf-8') as f:
    ind = 0
    while ind < len(all_data):
        data = all_data[ind]
        entity = data[1]
        if entity not in name_dict:
            ind += 1
        else:
            qid_name = name_dict[entity]
            data_list = []
            while entity == data[1]:
                data_list.append([data[0], data[2], data[3], data[4]])
                ind += 1
                if ind < len(all_data):
                    data = all_data[ind]
                else:
                    break
            item = {
                'entity': entity,
                'name': qid_name,
                'data_list': data_list
            }
            json_item = json.dumps(item)
            f.write(json_item + '\n')