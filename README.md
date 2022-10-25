## Dependencies
```
pip install tree-sitter
pip install tqdm 
pip install openai 

git clone https://github.com/JoranHonig/tree-sitter-solidity.git
```

## Code
### Data
**Example**: 
- Create a empty <ins>./data</ins> folder and clone [paraspace](https://github.com/para-space/paraspace-core).

**Use the below command:**
```
cd ./data
git clone https://github.com/para-space/paraspace-core
```

### Preprocessing Data --> Generating prompts --> storing CODEX output  
Run the bash script to get all the necessary scripts to run at once. 
**Note:** Add your openaiapi_key in the `--openaiapi_key` argument of `evaluate_prompt.py` when called from `job.sh`.  
```
bash job.sh
```
- Now Download the *eval-rlpg_prompt.csv* file generated to analyze the results.
