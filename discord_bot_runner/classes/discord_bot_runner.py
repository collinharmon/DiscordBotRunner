from behavior_sets.behavior_set import BehaviorSet
import os
import sys
import requests
import discord_bot_runner.utils.file_utils as file_utils
import discord
import asyncio
import queue
import json
import time
from jsonschema import validate
from importlib import import_module, reload
import inspect
from os import listdir
from os.path import isfile, join
import ntpath
import configparser

#below two path and module is with respect to main.py environment
B_SETS_ROOT_DIR = "./behavior_sets"
B_SETS_ROOT_MODULE = "behavior_sets"

SLEEP_DURATION = 5e-2  # 50 ms sleep


class DiscordBotRunner(discord.Client):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.mod_path_to_mod = {} #k=path to py mod v=module
    self.behavior_sets = {}  #k=('bset_name'),v=(bset_instance)
    self.message_queue = queue.Queue() #Parent queue. Every BehaviorSet used will send it's output to this queue, for parent thread (DiscordBotRunners) to handle. BehaviorSet responses are in JSON
    self.thread_count = 0

    """
    specificity of channel/user breadth managed by below data structs
    """
    self.b_set_managers = {} #k=(bset_name), v=(BehaviorSetManager instance)

    self.userchannel_ids = {}   #k=(user_id, channel_id),v=(behavior_set) behavior_set usage is solely dependent on who is allowed to use it and what channels are allowed to serve it

    self.guild_ids = []
    self.user_ids = []
    self.channel_ids = []

    #admin
    self.admin_id = None

    self.error_log   = [] #for any errors
    self.admin_log   = [] #for admin related actions 
    self.general_log = [] #for general information to log to discord

    self.log_enabled = False #by default logs are not relayed to discord. enable via admin

    #init admin
    config = configparser.ConfigParser()
    config.read("./discord_bot_runner/keys/admin.ini")
    self.ADMIN = config['admin']['user_id']
    #Load any pre-existing behavior sets under B_SETS_ROOT_DIR. Can be empty
    self.load_and_run_modules(B_SETS_ROOT_DIR, False)
    
  async def on_ready(self):
    """
    Parameters  -
    Description - Create asyncio loop for monitoring the BehaviorSet message queue. Initialize class data structures with guilds, channels, users, and admin ID
    """
    print('Logged in as')
    self.loop.create_task(self.check_queue())
    print(self.user.name)
    print('------')
    message = "\nBehaviorSets Available:"
    for b_set_name in self.behavior_sets:
      message = message + "\n- %s" % b_set_name
    if len(self.error_log) > 0:
      message = message + "\nInit Errors:"
      for msg in self.error_log:
        message = message + "\n%s" % msg
      self.error_log = []

    #get every guild ID, every channel ID, and every user ID
    for guild in self.guilds:
      self.guild_ids.append(guild.id)
      print(message)
      for member in guild.members:
        self.user_ids.append(member.id)
        if (member.display_name + "#" + member.discriminator) == self.ADMIN:
          self.admin_id = member.id
      for channel in guild.channels:
        self.channel_ids.append(int(channel.id))

    if len(self.guild_ids) == 0:
      print("Critical Error: This bot is not registered with any Discord guilds.")
      await self.exit_bot()
    
  async def on_member_join(self, member):
    """
    Parameters  -
    Description - Upon new member joining a monitored Guild, add to self.user_ids
    """
    self.user_ids.append(member.id)

  async def on_guild_channel_create(self, channel):
    """
    Parameters  -
    Description - Upon a new channel creation on a monitored Guild, add to self.channel_ids
    """
    self.channel_ids.append(int(channel.id))

  async def on_message(self, message):
    """
    Parameters  - message: Discord message to be inspected and read.
    Description - Determine if message is from admin, and if so conforms to valid admin command (see README). Else if the author of the message
                  and the channel from which it came is registered on a BehaviorSet then obtain the message queue of the corresponding BehaviorSet
                  and push the message for the BehaviorSet thread to handle.
    """
    user_id = message.author.id
    username = message.author.display_name + "#" + message.author.discriminator

    if message.author == self.user:
      return

    if user_id == self.admin_id:
      results = None
      if message.content == "./admin exit":
        exit_msg = "Master says to exit now. So good bot does, master says so. <@%s>" % self.admin_id
        await self.exit_bot(exit_msg)
      elif message.content.startswith("./admin"):
        self.handle_admin_cmd(message)
        if len(self.general_log) > 0:
          for msg in self.general_log:
            await message.channel.send(msg)
          self.general_log = []
        if self.log_enabled is True:
          for result_msg in self.admin_log:
            await message.channel.send(result_msg)
          self.admin_log = []
    try:
      b_set = self.userchannel_ids[(user_id, message.channel.id)]
    except:
      pass
    else:
      q = b_set.get_queue()
      q.put_nowait(message)

      #self.admin_queue.put(message.content)


  async def check_queue(self):
    """
    Parameters  -
    Description - This function get invoked periodically to check if any of the child threads (BehaviorSet instantiations) have pushed 
                  a message up onto the DiscordBotRunner's message queue. If so determine the format and content of the message and send it
                  to the Discord channel it originated from.
    """
    while True:
      try:
        item = self.message_queue.get_nowait()
      except:
        pass
      else:
        try:
          json_data = json.loads(item, strict=False)
        except Exception as e:
          print(str(e))
          continue
        channel = discord.utils.get(self.get_all_channels(), id=json_data['channel'])
        data_type = json_data['data_type']
        if data_type == "text_message":
          await channel.send(json_data['data'])
        elif data_type == "upload":
          file_path = json_data['file_path']
          await channel.send(file=discord.File(file_path))
        elif data_type == "text/upload":
          file_path = json_data['file_path']
          await channel.send(file=discord.File(file_path))
          await channel.send(json_data['data'])

        """
        for guild in self.guilds:
          message = "Parent got: %s" % str(item)
          await guild.text_channels[-1].send(message)
        print("Parent got: %s" % str(item))
        """
      await asyncio.sleep(SLEEP_DURATION)

  
  def handle_admin_cmd(self, message):
    """
    Parameters  - message: str of admin command to be parsed
    Description - Expects format "./admin <op> <args>"
                  valid operations (op) are: register, remove, show, load, and log (enable/disable)
                  The message results of the commands are inserted into self.admin_log.
                  See README for further details 
    """
    cmd = message.content
    #get admin token and cmd token, leave args as one string
    cmd_tokens = cmd.split(" ", 2)
    num_tokens = len(cmd_tokens)
    if num_tokens < 2:
      self.admin_log.append("See README for Admin commands")
    else:
      op = cmd_tokens[1].strip()
      if op == "register" or op == "reg":
        if num_tokens == 3:
          self.admin_log.extend(self.handle_register_cmd(cmd_tokens[2].strip(), False))
        else:
          self.admin_log.append("register command must have at least one argument")
      elif op == "remove" or op == "rm":
        if num_tokens == 3:
          self.admin_log.extend(self.handle_register_cmd(cmd_tokens[2].strip(), True))
        else:
          self.admin_log.append("remove command must have at least one argument")
      elif op == "show":
        if num_tokens != 2:
          self.general_log.extend(self.run_show_cmd(cmd_tokens[2].strip()))
        else:
          self.general_log.extend(self.run_show_cmd(""))
      elif op == "load":
        if num_tokens != 2:
          self.admin_log.append("Ignoring add command arguments. add command does not support arguments (See README).")
        if message.attachments:
          self.admin_log.extend(self.handle_module_upload_cmd(message.attachments))
        else:
          self.admin_log.append("add command expects at least one attachment.")
      elif op == "log":
        if num_tokens != 3:
          self.admin_log.append("log command expects exactly one argument, enable/disable.")
        else:
          if cmd_tokens[2].strip() == "enable":
            self.log_enabled = True
            self.admin_log.append("Successfully enabled logging")
          elif cmd_tokens[2].strip() == "disable":
            self.log_enabled = False
            self.admin_log.append("Successfully disabled logging")
          else:
            self.admin_log.append("Invalid argument to log command.")
      else:
        self.admin_log.append("Invalid command. \"%s\", is not a recognized command." % op)



  def handle_register_cmd(self, cmd_args, remove_entry):
    """
    Parameters  - cmd_args: the users, channels and/or behavior sets to be registered/removed
                - remove_entry: boolean, True if to unregister 
    Description - Register provided users and channels on provided behavior set (derived from cmd_args).
    """
    results_log = []

    l_and_r_value = cmd_args.split("on")

    if len(l_and_r_value) != 2:
      results_log.append("Invalid use of cmd \"register\", no \"on\" operation found.")
      return results_log

    l_val = l_and_r_value[0].strip() #channels and/or users to register
    r_val = l_and_r_value[1].strip() #b_set_name

    operand_strs = l_val.split(',')
    if len(operand_strs) == 1 and len(l_val.split(" ")) > 1:
      results_log.append("register/remove command operands must be comma separated.")
      return results_log

    try:
      b_set = self.behavior_sets[r_val]
      b_set_manager = self.b_set_managers[r_val]
    except:
      results_log.append("Invalid r-val: %s - nonexistent BehaviorSet" % r_val)
      return results_log
    
    for operand_str in operand_strs:
      operand_str = operand_str.strip()
      if operand_str.startswith('<#'): #channel
        results_log.append(self.handle_channel_reg(int(operand_str[2:-1]), b_set, b_set_manager, remove_entry))
      elif operand_str.startswith("<@"): #user
        results_log.append(self.handle_user_reg(int(operand_str[3:-1]), b_set, b_set_manager, remove_entry))
      elif operand_str == "#all":
        for channel in self.channel_ids:
          results_log.append(self.handle_channel_reg(channel, b_set, b_set_manager, remove_entry))
      elif operand_str == "@all":
        for user in self.user_ids:
          results_log.append(self.handle_user_reg(user, b_set, b_set_manager, remove_entry))
      else:
        results_log.append("Operand: %s is invalid." % operand_str)

    return results_log

  def handle_channel_reg(self, channel_id, b_set, b_set_manager, remove_channel):
    """
    Parameters  - channel_id: unique str id representing channel on guild
                - b_set: BehaviorSet instance for channel_id to register on
                - b_set_manager: BehaviorSetManager responsible for handling passed in b_set
                - remove_channel: boolean, True to remove channel registration
    Description - Provided discord channel ID register channel with provided behavior set and create (user_id, channel_id) pairs to
                  be inserted into self.userchannel_ids. If remove_channel is True then remove every (user_id, channel_id) pair in
                  self.userchannel_ids wherein the channel_id is equal to the one passed in as an argument.
    """
    result_msg = ""
    if channel_id not in self.channel_ids:
      result_msg = "Channel ID %d does not exist." % channel_id
      print(result_msg)
      return result_msg
    
    if b_set_manager.is_channel_registered(channel_id):
      if remove_channel is True:
        b_set_manager.remove_channel(channel_id)
        result_msg = "<#%d> has been removed from BehaviorSet: %s" % (channel_id, b_set_manager.get_name())
        print(result_msg)
      else:
        result_msg = "<#%d> has already been registered with %s" % (channel_id, b_set_manager.get_name())
        print(result_msg)
        return result_msg
    elif remove_channel is True:
      result_msg = "Cannot remove channel <#%d>. It is not registered with BehaviorSet: %s." % (channel_id, b_set_manager.get_name())
      print(result_msg)
      return result_msg

    user_ids = b_set_manager.get_users()
    for user_id in user_ids:
      #if remove then disassociate each bset from (channel,user) pair
      if remove_channel is True:
        self.userchannel_ids.pop((user_id, channel_id), None)
      else:
        #register each bset user with new channel
        self.userchannel_ids[(user_id, channel_id)] = b_set 

    if remove_channel is False:
      b_set_manager.add_channel(channel_id)
      result_msg = "Successfully registered <#%d> on BehaviorSet: %s" % (channel_id, b_set_manager.get_name())

    return result_msg

  def handle_user_reg(self, user_id, b_set, b_set_manager, remove_user):
    """
    Parameters  - user_id: unique str id representing user on guild
                - b_set: BehaviorSet instance for channel_id to register on
                - b_set_manager: BehaviorSetManager responsible for handling passed in b_set
                - remove_user: boolean, True to remove user registration
    Description - Provided discord user ID register user with provided behavior set and create (user_id, channel_id) pairs to
                  be inserted into self.userchannel_ids. If remove_user is True then remove every (user_id, channel_id) pair in
                  self.userchannel_ids wherein the user_id is equal to the one passed in as an argument.
    """
    result_msg = ""
    if user_id not in self.user_ids:
      result_msg = "User ID %d is not found to be associated with any users here." % user_id
      return result_msg

    if b_set_manager.is_user_registered(user_id) is True:
      if remove_user is True:
        b_set_manager.remove_user(user_id)
        result_msg = "<@%d> has been removed from BehaviorSet: %s" % (user_id, b_set_manager.get_name())
      else:
        result_msg = "<@%d> has already beed registered with %s" % (user_id, b_set_manager.get_name())
        return result_msg
    elif remove_user is True:
      result_msg = "Cannot remove user <@%d>. User is not registered with BehaviorSet: %s." % (user_id, b_set_manager.get_name())
      return result_msg

    channel_ids = b_set_manager.get_channels()
    for channel_id in channel_ids:
      if remove_user is True:
        self.userchannel_ids.pop((user_id, channel_id), None)
      else:
        #register each bset channel with new user
        self.userchannel_ids[(user_id, channel_id)] = b_set
    if remove_user is False:
      b_set_manager.add_user(user_id)
      result_msg = "Successfully registered user <@%d> on BehaviorSet: %s" % (user_id, b_set_manager.get_name())
      
    return result_msg

  def run_show_cmd(self, cmd_args):
    """
    Parameters  - cmd_args: either empty string or name of valid behavior set
    Description - Provided no command arguments then return list of strings of all available running BehaviorSets. Else if single 
                  command argument provided is the name of a valid BehaviorSet then return list of strings of channels and users that are registered on them.
    """
    b_set_description = []
    results = []
    
    #cmd was: './admin show'
    if cmd_args == "":
      b_set_description.append("***Available BehaviorSets***")
      for b_set_name, b_set in self.behavior_sets.items():
        b_set_description.append("- %s\n" % b_set_name)
      return b_set_description

    args = cmd_args.split(" ")
    #if arg provided must only be 1, the bset name
    if len(args) != 1:
      results.append("Invalid use of \"show\" cmd")
      return results
    

    b_set_name = cmd_args.strip()
    try:
      b_set_manager = self.b_set_managers[b_set_name]
    except:
      results.append("Invalid r-val: %s" % b_set_name)
      return results
    else:
      b_set_description.append("***\"%s\"***" % b_set_name)
      b_set_channels = b_set_manager.get_channels()
      for channel in b_set_channels:
        b_set_description.append("Channel: <#%s>" % channel)
      b_set_users = b_set_manager.get_users()
      for user in b_set_users:
        b_set_description.append("User: <@%s>" % user)

    return b_set_description

  def handle_module_upload_cmd(self, attachments):
    """
    Parameters  - attachments: list of file attachments provided along with the discord message
    Description - Obtains the url of each attachment and passes it into self.handle_module_upload to upload discord user provided python module
    """
    results_log = []
    for attachment in attachments:
      results_log.extend(self.handle_module_upload(attachment.url))
    return results_log

  async def exit_bot(self, exit_message):
    """
    Parameters  - exit_message: str
    Description - Notifies guilds of its exit then logs out 
    """
    if exit_message is None:
      exit_message = "Bot is exiting!"
    for guild in self.guilds:
      await guild.text_channels[-1].send(exit_message)
    await self.logout()

  def load_and_run_modules(self, package, reload_mods):
    """
    Parameters: - package: root folder to scan
                - reload_mods: boolean to determine if every module in package should be reloaded
    Description - will scan B_SETS_ROOT_DIR for python files and will import them. Each module imported will be inspected and if it is determined
                  the module contains a member of type subclass of BehaviorSet, then it will save the class object in a list. It will instantiate 
                  each BehaviorSet subclass as a new thread and save a reference to self.behavior_sets. A BehaviorSetManager object will be instantiated
                  for each BehaviorSet made. If reload_mods is True then every module already loaded will get reloaded using importlib's reload.
                  Existing BehaviorSet instantiations will be destroyed and replaced by new instances.
    """
    only_files = [f for f in listdir(package) if isfile(join(package, f))]
    py_files = []
    for f in only_files:
      if f.endswith('.py'):
        py_files.append(f)
      else:
        self.error_log.append("Provided file, %s, is not a Python file. Ignoring..." % f)

    bset_objs = {}
    for py_file in py_files:
      mod_name = B_SETS_ROOT_MODULE + ".%s" % path_leaf(py_file)[:-3]

      #below function will import and inspect mod_name, if mod contains member of type subclass BehaviorSet, then save in list.
      (name, obj) = self.is_class_bset_script(mod_name, reload_mods)
      if obj:
        bset_objs[name] = obj

    for bset_name, bset in bset_objs.items():
      #now we instantiate the bsets after all the imports--in case they have dependencies on external mods in package
      if bset_name in self.behavior_sets:
        #we already have an instance of this class derived from previous modules, skip
        continue
      else:
        child_queue = queue.Queue()
        b_set_instance = bset(thread_ID=self.thread_count, thread_name="%s" % bset_name + str(self.thread_count), event_queue=child_queue, parent_queue=self.message_queue) 
        self.behavior_sets[bset_name] = b_set_instance
        if reload_mods:
          #re-register channels/users with newest bset instance
          registered_channels = self.b_set_managers[bset_name].get_channels()
          registered_users = self.b_set_managers[bset_name].get_users()
          for channel in registered_channels:
            for user in registered_users:
              if(user, channel) in self.userchannel_ids:
                self.userchannel_ids[(user, channel)] = b_set_instance
        else:
          self.b_set_managers[bset_name] = self.BehaviorSetManager(bset_name)
        b_set_instance.start()
        self.thread_count = self.thread_count + 1

  def is_class_bset_script(self, mod_abs_path, reload_mods):
    """
    Parameters: - mod_abs_path: str path to the python file module
                - reload_mods: boolean
    Description - imports module and if module contains a member of type subclass, BehaviorSet then return the class object (does not instantiate)
    """
    mod = None
    if reload_mods and mod_abs_path in self.mod_path_to_mod:
      mod = self.mod_path_to_mod[mod_abs_path]
      mod = reload(mod)
      self.mod_path_to_mod[mod_abs_path] = mod
    else:
      mod = import_module(mod_abs_path)
      self.mod_path_to_mod[mod_abs_path] = mod
    for name, obj in inspect.getmembers(mod):
      if inspect.isclass(obj):
        if issubclass(obj, BehaviorSet) or name in self.behavior_sets:
          if name != "BehaviorSet":
            if reload_mods:
              del self.behavior_sets[name]
            return (name, obj)
    return ("", None)

  def handle_module_upload(self, url):
    """
    Parameters  - url: url string referencing python file
    Description - Retrieve text from provided url and write and sanitize to new python file in B_SETS_ROOT_DIR.
                  Then load the module. If module already exists then reload modules.
    """
    results = []
    try:
      r = requests.get(url = url)
    except requests.exceptions.RequestException as e:
      results.append("Failed requesting url \"%s\". Could be a problem with discord so keep trying. If persists contact <@%s>" % (url, self.admin_id))
      return
    else:
      attachment_name = path_leaf(url)
      reload_mods = False
      file_fullpath = B_SETS_ROOT_DIR + "/%s" % attachment_name
      if os.path.exists(file_fullpath):
        os.remove(file_fullpath)
        reload_mods = True
      
      lines = []
      line = ""
      #sanitize content retrieved from requested url
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

      import io
      with io.open(file_fullpath, "w", encoding="utf-8") as f:
        f.write(''.join(lines))

      try:
        self.load_and_run_modules(B_SETS_ROOT_DIR, reload_mods)
      except Exception as e:
        results.append("The file provided was an invalid Python Module")
        print(str(e))
      else:
        results.append("Successfully loaded module %s." % attachment_name)
      
    return results
  
  class BehaviorSetManager():
    """
    Class Description - Helper class for managing the guilds, channels and users a given BehaviorSet may be registered with.
    """
    def __init__(self, name):
      super().__init__()
      self.guilds = []
      self.channels = []
      self.users = []
      try:
        self.name = name
      except:
        pass


    def add_user(self, user_id):
      self.users.append(user_id)

    def add_channel(self, channel_id):
      self.channels.append(channel_id)

    def add_guild(self, guild_id):
      self.guilds.append(guild_id)
    
    def get_users(self):
      return self.users

    def get_channels(self):
      return self.channels

    def get_guilds(self):
      return self.guilds
    
    def get_name(self):
      return self.name
    
    def is_channel_registered(self, channel_id):
      if channel_id in self.channels:
        return True
      else:
        return False
    
    def is_user_registered(self, user_id):
      if user_id in self.users:
        return True
      else:
        return False
    
    def is_guild_registered(self, guild_id):
      if guild_id in self.guilds:
        return True
      else:
        return False
    
    def remove_channel(self, channel_id):
      if channel_id in self.channels:
        self.channels.remove(channel_id)

    def remove_user(self, user_id):
      if user_id in self.users:
        self.users.remove(user_id)

def path_leaf(path):
  head, tail = ntpath.split(path)
  return tail or ntpath.basename(head)