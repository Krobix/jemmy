#Jemmy bot for bluesky
import atproto, requests, getpass, os, json

home = os.getenv("HOME")

#Using this username, the bot will automatically follow everyone this user is following, in order to customize its feed.
follows_handle = "krobix.bsky.social"

handle = "jemmybot.bsky.social"
display_name = "jemmy"

bot_pass = getpass.getpass(prompt=f"{handle} password: ")

with open(f"{home}/bskyprompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

if os.path.isfile(f"{home}/bsky_follows.json"):
    with open(f"{home}/bsky_follows.json", "r") as f:
        bot_follows = json.load(f)
else:
    bot_follows = {}
    bot_follows["follows"] = []

def check_follows(client: atproto.Client):
    cursor = ""
    new_followed = 0
    more_follows = True
    while more_follows:
        follows = client.get_follows(actor=follows_handle, cursor=cursor)
        for f in follows.follows:
            if not f.did in bot_follows["follows"]:
                client.follow(f.did)
                bot_follows["follows"].append(f.did)
                new_followed += 1
        if cursor is None:
            more_follows = False
    with open(f"{home}/bsky_follows.json", "w") as f:
        json.dump(bot_follows, f)
    print(f"Checked follows and followed {new_followed} more people")

