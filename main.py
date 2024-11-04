import discord, asyncio, aiohttp, json

SYSTEM_PROMPT = ""

ai_urls = ["mari.lan", "mari.home"]

token = ""

with open("~/token.txt", "r") as f:
    global token
    token = f.read()
    token = token.strip()

class Jemmy(discord.Client):
    async def on_ready(self):
        print("Logged in!!!")

    async def on_message(self, msg):
        if msg.author.id == self.user.id:
            return

        print(f"Received message: {msg.author.name} // {msg.author.global_name}")
        print(f"Content: {msg.content}")

intents = discord.Intents.default()
intents.message_content = True

jemmy = Jemmy(intents=intents)

jemmy.run(token)