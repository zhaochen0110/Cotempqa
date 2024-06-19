import json
import pandas as pd
import argparse
from config import *
import os
from vllm import LLM, SamplingParams

def evaluate_cotemporal(model_name, data_path, mode, output_dir, evaluate_result_dir):
    """
    Evaluate the co-temporal reasoning capabilities of a model on a dataset.
    
    Parameters:
    model_name (str): Name of the model to evaluate.
    data_path (str): Path to the input dataset.
    mode (str): Evaluation mode (e.g., 'default', 'few_shot', 'few_shot_cot', 'few_shot_math_cot').
    output_dir (str): Directory to save the evaluation outputs.
    evaluate_result_dir (str): Directory to save the evaluation results.
    """
    all_data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            all_data.append(data)

    if mode == 'default':
        all_prompts = get_prompts(all_data, default_template)
    elif mode == 'few_shot':
        all_prompts = get_prompts(all_data, few_shot_template)
    elif mode == 'few_shot_cot':
        all_prompts = get_prompts(all_data, few_shot_cot_template)
    elif mode == 'few_shot_math_cot':
        all_prompts = get_prompts(all_data, few_shot_math_template)
        
    if model_name == 'gpt':
        filename = os.path.basename(data_path)
        output_path = os.path.join(output_dir, f"{mode}_{filename}")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            for cnt, prompt in enumerate(all_prompts):
                chatgpt(out_f, prompt, all_data[cnt], cnt, api_list) 
        
        output_data = []
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                output_data.append(json.loads(line))
        result = evaluate_gpt(output_data)
    else:
        llm = LLM(model=model_name, tensor_parallel_size=1)
        sampling_params = SamplingParams(temperature=0, max_tokens=50)
        all_outputs = llm.generate(all_prompts, sampling_params)
        all_outputs = [output.outputs[0].text for output in all_outputs]
        
        output_data = []
        for prompt, input_data, output in zip(all_prompts, all_data, all_outputs):
            prompt = 'Answer the question based on the context:' + prompt.split('Answer the question based on the context:')[-1]
            output_data.append({
                'input': prompt,
                'prediction': output,
                'gold': input_data['answer'],
                'triple_element': input_data['triple_element'],
                'question': input_data['question'],
                'facts': input_data['facts']
            })
        
        filename = os.path.basename(data_path)
        output_path = os.path.join(output_dir, f"{mode}_{filename}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for data in output_data:
                json_data = json.dumps(data)
                f.write(json_data + '\n')

        result = evaluate_model(output_data, mode)
        
    evaluate_result_path = os.path.join(evaluate_result_dir, f"{mode}_{filename}")
    with open(evaluate_result_path, 'w', encoding='utf-8') as f:
        json_data = json.dumps(result)
        f.write(json_data + '\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Co-temporal datasets")
    parser.add_argument("model_name", type=str, help="Path to the model")
    parser.add_argument("data_path", type=str, help="Path to the dataset file")
    parser.add_argument("mode", type=str, help="Method to evaluate the co-temporal ability of LLMs")
    parser.add_argument("output_dir", type=str, help="Path to save the outputs")
    parser.add_argument("evaluate_output", type=str, help="Path to save the evaluation result")
    
    args = parser.parse_args()

    evaluate_cotemporal(args.model_name, args.data_path, args.mode, args.output_dir, args.evaluate_output)
