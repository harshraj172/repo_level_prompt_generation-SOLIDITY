import os, json
import openai 
import pandas as pd
import time 
from tqdm.auto import tqdm

os.environ["OPENAI_API_KEY"]='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'
openai.api_key = os.getenv("OPENAI_API_KEY")

def gen_text(prompt):
    time.sleep(30)
    response = openai.Completion.create(
      engine="code-davinci-002",
      prompt=prompt,
      temperature=0.5,
      max_tokens=20,
      top_p=1.0,
      frequency_penalty=0.0,
      presence_penalty=0.0
    )
    return response['choices'][0]['text']


if __name__ == "__main__":
    dir_path = "rule_classifier_data/train/paraspace-core/codebert_mod/prompts"
    
    # prompts
    for dir_ in tqdm(os.listdir(f"{dir_path}/rlpg")):
        rlpg_outs, rlpg_ptypes, target_holes = [], [], []
        for file in os.listdir(f"{dir_path}/rlpg/{dir_}"):
            with open(f"{dir_path}/rlpg/{dir_}/{file}", 'r') as f:
                rlpg_prompt = f.read().rstrip()
            rlpg_out = gen_text(rlpg_prompt)
            rlpg_outs.append(rlpg_out)
            rlpg_ptypes.append(str(file).split('.')[0])
            
            with open(f"{'/'.join(dir_path.split('/')[:-1])}/meta/{dir_}.json", 'r') as f:
                dict_lst = json.load(f)
            target_holes.append(dict_lst[1]['target_hole'])

        with open(f"{dir_path}/normal/{dir_}.txt", 'r') as f:
            default_prompt = f.read().rstrip()
        default_out = gen_text(default_prompt)
        default_outs = [default_out]*len(rlpg_outs)
        

        temp_df = pd.DataFrame({
            'rlpg_prompt-type': rlpg_ptypes,
            'rlpg_output' : rlpg_outs,
            'default_output': default_outs,
            'target-hole': target_holes,
        })
        
        try:
            df = pd.concat([df, temp_df], axis=0)
        except:
            df = temp_df
        df.to_csv("eval-rlpg_prompt.csv", index=False)
        