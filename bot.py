import requests
import discord
import os
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from discord.app_commands import Choice
from openai import OpenAI
from PIL import Image
import csv
import aiohttp
import base64

openai_client = OpenAI(api_key="<INSERT OPENAI_API_KEY HERE>")

# Initialize Discord bot intents with default settings, including basic events like join/leave.
intents = discord.Intents.default()

# Enable the bot to read message content, necessary for responding to user messages.
intents.message_content = True

# Create a bot instance with a command prefix '!', ready to handle commands and intents.
client = commands.Bot(command_prefix="!", intents=intents)


# This is a slash command that calls the GPT-3 API to generate a response and sends it back to the user on discord
@client.tree.command(name='query_gpt', description='Ask GPT a question')
@app_commands.describe(query = "Ask GPT a question")
@app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id)) # This prevents people from spamming the command. They can only use it once every 60 seconds.
async def query_gpt(interaction: discord.Interaction, query: str):
    
    completion = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": query}
        ],
    )
    
    response = completion.choices[0].message.content
    await interaction.response.send_message(response)
    

# Helper function to encode images to base64.
# Used to send images to the GPT-4 Vision API.
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# How to generate memes from images.
# This sends a meme caption to the user on discord when they upload an image and type "memeify" in the message.
@client.event
async def on_message(message):
  
  if message.author == client.user:
        return
  
  if message.attachments and message.content.startswith('memeify') or message.content.startswith('Memeify'):
    # Get the image from the message.
    image_url = message.attachments[0].url
    
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer <OPENAI_API_KEY>" # Replace this with your OpenAI API key.
                }

                payload = {
                    "model": "gpt-4-vision-preview",
                    "messages": [
                    {
                        "role": "user",
                        "content": [
                        {
                            "type": "text",
                            "text": "Act as a professional at generating funny meme captions given images. Generate 1 meme caption for the image attached. Make the caption extremely specific to what's in the image. Output only the meme caption and nothing else."
                        },
                        {
                            "type": "image_url",
                            "image_url": image_url
                        }
                        ]
                    }
                    ],
                    "max_tokens": 300
                }
                try: 
                    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

                    meme_caption = response.json()['choices'][0]['message']['content']

                    print("MEME CAPTION:", meme_caption)
                    
                    await message.channel.send(meme_caption)

                except Exception as e:

                    return 



# Decorator to register an error handler for application command errors in the bot
@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    # Check if the error is a command cooldown error
    if isinstance(error, app_commands.CommandOnCooldown):
        # Send an ephemeral message informing the user of the cooldown with the remaining time
        await interaction.response.send_message(f"Please wait for {round(error.retry_after, 0)} seconds before running the command again!", ephemeral=True)
    else:
        # [Optional: Modify this part to handle other types of errors appropriately]
        # Currently, sends the same cooldown message for all types of errors, which may not be intended
        await interaction.response.send_message(f"Please wait for {round(error.retry_after, 0)} seconds before running the command again!", ephemeral=True)



# This is the code that runs the bot.
# Make sure to replace the DISCORD_TOKEN below with your bot's token.
# Get your bot token from the discord developer portal: https://discordapp.com/developers/applications/
# Use these articles to help you get started:
#  https://www.writebots.com/discord-bot-token/
#  https://realpython.com/how-to-make-a-discord-bot-python/

client.run('<INSERT YOUR DISCORD_TOKEN HERE>')
