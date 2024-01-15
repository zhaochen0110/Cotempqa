#!/bin/bash

python_script="evaluate_for_gpt.py"  # can choose evaluate_for_open_model.py
input_path="ob/gpt-3.5/equal_open.json"

# 执行 Python 脚本
python "$python_script" --input-path "$input_path"