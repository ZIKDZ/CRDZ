import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')

# Tokens
DISCORD_TOKEN = config['Tokens']['DISCORD_TOKEN']
CR_API_TOKEN = config['Tokens']['CR_API_TOKEN']

# Roles
ROLE_UNDER_5K = int(config['Roles']['ROLE_UNDER_5K'])
ROLE_ABOVE_5K = int(config['Roles']['ROLE_ABOVE_5K'])
ROLE_ABOVE_10K = int(config['Roles']['ROLE_ABOVE_10K'])

# Emojis
EMOJI_LAUGH = config['Emojis']['EMOJI_LAUGH']
EMOJI_TROPHY = config['Emojis']['EMOJI_TROPHY']
EMOJI_SAD = config['Emojis']['EMOJI_SAD']
EMOJI_THINK = config['Emojis']['EMOJI_THINK']
EMOJI_COOL = config['Emojis']['EMOJI_COOL']

# Paths
DATA_FILE = config['Paths']['DATA_FILE']
FONT_PATH = config['Paths']['FONT_PATH']