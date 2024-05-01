print("Booting up...")

# Modules
from discord.ext import commands
import discord
import sys
import os
import random
import asyncio
import sqlite3
import datetime

# Do not modify the below statement, this is
# to check whether this REPL has been forked
# or not. Feel free to remove these checks if
# you know what you are doing.
if os.getenv('REPL_ID') == '9600d51f-ae09-41bb-a923-5a8d3d772e07':
  raise sys.exit('You must fork this REPL in order to work.\n')

# Secret
#        (⛔ DO NOT PUT YOUR DISCORD BOT'S TOKEN HERE! ⛔)
my_secret = "token"  # Follow these examples for better understanding: https://pbs.twimg.com/media/Fm9A39vXEAEhV7R?format=png  (legacy screenshot: https://pbs.twimg.com/media/Fe5Ik9eXkAAr20r?format=png)

# Set up some intents
intents = discord.Intents.default()
intents.message_content = True

# Variables
bot = commands.Bot(
  intents            = intents, # Required
  command_prefix     = "!",
  case_insensitive   = True,  # e.g. !hElP
  strip_after_prefix = True, # e.g. ! help
  help_command       = None
)

# Connect to the database
conn = sqlite3.connect('user_data.db')
c = conn.cursor()

# Create a table to store user data if it doesn't exist already
c.execute('''CREATE TABLE IF NOT EXISTS user_points
             (user_id INTEGER PRIMARY KEY, points INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS user_daily
             (user_id INTEGER PRIMARY KEY, last_claimed TEXT)''')
conn.commit()

# Function to update user points in the database
def update_user_points(user_id, points):
    c.execute("INSERT OR REPLACE INTO user_points (user_id, points) VALUES (?, ?)", (user_id, points))
    conn.commit()

