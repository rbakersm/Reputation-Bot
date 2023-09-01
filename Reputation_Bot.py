import datetime
from xml.dom import NotFoundErr
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
TOKEN = os.getenv("TOKEN") #Discord bot auth token
CLIENT = os.getenv("CLIENT") #Client connection link

intents = discord.Intents.default()
intents.message_content = True

rep_client = MongoClient(CLIENT) #Server client
db = rep_client.ChroniclesOfArcane #Database
user_rep = db.UserRep #User collection

#Key symbol to identify the start of a command and set the commands of the bot
bot = commands.Bot(command_prefix='!', intents = intents)

ADMIN = None

@bot.event
async def on_ready():
    global ADMIN
    ADMIN = await bot.fetch_user(194518319900917761)

@bot.command(name = "addfeedback")
async def add_feedback(ctx, user: discord.User, feedback, *notes):
    """
    Adds feedback for a user, if the user does not exist in the database, add a new entry for the user.
    :param ctx: The message received
    :param user: User being tracked
    :param feedback: positive/negative
    :param *notes: Optional notes about transaction
    """
    #Checks to make sure the user giving feedback is not the same as the user the feedback is about
    sender = ctx.message.author

    if (sender.id != user.id):
        #Checks for a valid feedback input
        if (feedback.lower() == "positive" or feedback.lower() == "negative"):
            #Checks to see if a user has given the same user too many feedbacks in a timeframe
            await is_repeated(sender, user_rep.find_one({"id": user.id}))
            combined_notes = ' '.join(notes) #Combines tuple into a single string
            score = 1 if feedback.lower() == "positive" else -1 #reputation score
            date = datetime.datetime.utcnow() #Time the feedback is given

            #Look for the user in the database
            if (user_rep.find_one({"id": user.id})):
                user_rep.update_one({"id": user.id}, {"$push": {"reviews": {"id": sender.id, "score": score, "notes": combined_notes, "date": date}}})

            else:
                user_rep.insert_one({"id": user.id, "reviews": [{"id": sender.id, "score": score, "notes": combined_notes, "date": date}]})

            await ctx.message.add_reaction('✅')
        else:
            await ctx.message.add_reaction('❌')
            await ctx.send("Missing feedback (positive/negative).")
    else:
        await ctx.message.add_reaction('❌')
        await ctx.send("You cannot give yourself feedback.")

async def is_repeated(reviewer, reviewee):
    """
    Messages the Admin
    :param reviewer: User being reviewed
    :param reviewee: User leaving the review
    """
    if (reviewee):
        reviewee_name = await bot.fetch_user(reviewee['id'])
        reviews = reviewee["reviews"]
        total = 0
        threshold = 5

        date = datetime.datetime.utcnow()
        maxtime = date - datetime.timedelta(days = 1)

        for entry in reviews:
            if entry['id'] == reviewer.id and maxtime < entry['date']:
                total += 1

        if (total >= threshold):
            await ADMIN.send(f"{reviewer.display_name} has sent {threshold} or more reviews for {reviewee_name.display_name} in the last 24 hours.")

@bot.command(name = "getfeedback")
async def get_feedback(ctx, user: discord.User):
    """
    If the user exists in the database, output their name and score
    :param ctx: The message received
    :param user: User to retrieve
    """

    db_user = user_rep.find_one({"id": user.id})
    if (db_user):
        reviews = db_user["reviews"]
        total = 0
        positive = 0
        negative = 0

        for entry in reviews:
            total += 1
            if entry['score'] == 1:
                positive += 1
            else:
                negative += 1

        await ctx.send("__" + user.display_name + "__\nTotal: " + str(total) + " Positive: " + str(positive) + " Negative: " + str(negative))
    else:
        await ctx.send(user.display_name + " is not in our database.")

@bot.command("getnotes")
async def get_notes(ctx, user: discord.User):
    """
    Gets all the notes associated with the provided user and messages author with a list of the notes
    :param ctx: The message received
    :param user: User to get the notes of
    """
    
    db_user = user_rep.find_one({"id": user.id})
    #Checks for user in the database
    if (db_user):
        send_to = await bot.fetch_user(ctx.message.author.id) #User to message
        notes_list = "" #List of notes
        reviews = db_user['reviews'] #Reviews of the passed user
        i = 0

        for entry in reviews:
            if (entry['notes'] != ""):
                i += 1
                notes_list += f"Note {i}: {entry['notes']}\n"
        
        await send_to.send(f"__{user.display_name}__\n{notes_list}")
        await ctx.message.add_reaction('✅')
    else:
        await ctx.send(user.display_name + " is not in our database.")
        await ctx.message.add_reaction('❌')

@bot.event
async def on_command_error(ctx, error):

    #If the passed user is not in discord's database
    if isinstance(error, commands.UserNotFound):
        await ctx.message.add_reaction('❌')
        await ctx.send("User not found. If user is not in the server, please either invite them and resend your feedback or user their User ID.")

bot.run(TOKEN)