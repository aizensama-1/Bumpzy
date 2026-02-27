import discum
import os
import sys
import time
import random
import threading
import re
import requests
from datetime import datetime
from colorama import init, Fore, Style
from flask import Flask

init(autoreset=True)

app = Flask(__name__)

@app.route('/')
def index():
    return "Selfbot 24/7 alive on Render - Master YASH"

@app.route('/ping')
def ping():
    return "pong"

# Config from Render env
TOKEN = os.getenv('TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))
CHANNELS = [x.strip() for x in os.getenv('CHANNELS', '').split(',') if x.strip()]
GLOBAL_TOGGLE = os.getenv('GLOBAL_TOGGLE', 'true').lower() == 'true'
AUTO_RESTART = int(os.getenv('AUTO_RESTART_HOURS', 24))

DISBOARD_ID = "302050872383242240"
HEADERS = {"authorization": TOKEN}

bot = discum.Client(token=TOKEN, log=False)

bump_data = {ch: {"next_time": time.time() + random.randint(60, 300), "enabled": True, "last_success": None} for ch in CHANNELS}
fake_msgs = ["bump", "up", "lets go", ".", "gg", "b", "bump it", "push", "go", "now", "yes", "!", "bump pls", "time", "ready", "hey", "sup", "bumping", "bump time", "lets bump", "up up", "ggs", "nice", "cool", "fire", "lit", "on", "go go", "yes yes", "b", "bb", "bbb", "bump bump", "push it", "do it", "now now", "ready?", "bump?", "up?", "go?", "yes?", "!", "!!", "bump now", "time to bump", "server up"]
emojis = ["👍", "🔥", "🚀", "💥", "✅", "📈", "⭐", "❤️", "😂", "👀", "🔝", "🏆", "🎉", "🙌"]
last_status = time.time()
last_deleted = None

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.CYAN}[{ts}] {msg}{Style.RESET_ALL}")
    with open("autobump.log", "a") as f:
        f.write(f"[{ts}] {msg}\n")

def parse_time(content):
    m = re.search(r'(\d+)\s*(h(?:ours?)?|m(?:inutes?)?)', content.lower())
    if m:
        num = int(m.group(1))
        unit = m.group(2)[0]
        return num * 3600 if unit == 'h' else num * 60
    return 7200

def send_typing(channel):
    requests.post(f"https://discord.com/api/v9/channels/{channel}/typing", headers=HEADERS)

def human_bump(ch):
    if not GLOBAL_TOGGLE or not bump_data[ch]["enabled"] or time.time() < bump_data[ch]["next_time"]:
        return
    log(f"Thinking in {ch}")
    time.sleep(random.uniform(1.8, 7.2))
    send_typing(ch)
    time.sleep(random.uniform(1, 4))
    if random.random() < 0.25:
        bot.sendMessage(ch, random.choice(fake_msgs))
        time.sleep(random.uniform(3, 12))
    log(f"Bumping {ch}")
    try:
        bot.triggerSlashCommand(ch, DISBOARD_ID, "bump")
        if random.random() < 0.20:
            bot.sendMessage(ch, random.choice(emojis))
        log(f"{Fore.GREEN}✅ BUMP SENT {ch}{Style.RESET_ALL}")
    except:
        log(f"{Fore.RED}⚠️ Failed {ch}{Style.RESET_ALL}")

def status_loop():
    global last_status
    while True:
        if time.time() - last_status > random.randint(480, 2100):
            acts = random.choice([{"name":"Valorant","type":0},{"name":"Drake - God's Plan","type":2},{"name":"Minecraft","type":0},{"name":"Chilling 🔥","type":3}])
            bot.gateway.send({"op":3,"d":{"status":"online","afk":False,"activities":[acts]}})
            last_status = time.time()
        time.sleep(30)

def scheduler():
    start = time.time()
    while True:
        now = time.time()
        for ch in CHANNELS:
            if bump_data[ch]["enabled"] and now >= bump_data[ch]["next_time"]:
                human_bump(ch)
                bump_data[ch]["next_time"] = now + 6300 + random.randint(0, 600)
        if AUTO_RESTART > 0 and (now - start) > AUTO_RESTART * 3600:
            log("Auto-restarting")
            os.execv(sys.executable, ['python'] + sys.argv)
        time.sleep(10)