# Function to retrieve user points from the database
def get_user_points(user_id):
    c.execute("SELECT points FROM user_points WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        return row[0]
    else:
        return None

# Function to retrieve the leaderboard from the database
def get_leaderboard():
    c.execute("SELECT * FROM user_points ORDER BY points DESC")
    return c.fetchall()

# Function to handle the daily command
@bot.command()
async def daily(ctx):
    last_claimed = get_last_claimed(ctx.author.id)
    today = datetime.date.today()

    # Check if the user has already claimed their daily points for the day
    if last_claimed is not None and last_claimed.date() == today:
        await ctx.send("You have already claimed your daily points for today.")
        return

    # Add 30 points to the user's balance
    current_points = get_user_points(ctx.author.id)
    if current_points is None:
        current_points = 0
    update_user_points(ctx.author.id, current_points + 30)

    # Update the last claimed timestamp
    update_last_claimed(ctx.author.id, today)

    # Send the result in an embed message
    embed = discord.Embed(title="Daily Points Claimed", description="You have claimed your daily points. You received 30 points!", color=0x00ff00)
    await ctx.send(embed=embed)

# Function to retrieve the last claimed timestamp from the database
def get_last_claimed(user_id):
    c.execute("SELECT last_claimed FROM user_daily WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        return datetime.datetime.fromisoformat(row[0])
    else:
        return None

# Function to update the last claimed timestamp in the database
def update_last_claimed(user_id, last_claimed):
    c.execute("INSERT OR REPLACE INTO user_daily (user_id, last_claimed) VALUES (?, ?)", (user_id, last_claimed.isoformat()))
    conn.commit()

# Gateway Events
@bot.event
async def on_ready():
    print(f"✅ {bot.user}")

# Bot Commands
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! `{bot.latency:.2f}ms`")

@bot.command()
async def peng(ctx):
    await ctx.send(f"Give me a sign")

# Update the guess command to use the database
@bot.command()
async def guess(ctx):
    randomguess = [
        {"url": "https://media.discordapp.net/attachments/1227527405779025923/1234866478218608781/20240425_233222251.jpg?ex=66324a87&is=6630f907&hm=b37e4d8670c11a383a0aa96f1d33d221e3c197cf3ef6d1776ae2b8e6096563f0&", "name": "Bling Bang Born"},
        {"url": "https://media.discordapp.net/attachments/1227527405779025923/1234866477794852994/20240425_233626454.jpg?ex=66324a87&is=6630f907&hm=43cb8f8aab39ff7bbe6a2a788af3fc822d841b539412e867ef768b5be98cffff&", "name": "Nevada"},
        {"url": "https://example.com/image3.jpg", "name": "image3"},
        # Add more entries as needed
    ]
    entry = random.choice(randomguess)
    correct_name = entry["name"]
    
    embed = discord.Embed(title="Guess the Picture!", description="You have 10 seconds to guess.", color=0x00ff00)
    embed.set_image(url=entry["url"])
    message = await ctx.send(embed=embed)
    
    try:
        user_guess = await bot.wait_for('message', timeout=10.0, check=lambda message: message.author == ctx.author)
    except asyncio.TimeoutError:
        await ctx.send("Time's up! You didn't guess in time. The correct name was: " + correct_name)
        return
    
    if user_guess.content.lower() == correct_name.lower():
        await ctx.send("Congratulations! You guessed it right.")
        current_points = get_user_points(ctx.author.id)
        if current_points is None:
            current_points = 0
        update_user_points(ctx.author.id, current_points + 10)
    else:
        await ctx.send(f"Sorry, that's not the correct name. The correct name was: {correct_name}")

# Update the balance command to use the database
@bot.command()
async def balance(ctx):
    points = get_user_points(ctx.author.id)
    if points is not None:
        await ctx.send(f"Your balance: {points} points")
    else:
        await ctx.send("You don't have any points yet.")

# Update the leaderboard command to use the database
@bot.command()
async def leaderboard(ctx):
    leaderboard = get_leaderboard()
    if not leaderboard:
        await ctx.send("The leaderboard is empty.")
        return
    
    leaderboard_msg = "Leaderboard:\n"
    for idx, (user_id, points) in enumerate(leaderboard, start=1):
        user = bot.get_user(user_id)
        if user:
            leaderboard_msg += f"{idx}. {user.display_name}: {points} points\n"
    
    await ctx.send(leaderboard_msg)

# Close the database connection when the bot exits
@bot.event
async def on_disconnect():
    close_db_connection()

# Checks if the Secret exists in the Secrets tab
_error_message = f"[31m\n\nI could not find any secret named\x20[0m[41m\x20{my_secret}\x20[0m[31m\x20in the Secrets tab.\n\n[90m[!][0m[31m\x20Here are some links that might help you:\n\t[0m-\x20🔗\x20[34mhttps://pbs.twimg.com/media/Fm9A39vXEAEhV7R?format=png[0m[31m\n\t[0m-\x20🔗\x20[34mhttps://pbs.twimg.com/media/Fe5Ik9eXkAAr20r?format=png[0m[31m\n[0m"
assert my_secret in os.environ, _error_message  # [1mFeel free to delete the lines 53 & 54 once you've forked it![0m

# Run the bot
bot.run(os.getenv(my_secret))
c.execute('''CREATE TABLE IF NOT EXISTS user_points
             (user_id INTEGER PRIMARY KEY, points INTEGER)''')
conn.commit()

# Function to update user points in the database
def update_user_points(user_id, points):
    c.execute("INSERT OR REPLACE INTO user_points (user_id, points) VALUES (?, ?)", (user_id, points))
    conn.commit()

# Function to retrieve user points from the database
def get_user_points(user_id):
    c.execute("SELECT points FROM user_points WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        return row[0]
    else:
        return None

# Function to retrieve the leaderboard from the database
def get_leaderboard():
    c.execute("SELECT * FROM user_points ORDER BY points DESC")
    return c.fetchall()

# Close the database connection when the bot exits
def close_db_connection():
    conn.close()

# Gateway Events
@bot.event
async def on_ready():
    print(f"✅ {bot.user}")

# Bot Commands
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! `{bot.latency:.2f}ms`")

@bot.command()
async def peng(ctx):
    await ctx.send(f"Give me a sign")

# Update the guess command to use the database
@bot.command()
async def guess(ctx):
    randomguess = [
        {"url": "https://media.discordapp.net/attachments/1227527405779025923/1234866478218608781/20240425_233222251.jpg?ex=66324a87&is=6630f907&hm=b37e4d8670c11a383a0aa96f1d33d221e3c197cf3ef6d1776ae2b8e6096563f0&", "name": "Bling Bang Born"},
        {"url": "https://media.discordapp.net/attachments/1227527405779025923/1234866477794852994/20240425_233626454.jpg?ex=66324a87&is=6630f907&hm=43cb8f8aab39ff7bbe6a2a788af3fc822d841b539412e867ef768b5be98cffff&", "name": "Nevada"},
        {"url": "https://example.com/image3.jpg", "name": "image3"},
        # Add more entries as needed
    ]
    entry = random.choice(randomguess)
    correct_name = entry["name"]
    
    embed = discord.Embed(title="Guess the Picture!", description="You have 10 seconds to guess.", color=0x00ff00)
    embed.set_image(url=entry["url"])
    message = await ctx.send(embed=embed)
    
    try:
        user_guess = await bot.wait_for('message', timeout=10.0, check=lambda message: message.author == ctx.author)
    except asyncio.TimeoutError:
        await ctx.send("Time's up! You didn't guess in time. The correct name was: " + correct_name)
        return
    
    if user_guess.content.lower() == correct_name.lower():
        await ctx.send("Congratulations! You guessed it right.")
        current_points = get_user_points(ctx.author.id)
        if current_points is None:
            current_points = 0
        update_user_points(ctx.author.id, current_points + 10)
    else:
        await ctx.send(f"Sorry, that's not the correct name. The correct name was: {correct_name}")

# Update the balance command to use the database
@bot.command()
async def balance(ctx):
    points = get_user_points(ctx.author.id)
    if points is not None:
        await ctx.send(f"Your balance: {points} points")
    else:
        await ctx.send("You don't have any points yet.")

# Update the leaderboard command to use the database
@bot.command()
async def leaderboard(ctx):
    leaderboard = get_leaderboard()
    if not leaderboard:
        await ctx.send("The leaderboard is empty.")
        return
    
    leaderboard_msg = "Leaderboard:\n"
    for idx, (user_id, points) in enumerate(leaderboard, start=1):
        user = bot.get_user(user_id)
        if user:
            leaderboard_msg += f"{idx}. {user.display_name}: {points} points\n"
    
    await ctx.send(leaderboard_msg)



# Function to handle the daily command
@bot.command()
async def daily(ctx):
    last_claimed = get_last_claimed(ctx.author.id)
    today = datetime.date.today()

    # Check if the user has already claimed their daily points for the day
    if last_claimed is not None and last_claimed.date() == today:
        await ctx.send("You have already claimed your daily points for today.")
        return

    # Add 30 points to the user's balance
    current_points = get_user_points(ctx.author.id)
    if current_points is None:
        current_points = 0
    update_user_points(ctx.author.id, current_points + 30)

    # Update the last claimed timestamp
    update_last_claimed(ctx.author.id, today)

    # Send the result in an embed message
    embed = discord.Embed(title="Daily Points Claimed", description="You have claimed your daily points. You received 30 points!", color=0x00ff00)
    await ctx.send(embed=embed)

# Function to retrieve the last claimed timestamp from the database
def get_last_claimed(user_id):
    c.execute("SELECT last_claimed FROM user_daily WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        return datetime.datetime.fromisoformat(row[0])
    else:
        return None

# Function to update the last claimed timestamp in the database
def update_last_claimed(user_id, last_claimed):
    c.execute("INSERT OR REPLACE INTO user_daily (user_id, last_claimed) VALUES (?, ?)", (user_id, last_claimed.isoformat()))
    conn.commit()

# Close the database connection when the bot exits
@bot.event
async def on_disconnect():
    close_db_connection()

# Checks if the Secret exists in the Secrets tab
_error_message = f"[31m\n\nI could not find any secret named\x20[0m[41m\x20{my_secret}\x20[0m[31m\x20in the Secrets tab.\n\n[90m[!][0m[31m\x20Here are some links that might help you:\n\t[0m-\x20🔗\x20[34mhttps://pbs.twimg.com/media/Fm9A39vXEAEhV7R?format=png[0m[31m\n\t[0m-\x20🔗\x20[34mhttps://pbs.twimg.com/media/Fe5Ik9eXkAAr20r?format=png[0m[31m\n[0m"
assert my_secret in os.environ, _error_message  # [1mFeel free to delete the lines 53 & 54 once you've forked it![0m

# Run the bot
bot.run(os.getenv(my_secret))


