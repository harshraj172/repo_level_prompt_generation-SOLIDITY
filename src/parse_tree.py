import os
import pickle
import argparse
from tree_sitter import Language, Parser
from utils import *
import numpy as np

import copy

"""
Obtain the parse tree for individual files and collate data at repo-level for rules.
"""

Language.build_library('build/my-languages.so', ['tree-sitter-solidity']) 

SOLIDITY_LANGUAGE = Language('build/my-languages.so', 'solidity') 

parser = Parser()
parser.set_language(SOLIDITY_LANGUAGE)


def get_sibling_files(file, all_files):
  file_parts = file.split('/')
  root_dir = '/'.join(file_parts[:-1])
  sibling_files = []
  for f in os.listdir(root_dir):
    if os.path.splitext(f)[1] == '.sol' and f != file_parts[-1]:
      sib_file = os.path.join(root_dir, f)
      sibling_files.append(sib_file)
  return sibling_files

def camel_case_split(str):      
  start_idx = [i for i, e in enumerate(str)
               if e.isupper()] + [len(str)]

  start_idx = [0] + start_idx
  return [str[x: y] for x, y in zip(start_idx, start_idx[1:])]

def match_by_parts(file1, file2, split_type):
  # omit .sol in the end
  f1 = file1.split('.')[0]
  f2 = file2.split('.')[0]

  if split_type == 'camel-case':
    f1_parts = camel_case_split(f1)
    f2_parts = camel_case_split(f2)

  if split_type == 'underscore':
    f1_parts = f1.split('_')
    f2_parts = f2.split('_')

  for p1 in f1_parts:
    if p1 and p1 in f2_parts:
      #print(split_type, file1, file2, p1, f1_parts, f2_parts)
      return True
  return False


def match_similar_filenames(file1, file2):
  # exactly same name
  if file1 == file2:
    return True

  #camelcase split similar parts
  return match_by_parts(file1, file2, 'camel-case')

  #underscore split similar parts
  return match_by_parts(file1, file2, 'underscore')


def get_similar_name_files(file, all_files):
  filename = file.split('/')[-1]
  similar_name_files = []
  for f in all_files:
    if f != file and match_similar_filenames(f.split('/')[-1], filename):
      similar_name_files.append(f)
  return similar_name_files

def get_tree(filename):
  """
  obtain parse tree for a file
  """
  file_str = open(filename, encoding="utf8", errors='backslashreplace').read()
  tree = parser.parse(bytes(file_str, "utf-8"))
  root_node = tree.root_node
  return root_node

def parse_captures(captures, filename):
  text_spans = []
  for capture in captures:
    #capture[1] = property_name
    start, end = capture[0].start_point, capture[0].end_point
    #text = get_string(filename, start, end)
    text_spans.append((start, end))
  return text_spans

def get_query(attribute_type):

  # if attribute_type == 'class_name':
  #   query = SOLIDITY_LANGUAGE.query("""(class_declaration
  #                                 name: (identifier) @class_name)""")
  if attribute_type == 'contract_name':
    query = SOLIDITY_LANGUAGE.query("""(contract_declaration
                                  name: (identifier) @contract_name)""")
    
  # if attribute_type == 'class_body':
  #   query = SOLIDITY_LANGUAGE.query("""(class_declaration
  #                                 body: (class_body) @class_body)""")
  if attribute_type == 'contract_body': 
    query = SOLIDITY_LANGUAGE.query("""(contract_declaration
                                  body: (contract_body) @contract_body)""")
    
  # if attribute_type == 'parent_class_name':
  #   query = SOLIDITY_LANGUAGE.query("""(class_declaration
  #                                 name: (identifier)
  #                                 superclass: (superclass (type_identifier) @superclass_name))""")
  if attribute_type == 'parent_contract_name':
    query = SOLIDITY_LANGUAGE.query("""(contract_declaration
                                    name: (identifier)
                                    (inheritance_specifier
                                    ancestor: (user_defined_type
                                    (identifier)) @parent_contract_name))""")

  # if attribute_type == 'all_method_name':
  #   query = SOLIDITY_LANGUAGE.query("""(method_declaration
  #                                   name: (identifier) @all_method_name)""")
  if attribute_type == 'all_function_name':
    query = SOLIDITY_LANGUAGE.query("""(function_definition
                                          name: (identifier) @all_function_name)""")

  # if attribute_type == 'all_method_body':
  #   query = SOLIDITY_LANGUAGE.query("""(method_declaration body: (block) @all_method_block)""")
  if attribute_type == 'all_function_body':
    query = SOLIDITY_LANGUAGE.query("""(function_definition
                                          body: (function_body) @all_function_body)""")
    
  # if attribute_type == 'import_statement':
  #   query = SOLIDITY_LANGUAGE.query("""(import_declaration (
  #                                  scoped_identifier
  #                                  name: (identifier)) @import_statement)""")
  if attribute_type == 'import_statement':
    query = SOLIDITY_LANGUAGE.query("""(source_file (
                                   import_directive
                                   import_name: (identifier)) @import_statement)""")

  # if attribute_type == 'all_field_declaration':
  #   query = SOLIDITY_LANGUAGE.query("""(field_declaration) @field_declaration""")
  if attribute_type == 'all_field_declaration':
    query = SOLIDITY_LANGUAGE.query("""(state_variable_declaration) @state_variable_declaration""")

  if attribute_type == 'all_string_literal':
    query = SOLIDITY_LANGUAGE.query("""(string_literal) @string_literal""")

  if attribute_type == 'all_identifier':
    query = SOLIDITY_LANGUAGE.query("""(identifier) @identifier""")

  # if attribute_type == 'all_type_identifier':
  #   query = SOLIDITY_LANGUAGE.query("""(type_identifier) @type_identifier""")
  if attribute_type == 'all_type_identifier':
    query = SOLIDITY_LANGUAGE.query("""(contract_declaration
                                        name: (identifier) @contract_name)
                                       (interface_declaration
                                        name: (identifier) @interface_name)
                                       (enum_declaration
                                        name: (identifier) @enum_name)""")

  return query

