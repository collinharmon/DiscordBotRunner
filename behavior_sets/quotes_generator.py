import json
import os
from os import path
from jsonschema import validate
import random

path_to_schema = "/data/quote_generator_schema.json"
path_to_schema = os.path.join(os.path.dirname(os.path.realpath(__file__)), path_to_schema)

class QuoteGenerator:
  def __init__(self, *args, **kwargs):
    super().__init__()
    self.files_to_parse = []
    self.json_schema = None

    self.generic_quotes = []
    self.quote_objects = []

    self.error_log = []
    self.bad_file_list = []

    try:
      print("Path to schema: %s" % path_to_schema)
      self.set_schema(path_to_schema)
    except:
      #in case user moves file should really program this to at least search descendents for file
      error_msg = "Error opening and reading schema: %s. JSON input will not be supported." % path_to_schema
      print(error_msg)
      self.error_log.append(error_msg)

    arg_count = len(args)

    if arg_count > 0:
      arg_index = 0
      for arg in args:
        """
        Any amount of arguments of type str or list[str] supported
        """
        self.process_arg(arg, arg_index)
        arg_index = arg_index + 1
    else:
      error_msg = "Warning. No files passed into QuoteGenerator but object still created. See member functions for adding strings after object instantiation"
      self.error_log.append(error_msg)
    
    if arg_count > 0 and len(self.files_to_parse) == 0:
      error_msg = "Error: none of the arguments provided were valid files. QuoteGenerator is running but has no quotes to generate. See member functions for adding quotes after instantiation"
      self.error_log.append(error_msg)
    else:
      self.parse_files()

  """
  args: (str, []) 
  description: Determines if arg is str or [].
               Add to self.files_to_parse[] if valid file path for str or any item in [],
  """
  def process_arg(self, arg, arg_index):
    if is_file(arg):
      self.files_to_parse.append(arg)
    elif(isinstance(arg, list)):
      """
      arg[arg_index]==[]
      check for any filepaths...
      """
      list_of_filepaths = arg
      filepaths_index = 0
      #if an arg provided is a list assume it is a list of file paths
      for filepath in list_of_filepaths:
        if is_file(filepath):
          self.files_to_parse.append(filepath)
        else:
          error_msg = "Error: Item at index %d in provided list (args[%d]) is not a valid filepath. Skipping file..." % (filepaths_index, arg_index)
          self.bad_file_list.append(str(filepath))

        filepaths_index = filepaths_index + 1
    else:
      error_msg = "Error: Item provided in args[%d]=%s is not a valid filepath. Skipping file..." % (arg_index, str(arg))
      self.bad_file_list.append(str(arg))


  def set_schema(self, schema):
    try:
      data = get_json_data(schema)
    except:
      raise ValueError("Invalid JSON Error: Failed to initialize schema with provided filepath: \"%s\"." % schema)
    else:
      self.json_schema = data

  def add_file(self, file_path):
    self.files_to_parse.append(file_path)

  #these parse functions should be class members since they're specific to the class. the csv parser might be able to be programmed in a generic manner but probably not worth it
  def parse_files(self):
    for filepath in self.files_to_parse:
      print("parsing this file: %s" % filepath)
      error_occurred = False

      if filepath.endswith('.csv'):
        self.parse_quotes_csv(filepath)
      elif filepath.endswith('.json'):
        if self.json_schema is None:
          error_msg = "JSON file provided but QuoteGenerator currently has no schema to validate it. See class interface for setting schema after instantiation of class. Skipping file \"%s\"..." % filepath
          error_occurred = True
        else:
          json_data = get_json_data(filepath)
          if self.validate_json(json_data, self.json_schema) is False:
            error_msg = "Provided json file, \"%s\", does not follow the specifications of schema \"%s\"" % (filepath, path_to_schema)
            error_occurred = True
          else:
            self.parse_quotes_json(filepath)
      else:
        #splitext..
        error_msg = "Provided file, %s, is not supported." % filepath
        error_occurred = True
      
      if error_occurred:
        print("Error: %s" % error_msg)
      else:
        print("no error")

      if error_occurred:
        self.error_log.append(error_msg)
        self.bad_file_list.append(filepath)

    self.files_to_parse = []


  """
  def parse_file(self, filepath, allowed_extensions):
    if path.exists(filepath):
      if filepath.endswith('csv'):
        parse_quotes_csv(filepath)
      elif filepath.endswith('json'):
        parse_quotes_json(filepath)
      else:
        raise ValueError("File Parser Error, Invalid File Type: file type of %s is currently not supported" % path.splitext(filepath)[1])
  """


  def parse_quotes_json(self, filepath):
    data = get_json_data(filepath)

    for quote in data['quotes']:
      self.generic_quotes.append(quote['quote'])


  def parse_quotes_csv(self, filepath):
    with open(filepath) as f:
      csv_reader = csv.reader(f, delimiter=',')
      for row in csv_reader:
        for column in row:
          print("before: %s" % str(column))
          print("after: %s" % str(column).strip())
          self.generic_quotes.append(str(column.str).strip('"'))

  def add_quote(self, quote):
    self.generic_quotes.append(quote)

  def validate_json(self, json_data, schema):
    """
    validate json file with quote_generator_schema.json
    Rather than this function directly accessing class member for schema, keeping it generic in case more schemas are supported down the line
    """
    try:
        validate(instance=json_data, schema=schema)
    except jsonschema.exceptions.ValidationError as err:
      return False
    else:
      return True
  
  def print_quotes(self):
    for quote in self.generic_quotes:
      print(quote)

  def get_random_quote(self):
    if len(self.generic_quotes) > 0:
      return self.generic_quotes[( random.randint(0, len(self.generic_quotes) - 1 ) )]
    else:
      return "No quotes have been added yet! But here is a default one: “Hard work is worthless for those that don't believe in themselves.” – Naruto Uzumaki."

"""
helper functions
"""
def get_json_data(json_path):
    """This function loads the given schema available"""
    try:
      with open(json_path, 'r') as file:
          data = json.load(file)
          if data == None:
            raise ValueError("Failed to load file \"%s\" as JSON file.")
    except Exception as e:
      raise(e)
    return data

def is_file(filepath_arg):
  """
  checks if argument provided is a valid filepath
  """
  if(isinstance(filepath_arg, str) and path.exists(filepath_arg)):
    return True
  else:
    return False