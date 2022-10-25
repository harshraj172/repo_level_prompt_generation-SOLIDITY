import os
base_data_dir = 'gcode-data'

projects = { 'train': [
                      'paraspace-core',
                      'DeFiHackLabs',
                      ], 

              'val': [
                      'ERC721A', 
                      ],

              'test': [
                      'solmate',
                      ] 
            }

commands = []
for data_split, data_split_repos in projects.items():
  for proj in data_split_repos:
    proj_name = proj.strip()
    command = "python create_hole_data.py --proj_name " + proj_name \
              + " --base_dir " + base_data_dir + " --data_split " + data_split
    commands.append(command)
    command = "python parse_tree.py --proj_name " + proj_name \
              + " --base_dir " + os.path.join('rule_classifier_data', data_split)
    commands.append(command)
    command = "python check_duplication.py --proj_name " + proj_name \
              + " --base_dir " + os.path.join('rule_classifier_data', data_split)
    commands.append(command)

with open("commands_gen_and_preprocess", 'w') as f:
  f.writelines("%s\n" % command for command in commands)
f.close()