def get_attribute(root_node, filename, attribute_type):

  query = get_query(attribute_type)
  captures = query.captures(root_node)
  if captures:
    attributes = parse_captures(captures, filename)
  else:
    attributes = [((-1, -1), (-1, -1))]
  return attributes

def get_import_path(import_stat, file):
  import_stat_str = get_string(file, import_stat[0], import_stat[1])
  #print(import_stat_str, file)
  import_path_parts = import_stat_str.split(".")
  absolute_import_path = []
  import_path_part = import_path_parts[0]
  if import_path_part != 'sol':
    file_path_parts = file.split("/")
    try:
      index_pos = len(file_path_parts) - file_path_parts[::-1].index(import_path_part) - 1
      absolute_import_path = file_path_parts[:index_pos] + import_path_parts
    except ValueError as e:
      print('')
  # print(absolute_import_path)
  if absolute_import_path:
    import_path = '/'.join(absolute_import_path)
    import_path = import_path + '.sol'
    return import_path
  else:
    return ''

def get_parent_contract_filename(parent_contract_name, file_contract_info, file):
  parent_contract_filename = ''
  if parent_contract_name:
    parent_contract_name_text = get_string(file, parent_contract_name[0], parent_contract_name[1])
    # we don't want the current file to be the parent contract file
    copy_file_contract_info = copy.deepcopy(file_contract_info)
    del copy_file_contract_info[file]

    if parent_contract_name_text:
      # search for the parent contract name in all files
      found = False
      for (k,v) in copy_file_contract_info.items():
        for val in v:
          if val==parent_contract_name_text:
            parent_contract_filename = k
            found = True
            break
  return parent_contract_filename

def find_relevant_file_identifier(import_identifier, file_identifiers, file):
  candidate_file_identifiers = []
  for file_identifier in file_identifiers:
    if file_identifier:
      file_identifier_str = get_string(file, file_identifier[0], file_identifier[1])
      if file_identifier_str == import_identifier:
        candidate_file_identifiers.append(file_identifier)
  return candidate_file_identifiers[1:]

def get_imports(import_statements, file, all_identifiers, all_type_identifiers):
  imports = {}
  file_identifiers = all_identifiers
  file_identifiers.extend(all_type_identifiers)
  for import_stat in import_statements:
    import_file_path = get_import_path(import_stat, file)
    if import_file_path and os.path.isfile(import_file_path):
      import_identifier = import_file_path.split('/')[-1].split('.')[0]
      candidate_file_identifiers = find_relevant_file_identifier(import_identifier, file_identifiers, file)
      if candidate_file_identifiers:
        imports[import_file_path] = candidate_file_identifiers
  return imports

def check_empty_attribute(attribute):
  if len(attribute) == 1 and attribute[0][0][0] == -1:
      attribute = []
  return attribute

def update_attribute(parse_data, att_type, files):
  count = 0
  for file in files:
    current_file_imports = list(parse_data[file]['imports'].keys())
    att_files = parse_data[file][att_type]
    att_info = []
    for att_file in att_files:
      if att_file:
        att_file_imports = list(parse_data[att_file]['imports'].keys())
        overlapping_imports = find_similar_intersection(att_file_imports, current_file_imports)
        #if len(overlapping_imports) > 0:
        att_info.append((att_file, len(overlapping_imports)))
        #print(file, att_file, overlapping_imports)
    parse_data[file][att_type] = att_info
    if att_info:
      count+=1
      #print(file, parse_data[file][att_type])
  #print(count)
  return parse_data

def update_child_contract_info(parse_data, child_contract_info):
  for file, file_parse_data in parse_data.items():
    if file in child_contract_info:
      parse_data[file]['child_contract_filenames'] = child_contract_info[file]
    else:
      parse_data[file]['child_contract_filenames'] = []
  return parse_data
          
def setup_args():
  """
  Description: Takes in the command-line arguments from user
  """
  parser = argparse.ArgumentParser()

  parser.add_argument("--seed", type=int, default=9, help="seed for reproducibility")
  parser.add_argument("--base_dir", type=str, default='rule_classifier_data/val', \
                            help="base directory for the data")
  parser.add_argument("--proj_name", type=str, default='solmate', \
                            help="name of the input repo")

  return parser.parse_args()

