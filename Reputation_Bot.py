import datetime
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

@bot.command(name = "addfeedback")
async def add_feedback(ctx, user: discord.User, feedback, *notes):
    """
    Adds feedback for a user, if the user does not exist in the database, add a new entry for the user.
    :param ctx: The message received
    :param user: User being tracked
    :param feedback: positive/negative
    :param *notes: Optional notes about transaction
    """

    #Checks for a valid feedback input
    if (feedback.lower() == "positive" or feedback.lower() == "negative"):
        combined_notes = ' '.join(notes) #Combines tuple into a single string
        sender = ctx.message.author #Uses to store the reviewer for security checks
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
        await ctx.send("Missing feedback (positive/negative)")

@add_feedback.error
async def feedback_error(ctx, error):
    """
    If the user sending the message doesn't use @ before the reported user's name, it will throw an error
    :param ctx: Message with the error
    :param error: UserNotFound
    """

    await ctx.message.add_reaction('❌')
    await ctx.send("User not found. If user is not in the server, please either invite them and resend your feedback or user their User ID.")

@bot.command(name = "getfeedback")
async def get_feedback(ctx, user: discord.User):
    """
    If the user exists in the database, output their name and score
    :param ctx: Message received
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


#Look to see if get_feedback error can link with feedback_error
@get_feedback.error
async def get_error(ctx, error):
    """
    :param ctx: Message with the error
    :param error: UserNotFound
    """
    await ctx.message.add_reaction('❌')
    await ctx.send("User not found")

bot.run(TOKEN)