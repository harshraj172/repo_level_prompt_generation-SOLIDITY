import os
base_dir = 'rule_classifier_data'

projects = { 'train': [
                    'paraspace-core',                   
                    ], 

            'val': [
                    'solmate',
                    ],
                    
            'test': [
                      'FractonV1',
                    ] 
          }

commands = []
for data_split, data_split_repos in projects.items():
  for proj in data_split_repos:
    proj_name = proj.strip()
    command = "python analyze_results.py --proj_name " + proj_name \
              + " --base_dir " + base_dir + " --data_split " + data_split
    commands.append(command)

with open("commands_analyze_results", 'w') as f:
  f.writelines("%s\n" % command for command in commands)
f.close()

