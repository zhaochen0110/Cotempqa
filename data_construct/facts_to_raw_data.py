import collections
import csv
import datetime
import json
import os
import random

from absl import app
from absl import flags
from absl import logging
import sling
import tensorflow as tf
from tqdm import tqdm

FLAGS = flags.FLAGS

flags.DEFINE_string("out_dir", None, "Path to store constructed queries.")
flags.DEFINE_string(
    "facts_file", None,
    "File containing facts with qualifiers extracted from `sling2facts.py`.")
flags.DEFINE_string("sling_kb_file", None, "SLING file containing wikidata KB.")
flags.DEFINE_string(
    "sling_wiki_mapping_file", None,
    "SLING file containing mapping from QID to english wikipedia pages.")
flags.DEFINE_integer(
    "min_year", 600,
    "Starting year to construct queries from. Only facts which have a start / "
    "end date after this will be considered.")
flags.DEFINE_integer("max_year", 2023,
                     "Ending year to construct queries up till.")
flags.DEFINE_integer(
    "max_subject_per_relation", 1000,
    "Maximum number of subjects to retain per relation. Subjects are sorted "
    "based on popularity before filtering.")
flags.DEFINE_float("train_frac", 0.2,
                   "Fraction of queries to hold out for training set.")
flags.DEFINE_float("val_frac", 0.1,
                   "Fraction of queries to hold out for validation set.")

random.seed(42)
Y_TOK = "_X_"
WIKI_PRE = "/wp/en/"

def read_templates(filepath):
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return {row["Wikidata ID"]: row["Template"] for row in reader}

def parse_date(date_str):
  """Try to parse date from string.

  Args:
    date_str: String representation of the date.

  Returns:
    date: Tuple of (year, month, day).
  """
  date = None
  try:
    if len(date_str) == 4:
      date_obj = datetime.datetime.strptime(date_str, "%Y")
      date = (date_obj.year, None, None)
    elif len(date_str) == 6:
      date_obj = datetime.datetime.strptime(date_str, "%Y%m")
      date = (date_obj.year, date_obj.month, None)
    elif len(date_str) == 8:
      date_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
      date = (date_obj.year, date_obj.month, date_obj.day)
  except ValueError:
    pass
  if date is not None and date[0] > 2100:
    # Likely an error
    date = None
  return date


def load_sling_mappings(sling_kb_file, sling_wiki_mapping_file):
  """Loads entity names, number of facts and wiki page titles from SLING.

  Args:
    sling_kb_file: kb.sling file generated from SLING wikidata processor.
    sling_wiki_mapping_file: mapping.sling file generated from SLING 'en'
      wikipedia processor.

  Returns:
    qid_names: dict mapping wikidata QIDs to canonical names.
    qid_mapping: dict mapping wikidata QIDs to wikipedia page titles.
    qid_numfacts: dict mapping wikidata QIDs to number of facts.
  """
  # Load QID names.
  logging.info("Extracting entity names and num-facts from SLING KB.")
  commons = sling.Store()
  commons.load(sling_kb_file)
  commons.freeze()
  qid_names = {}
  qid_numfacts = {}
  total = 0
  for f in commons:
    total += 1
    # import pdb; pdb.set_trace()
    if f is not None:
      if "name" in str(f):
        if isinstance(f.name, sling.String):
          qid_names[f.id] = f.name.text()
        elif isinstance(f.name, bytes):
          qid_names[f.id] = f.name.decode("utf-8", errors="ignore")
        elif isinstance(f.name, str):
          qid_names[f.id] = f.name
        else:
          logging.warn("Could not read name of type %r", type(f.name))
      # import pdb; pdb.set_trace()
      ln = len(str(f))

      qid_numfacts[f.id] = ln
  logging.info("Processed %d QIDs out of %d", len(qid_names), total)
  # Load QID mapping.
  logging.info("Extracting entity mapping to Wikipedia from SLING.")
  commons = sling.Store()
  commons.load(sling_wiki_mapping_file)
  commons.freeze()
  qid_mapping = {}
  for f in commons:
    try:
      if f["/w/item/qid"] is not None:
        # import pdb; pdb.set_trace()
        pg = f.id[len(WIKI_PRE):] if f.id.startswith(WIKI_PRE) else f.id
        qid_mapping[f["/w/item/qid"].id] = pg
    except UnicodeDecodeError:
      continue
  logging.info("Extracted %d mappings", len(qid_mapping))
  return qid_names, qid_mapping, qid_numfacts


