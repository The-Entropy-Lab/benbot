import chromadb
import discord
import os

from dotenv import load_dotenv
from tinydb import TinyDB
from benbot.core import (
    get_session,
    rag,
    run_llm,
    update_session
)

load_dotenv()

APPLICATION_BOT_TOKEN = os.getenv("APPLICATION_BOT_TOKEN")
CHAT_LIMIT = int(os.getenv("CHAT_LIMIT", 20))
DISCORD_PRIVATE_CHANNEL_ID = int(os.getenv("DISCORD_PRIVATE_CHANNEL_ID",0))
SYSTEM_MESSAGE = os.getenv("SYSTEM_MESSAGE", "You are a helpful assistant.")
LTM_SYSTEM_MESSAGE = os.getenv("LTM_SYSTEM_MESSAGE", "Summarize the conversation.")
DATA_FOLDER = os.getenv("DATA_FOLDER", "_data")


def handler(content=None, user=None, db=None, docs=None):
    # get user information from db, create if it does not exist
    user_info = get_session(session=user, db=db)

    # append the user's message to the user's message history
    user_info["messages"].append({"role": "user", "content": content})

    # truncate the message history to the chat limit
    if len(user_info["messages"]) > CHAT_LIMIT:
        user_info["messages"] = user_info["messages"][-CHAT_LIMIT:]

    # get the bot's response from the LLM
    response = run_llm(messages=[
        {"role": "system", "content": SYSTEM_MESSAGE + "\n\n" + rag(content, docs=docs) + f"\n\nSummary of my conversation with {user}:\n{user_info['ltm']}"},
        # {"role": "system", "content": SYSTEM_MESSAGE + f"\n\nSummary of my conversation with {user}:\n{user_info['ltm']}"},
    ] + user_info["messages"])

    # append the bot's response to the user's message history
    user_info["messages"].append({"role": "assistant", "content": response})

    # truncate the message history to the chat limit
    if len(user_info["messages"]) > CHAT_LIMIT:
        user_info["messages"] = user_info["messages"][-CHAT_LIMIT:]

    # create a long term memory (ltm) summary of the conversation (helps with conversational persistance)
    ltm = run_llm(messages=[
        {"role": "system", "content": LTM_SYSTEM_MESSAGE},
        {"role": "user", "content": "\n".join([f"{msg['role']}: {msg['content']}" for msg in user_info["messages"]])}
    ])

    # update the user's information in the db
    update_session(session=user, db=db, messages=user_info["messages"], ltm=ltm)

    return response


def main():
    db = TinyDB(f"{DATA_FOLDER}/tinydb.json")
    chroma_client = chromadb.PersistentClient(path=f"{DATA_FOLDER}")
    docs = chroma_client.get_or_create_collection("benbot")
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    discord_client = discord.Client(intents=intents)

    @discord_client.event
    async def on_ready():
        print(f'We have logged in as {discord_client.user}')

    # reference: https://discordpy.readthedocs.io/en/stable/api.html#discord.Message
    @discord_client.event
    async def on_message(message):
        # this prevents the bot from responding to itself
        if message.author == discord_client.user:
            return

        # this prevents the bot from responding to messages that do not mention the bot
        if discord_client.user not in message.mentions:
            if not isinstance(message.channel, discord.channel.DMChannel):
                print(f'message neither mentions bot or is DM')
                return
            
        # get the private channel
        channel = discord_client.get_channel(DISCORD_PRIVATE_CHANNEL_ID)

        for c in discord_client.get_all_channels():
            print(f'channel: {c.name}')

        # check if the user is a member of the private channel
        if message.author.id in [m.id for m in channel.members]:
            print(f'user "{message.author.name}" is a member of channel "{channel.name}"')

            # invoke message handler to get the response
            response = handler(
                content=message.content,
                user=message.author.name,
                db=db,
                docs=docs
            )

            # send the response back to the user
            await message.channel.send(response)
        else:
            print(f'user "{message.author.name}" is NOT a member of "{channel.name}"')

    discord_client.run(APPLICATION_BOT_TOKEN)


if __name__ == "__main__":
    main()