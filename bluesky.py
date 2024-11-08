#Jemmy bot for bluesky
import atproto, aiohttp, getpass, os, json, asyncio, aiofiles

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

home = os.getenv("HOME")

#Using this username, the bot will automatically follow everyone this user is following, in order to customize its feed.
follows_handle = "krobix.bsky.social"

handle = "jemmybot.bsky.social"
display_name = "jemmy"
#KoboldAI URL including port
koboldai_url = "localhost:5001"

POST_FEED_AMOUNT = 10

bot_pass = getpass.getpass(prompt=f"{handle} password: ")

with open(f"{home}/bskyprompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

with open("badwords.txt", "r") as f:
    badwords = f.read()

if os.path.isfile(f"{home}/bsky_follows.json"):
    with open(f"{home}/bsky_follows.json", "r") as f:
        bot_follows = json.load(f)
else:
    bot_follows = {}
    bot_follows["follows"] = []

async def censor(text):
    for w in badwords:
        wlen = len(w)
        while w in (tlower:=text.lower()):
            loc = tlower.find(w)
            text = text[:loc] + ("*"*wlen) + text[(loc+wlen):]
        return text

async def strip_post(text):
    text = await censor(text)
    if "</s>" in text:
        text = text.split("</s>")[0]
    if "\n\n" in text:
        text = text.split("\n\n")[0]
    return text

async def koboldai_gen(req):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://{koboldai_url}/api/v1/generate", json=req) as res:
            print(f"Got response from KoboldAI: {res.status} {res.reason}\n\n")

            if res.status == 200:
                return (await res.json())['results'][0]['text']
            else:
                return None

async def check_follows(client: atproto.AsyncClient):
    cursor = ""
    new_followed = 0
    more_follows = True
    while more_follows:
        follows = await client.get_follows(actor=follows_handle, cursor=cursor)
        for f in follows.follows:
            if not f.did in bot_follows["follows"]:
                await client.follow(f.did)
                bot_follows["follows"].append(f.did)
                new_followed += 1
        if cursor is None:
            more_follows = False
    async with aiofiles.open(f"{home}/bsky_follows.json", "w") as f:
        await f.write(json.dumps(bot_follows))
    print(f"Checked follows and followed {new_followed} more people")


async def make_feed_post(client: atproto.AsyncClient):
    print("Making feed post")
    timeline = await client.get_timeline(limit=POST_FEED_AMOUNT)
    prompt = f"<|system|>\n{SYSTEM_PROMPT}</s>\n"
    req = default_gen_params.copy()

    for post in timeline.feed:
        post = post.post
        author = post.author
        if not author.display_name is None:
            name = author.display_name
        else:
            name = author.handle

        print(f"Read post by {name}: {post.record.text}")

        prompt += f"<|{name}|>\n{post.record.text}</s>"

    prompt += f"<|{display_name}|>\n"
    req["prompt"] = prompt

    generated = await koboldai_gen(req)
    if generated is None:
        return

    generated = await strip_post(generated)

    await client.post(generated)

