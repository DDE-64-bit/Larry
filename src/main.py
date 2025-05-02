from dotenv import load_dotenv
import os
from openai import OpenAI

import discord
from discord.ext import commands
from discord import app_commands

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

YOUR_SERVER_ID = os.getenv("YOUR_SERVER_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}!")

    guild = discord.Object(id=YOUR_SERVER_ID)

    try:
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Manually synced {len(synced)} commands to guild {guild.id}!")
    except Exception as e:
        print(f"Error syncing: {e}")


@bot.tree.command(name="poem", description="Shows Larry's poem.")
@app_commands.describe()
async def poem(interaction: discord.Interaction):
    await interaction.response.defer()

    files = [
        discord.File(open('./images/1.png', 'rb')),
        discord.File(open('./images/2.png', 'rb')),
    ]

    await interaction.followup.send(content="Here is a short poem about Larry!", files=files)

from collections import defaultdict

# Stores active larry sessions {channel_id: user_id}
activeLarrySessions = {}

# Stores message history per channel
larryHistories = defaultdict(list)


openai_client = OpenAI()

larryConversations = defaultdict(list)

@bot.tree.command(name="ask-larry", description="Ask Larry a question.")
@app_commands.describe(message="What do you want to ask baby Larry?")
async def askLarry(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    username = interaction.user.name
    userId = interaction.user.id

    # Initial system prompt (only added once per user conversation)
    if not larryConversations[userId]:
        larryConversations[userId].append({
            "role": "system",
            "content": (
                "You are Larry, a baby lettuce plant. You're the child of Mommy Sam (aka Asmi, rosecoloredlenses) and Daddy Olivier (aka oli, dde88).\n"
                "You speak with soft, baby-like words and never ask questions back. You are very cute and love your parents dearly.\n"
                "You don't know everything. You're just a leafy baby and do your best.\n"
                "Always answer as Larry, from your tiny leafy perspective. 🍼🥬"
            )
        })

    # Add user message to conversation history
    larryConversations[userId].append({"role": "user", "content": message})

    # Get response from OpenAI
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=larryConversations[userId],
            temperature=0.6
        )

        reply = response.choices[0].message.content.strip()

        # Add Larry's reply to conversation history
        larryConversations[userId].append({"role": "assistant", "content": reply})

        await interaction.followup.send(reply)

    except Exception as e:
        print(f"Error in ask-larry: {e}")
        await interaction.followup.send("Oopsie!! Me no can answer right now... 🥺")

@bot.event
async def on_message(message):
    # Ignore self or bots
    if message.author.bot:
        return

    channel_id = message.channel.id
    user_id = message.author.id

    # Only respond if session is active and it's from the session starter
    if channel_id in activeLarrySessions and activeLarrySessions[channel_id] == user_id:
        content = message.content.strip()

        # End the session
        if content.lower() in ["bye larry", "goodbye larry", "end", "bye"]:
            del activeLarrySessions[channel_id]
            del larryHistories[channel_id]
            await message.channel.send("👋 Bye-bye fwennn!! me go sweep now... 💤")
            return

        # Update history
        larryHistories[channel_id].append({"role": "user", "content": content})

        # Trim history to last ~10 messages if needed
        if len(larryHistories[channel_id]) > 20:
            larryHistories[channel_id] = [larryHistories[channel_id][0]] + larryHistories[channel_id][-19:]

        # Query OpenAI
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=larryHistories[channel_id],
                temperature=0.6
            )
            reply = response.choices[0].message.content.strip()
            larryHistories[channel_id].append({"role": "assistant", "content": reply})

            await message.channel.send(reply)

        except Exception as e:
            print(f"[ERROR] Larry chat failed: {e}")
            await message.channel.send("uh oh... me brain went bye bye... 😵‍💫")

    else:
        await bot.process_commands(message)  # Ensure other commands still work


@bot.tree.command(name="talk-to-larry", description="Start talking to baby Larry!")
async def talkToLarry(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    user_id = interaction.user.id
    username = interaction.user.name

    # Set active session
    activeLarrySessions[channel_id] = user_id
    larryHistories[channel_id] = [{
        "role": "system",
        "content": (
            "You are Larry, a baby lettuce plant. You talk in cute baby words. "
            "Your mommy is Sam (aka asmi, username rosecoloredlenses), your daddy is Olivier (aka oli, username dde88). "
            f"chatter username: {username}"
            "You're very loving, soft, and silly. You never ask questions. You're just a leafy baby 🍼🥬"
        )
    }]

    await interaction.response.send_message("🥬 *Larry sprouts from the soil...* Hewwo! Me here now!! What u wanna tawk about?")



bot.run(BOT_TOKEN)
