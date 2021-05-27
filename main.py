import concurrent.futures.thread
from discord_bot_runner.classes.discord_bot_runner import DiscordBotRunner
import discord
import configparser

"""
MODULE_PATH = "./behavior_sets/"
MODULE_NAME = "behavior_sets.bset"
MODULE_BASE = "behavior_sets"
TOKEN = 'ODA5NTc4NzQzNjY4Mjc3MjU0.YCXI9Q.FuiYEDTnoQIN0_dQ8huIqIfdJGs'
#TOKEN = 'ODI5NDIyMDk4NzYxNzc3MjMz.YG35hg.siRgSo7HBEQYQ_cXlo42ywsi9Cs'
"""

def main():
  config = configparser.ConfigParser()
  config.read("./discord_bot_runner/config/tokens.ini")
  TOKEN = config['tokens']['discord']
  intents = discord.Intents.all()
  client = DiscordBotRunner(intents=intents)
  client.run(TOKEN)
  
if __name__ == "__main__":
  main()