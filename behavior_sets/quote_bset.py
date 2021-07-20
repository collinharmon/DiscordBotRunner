from .behavior_set import BehaviorSet
import requests
import sys
import sys
from os import path
import os
import ntpath
import csv
import json
from jsonschema import validate
import discord
from .quotes_generator import QuoteGenerator


MAX_WAIT = 1000

class QuotesBehaviorSet(BehaviorSet):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    quotes_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "/data/quotes.json")
    print("The quotes file: %s" % quotes_file)
    self.quote_generator = QuoteGenerator(quotes_file)

  def handle_discord_event_loop(self):
    #while soon
    while True:
      try:
        item = self.event_queue.get(block=True, timeout=MAX_WAIT)
      except:
        continue
      else:
        if item.content == "./quotes get":
          quote = self.quote_generator.get_random_quote()
          tokens = quote.split("<@>")
          message = ""
          if len(tokens) > 1:
            user_str = "<@%d>" % item.author.id
            message = message + tokens[0].strip() + " " + user_str + " " + tokens[1]
          else:
            message = quote 

          print(message)
          json_obj = '{"channel":%d, "data_type":"%s", "data":"%s"}' % (item.channel.id, "text_message", message)
          #x =  '{ "channel":, "age":30, "city":' + '"New York"}'
        elif item.content.startswith("./quotes add"):
          tokens = item.content.split("./quotes add")
          message = None
          if len(tokens) == 2:
            self.quote_generator.add_quote(tokens[1])
            message = "Successfully added quote"
          else:
            message = "Failed to add quote"

          json_obj = '{"channel":%d, "data_type":"%s", "data":"%s"}' % (item.channel.id, "text_message", message)
        elif item.content.startswith("./quotes") and item.attachments:
          if not os.path.exists(os.path.dirname(os.path.realpath(__file__)) + '//quote_files'):
            os.makedirs(os.path.dirname(os.path.realpath(__file__)) + '//quote_files')
          quote_file_url = item.attachments[0].url
          try:
            #fudge url here to verify behavior
            r = requests.get(url = quote_file_url)
          except requests.exceptions.RequestException as e:
            message = "Bad URL. Contact Admin."
            json_obj = '{"channel":%d, "data_type":"%s", "data":"%s"}' % (item.channel.id, "text_message", message)
            self.parent_queue.put(json_obj)
            continue

          base_path = os.path.dirname(os.path.realpath(__file__)) + "//quote_files"
          
          file_name = path_leaf(quote_file_url)
          full_path = base_path + "//" + file_name
          if os.path.exists(full_path):
            os.remove(full_path)
          
          file = open(full_path, "w")
          lines = []
          line = ""
          for char in r.text:
            if char != "\n":
              line = line + char
            else:
              if line == "":
                continue
              else:
                lines.append(line)
                line = ""
          if line != "":
            lines.append(line)
          file.write(''.join(lines))
          file.close()
          self.quote_generator.add_file(full_path)
          self.quote_generator.parse_files()
          message = "Successfully uploaded and parsed provided file, %s" % file_name
          json_obj = '{"channel":%d, "data_type":"%s", "data":"%s"}' % (item.channel.id, "text_message", message)
        else: 
          continue
          #x =  '{ "channel":, "age":30, "city":' + '"New York"}'
        self.parent_queue.put(json_obj)

def path_leaf(path):
  head, tail = ntpath.split(path)
  return tail or ntpath.basename(head)