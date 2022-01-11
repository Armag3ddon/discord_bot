#!/usr/bin/python3
"""
Miniac Discord Bot
"""

import sqlite3
import re
import asyncio #pylint: disable=unused-import
import random
import datetime
from sqlite3 import Error

import discord # pylint: disable=import-error

f = open("./discord_auth.txt", encoding="utf-8")
lines=f.readlines()
TOKEN = lines[0]
miniac_server_id = int(lines[1])
miniac_general_channel_id = int(lines[2])
miniac_welcome_channel_id = int(lines[3])
f.close()
print(discord.__version__)
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
DATABASE = "./points.db"

def create_user_table(user, conn):
    """
    Create a table for a discord user that will contain links to their images.
    :param user: string discord user
    :param conn: connection to database
    :return: nothing
    """
    create_user_query = f"""CREATE TABLE IF NOT EXISTS '{user}' (
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             link text
                           )"""
    if conn is not None:
        try:
            with conn:
                cur = conn.cursor()
                cur.execute(create_user_query)
        except Error as e:
            print(f"Failed to create user {user}. There error is below.")
            print(e)
    else:
        print("Error! Database connection was not established before creating a user's table.")

def create_leaderboard_table(conn):
    """
    This method creates the leaderboard table. It shouldn't need to be run more than once per year when the table resets.
    :param conn: connection to database
    :return: nothing
    """
    create_leaderboard_query = """CREATE TABLE IF NOT EXISTS leaderboard (
                                    id integer PRIMARY KEY AUTOINCREMENT,
                                    user text NOT NULL,
                                    points integer NOT NULL
                                  )"""
    if conn is not None:
        try:
            with conn:
                cur = conn.cursor()
                cur.execute(create_leaderboard_query)
        except Error as e:
            print("Failed to create leaderboard table. The error is below.")
            print(e)
    else:
        print("Error! Database connection was not established before creating leaderboard table.")

def create_meme_table(conn):
    """
    Create the meme table if it doesn't exist.
    :param conn: connection to database
    :return: nothing
    """
    create_meme_query = """CREATE TABLE IF NOT EXISTS memes (
                                    id integer PRIMARY KEY AUTOINCREMENT,
                                    link text,
                                    year integer NOT NULL
                                  )"""
    if conn is not None:
        try:
            with conn:
                cur = conn.cursor()
                cur.execute(create_meme_query)
        except Error as e:
            print("Failed to create meme table. The error is below.")
            print(e)
    else:
        print("Error! Database connection was not established before creating meme table.")

def insert_meme(link, conn):
    """
    Save a meme in the meme table.
    :param link: a discord message link
    :param conn: connection to database
    :return: a message to send to discord
    """
    current_year = datetime.datetime.now().date().strftime("%Y")
    insert_query = f"INSERT INTO 'memes' (link, year) VALUES ('{link}', '{current_year}')"
    return_message = ''
    if conn is not None:
        try:
            with conn:
                cur = conn.cursor()
                cur.execute(insert_query)
                return_message = "Haha! This is a funny one."
        except Error as e:
            print("Failed to add meme. There error is below.")
            print(e)
            return_message = "Error. :sob:"
    else:
        print("Error! Database connection was not established before adding to a user's gallery.")
        return_message = "Error. :sob:"
    return return_message

def insert_link(user, link, conn):
    """
    Insert a link into a discord user's table
    :param user: string discord user
    :param link: a link to the image
    :param conn: connection to the database
    :return: nothing
    """
    create_user_table(user, conn)
    insert_query = f"INSERT INTO '{user}' (link) VALUES ('{link}')"
    if conn is not None:
        try:
            with conn:
                cur = conn.cursor()
                cur.execute(insert_query)
        except Error as e:
            print(f"Failed to add image to {user}'s gallery. There error is below.")
            print(e)
    else:
        print("Error! Database connection was not established before adding to a user's gallery.")

def find_user(user, conn):
    """
    Find a user in the leaderboard
    :param user: string discord user
    :param conn: connection to the database
    :return: a boolean as to whether or not the user exists in the database. Can be null if query fails.
    """
    find_query = f"SELECT rowid FROM leaderboard WHERE user = '{user}'"
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute(find_query)
            data = cur.fetchall()
            return bool(len(data))
        except Error as e:
            print(f"Failed when querying to find {user}. The error is below.")
            print(e)
    else:
        print("Error! Database connection was not established when trying to find a user")

