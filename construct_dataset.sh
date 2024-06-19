#!/bin/bash
python data_construct/construct_cotempqa.py --rawdata_path raw_data/all_kg.tsv \
                  --qid_path raw_data/qid_names.txt \
                  --subject_path raw_data/subject_facts.json \
                  --object_path raw_data/object_facts.json \
                  --output_path output_data/