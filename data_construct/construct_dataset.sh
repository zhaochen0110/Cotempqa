#!/bin/bash
python construct_comtempqa.py --rawdata_path /opt/data/private/szc/Cotempqa/raw_data/all_kg.tsv \
                  --qid_path /opt/data/private/szc/Cotempqa/raw_data/qid_names.txt \
                  --subject_path /opt/data/private/szc/Cotempqa/raw_data/subject_facts.json \
                  --object_path /opt/data/private/szc/Cotempqa/raw_data/object_facts.json \
                  --output_path test/