def increment_points(user, points, conn):
    """
    Increment a user's points by a specific value
    :param user: an ID for a discord user
    :param points: int value
    :param conn: connection to the database
    :return: tuple that contains the users points before the addition, and the curren total
    """
    increment_query = f"UPDATE leaderboard SET points = points + {points} WHERE user = '{user}'"
    create_user_query = f"INSERT INTO leaderboard (points, user) VALUES ({points}, '{user}')"
    get_user_point = f"SELECT points FROM leaderboard WHERE user='{user}'"
    if conn is not None:
        if find_user(user, conn):
            try:
                with conn:
                    cur = conn.cursor()
                    cur.execute(increment_query)
            except Error as e:
                print(f"Failed to increment {user}'s points. Error is below.")
                print(e)
        else:
            try:
                with conn:
                    cur = conn.cursor()
                    cur.execute(create_user_query)
            except Error as e:
                print(f"Failed to create {user} in leaderboard. Error is below.")
                print(e)
        try:
            with conn:
                cur = conn.cursor()
                cur.execute(get_user_point)
                current_points = cur.fetchone()[0]
                return (int(current_points) - int(points), current_points)

        except Error as e:
            print(f"Failed to get {user}'s current points. Error is below.")
            print(e)
    else:
        print("Error! Database connection was not established when incrementing a user's point total")

def retrieve_sorted_leaderboard(conn):
    """
    Returns the top 20 users on the discord server ordered by points.
    :param: conn: connection to the database
    :return: list
    """
    # We're querying for 20 people instead of 10 because sometimes the top 10 will include people who
    # are no longer in the server. This way, we can sort the "None" types out and get a real top 10.
    get_sorted_leaderboard_query = "SELECT user, points FROM leaderboard ORDER BY points DESC LIMIT 20"
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute(get_sorted_leaderboard_query)
            return cur.fetchall()
        except Error as e:
            print('Failed to retrieve the leaderboard. Error is below.')
            print(e)
    else:
        print("Error! Database connection was not established when querying the order of the leaderboard.")

def retrieve_user_points(conn, user):
    """
    Returns a specific user's point value.
    :param: conn: connection to the database.
    :param: user: the user in question
    :return: string int value of their point total.
    """
    get_user_points_query = f"SELECT points FROM leaderboard WHERE user = '{user}'"
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute(get_user_points_query)
            return cur.fetchone()[0]
        except TypeError:
            return "0"
        except Error as e:
            print(f"Failed to retrieve {user}'s point total. Error is below.")
            print(e)
    else:
        print("Error! Database connection was not established when querying a user's point total.")

def retrieve_gallery(user, conn):
    """
    This returns the content of a user's gallery table.
    :param user: the ID of a discord user
    :param conn: connection to the database
    :return: returns a list of tuples
    """
    get_gallery_query = f"SELECT link FROM '{user}'"
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute(get_gallery_query)
            return cur.fetchall()
        except Error as e:
            print(f"Failed to retrieve {user}'s gallery. Error is below.")
            print(e)
    else:
        print("Error! Database connection was not established when querying a user's gallery.")

def retrieve_memes(year, conn):
    """
    Returns the memes for a specific year or all of them.
    :param year: Either a specific or "ALL"
    :param conn: connection to the database
    :return: returns a list of tuples
    """
    if year != "ALL":
        get_memes_query = f"SELECT link, year FROM 'memes' WHERE year = {year}"
    else:
        get_memes_query = "SELECT link, year FROM 'memes'"

    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute(get_memes_query)
            return cur.fetchall()
        except Error as e:
            print("Failed to retrieve memes. Error is below.")
            print(e)
    else:
        print("Error! Database connection was not established when querying memes.")

