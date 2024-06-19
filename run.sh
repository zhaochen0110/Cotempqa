#!/bin/bash

export CUDA_VISIBLE_DEVICES=0,1,2,3
export RAY_memory_monitor_refresh_ms=0

model_name=("meta-llama/Llama-2-7b")
data_paths=("output_data/overlap.json" "output_data/equal.json" "output_data/mix.json" "output_data/during.json")
mode='default'
output_path="generate_result/"
result_path='evaluate_result/'
for model_name in "${model_name[@]}"
do
  for data_path in "${data_paths[@]}"
  do
    python inference.py "$model_name" "$data_path" "$mode" "$output_path" "$result_path"
  done
done
