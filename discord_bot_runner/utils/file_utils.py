import json

def get_json_date(json_path):
  try:
    with open(json_path, 'r') as file:
        data = json.load(file)
        if data == None:
          raise ValueError("Failed to load file \"%s\" as JSON file.")
  except Exception as e:
    raise(e)
  return data