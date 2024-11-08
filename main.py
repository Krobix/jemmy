import discord, asyncio, aiohttp, json, os
from pathlib import Path

SYSTEM_PROMPT = """"""

default_gen_params = {
  "max_context_length": 4096,
  "max_length": 200,
  "quiet": False,
  "rep_pen": 1.1,
  "rep_pen_range": 256,
  "rep_pen_slope": 1,
  "temperature": 1.2,
  "tfs": 1,
  "top_a": 0,
  "top_k": 100,
  "top_p": 0.9,
  "typical": 1
}

MAX_MSG_HISTORY = 50

ai_urls = ["mari.lan", "mari.home"]

token = ""

if not os.path.isdir(f"{os.getenv('HOME')}/history"):
    os.mkdir(f"{os.getenv('HOME')}/history")

if os.path.isfile(f"{os.getenv('HOME')}/systemprompt.txt"):
    with open(f"{os.getenv('HOME')}/systemprompt.txt", 'r') as f:
        SYSTEM_PROMPT = f.read()

with open(f"{os.getenv('HOME')}/token.txt", "r") as f:
    token = f.read()
    token = token.strip()

with open("badwords.txt", "r") as f:
    badwords = f.read().strip().split(" ")

async def censor(text):
    for w in badwords:
        wlen = len(w)
        while w in (tlower:=text.lower()):
            loc = tlower.find(w)
            text = text[:loc] + ("~"*wlen) + text[(loc+wlen):]
        return text

class Jemmy(discord.Client):
    async def on_ready(self):
        print("Logged in!!!")

    async def on_message(self, msg):
        is_dm = isinstance(msg.channel, discord.channel.DMChannel)
        is_reply = (msg.reference is not None)
        if is_reply:
            is_reply_to_me = (await msg.channel.fetch_message(msg.reference.message_id)).author.id==self.user.id
        else:
            is_reply_to_me = False
        if msg.author.id == self.user.id:
            return

        if is_dm or (str(self.user.id) in msg.content) or is_reply_to_me:
            async with msg.channel.typing():
                print(f"Received message: {msg.author.name}")
                print(f"Content: {msg.content}\n\n")

                req = default_gen_params.copy()
                history = {}
                filename = f"{os.getenv('HOME')}/history/{msg.author.id}.json"
                prompt = f"<|system|>\n{SYSTEM_PROMPT}</s>\n"
                addr = ai_urls[0]
                generated = ""

                for url in ai_urls:
                    res = os.system(f"ping -c 1 {url}")
                    if res==0:
                        addr = url
                        break

                if is_reply_to_me:
                    reply_thread = []
                    tmes = msg
                    while True:
                        reply_thread.append(tmes)
                        try:
                            tmes = await msg.channel.fetch_message(tmes.reference.message_id)
                        except:
                            break
                    reply_thread.reverse()

                    for m in reply_thread:
                        if m.author.id==self.user.id:
                            sender = "assistant"
                        else:
                            sender = "user"
                        prompt += f"<|{sender}|>\n{m.content}</s>\n"

                if is_dm:
                    if os.path.isfile(filename):
                        with open(filename, "r") as f:
                            history = json.load(f)
                    else:
                        history["messages"] = []

                    umsg_h = {
                        "author": "user",
                        "content": msg.content
                    }

                    history["messages"].append(umsg_h)

                    while "<|system|>" in umsg_h["content"] or "<|user|>" in umsg_h["content"] or "<|assistant|>" in umsg_h["content"]:
                        for s in ("<|system|>", "<|assistant|>", "<|user|>"):
                            umsg_h["content"] = umsg_h["content"].replace(s, "")

                    i = 0
                    for m in history["messages"]:
                        if i >= MAX_MSG_HISTORY:
                            break
                        prompt += f"<|{m['author']}|>\n{m['content']}</s>\n"
                        i += 1

                    prompt += "<|assistant|>\n"

                else:
                    prompt += f"<|user|>\n{msg.content}</s>\n<|assistant|>\n"

                req["prompt"] = prompt

                async with aiohttp.ClientSession() as session:
                    async with session.post(f"http://{addr}:5001/api/v1/generate", json=req) as res:
                        print(f"Got response from KoboldAI: {res.status} {res.reason}\n\n")

                        if res.status==200:
                            generated += (await res.json())['results'][0]['text']

                        else:
                            await msg.channel.send(f"Error contacting KoboldAI: {res.status}: {res.reason}")
                            return

                if is_dm:
                    amsg_h = {
                        "author": "assistant",
                        "content": generated
                    }
                    history["messages"].append(amsg_h)

                    with open(filename, "w") as f:
                        json.dump(history, f)

                if "</s>" in generated:
                    generated = generated.split("</s>")[0]

                generated = await censor(generated)

                await msg.reply(generated)



intents = discord.Intents.default()
intents.message_content = True

jemmy = Jemmy(intents=intents)

jemmy.run(token)