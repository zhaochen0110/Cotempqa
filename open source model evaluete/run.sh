#!/bin/bash

export CUDA_VISIBLE_DEVICES=4,5,6,7
export RAY_memory_monitor_refresh_ms=0

models=('/opt/data/private/szc/llm/Llama-2-7b-hf')
data_path="/opt/data/private/szc/vllm_inference/co-temporal/co-temproal-datasets/equal.json"
mode='few_shot'
output_path="/opt/data/private/szc/vllm_inference/co-temporal/result"
for model_name in "${models[@]}"
do
  python inference.py "$model_name" "$data_path" "$mode" "$output_path"  
done