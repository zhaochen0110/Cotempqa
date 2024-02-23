# Living in the Moment: Can Large Language Models Grasp Co-Temporal Reasoning?


<img src="picutre.pdf" width="300" alt="Magic mirror">


<hr>
😎: This is the official implementation repository of our study on co-temporal reasoning capabilities in Large Language Models (LLMs).

## 1.Dataset

The dataset can be downloaded from [this link](https://drive.google.com/drive/folders/1HLnVdPPerWS1KX5p1Q38UQaHOGidsf5X?usp=drive_link)

Meanwhile, you can also choose to use linux command to download the dataset:

```bash
wget https://drive.google.com/drive/folders/1HLnVdPPerWS1KX5p1Q38UQaHOGidsf5X?usp=drive_link
```
![image](https://github.com/zhaochen0110/Cotempqa/blob/main/data.png)
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

In this step, we will traverse and compare the time occurrences of relevant tasks, converting synchronous events into structured representations. Meanwhile, we will transform the structured representation into  natural language forms. Then we will categorize the obtained data into four types, namely equal, during, overlap, and mix. Notably, we have prepared raw data of various sizes. In order to generate datasets of different volumes, we can use raw data of different sizes.

```bash
python extract.py --data_level v3 --output_path test
```



### (3) Add Co-temporal expression

In this step, we will add suffixes to the preliminary data to incorporate co-temporal descriptions, for instance, 'during the same time span'.

```bash
python transfer_template.py
```



### (4) Evaluation

After the model performs inference on this dataset, we can extract answers from the generative answer using template matching, with accuracy and F1 score as evaluation metrics. We prepare two python script, evaluate_for_gpt.py is used for evaluate chatgpt, evaluate_for_open_model.py is used for evaluate other open model in huggingface. 

```bash
./evaluate.sh
```

