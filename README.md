# CoTempQA

## 1.Dataset

The dataset can be downloaded from [this link](https://drive.google.com/drive/folders/1HLnVdPPerWS1KX5p1Q38UQaHOGidsf5X?usp=drive_link)

Meanwhile, you can also choose to use linux command to download the dataset:

```bash
wget https://drive.google.com/drive/folders/1HLnVdPPerWS1KX5p1Q38UQaHOGidsf5X?usp=drive_link
```

## 2.Data Creation

Beside the dataset can be used straightly, we also reveal all details to generate the different CoTempQA Dataset versions.

#### （1）download the row data

Before generating the data, we need to undertake some preparatory steps, including gathering essential raw data. Notably, all raw data can be categorized into four levels, namely v3, v4, v5, and all. As the levels progress, the volume of data contained in the raw data also increases.

1. [row data](https://drive.google.com/drive/folders/1HLnVdPPerWS1KX5p1Q38UQaHOGidsf5X?usp=sharing). This directory includes the structured data representation of the events. Each row contains (relation, subject, object, start time, end time). 

   ```bash
   wget https://drive.google.com/drive/folders/1HLnVdPPerWS1KX5p1Q38UQaHOGidsf5X?usp=sharing
   ```

2. [qid](https://drive.google.com/drive/folders/1doUX0CK_zT001dn16nhftT-QQ6SzDEUD?usp=drive_link). To ensure correspondence between subjects and objects in the structured data within the 'raw data' directory, abstract objects are utilized for both subjects and objects, necessitating the use of qid for identification.

   ```bash
   wget https://drive.google.com/drive/folders/11XNX9GvuD8j_3vbmmFt2qQUPXs4qqFx6?usp=drive_link
   ```

3. [facts](https://drive.google.com/drive/folders/1HLnVdPPerWS1KX5p1Q38UQaHOGidsf5X?usp=drive_link). In this directory, some facts have been prepared with subjects or objects as entities, aiming to facilitate testing the OpenBook model's capabilities for co-temporal comprehension.

   ```bash
   wget https://drive.google.com/drive/folders/1lY28s47TlIE7Ff8vBfqJT8vTmWB-jAgY?usp=drive_link
   ```

4. [templates](https://drive.google.com/drive/folders/1pB4xQZqI6_rB4Wgym3eHrcGNbf6IQsC-?usp=drive_link). The templates to generate the data.

   ```bash
   wget https://drive.google.com/drive/folders/1pB4xQZqI6_rB4Wgym3eHrcGNbf6IQsC-?usp=drive_link
   ```

5. [generate_interval_templates](https://drive.google.com/drive/folders/1gzOH5C22oKrUBfXbGOqEu3uVRkjSglxT?usp=drive_link). The templates used for data augmentation, generating facts for a specific time period (from start time to end time).

   ```bash
   wget https://drive.google.com/drive/folders/1gzOH5C22oKrUBfXbGOqEu3uVRkjSglxT?usp=drive_link
   ```

6. [generate_point_templates](https://drive.google.com/drive/folders/1oBZuU50i5AX3HLjak4mR6qIJssM8uh7y?usp=drive_link).The templates used for data augmentation, generating facts at a specific point in time (in start time).

   ```bash
   wget https://drive.google.com/drive/folders/1oBZuU50i5AX3HLjak4mR6qIJssM8uh7y?usp=drive_link
   ```

### (2) Extract co-temporal relationship from raw data

In this step, we will traverse and compare the time occurrences of relevant tasks, converting synchronous events into structured representations. We can input the mission_name to assign which kind structured data to generate, output_file to assign where to store the output and data_level to assign the amount of the raw data we use, we can choose different data_level depends on the number of final data you need.

```bash
python extract.py --mission_name S1_R1_O2.json --output_file structured_data --data_level all
```

### (3) Transfer structured data to query

In this step, we will translate the obtained structured synchronous events into textual representations, and for data with a low quantity of facts, we will utilize templates for data augmentation. 

```bash
python structured_to_query.py --task S1_R1_O2 --question_templates templates\level_4.csv --data_level all --output_path data_without_temporal_expression
```

### (4) Add Co-temporal expression

In this step, we will add suffixes to the preliminary data to incorporate co-temporal descriptions, for instance, 'during the same time span'.

```bash
python transfer_template.py
```

### (5) Classify the data

In this phase, we will classify the acquired data into four categories: 'equal' denotes events happening concurrently, 'overlap' indicates time periods where events coincide, 'during' signifies a containment relationship among simultaneous events' time intervals, and 'mix' represents scenarios within the synchronic timeframe involving at least two of the following: 'equal', 'overlap', and 'during'.

```bash
python classification_original_data.py
```

### (6) Evaluation

After the model performs inference on this dataset, we can extract answers from the generative answer using template matching, with accuracy and F1 score as evaluation metrics. We prepare two python script, evaluate_for_gpt.py is used for evaluate chatgpt, evaluate_for_open_model.py is used for evaluate other open model in huggingface. 

```bash
./evaluate.sh
```

