import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
TOKEN = os.getenv("TOKEN")
CLIENT = os.getenv("CLIENT")

intents = discord.Intents.default()
intents.message_content = True

rep_client = MongoClient(CLIENT)
db = rep_client.ChroniclesOfArcane
user_rep = db.UserRep

#Key symbol to identify the start of a command
bot = commands.Bot(command_prefix='!', intents = intents)

@bot.command(name = "addfeedback")
async def add_feedback(ctx, user: discord.User, feedback, *notes):
    """
    Adds feedback for a user, if the user does not exist in the database, add a new entry for the user.
    :param user: User being tracked
    :param feedback: positive/negative
    :param *notes: Optional notes about transaction
    """

    if (feedback == "positive" or feedback == "negative"):
        combined_notes = ' '.join(notes)

        if (user_rep.find_one({"id": user.id})):
            user_rep.update_one({"id": user.id}, {"$inc": {"rep": 1 if feedback == "positive" else -1}})
            if (combined_notes):
                user_rep.update_one({"id": user.id}, {"$push": {"notes": combined_notes}})
        else:
            user_rep.insert_one({"id": user.id, "rep": 1 if feedback == "positive" else -1, "notes": [combined_notes]})

        await ctx.message.add_reaction('✅')
    else:
        await ctx.message.add_reaction('❌')
        await ctx.send("Missing feedback (positive/negative)")

@add_feedback.error
async def feedback_error(ctx, error):
    """
    If the user sending the message doesn't use @ before the reported user's name, it will throw an error
    :param error: UserNotFound
    """

    await ctx.message.add_reaction('❌')
    await ctx.send("User not found")

@bot.command(name = "getfeedback")
async def get_feedback(ctx, user: discord.User):
    """
    If the user exists in the database, output their name and score
    :param user: User to retrieve
    """

    db_user = user_rep.find_one({"id": user.id})
    await ctx.send(user.display_name + "'s reputation: " + str(db_user["rep"]))

@get_feedback.error
async def get_error(ctx, error):
    await ctx.message.add_reaction('❌')
    await ctx.send("User not found")

bot.run(TOKEN)