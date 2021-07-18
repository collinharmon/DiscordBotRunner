import concurrent.futures.thread
from discord_bot_runner.classes.discord_bot_runner import DiscordBotRunner
import discord
import configparser
import sys

def main():
  config = configparser.ConfigParser()
  config_files = [arg for arg in sys.argv if arg.endswith('.ini')]
  if len(config_files) < 1:
    print("Error: No .ini file for the Discord token(s) were provided as an argument.")
    return

  clients = []
  for cf in config_files:
    config.read(cf)
    try:
      token = config['tokens']['discord']
    except Exception as e:
      print("KeyError: Invalid .ini file provided.")
      continue
    else:
      intents = discord.Intents.all()
      client = DiscordBotRunner(intents=intents)
      client.run(token)
      clients.append(client)
  
if __name__ == "__main__":
  main()