async def set_name(user_points, member_id):
    """
    Change the user's nickname to include the correct emoji based on their points.
    :param user_points: The current points of the user
    :param member_id: The discord guild member ID of the user
    :return: nothing
    """
    #If possible, use the members nick name on the server before their account name
    member = await client.get_guild(miniac_server_id).fetch_member(member_id)
    user_name = ''
    try:
        user_name = member.nick
    except AttributeError:
        print('This member has no nickname, will proceed using their user account name')
    if not user_name:
        user_name = member.name
    # Everytime we award points, the emojis we award are removed, the person's bracket is
    # recalculated, and they are given the correct emoji so everything stays straight.
    if '\N{money bag}' in user_name:
        user_name = user_name.replace('\N{money bag}', '').strip()
        await member.edit(nick=user_name)

    if '\N{crossed swords}' in user_name:
        user_name = user_name.replace('\N{crossed swords}', '').strip()
        await member.edit(nick=user_name)

    if '\N{crown}' in user_name:
        user_name = user_name.replace('\N{crown}', '').strip()
        await member.edit(nick=user_name)

    if '\N{banana}' in user_name:
        user_name = user_name.replace('\N{banana}', '').strip()
        await member.edit(nick=user_name)

    if user_points >= 50 and user_points < 120:
        new_nick = f"{user_name} \N{money bag}"
        await member.edit(nick=new_nick)

    elif user_points >= 120 and user_points < 400:
        new_nick = f"{user_name} \N{crossed swords}"
        await member.edit(nick=new_nick)

    elif user_points >= 400 and user_points < 1000:
        new_nick = f"{user_name} \N{crown}"
        await member.edit(nick=new_nick)

    elif user_points >= 1000:
        new_nick = f"{user_name} \N{banana}"
        await member.edit(nick=new_nick)

async def increment_points_wrapper(message):
    """
    This is a wrapper for the function to add points to a discord user.
    :param message: this is a discord message containing all the params to run this function
    :return: a message to print out in discord
    """

    # The message to print out in discord
    return_message = ''
    roles = []
    for role in message.author.roles:
        roles.append(role.name)

    if 'Wight King' not in roles and 'Thrall' not in roles:
        # ah ah ah!
        return 'http://gph.is/15wY87J'

    # split out the various params
    command_params = message.content.split()

    if len(command_params) < 3:
        return "You are missing some parameters. Please see !brian for help on how to use this command."

    if len(command_params) == 3:
        if "-" not in command_params[2]:
            return "You can only use this format of the command to remove points."
    try:
        int(command_params[2])
    except ValueError:
        return 'You need to use an integer when giving a user points.'

    if '@' not in command_params[1] or re.search('[a-zA-Z]', command_params[1]):
        return 'You need to tag a user with this command. Their name should appear blue in discord.'

    if len(command_params) == 3:
        if "-" not in command_params[2]:
            return_message = "You can only use this format of the command to remove points."
            return return_message

        # using the !add command to remove points

        # remove non digit characters like !, @, <, or >
        discord_user_id = int(re.sub(r"\D", "", command_params[1]))
        points = command_params[2]

        conn = sqlite3.connect(DATABASE)
        before_points, user_points = increment_points(discord_user_id, points, conn)
        conn.close()
        await set_name(user_points, discord_user_id)
        display_name = client.get_user(discord_user_id).display_name
        return_message = f":sob: Woops, {display_name}. You now have {user_points} points :sob:"
        return return_message

    elif len(command_params) == 4:
        # using the !add command to actually add points

        image_link = command_params[3]
        # remove non digit characters like !, @, <, or >
        discord_user_id = int(re.sub(r"\D", "", command_params[1]))
        points = command_params[2]
        image_link = command_params[3]

        conn = sqlite3.connect(DATABASE)
        before_points, user_points = increment_points(discord_user_id, points, conn)
        insert_link(discord_user_id, image_link, conn)
        conn.close()

        await set_name(user_points, discord_user_id)
        if user_points >= 50 and before_points < 50:
            return_message = ":moneybag: HOOTY HOO! You've earned your first emoji. FLEX ON THE HATERS WHO DON'T PAINT! :moneybag:"

        elif user_points >= 120 and before_points < 120:
            return_message = ":crossed_swords: KACAW! You've earned your second emoji. HAIL AND KILL! :crossed_swords:"

        elif user_points >= 400 and before_points < 400:
            return_message = ":crown: SKKKRT! You've earned your third emoji. YOU DA KING :crown:"

        elif user_points >= 1000 and before_points < 1000:
            return_message = ":banana: LORD ALMIGHTY! You've earned your fourth and final emoji. You've ascended to minipainting godhood :banana:"

        else:
            display_name = client.get_user(discord_user_id).display_name
            return_message = f":metal:Congratulations, {display_name}. You now have {user_points} points:metal:"

        return return_message

    else:
        return_message = 'You\'re missing a parameter. Please see the !brian documentation'
        return return_message