def read_facts(facts_file, qid_mapping, qid_names, min_year):
  """Loads facts and filters them using simple criteria.

  Args:
    facts_file: File containing wikidata facts with qualifiers.
    qid_mapping: dict mapping wikidata QIDs to wikipedia page titles.
    min_year: An int. Only facts with a start / end year greater than this will
      be kept.

  Returns:
    all_facts: list of tuples, where each tuple is a fact with
      (relation, subject, object, start, end).
  """
  logging.info("Reading facts from %s", facts_file)
  all_facts = []
  with tf.io.gfile.GFile(facts_file) as f:
    for line in tqdm(f):
      fact = line.strip().split("\t")
      # import pdb; pdb.set_trace()
      # Skip boring properties.
      if not fact[0].startswith("P"):
        continue
      # Skip instance of facts.
      if fact[0] == "P31":
        continue
      # Skip facts where object is not an entity.
      if not fact[2].startswith("Q"):
        continue
      # Skip facts whose subject and objects are not wiki pages.
      if fact[1] not in qid_mapping or fact[2] not in qid_mapping:
        continue
      # if fact[1] not in qid_names or fact[2] not in qid_names:
      #   continue
      # Get date qualifiers.

      start, end = None, None
      for qual in fact[3:]:
        if not qual:
          continue
        # import pdb; pdb.set_trace()
        elems = qual.split("=")
        # Skip inherited qualifier.
        if elems[0].endswith("*"):
          continue
        if len(elems) != 2:
          continue
        if elems[0].startswith("P580"):
          start = parse_date(elems[1])
        elif elems[0].startswith("P582"):
          end = parse_date(elems[1])
      if start is None and end is None:
        continue
      # Skip facts whose start and end are both before min_date.
      if ((start is None or start[0] < min_year) and
          (end is None or end[0] < min_year)):
        continue
      # import pdb; pdb.set_trace()
      all_facts.append(fact[:3] + [start, end])
  logging.info("Loaded total %d facts", len(all_facts))
  return all_facts

def read_qid_names(filepath):   
    name_dict = {}
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                key, value = line.strip().split('\t')
                name_dict[key] = value
            except Exception as e:
                continue
    return name_dict

def read_tsv(filepath):
    all_data = []
    with open(filepath, 'r', encoding='utf-8') as tsvfile:
        tsv_reader = csv.reader(tsvfile, delimiter='\t')
        for row in tsv_reader:
            all_data.append(row)
    return all_data

months_dict = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

def time_transfer(time):
    # print(time)
    if time[1]==0:
        return str(time[0])
    elif time[2]==0:
        return '{0}, {1}'.format(months_dict[time[1]],time[0])
    else:
        return '{0} {1}, {2}'.format(months_dict[time[1]],time[2],time[0])

def complete_time(time):
    year, month, day = time
    return (year, month if month is not None else 0, day if day is not None else 0)

