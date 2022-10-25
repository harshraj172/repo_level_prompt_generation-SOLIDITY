#!/bin/sh

python src/create_hole_data.py \
--base_dir data \
--data_split train \
--proj_name paraspace-core \

python src/parse_tree.py \
--base_dir rule_classifier_data/train \
--proj_name paraspace-core \

python src/check_duplication.py \
--base_dir rule_classifier_data/train \
--proj_name paraspace-core \

# python src/generate_completions.py \
# --base_dir rule_classifier_data/train \
# --repo_name paraspace-core

# python src/analyze_results.py \
# --base_dir rule_classifier_data/train \
# --data_split train \
# --proj_name paraspace-core

python src/generate_rule_representations.py \
--data_split train \
--repo paraspace-core \
--emb_model_type codebert

# python evaluate_prompt.py \
# --dir_path "rule_classifier_data/train/paraspace-core/codebert_mod/prompts" \
# --openai_api_key "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"