if __name__ == '__main__':

  args = setup_args()

  #Fix seeds
  np.random.seed(args.seed)
  os.environ['PYTHONHASHSEED']=str(args.seed)

  input_data_path = os.path.join(args.base_dir, args.proj_name)
  os.makedirs(input_data_path, exist_ok=True)

  files = [os.path.join(dp, f) \
            for dp, dn, filenames in os.walk(input_data_path) \
            for f in filenames \
            if os.path.splitext(f)[1] == '.sol']

  file_contract_info = {}
  for file in files:
    root_node = get_tree(file)
    contract_names = get_attribute(root_node, file, 'contract_name')
    file_contract_names = []
    for cn in contract_names:
      start, end = cn
      contract_name = get_string(file, start, end)
      file_contract_names.append(contract_name)
    file_contract_info[file] = file_contract_names
  print(file_contract_info)
  
  with open(os.path.join(input_data_path, 'file_contract_data'), 'wb') as f:
    pickle.dump(file_contract_info, f)

  parse_data = {}
  child_contract_info = {}

  similar_count = 0
  sibling_count = 0

  for file in files:
    root_node = get_tree(file)
    sibling_files = get_sibling_files(file, files)
    similar_name_files = get_similar_name_files(file, files)
    if len(similar_name_files) > 0:
      similar_count +=1
    if len(sibling_files) > 0:
      sibling_count +=1

#     class --> contract ; method --> function

    contract_names = get_attribute(root_node, file, 'contract_name')
    contract_bodies = get_attribute(root_node, file, 'contract_body')
    parent_contract_names = get_attribute(root_node, file, 'parent_contract_name')
    all_field_declarations = get_attribute(root_node, file, 'all_field_declaration') #(variable inside a class))
    all_string_literals = get_attribute(root_node, file, 'all_string_literal')
    all_identifiers = get_attribute(root_node, file, 'all_identifier')
    all_type_identifiers = get_attribute(root_node, file, 'all_type_identifier') #(name of Interface, class, enum)
    all_function_names = get_attribute(root_node, file, 'all_function_name')
    all_function_bodies = get_attribute(root_node, file, 'all_function_body')
    import_statements = get_attribute(root_node, file, 'import_statement')

    contract_names = check_empty_attribute(contract_names)
    contract_bodies = check_empty_attribute(contract_bodies)
    parent_contract_names = check_empty_attribute(parent_contract_names)
    all_field_declarations = check_empty_attribute(all_field_declarations)
    all_identifiers = check_empty_attribute(all_identifiers)
    all_type_identifiers = check_empty_attribute(all_type_identifiers)
    all_string_literals = check_empty_attribute(all_string_literals)
    all_function_names = check_empty_attribute(all_function_names)
    all_function_bodies = check_empty_attribute(all_function_bodies)
    import_statements = check_empty_attribute(import_statements)

    # get imports
    imports = get_imports(import_statements, file, all_identifiers, all_type_identifiers)
    print(imports)
    parent_contract_filenames = []
    mod_parent_contract_names = []
    for parent_contract_name in parent_contract_names:
      parent_contract_filename = get_parent_contract_filename(parent_contract_name, file_contract_info, file)
      if parent_contract_filename:
        mod_parent_contract_names.append(parent_contract_name)
        if parent_contract_filename in child_contract_info:
          child_contract_info[parent_contract_filename].append(file)
        else:
          child_contract_info[parent_contract_filename] = [file]
        parent_contract_filenames.append(parent_contract_filename)

    print(parent_contract_names, parent_contract_filenames)
    assert len(mod_parent_contract_names) == len(parent_contract_filenames)

    #store the data in dict form
    parse_data[file] = {
                        'contract_names': contract_names,\
                        'contract_bodies': contract_bodies, \
                        'parent_contract_names': mod_parent_contract_names, \
                        'parent_contract_filenames': parent_contract_filenames, \
                        'imports': imports, \
                        'field_declarations': all_field_declarations, \
                        'string_literals': all_string_literals, \
                        'identifiers': all_identifiers, \
                        'type_identifiers': all_type_identifiers, \
                        'all_function_names': all_function_names, \
                        'all_function_bodies': all_function_bodies, \
                        'sibling_files': sibling_files, \
                        'similar_name_files': similar_name_files}

  print(len(files), sibling_count, similar_count)
  print("updating sibling files")
  parse_data = update_attribute(parse_data, 'sibling_files', files)
  print("updating similar_name_files")
  parse_data = update_attribute(parse_data, 'similar_name_files', files)
  print("updating child contract filenames")
  parse_data = update_child_contract_info(parse_data, child_contract_info)
  parse_data = update_attribute(parse_data, 'child_contract_filenames', files)
  print("updating parent contract filenames")
  parse_data = update_attribute(parse_data, 'parent_contract_filenames', files)

  print("Writing parse data...")
  with open(os.path.join(input_data_path, 'parsed_data'), 'wb') as f:
    pickle.dump(parse_data, f)