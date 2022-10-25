import numpy as np
import os, json
import torch
import re
import argparse
import random
from torch.utils.data import DataLoader
from torch import nn
from tqdm import tqdm
from rule_representation_data import *
from torch import FloatTensor

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def setup_args():
  """
  Description: Takes in the command-line arguments from user
  """
  parser = argparse.ArgumentParser()

  # data related hyperparameters
  parser.add_argument("--seed", type=int, default=9, help="seed for reproducibility")
  parser.add_argument("--input_data_dir", type=str, default='rule_classifier_data', help="base directory for the data")
  parser.add_argument("--data_split", type=str, default='val', help="train, val, test")
  parser.add_argument("--rule_context_frac", type=float, default=0.5, help="0.25, 0.5, 0.75")

  # model related hyperparameters
  parser.add_argument("--emb_model_type", type=str, default='codebert', help="model to obtain embedding from")
  parser.add_argument("--repo", type=str, default='jata4test', help="model to obtain embedding from")
  parser.add_argument("--num_examples_to_test", type=int, default=15, help="# of samples to take for testing")
  return parser.parse_args()

def get_target_hole(hole_info):
  l, c = int(hole_info.split('_')[-2]), int(hole_info.split('_')[-1])
  file_lines = open(hole_info.split('.')[0]+'.sol', encoding="utf8", errors='backslashreplace').readlines()
  return file_lines[l][c:]
 
def make_prompt(rule_context_dct_lst, rule_context_frac=0.5):
  prompt_rlpg = """"""
  for dct in rule_context_dct_lst:
    (k, v) = list(dct.items())[0]
    v = re.sub('<s>|</s>', '', v)
    if k=='codex':
      default_prompt = v
    elif k.split('#')[0] == 'in_file':
      prompt_rlpg = prompt_rlpg  +'\n'+ v 
    else:
      prompt_rlpg = v +'\n'+ prompt_rlpg 
  return prompt_rlpg + default_prompt, default_prompt
    
if __name__ == '__main__':

  args = setup_args()

  #Fix seeds
  np.random.seed(args.seed)
  os.environ['PYTHONHASHSEED'] = str(args.seed)
  torch.manual_seed(args.seed)
  random.seed(args.seed)


  # Define dataloaders
  kwargs = {'num_workers': 8, 'pin_memory': True} if device=='cuda' else {}
  tokenizer = set_tokenizer(args.emb_model_type)
  base_dir = os.path.join(args.input_data_dir, args.data_split)
  dataset = RuleReprDataset(base_dir, emb_model_type=args.emb_model_type, tokenizer=tokenizer)
  #for repo in os.listdir(base_dir):
  start, end = dataset.get_start_index(args.repo, start_offset=0, interval=0)
  end = min(args.num_examples_to_test, end)
  print(args.repo, start, end)
  for batch, (rule_context_dct_lst, hole_info, repo_name) in enumerate(dataset):
     if batch > end:
       break
     if repo_name == args.repo:
       save_dir = os.path.join(base_dir, repo_name, args.emb_model_type +'_mod')
       os.makedirs(f"{save_dir}/meta", exist_ok=True)
       os.makedirs(f"{save_dir}/prompts/rlpg", exist_ok=True)
       os.makedirs(f"{save_dir}/prompts/normal", exist_ok=True)
       
       default_context_dct = [dct for dct in rule_context_dct_lst if list(dct.keys())[0]=='codex']
       for j in range(len(rule_context_dct_lst)):
         k = list(rule_context_dct_lst[j].keys())[0]
         if k != 'codex':
           prompt_rlpg, prompt_norm = make_prompt(list(default_context_dct)+[rule_context_dct_lst[j]], args.rule_context_frac)
           os.makedirs(f"{save_dir}/prompts/rlpg/{batch}", exist_ok=True)
           with open(f"{save_dir}/prompts/rlpg/{batch}/{k}.txt", "w") as text_file:
             text_file.write(prompt_rlpg)

       target_hole = get_target_hole(hole_info)
       rule_representation = [{'hole_info': hole_info}, {'target_hole': target_hole}] + rule_context_dct_lst
      
       with open(f"{save_dir}/meta/{str(batch)}.json" , 'w') as f:
         json.dump(rule_representation, f)
       # with open(f"{save_dir}/prompts/rlpg-{args.rule_context_frac}/{batch}.txt", "w") as text_file:
       #   text_file.write(prompt_rlpg)
       with open(f"{save_dir}/prompts/normal/{batch}.txt", "w") as text_file:
         text_file.write(prompt_norm)
 
       # rule_representation = {hole: rule_context}
       # with open(os.path.join(save_dir, str(batch)) , 'wb') as f:
       #   pickle.dump(rule_representation, f)
