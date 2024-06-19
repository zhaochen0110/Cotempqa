SLING_BASE="$1"
OUT_BASE="$2"

WIKIOUT="$OUT_BASE/wikidata/"
TEMPOUT="$OUT_BASE/templama/"
SLING_KB="$SLING_BASE/data/e/kb/kb.sling"
SLING_WIKI="$SLING_BASE/data/e/wiki/en/mapping.sling"

python3 data_construct/sling2facts.py \
  --basedir=$WIKIOUT \
  --sling_kb_file=$SLING_KB \
  --action="make_kb" \
  --quick_test=False \
  --keep_only_numeric_slots=False \
  --keep_only_date_slots=True \
  --skip_empty_objects=True \
  --skip_nonentity_objects=False \
  --skip_nonentity_qualifiers=False \
  --skip_qualifiers=False \
  --skip_nonenglish=True \
  --show_names=False \
  --close_types_with_inheritance=False \
  --close_locations_with_containment=False \
  --frame_to_echo="Q1079" \
  --inherit_props_from_entity="P580,P582,P585" \
  --logtostderr

python3 data_construct/facts_to_raw_data.py \
  --out_dir=$TEMPOUT \
  --facts_file=$WIKIOUT/kb.cfacts \
  --sling_kb_file=$SLING_KB \
  --sling_wiki_mapping_file=$SLING_WIKI \
  --logtostderr



