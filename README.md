## OVERVIEW
An implementation of the paper [Repo-Level Prompt Generation](https://arxiv.org/abs/2206.12839) to support SOLIDITY codes, a widely used programming language in the Blockchain Industry.

## SETUP

## Dependencies
Clone this repo :
```
git clone https://github.com/harshraj172/repo_level_prompt_generation-SOLIDITY.git
```

Install necessary libraries :
```
pip install tree-sitter
pip install tqdm 
pip install openai 

cd /repo_level_prompt_generation-SOLIDITY
git clone https://github.com/JoranHonig/tree-sitter-solidity.git
```


### Data
**Example**: 
- Create an empty <ins>repo_level_prompt_generation-SOLIDITY/data</ins> folder and clone [paraspace](https://github.com/para-space/paraspace-core).

**Use the below command:**
```
cd /repo_level_prompt_generation-SOLIDITY/data
git clone https://github.com/para-space/paraspace-core
```

### Preprocessing Data --> Generating prompts --> storing CODEX output  
Run the bash script to get all the necessary scripts to run at once.

**Note:** Add your openaiapi_key in the `--openaiapi_key` argument of `evaluate_prompt.py` when called from `job.sh`.  
```
cd /repo_level_prompt_generation-SOLIDITY
bash job.sh
```
- Now Download the *eval-rlpg_prompt.csv* file generated to analyze the results.