@bot.gateway.command
def on_message(resp):
    global last_deleted
    if resp.event.message:
        m = resp.parsed.auto()
        if m['author']['id'] == DISBOARD_ID and m['channel_id'] in bump_data:
            content = m.get('content') or (m.get('embeds',[{}])[0].get('description',''))
            if "Bump done" in content or "bump again" in content.lower():
                sec = parse_time(content)
                bump_data[m['channel_id']]["next_time"] = time.time() + sec + random.randint(60,600)
                bump_data[m['channel_id']]["last_success"] = datetime.now().strftime("%H:%M")
                log(f"{Fore.GREEN}Success → next in \~{(sec+300)//60} min{Style.RESET_ALL}")
            elif "Try again in" in content:
                sec = parse_time(content)
                bump_data[m['channel_id']]["next_time"] = time.time() + sec + random.randint(30,180)
                log(f"Cooldown → waiting {sec//60} min")
        if str(m['author']['id']) != str(OWNER_ID):
            return
        content = m['content'].strip().lower()
        guild = m.get('guild_id')
        ch = m['channel_id']
        if content.startswith('ban '):
            u = content.split()[1].replace('<@','').replace('>','').replace('!','')
            requests.put(f"https://discord.com/api/v9/guilds/{guild}/bans/{u}", headers=HEADERS)
            bot.sendMessage(ch, f"Banned {u}")
        elif content.startswith('kick '):
            u = content.split()[1].replace('<@','').replace('>','').replace('!','')
            requests.delete(f"https://discord.com/api/v9/guilds/{guild}/members/{u}", headers=HEADERS)
            bot.sendMessage(ch, f"Kicked {u}")
        elif content.startswith('mute '):
            u = content.split()[1].replace('<@','').replace('>','').replace('!','')
            requests.patch(f"https://discord.com/api/v9/guilds/{guild}/members/{u}", headers=HEADERS, json={"mute":True})
            bot.sendMessage(ch, f"Muted {u}")
        elif content.startswith('unmute '):
            u = content.split()[1].replace('<@','').replace('>','').replace('!','')
            requests.patch(f"https://discord.com/api/v9/guilds/{guild}/members/{u}", headers=HEADERS, json={"mute":False})
            bot.sendMessage(ch, f"Unmuted {u}")
        elif content.startswith('timeout '):
            u = content.split()[1].replace('<@','').replace('>','').replace('!','')
            requests.patch(f"https://discord.com/api/v9/guilds/{guild}/members/{u}", headers=HEADERS, json={"communication_disabled_until":"2027-01-01T00:00:00"})
            bot.sendMessage(ch, f"Timeout {u}")
        elif content.startswith('purge '):
            try:
                amt = int(content.split()[1])
                msgs = bot.getMessages(ch, amt)
                for msg in msgs:
                    bot.deleteMessage(ch, msg['id'])
            except:
                pass
        elif content == 'snipe' and last_deleted:
            bot.sendMessage(ch, f"Sniped: {last_deleted.get('content','[no content]')}")
        elif content == '!bumpstatus':
            txt = "Bump Status:\n"
            for c,d in bump_data.items():
                nxt = datetime.fromtimestamp(d["next_time"]).strftime("%H:%M")
                txt += f"{c}: Next {nxt} | Last {d['last_success'] or 'N/A'} | {'ON' if d['enabled'] else 'OFF'}\n"
            bot.sendMessage(ch, txt)
        elif content.startswith('!togglebump'):
            parts = m['content'].split()
            if len(parts)>1 and parts[1] in bump_data:
                bump_data[parts[1]]["enabled"] = not bump_data[parts[1]]["enabled"]
                bot.sendMessage(ch, f"{parts[1]}: {'ON' if bump_data[parts[1]]['enabled'] else 'OFF'}")
            else:
                global GLOBAL_TOGGLE
                GLOBAL_TOGGLE = not GLOBAL_TOGGLE
                bot.sendMessage(ch, f"Global: {'ON' if GLOBAL_TOGGLE else 'OFF'}")
        elif content in ['$destroy','.attack']:
            log("NUKE STARTED")
            g = bot.getGuild(guild)['channels']
            for c in g:
                requests.delete(f"https://discord.com/api/v9/channels/{c['id']}", headers=HEADERS)
                time.sleep(0.6)
            for r in bot.getGuild(guild)['roles']:
                if r['id'] != guild:
                    requests.delete(f"https://discord.com/api/v9/guilds/{guild}/roles/{r['id']}", headers=HEADERS)
                    time.sleep(0.6)
            log("Nuke done")
        elif content in ['$ball','.banall']:
            members = bot.getGuildMembers(guild, limit=100)
            for mem in members:
                requests.put(f"https://discord.com/api/v9/guilds/{guild}/bans/{mem['user']['id']}", headers=HEADERS)
                time.sleep(1.2)
        elif content in ['$kall','.kickall']:
            members = bot.getGuildMembers(guild, limit=100)
            for mem in members:
                requests.delete(f"https://discord.com/api/v9/guilds/{guild}/members/{mem['user']['id']}", headers=HEADERS)
                time.sleep(1.2)
        elif content == '$mall':
            members = bot.getGuildMembers(guild, limit=100)
            for mem in members:
                try:
                    dm = bot.createDM(mem['user']['id'])
                    bot.sendMessage(dm['id'], "Server message from owner")
                except:
                    pass
                time.sleep(2)
        elif content in ['$channels','.channelbomb']:
            for i in range(80):
                requests.post(f"https://discord.com/api/v9/guilds/{guild}/channels", headers=HEADERS, json={"name":f"destroyed-{i}","type":0})
                time.sleep(0.7)
        elif content in ['$roles','.rolebomb']:
            for i in range(80):
                requests.post(f"https://discord.com/api/v9/guilds/{guild}/roles", headers=HEADERS, json={"name":f"destroyed-{i}"})
                time.sleep(0.7)

    if resp.event.message_delete:
        last_deleted = resp.parsed.auto()

def gateway_thread():
    bot.gateway.run(auto_reconnect=True)

if __name__ == "__main__":
    threading.Thread(target=gateway_thread, daemon=True).start()
    time.sleep(6)
    threading.Thread(target=status_loop, daemon=True).start()
    log(f"{Fore.GREEN}MASTER SELF BOT STARTED ON RENDER 24/7 — ALL FEATURES ACTIVE{Style.RESET_ALL}")
    threading.Thread(target=scheduler, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
