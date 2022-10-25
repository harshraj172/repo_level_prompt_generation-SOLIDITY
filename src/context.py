import os
from utils import *
import numpy as np

class getContext():

  def __init__(self, context_location='in_file', tokenizer=None, file='',
                context_len=4072, parse_data=None,
                context_type='lines', context_scope='pre', top_k=-1, top_k_type='first',
                attention_scores=None, rule_context_formatting='space',
                file_lines=None):

    super(getContext, self).__init__()

    self.file = file
    self.context_len = context_len
    self.context_location = context_location
    self.tokenizer = tokenizer
    self.top_k = top_k
    self.top_k_type = top_k_type
    self.context_type = context_type
    self.parse_data = parse_data
    self.attention_scores = attention_scores
    self.rule_context_formatting = rule_context_formatting
    if file_lines !=None:
      self.file_lines = file_lines
    else:
      self.file_lines = open(file, encoding="utf8", errors='backslashreplace').readlines()
    if self.context_location == 'in_file':
      self.set_context_scope_and_inclusion_type(context_scope)
    elif self.context_location == 'parent_contract_file':
      self.codex_completion_inclusion_type = 'back'
    else:
      self.import_overlap_type_files = {}
      self.codex_completion_inclusion_type = 'front'

  def is_non_empty(self, parse_data_attribute_str):
    parse_data_attribute = self.parse_data[self.file][parse_data_attribute_str]
    if parse_data_attribute:
      return True
    else:
      return False

  def is_out_files(self):
    if self.context_location == 'parent_contract_file' or self.context_location == 'import_of_parent_contract_file':
      return self.is_non_empty('parent_contract_filenames')
    if self.context_location == 'import_file':
      return self.is_non_empty('imports')
    if self.context_location == 'sibling_file' or self.context_location == 'reverse_sibling_file' or self.context_location == 'import_of_sibling_file':
      return self.is_non_empty('sibling_files')
    if self.context_location == 'similar_name_file' or self.context_location == 'reverse_similar_name_file' or self.context_location == 'import_of_similar_name_file':
      return self.is_non_empty('similar_name_files')
    if self.context_location == 'child_contract_file' or self.context_location == 'import_of_child_contract_file':
      return self.is_non_empty('child_contract_filenames')

  def set_context_scope_and_inclusion_type(self, new_scope):
    self.context_scope = new_scope
    if self.context_scope == 'pre' or self.context_scope =='pre_post':
      self.codex_completion_inclusion_type ='back'
    if self.context_scope == 'post':
      self.codex_completion_inclusion_type ='front'

  def set_hole_pos(self, hole_pos):
    self.hole_pos = hole_pos

  def get_context_len(self):
    return self.context_len

  def set_context_len(self, new_context_len):
    self.context_len = new_context_len

  def get_rule_context_format(self, lst):
    if self.rule_context_formatting == 'space':
      context = " ".join(lst)

    if self.rule_context_formatting == 'newline':
      context = "\n".join(lst)

    if self.rule_context_formatting == 'function_name'\
    or self.rule_context_formatting == 'contract_name'\
    or self.rule_context_formatting == 'contract_function_name':
      context = " ".join(lst)

    if self.rule_context_formatting == 'comment':
      context = " ".join(lst)
      context = "/*" + context + "*/"

    return context

  def get_nearest_attribute_index(self, attribute_names, type='contract'):
    hole_start_line = self.hole_pos[0]
    min_pos_diff = 100000
    min_pos_diff_index = -1
    for i in range(len(attribute_names)):
      if attribute_names[i]:
        attribute_start_line = attribute_names[i][0][0]
        if type == 'contract':
          pos_diff = hole_start_line - attribute_start_line
        if type == 'import':
          pos_diff = np.abs(hole_start_line - attribute_start_line)
        if pos_diff < min_pos_diff:
          if type == 'contract':
            if pos_diff > 0:
              min_pos_diff = pos_diff
              min_pos_diff_index = i
              #print(pos_diff, min_pos_diff, min_pos_diff_index)
          if type == 'import':
            if pos_diff != 0 or (pos_diff == 0 and attribute_names[i][1][1] < self.hole_pos[1]):
              min_pos_diff = pos_diff
              min_pos_diff_index = i
    if type == 'contract':
      return min_pos_diff_index
    if type == 'import':
      return pos_diff

  def get_relevant_import_of_att_files(self, att_type):
    att_import_ranking = {}
    att_files = self.parse_data[self.file][att_type]
    #att_files = list(set(att_files))
    for att_file, att_file_overlap in att_files:
      if 'small_' in self.file.split('/')[1]:
        att_file = '/'.join([att_file.split('/')[0]] + [self.file.split('/')[1]] + att_file.split('/')[2:])
      att_file_imports = list(self.parse_data[att_file]['imports'].keys())
      for att_file_import in att_file_imports:
        if att_file_import in att_import_ranking:
          att_import_ranking[att_file_import]+=1
        else:
          att_import_ranking[att_file_import] = 1
    sorted_att_import_ranking = sorted(att_import_ranking.items(), key=lambda x: x[1], reverse=True)
    sorted_att_import_ranking = [imp_file for imp_file, _ in sorted_att_import_ranking]
    return sorted_att_import_ranking

  def get_relevant_import_files(self):
    all_imports = self.parse_data[self.file]['imports']
    import_distances_from_hole = {}
    for import_file, import_identifier_loc in all_imports.items():
      pos_diff = self.get_nearest_attribute_index(import_identifier_loc, type='import')
      if pos_diff != -1:
        import_distances_from_hole[import_file] = pos_diff

    # less the position difference from the hole, higher the ranking
    sorted_import_distances_from_hole = sorted(import_distances_from_hole.items(), key=lambda x: x[1])
    sorted_import_files = [imp_file for imp_file, _ in sorted_import_distances_from_hole]
    return sorted_import_files

  def get_relevant_files(self, type_str, sort_order='descending'):
    all_type_files = self.parse_data[self.file][type_str]
    if not all_type_files:
      return all_type_files

    sorted_file_imports = self.get_relevant_import_files()
    overlapping_type_files = {}
    found = False
    # find type files(e.g. sibling files) with imports common with current file based on the position with the hole.
    # in case multiple such files exist, sort based on number of common import statements.
    for imp_file in sorted_file_imports:
      if imp_file in self.import_overlap_type_files:
        return self.import_overlap_type_files[imp_file]
      if found:
        break
      for type_file, type_file_overlap in all_type_files:
        if type_file_overlap > 0:
          if 'small_' in self.file.split('/')[1]:
            type_file = '/'.join([type_file.split('/')[0]] + [self.file.split('/')[1]] + type_file.split('/')[2:])
          type_file_import_files = list(self.parse_data[type_file]['imports'].keys())
          if imp_file in type_file_import_files:
            overlapping_type_files[type_file] = type_file_overlap
            found = True

    if not found:
      type_files = [x[0] for x in all_type_files]
      return type_files

    # more the overlap, higher the ranking
    if sort_order == 'descending':
      sorted_overlapping_type_files = sorted(overlapping_type_files.items(), key=lambda x: x[1], reverse=True)
    else:
      sorted_overlapping_type_files = sorted(overlapping_type_files.items(), key=lambda x: x[1])

    sorted_type_files = [type_file for type_file, _ in sorted_overlapping_type_files]
    self.import_overlap_type_files[imp_file] = sorted_type_files
    return sorted_type_files

  def get_parent_contract_filename(self):
    """
    Return the parent contract filename that corresponds to the immediate scope of the hole location
    """
    file_parsed_data = self.parse_data[self.file]
    parent_contract_filenames = file_parsed_data['parent_contract_filenames']
    parent_contract_names = file_parsed_data['parent_contract_names']
    relevant_index = self.get_nearest_attribute_index(parent_contract_names)
    if relevant_index != -1:
      return parent_contract_filenames[relevant_index][0], parent_contract_names[relevant_index]
    else:
      return '', ''

  def get_function_names_and_bodies(self, function_names, function_bodies, file):
    if self.top_k != -1 and len(function_names) >= self.top_k:
      function_context_len = int(self.context_len/self.top_k)
    else:
      function_context_len = int(self.context_len/len(function_names))

    function_contexts = []
    context_len = 0
    for function_name in function_names:
      if function_name:
        found = False
        for function_body in function_bodies:
          # for each function name, find the corresponding function_body
          if function_body and function_body[0][0] == function_name[0][0]:
            ms, me = function_body
            full_ms = (ms[0], 0)
            full_me = me
            found = True
            break

        if found == False:
          ms, me = function_name
          full_ms = (ms[0], 0)
          full_me = (ms[0], -1)

        function_name_and_body = get_string(file, full_ms, full_me)
        function_context, function_context_len = get_codex_tokenized_string(self.tokenizer, function_name_and_body, \
                                        function_context_len)
        if self.rule_context_formatting == 'function_name'\
        or self.rule_context_formatting =='contract_function_name':
          function_name_str = "[" + get_string(file, function_name[0], function_name[1]) + "]"
          function_contexts.append(function_name_str)
        function_contexts.append(function_context)
        context_len += function_context_len

    context = self.get_rule_context_format(function_contexts)
    return context, context_len

  def get_context_string(self, candidate_attributes):

    if self.top_k == -1:
      attributes_str = self.get_rule_context_format(candidate_attributes)
    else:
      if self.top_k_type == 'first':
        attributes_str = self.get_rule_context_format(candidate_attributes[:self.top_k])
      if self.top_k_type == 'last':
        attributes_str = self.get_rule_context_format(candidate_attributes[-self.top_k:])

    context, context_len = get_codex_tokenized_string(self.tokenizer, attributes_str, self.context_len,
                                        type=self.codex_completion_inclusion_type)

    return context, context_len

  def get_attribute_context(self, attributes, file):
    candidate_attributes = []
    for attribute in attributes:
      if attribute:
        start, end = attribute

        if self.context_location == 'in_file':
          start_line, start_char = start
          end_line, end_char = end
          hole_pos_line, hole_pos_char = self.hole_pos
          #assert start_line == end_line, "attribute doesn't span a single line"

          if self.context_scope == 'pre' or self.context_scope == 'pre_post':
            if end_line < hole_pos_line or (end_line == hole_pos_line and end_char < hole_pos_char):
              attribute_string = get_string(file, start, end)
              candidate_attributes.append(attribute_string.strip())

          if self.context_scope == 'post' or self.context_scope == 'pre_post':
            if start_line > hole_pos_line:
              attribute_string = get_string(file, start, end)
              candidate_attributes.append(attribute_string.strip())

        else:
          # checking for overlap with the hole is not needed here as it is a different file
          attribute_string = get_string(file, start, end)
          candidate_attributes.append(attribute_string.strip())

    context, context_len = self.get_context_string(candidate_attributes)
    return context, context_len

  def get_line_context(self, num_of_lines_to_exclude=0):
    num_of_lines_to_be_taken = self.top_k
    pre_context = ''
    post_context = ''
    if self.context_scope == 'pre' or self.context_scope == 'pre_post':
      end = self.hole_pos
      if num_of_lines_to_be_taken == -1:
        start = (0, 0)
      else:
        hole_pos_line = self.hole_pos[0]
        start_line = hole_pos_line - num_of_lines_to_be_taken
        if start_line < 0:
          start_line = 0
        start = (start_line, 0)
      pre_context = get_string(self.file, start, end)

    if self.context_scope == 'post' or self.context_scope == 'pre_post':
      hole_pos_line = self.hole_pos[0]
      start = (hole_pos_line + 1 + num_of_lines_to_exclude, 0)
      if num_of_lines_to_be_taken != -1:
        end_line = hole_pos_line + num_of_lines_to_be_taken + num_of_lines_to_exclude
        if end_line >= len(self.file_lines):
          end_line = len(self.file_lines) - 1
        end_char =  len(self.file_lines[end_line])
        end = (end_line, end_char)
      else:
        end_line = len(self.file_lines)-1
        end_char = len(self.file_lines[end_line])
        end = (end_line, end_char)

      post_context = get_string(self.file, start, end)

    if self.context_scope == 'pre':
      context, context_len = get_codex_tokenized_string(self.tokenizer, pre_context, self.context_len,
                                            type=self.codex_completion_inclusion_type)
    if self.context_scope == 'post':
      context, context_len = get_codex_tokenized_string(self.tokenizer, post_context, self.context_len,
                                              type=self.codex_completion_inclusion_type)
    if self.context_scope == 'pre_post':
      pre_context, pre_context_len = get_codex_tokenized_string(self.tokenizer, pre_context, int(self.context_len/2),
                                            type='back')
      post_context, post_context_len = get_codex_tokenized_string(self.tokenizer, post_context, int(self.context_len/2),
                                            type='front')

      context = pre_context + "\n" + post_context
      context_len = pre_context_len + post_context_len

    return context, context_len

  def get_base_context(self):
    base_contract_names = self.parse_data[self.file]['contract_names']
    contract_index = self.get_nearest_attribute_index(base_contract_names)
    if contract_index != -1:
      base_contract_name = get_string(self.file, base_contract_names[contract_index][0], base_contract_names[contract_index][1])
      base_context = "[" + base_contract_name + "]"
    else:
      base_context = ''
    return base_context

  def get_attribute_context_from_context_type(self, file_type):
    if 'small_' in self.file.split('/')[1]:
      file_type = '/'.join([file_type.split('/')[0]] + [self.file.split('/')[1]] + file_type.split('/')[2:])
    if self.context_type == 'identifiers':
      context, context_len = self.get_attribute_context(self.parse_data[file_type]['identifiers'], file_type)

    if self.context_type == 'type_identifiers':
      context, context_len = self.get_attribute_context(self.parse_data[file_type]['type_identifiers'], file_type)

    if self.context_type == 'string_literals':
      context, context_len = self.get_attribute_context(self.parse_data[file_type]['string_literals'], file_type)

    if self.context_type == 'function_names':
      context, context_len = self.get_attribute_context(self.parse_data[file_type]['all_function_names'], file_type)

    if self.context_type == 'function_names_and_bodies':
      function_names = self.parse_data[file_type]['all_function_names']
      function_bodies = self.parse_data[file_type]['all_function_bodies']
      if function_names:
        context, context_len = self.get_function_names_and_bodies(function_names, function_bodies, file_type)
      else:
        context= ''
        context_len = 0

    if self.context_type == 'field_declarations':
      context, context_len = self.get_attribute_context(self.parse_data[file_type]['field_declarations'], file_type)

    return context, context_len

  def get_context_from_multiple_files(self, files):
    total_context_len = 0
    total_context = ''
    if files:
      for file in files:
        if total_context_len < self.get_context_len():
          if self.rule_context_formatting == 'contract_name' or self.rule_context_formatting == 'contract_function_name':
            base_context = self.get_base_context()
            file_name = file.split('/')[-1].split('.')[0]
            file_name = "[" + file_name + "]"
          # get context
          context, context_len = self.get_attribute_context_from_context_type(file)

          # import contexts are added to the front based on decreasing priority
          if self.rule_context_formatting == 'contract_name' or self.rule_context_formatting == 'contract_function_name':
            total_context = file_name + " " + context + " " + total_context
          else:
            total_context = context + " " + total_context
          total_context_len += context_len
        else:
          break

      if self.rule_context_formatting == 'contract_name' or self.rule_context_formatting == 'contract_function_name':
        total_context = total_context + "\n" + base_context
    return total_context, total_context_len

  def get_in_file_context(self, num_of_lines_to_exclude=0):
    """
    for in_file only post lines makes sense.
    for others, first post is tried, if post is not successful in finding any context the pre_post is tried.
    """
    if self.context_type == 'lines':
      self.set_context_scope_and_inclusion_type('post')
      context, context_len = self.get_line_context(num_of_lines_to_exclude)
      # doesn't mean much to have pre_post in this setting

    if self.context_type == 'identifiers':
      self.set_context_scope_and_inclusion_type('post')
      context, context_len = self.get_attribute_context(self.parse_data[self.file]['identifiers'], self.file)
      if not context:
        self.set_context_scope_and_inclusion_type('pre_post')
        context, context_len = self.get_attribute_context(self.parse_data[self.file]['identifiers'], self.file)

    if self.context_type == 'type_identifiers':
      self.set_context_scope_and_inclusion_type('post')
      context, context_len = self.get_attribute_context(self.parse_data[self.file]['type_identifiers'], self.file)
      if not context:
        self.set_context_scope_and_inclusion_type('pre_post')
        context, context_len = self.get_attribute_context(self.parse_data[self.file]['type_identifiers'], self.file)

    if self.context_type == 'string_literals':
      self.set_context_scope_and_inclusion_type('post')
      context, context_len = self.get_attribute_context(self.parse_data[self.file]['string_literals'], self.file)
      if not context:
        self.set_context_scope_and_inclusion_type('pre_post')
        context, context_len = self.get_attribute_context(self.parse_data[self.file]['string_literals'], self.file)

    if self.context_type == 'function_names':
      self.set_context_scope_and_inclusion_type('post')
      context, context_len = self.get_attribute_context(self.parse_data[self.file]['all_function_names'], self.file)
      if not context:
        self.set_context_scope_and_inclusion_type('pre_post')
        context, context_len = self.get_attribute_context(self.parse_data[self.file]['all_function_names'], self.file)

    if self.context_type == 'field_declarations':
      self.set_context_scope_and_inclusion_type('post')
      context, context_len = self.get_attribute_context(self.parse_data[self.file]['field_declarations'], self.file)
      if not context:
        self.set_context_scope_and_inclusion_type('pre_post')
        context, context_len = self.get_attribute_context(self.parse_data[self.file]['field_declarations'], self.file)

    return context, context_len

  def get_parent_contract_file_context(self):
    self.parent_contract_file, self.parent_contract_name = self.get_parent_contract_filename()
    if self.parent_contract_file:
      if self.rule_context_formatting == 'contract_name' or self.rule_context_formatting == 'contract_function_name':
        base_context = self.get_base_context()
        parent_contract_name = get_string(self.file, self.parent_contract_name[0], self.parent_contract_name[1])
        parent_context = "[" + parent_contract_name + "]"
      # get context
      context, context_len = self.get_attribute_context_from_context_type(self.parent_contract_file)
      if self.rule_context_formatting == 'contract_name' or self.rule_context_formatting == 'contract_function_name':
        context = parent_context + " " + context + "\n" + base_context
    else:
      context = ''
      context_len = 0

    return context, context_len

  def get_import_file_context(self):
    import_files = self.get_relevant_import_files()
    return self.get_context_from_multiple_files(import_files)

  def get_sibling_file_context(self):
    if self.context_location.startswith('reverse'):
      sort_order ='ascending'
    else:
      sort_order = 'descending'
    sibling_files = self.get_relevant_files(type_str='sibling_files', sort_order=sort_order)
    return self.get_context_from_multiple_files(sibling_files)

  def get_similar_name_file_context(self):
    if self.context_location.startswith('reverse'):
      sort_order ='ascending'
    else:
      sort_order = 'descending'
    similar_name_files = self.get_relevant_files(type_str='similar_name_files', sort_order=sort_order)
    return self.get_context_from_multiple_files(similar_name_files)

  def get_child_contract_file_context(self):
    child_contract_files = self.get_relevant_files(type_str='child_contract_filenames')
    return self.get_context_from_multiple_files(child_contract_files)

  def get_import_of_sibling_file_context(self):
    imports_of_sibling_files = self.get_relevant_import_of_att_files('sibling_files')
    return self.get_context_from_multiple_files(imports_of_sibling_files)

  def get_import_of_similar_name_file_context(self):
    imports_of_similar_name_files = self.get_relevant_import_of_att_files('similar_name_files')
    return self.get_context_from_multiple_files(imports_of_similar_name_files)

  def get_import_of_parent_contract_file_context(self):
    imports_of_parent_contract_files = self.get_relevant_import_of_att_files('parent_contract_filenames')
    return self.get_context_from_multiple_files(imports_of_parent_contract_files)

  def get_import_of_child_contract_file_context(self):
    imports_of_child_contract_files = self.get_relevant_import_of_att_files('child_contract_filenames')
    return self.get_context_from_multiple_files(imports_of_child_contract_files)
