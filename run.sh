#!/bin/bash

export CUDA_VISIBLE_DEVICES=0,1,2,3
export RAY_memory_monitor_refresh_ms=0

models=('/opt/data/private/szc/llm/Llama-2-7b-hf')
data_paths=("/opt/data/private/szc/co-temproal-datasets/overlap.json" "/opt/data/private/szc/co-temproal-datasets/equal.json" "/opt/data/private/szc/co-temproal-datasets/mix.json" "/opt/data/private/szc/co-temproal-datasets/during.json")
mode='default'
output_path="/opt/data/private/szc/co-temporal/generate_result"
result_path='/opt/data/private/szc/co-temporal/evaluate_result'
for model_name in "${models[@]}"
do
  for data_path in "${data_paths[@]}"
  do
    python inference.py "$model_name" "$data_path" "$mode" "$output_path" "$result_path"
  done
done