def get_leaderboard():
    """
    Get a discord friendly leader message with up to 10 leaderboard members.
    :return: leaderboard string
    """
    discord_message = ''
    conn = sqlite3.connect(DATABASE)
    leaderboard = retrieve_sorted_leaderboard(conn)
    conn.close()
    discord_message = ''
    if leaderboard is None:
        print("Leaderboard doesn't exist. Creating it now..")
        conn = sqlite3.connect(DATABASE)
        create_leaderboard_table(conn)
        conn.close()
    elif not leaderboard:
        return '```leaderboard is empty.```'
    else:
        x = 0
        y = 0
        while(x < 10 and y < 20 and y < len(leaderboard)):
            member = client.get_user(int(leaderboard[y][0]))
            if member:
                x +=1
                discord_message += f'{member.display_name}: {leaderboard[y][1]}\n'
            y +=1
        return f'```{discord_message}```'

def get_points(message):
    """
    Assemble the points info message.
    :param message: this is a discord message containing all the params to run this function
    :return: a message to print out in discord
    """
    conn = sqlite3.connect(DATABASE)
    command_params = message.content.split()
    insults = [
            "Looks like you have no points. Time to PAINT MORE MINIS!",
            "0/10 did not enjoy how pretentious you come off when talking about having literally zero points. Nothing you painted has received points since 10 years ago... you know back when you were born.",
            "Those unprimed and unpainted minis won't paint themselves! You have 0 points.",
            "Sucks to suck! You have zero points!",
            "Bro, do you even paint? You have zero points.",
            "Sometimes I think I'm unproductive, and then I remember you exist. You have zero points!",
            "You're beautiful even if you have zero points. I still love you.",
            "I believe in you. In a week you'll be on the board. For now you have zero points, though."
            ]
    if len(command_params) == 1:
        points = retrieve_user_points(conn, message.author.id)
        if int(points):
            return_message = f"```{message.author.display_name}: {points}```"
        else:
            return_message = insults[random.randint(0,7)]

        conn.close()
        return return_message
    elif len(command_params) == 2:
        if '@' not in command_params[1] or re.search('[a-zA-Z]', command_params[1]):
            return_message = 'You need to tag a user with this command. Their name should appear blue in discord.'
            return return_message

        discord_user_id = int(re.sub(r"\D", "", command_params[1]))
        points = retrieve_user_points(conn, discord_user_id)
        display_name = client.get_user(discord_user_id).display_name
        return_message = f"```{display_name}: {points}```"
        conn.close()
        return return_message
    else:
        return_message = 'You have one too many parameters. Check !brian for help on how this command works.'
        conn.close()
        return return_message

def get_gallery(message):
    """
    Assemble the gallery message.
    :param message: this is a discord message containing all the params to run this function
    :return: a message to print out in discord
    """
    # split out the various params
    command_params = message.content.split()
    if len(command_params) != 2:
        command_params = [ command_params[0] , str(message.author.id)]
    elif '@' not in command_params[1]:
        return_message = 'You need to tag a user with this command. Their name should appear blue in discord.'
        return return_message

    # remove non digit characters like !, @, <, or >
    discord_user_id = int(re.sub(r"\D", "", command_params[1]))
    conn = sqlite3.connect(DATABASE)
    gallery = retrieve_gallery(discord_user_id, conn)
    conn.close()
    discord_private_message = ''
    discord_private_message_list = []
    index = 1
    try:
        for link in gallery:
            if (len(discord_private_message) + len(link[0])) > 2000:
                discord_private_message_list.append(discord_private_message)
                discord_private_message = ""

            discord_private_message += f"{index}. {link[0]}\n"
            index += 1

        # Append the final message that didn't make it to 2k characters
        discord_private_message_list.append(discord_private_message)
    except TypeError:
        discord_private_message_list.append("User has no gallery. Harass them to paint some minis!")

    return discord_private_message_list

def get_memes(message):
    """
    Show all the memes for a specific year or just all memes
    :param message: this is a discord message containing all the params to run this function
    :return: a message to print out in discord
    """
    command_params = message.content.split()
    if len(command_params) != 2:
        year = "ALL"
    else:
        # sanitisation: years only contain numbers
        year = re.sub('[^0-9]', '', command_params[1])

    if year == '':
        return ["Please give me a valid year or none at all."]

    # establish a read-only database connection for extra security
    conn = sqlite3.connect(f"file:{DATABASE}", uri=True)
    memes = retrieve_memes(year, conn)
    conn.close()

    discord_private_message = ''
    discord_private_message_list = []
    index = 1
    try:
        for meme in memes:
            new_message = f"{index}. {meme[0]} ({meme[1]})\n"
            if (len(discord_private_message) + len(new_message) ) > 2000:
                discord_private_message_list.append(discord_private_message)
                discord_private_message = ""

            discord_private_message += new_message
            index += 1

        # Append the final message that didn't make it to 2k characters
        if discord_private_message != '':
            discord_private_message_list.append(discord_private_message)
    except TypeError:
        discord_private_message_list.append("Something went wrong with fetching memes. Better call a Thrall!")

    if not discord_private_message_list:
        discord_private_message_list.append(f"No memes have been made in {year}. Sad times.")

    return discord_private_message_list