def main(_):

  # Load entity names, number of facts and wiki page titles from SLING.
  qid_names, qid_mapping, qid_numfacts = load_sling_mappings(
      FLAGS.sling_kb_file, FLAGS.sling_wiki_mapping_file)
  print('qid_names_len',len(qid_names))
  # Load facts with qualifiers.
  all_facts = read_facts(FLAGS.facts_file, qid_mapping, qid_names, FLAGS.min_year)
  qid_path = 'raw_data/qid_names.txt'
  with open(qid_path, 'w', encoding='utf-8') as file:
      for key, value in qid_names.items():
          file.write(f"{key}\t{value}\n")
  logging.info(f"Saved qid_names to {qid_path}")
  # Create queries.
  raw_data_path = "raw_data/all_kg.tsv"
  # all_facts = [['P54', 'Q18638850', 'Q514714', (2014, None, None), (2014, None, None)], ['P26', 'Q6788484', 'Q229507', (1964, None, None), (1966, None, None)], ['P97', 'Q969823', 'Q3519259', (1808, 3, 19), None], ['P410', 'Q969823', 'Q2487961', (1797, 5, 2), None], ['P2962', 'Q27527529', 'Q105269', (2016, None, None), None], ['P54', 'Q2017737', 'Q499616', (1971, None, None), (1972, None, None)], ['P54', 'Q2017737', 'Q249643', (1974, None, None), (1974, None, None)], ['P54', 'Q2017737', 'Q248765', (1972, None, None), (1973, None, None)], ['P54', 'Q7938967', 'Q181216', (1986, None, None), (1988, None, None)], ['P54', 'Q7938967', 'Q154293', (1992, None, None), (1994, None, None)], ['P54', 'Q7938967', 'Q647893', (1998, None, None), (2000, None, None)], ['P54', 'Q7938967', 'Q155730', (2000, None, None), (2002, None, None)], ['P1435', 'Q5139009', 'Q15700834', (1955, 6, 21), None]]
  with open(raw_data_path, "w", encoding="utf-8") as f:
      for row in all_facts:
          formatted_row = "\t".join([str(item) if item is not None else "None" for item in row])
          f.write(formatted_row + "\n")

  print("Data has been successfully written to", raw_data_path)

  # Load relation templates.
  templates_path = 'templates/templates.csv'
  all_data = read_tsv(raw_data_path)
  name_dict = read_qid_names(qid_path)
  templates = read_templates(templates_path)
  
  subject_output_path = 'raw_data/subject_facts.json'
  with open(subject_output_path, 'w', encoding='utf-8') as f:
      ind = 0
      while ind < len(all_data):
          data = all_data[ind]
          entity = data[1]
          if entity not in name_dict:
              ind += 1
              continue
          
          qid_name = name_dict[entity]
          data_list = []
          facts = []
          
          while ind < len(all_data) and entity == data[1]:
              start = eval(data[3]) if data[3] != 'None' else (None, None, None)
              if data[3]!='None':
                start = time_transfer(complete_time(start))
              end = eval(data[4]) if data[4] != 'None' else (None, None, None)
              if data[4]!='None':
                end = time_transfer(complete_time(end))
              
              if data[3] == 'None' and data[4] == 'None' or data[0] not in templates or data[2] not in name_dict:
                  ind += 1
                  if ind < len(all_data):
                      data = all_data[ind]
                  continue
              fact = templates[data[0]].replace('<subject>', qid_name).replace('<object>', name_dict[data[2]])
              
              if data[3] == 'None':
                  fact += f' in {end}.'
              elif data[4] == 'None':
                  fact += f' in {start}.'
              else:
                  fact += f' from {start} to {end}.'
              
              facts.append(fact)
              data_list.append([data[0], data[2], data[3], data[4]])
              ind += 1
              
              if ind < len(all_data):
                  data = all_data[ind]
          
          if len(data_list) > 1:
              item = {
                  'entity': entity,
                  'name': qid_name,
                  'data_list': data_list,
                  'facts': facts
              }
              json_item = json.dumps(item)
              f.write(json_item + '\n')



  object_output_path = 'raw_data/object_facts.json'

  entity_data = {}

  for data in tqdm(all_data):
      entity = data[2]
      if entity not in name_dict:
          continue
      if entity not in entity_data:
          entity_data[entity] = {
              'data_list': [],
              'facts': [],
              'name': name_dict[entity]
          }

      start = eval(data[3]) if data[3] != 'None' else (None, None, None)
      if data[3]!='None':
        start = time_transfer(complete_time(start))
      end = eval(data[4]) if data[4] != 'None' else (None, None, None)
      if data[4]!='None':
        end = time_transfer(complete_time(end))

      if (data[3] == 'None' and data[4] == 'None') or data[0] not in templates or data[1] not in name_dict:
          continue

      fact = templates[data[0]].replace('<subject>', name_dict[data[1]]).replace('<object>', name_dict[entity])
      if data[3] == 'None':
          fact += ' in {0}.'.format(end)
      elif data[4] == 'None':
          fact += ' in {0}.'.format(start)
      else:
          fact += ' from {0} to {1}.'.format(start, end)
      
      entity_data[entity]['facts'].append(fact)
      entity_data[entity]['data_list'].append([data[0], data[1], data[3], data[4]])

  with open(object_output_path, 'w', encoding='utf-8') as f:
      for entity, info in entity_data.items():
          if len(info['data_list']) > 1:
              item = {
                  'entity': entity,
                  'name': info['name'],
                  'data_list': info['data_list'],
                  'facts': info['facts']
              }
              json_item = json.dumps(item)
              f.write(json_item + '\n')

if __name__ == "__main__":
  app.run(main)


