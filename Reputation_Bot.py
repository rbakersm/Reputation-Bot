import datetime
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
TOKEN = os.getenv("TOKEN") #Discord bot auth token
CLIENT = os.getenv("CLIENT") #Client connection link

intents = discord.Intents.default() #Discord bot permissions
intents.message_content = True

SERVER_CLIENT = MongoClient(CLIENT) #Server client
USER_DATABASE = SERVER_CLIENT.ChroniclesOfArcane #Database
REP_COLLECTION = USER_DATABASE.UserRep #User collection

#Key symbol to identify the start of a command and set the commands of the bot
bot = commands.Bot(command_prefix='!', intents = intents)

ADMIN = None

@bot.event
async def on_ready():
    """
    Sets the Admin user to the provided ID
    """
    global ADMIN
    ADMIN = await bot.fetch_user(194518319900917761)

@bot.command(name = "addfeedback")
async def add_feedback(ctx, feedback_receiver: discord.User, feedback, *notes):
    """
    Adds feedback for a user, if the user does not exist in the database, add a new entry for the user.
    :param ctx: The message received
    :param feedback_receiver: User being tracked
    :param feedback: positive/negative
    :param *notes: Optional notes about transaction
    """
    #Checks to make sure the user giving feedback is not the same as the user the feedback is about
    feedback_provider = ctx.message.author

    if (feedback_provider.id != feedback_receiver.id):
        #Checks for a valid feedback input
        if (feedback.lower() == "positive" or feedback.lower() == "negative"):
            #Checks to see if a user has given the same user too many feedbacks in a timeframe
            combined_notes = ' '.join(notes) #Combines tuple into a single string
            score = 1 if feedback.lower() == "positive" else -1 #reputation score
            date = datetime.datetime.utcnow() #Time the feedback is given

            #Look for the user in the database
            if (REP_COLLECTION.find_one({"id": feedback_receiver.id})):
                await check_if_suspicious(feedback_provider, feedback_receiver)
                REP_COLLECTION.update_one({"id": feedback_receiver.id}, {"$push": {"reviews": {"id": feedback_provider.id, "score": score, "notes": combined_notes, "date": date}}})

            else:
                REP_COLLECTION.insert_one({"id": feedback_receiver.id, "reviews": [{"id": feedback_provider.id, "score": score, "notes": combined_notes, "date": date}]})

            await ctx.message.add_reaction('✅')
        else:
            await ctx.message.add_reaction('❌')
            await ctx.send("Missing feedback (positive/negative).")
    else:
        await ctx.message.add_reaction('❌')
        await ctx.send("You cannot give yourself feedback.")

async def check_if_suspicious(feedback_provider, feedback_receiver):
    """
    Messages the Admin
    :param feedback_provider: User being reviewed
    :param feedback_receiver: User leaving the review
    """

    reviews = REP_COLLECTION.find_one({"id": feedback_receiver})['reviews'] #Receiver's dictionary of reviews
    total_reviews = 0 #Total number of reviews the provider has given the receiver in the time frame
    review_threshold = 5 #Number of reviews the provider has to give to the receiver before it's flagged as suspicious
    date = datetime.datetime.utcnow() #The datetime the review is entered (in UTC)
    day_max = 1 #Day range to check
    hour_max = 0 #Hour range to check
    date_check = date - datetime.timedelta(days = day_max, hours = hour_max) #The range to check for number of reviews sent by provider to receiver

    #Checks each entry in the date range for user feedback and adds one for each valid entry
    for entry in reviews:
        if entry['id'] == feedback_provider.id and date_check < entry['date']:
            total_reviews += 1

    #Sends the Admin a warning for suspicious activity
    if (total_reviews >= review_threshold):
        await ADMIN.send(f"{feedback_provider.display_name} has sent {review_threshold} or more reviews for {feedback_receiver.display_name} in the last 24 hours.")

@bot.command(name = "getfeedback")
async def get_feedback(ctx, feedback_receiver: discord.User):
    """
    If the user exists in the database, output their name and score
    :param ctx: The message received
    :param feedback_receiver: User to retrieve
    """

    receiver = REP_COLLECTION.find_one({"id": feedback_receiver.id}) #Receiver entry in the database
    if (receiver):
        reviews = receiver["reviews"] #Dictionary of User's reviews
        total_reviews = 0 #Number of reviews
        positive_reviews = 0 #Number of positive reviews
        negative_reviews = 0 #Number of negative reviews

        #Goes through each review and adds up each review score
        for entry in reviews:
            total_reviews += 1
            if entry['score'] == 1:
                positive += 1
            elif entry['score'] == -1:
                negative += 1
            else:
                await ctx.send(f"I cannot compute {entry['score']}")

        await ctx.send(f"__{feedback_receiver.display_name}__\nTotal: {str(total_reviews)} Positive: {str(positive_reviews)} Negative: {str(negative_reviews)}")
    else:
        await ctx.send(f"{feedback_receiver.display_name} is not in our database.")

@bot.command("getnotes")
async def get_notes(ctx, feedback_receiver: discord.User):
    """
    Gets all the notes associated with the provided user and messages author with a list of the notes
    :param ctx: The message received
    :param feedback_receiver: User to get the notes of
    """
    
    receiver = REP_COLLECTION.find_one({"id": feedback_receiver.id}) #Receiver entry in the database
    #Checks for user in the database
    if (receiver):
        feedback_getter = await bot.fetch_user(ctx.message.author.id) #User to message
        notes_list = "" #List of notes
        reviews = receiver['reviews'] #Reviews of the passed user
        review_number = 0 #Current Review number

        #Goes through each review and combines each non-empty notes into a string list
        for entry in reviews:
            if (entry['notes'] != ""):
                review_number += 1
                notes_list += f"Note {review_number}: {entry['notes']}\n"
        
        await feedback_getter.send(f"__{feedback_receiver.display_name}__\n{notes_list}")
        await ctx.message.add_reaction('✅')
    else:
        await ctx.send(f"{feedback_receiver.display_name} is not in our database.")
        await ctx.message.add_reaction('❌')

@bot.event
async def on_command_error(ctx, error):

    #If the passed user is not in discord's database
    if isinstance(error, commands.UserNotFound):
        await ctx.message.add_reaction('❌')
        await ctx.send("User not found. If user is not in the server, please either invite them and resend your feedback or user their User ID.")

bot.run(TOKEN)