async def save_meme(message):
    """
    Save a Miniac meme for a yearly overview
    :param message: a discord message object
    """
    # Only qualified people can add a meme
    roles = []
    for role in message.author.roles:
        roles.append(role.name)

    if "Wight King" not in roles and "Thrall" not in roles:
        # ah ah ah!
        return "The wrath of Clonk will be upon you."

    # split out the various params
    command_params = message.content.split()
    if len(command_params) != 2:
        return "Wrong usage! The command should be used like this: !meme <Discord message link>."

    conn = sqlite3.connect(DATABASE)
    create_meme_table(conn)
    return_message = insert_meme(command_params[1], conn)
    conn.close()
    return return_message

def brian():
    """
    The !brian or !help message.
    :returns: message string
    """
    return_message = """
    Hi, I'm Brian. You can call me Bryguy. I'm your friendly bot companion. Here are the commands you can do: \n
    `!leaderboard`\n
    This returns the current point totals for the top 10 painters on the discord server.\n
    `!gallery [discord_user]`\n
    This private messages you a discord user's personal gallery. These are all the pictures they've gotten points for. Make sure to actually tag the user, their name should appear blue.\n
    `!points [discord_user]`\n
    This command can be run with a parameter or without a parameter. If you want to find someone's point total, run "!points @[name-of-person]". If you want to know your own points, run "!points"\n
    `!7years`\n
    Never do this.\n
    `!add [discord_user] [points] [link]`\n
    Only Wight Kings and Thralls can run this command. This increments your point total by [points], and adds a new image to your gallery.\n
    `!brian` or `!help`\n
    This prints this message!
    """
    return return_message

# Custom welcome message
@client.event
async def on_member_join(member):
    """
    Welcome new members to the server.
    :param member: discord member object
    :return: nothing
    """
    print(f"Recognized that {member.name} joined")
    await client.get_channel(miniac_general_channel_id).send(f"Welcome to the Miniac Discord, {member.mention} Make sure to check out the <#537337389400719360> channel for all the information and rules!")
    print(f"Sent message about {member.name} to #general")

@client.event
async def on_message(message):
    """
    Discord event on receival of new messages.
    :param message: discord message object
    :return: nothing
    """
    # Find string versions of the name and add them to a list

    if message.content.startswith('!add'):
        discord_message = await increment_points_wrapper(message)
        await message.channel.send( discord_message)
    if message.content == "!submit":
        await message.channel.send( 'Submit your models for points with this form: https://forms.gle/FkvMWfyCVgAZvGLd6')

    if message.content == '!leaderboard':
        discord_message = get_leaderboard()
        await message.channel.send(discord_message)

    if message.content.startswith('!gallery'):
        discord_private_message_list = get_gallery(message)
        if len(message.content.split()) == 2:
            user = message.content.split()[1]
            await message.author.send(f"{user}'s Gallery")
        else:
            await message.author.send(f"{message.author.mention}'s Gallery")
        for discord_message in discord_private_message_list:
            await message.author.send(f"{discord_message}")

    if message.content == "!7years":
        await message.channel.send( 'https://i.imgur.com/9NYdTDj.gifv')

    if message.content.startswith('!points'):
        await message.channel.send(get_points(message))

    if message.content.startswith("!meme"):
        discord_message = await save_meme(message)
        await message.channel.send(discord_message)

    if message.content.startswith('!show_meme'):
        discord_private_message_list = get_memes(message)
        for discord_message in discord_private_message_list:
            await message.author.send(f"{discord_message}")

    if message.content == "!brian" or message.content == "!help":
        await message.channel.send(brian())

@client.event
async def on_ready():
    """Discord event on successful connection."""
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
#client.loop.create_task(boot_non_roles())
client.run(TOKEN)
