import concurrent.futures.thread
from discord_bot_runner.classes.discord_bot_runner import DiscordBotRunner
import discord
import configparser

def main():
  config = configparser.ConfigParser()
  config.read("./discord_bot_runner/keys/tokens.ini")
  TOKEN = config['tokens']['discord']
  intents = discord.Intents.all()
  client = DiscordBotRunner(intents=intents)
  client.run(TOKEN)
  
if __name__ == "__main__":
  main()
