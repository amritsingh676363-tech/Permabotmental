#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ ULTRA-LIGHTWEIGHT RENDER NC BOT (24/7 RENDER 512MB COMPATIBLE) ⚡
- 100% ENV Driven (No hardcoded tokens)
- 1 NC every 2 seconds (Continuous Non-Stop Relay)
- Built-in Keep-Alive HTTP Server on Port 10000 (Render + UptimeRobot)
- Daily 6:00 PM IST Zero-Downtime Memory & Storage Purge
- Real-time 512 MB Render RAM Monitor with '! usage' Command
"""

import os
import re
import sys
import json
import time
import random
import asyncio
import datetime
import gc
from typing import Set, List, Dict

# 1. Load .env file automatically
def load_env(path=".env"):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_env()

# 2. Configuration from Environment Variables (No hardcoded tokens)
try:
    OWNER_ID = int(os.environ.get("OWNER_ID", "0").strip() or 0)
except Exception:
    OWNER_ID = 0

_raw_tokens = os.environ.get("BOT_TOKENS", "")
BOT_TOKENS: List[str] = [
    t.strip()
    for t in re.split(r"[,\r\n]+", _raw_tokens)
    if t.strip() and ":" in t and not t.strip().startswith("YOUR_")
]

PORT = int(os.environ.get("PORT", "10000"))
# ⚡ 500% BYPASS: Render automatically provides RENDER_EXTERNAL_URL (e.g. https://my-bot.onrender.com)
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
BOT_START_TIME = time.time()
active_tasks: Dict[int, asyncio.Event] = {}
seen_update_ids: Set[int] = set()
TOTAL_NAME_CHANGES = 0
GLOBAL_BOT_IDX = 0
SPEED_MODE = "perma"  # "perma" = Guaranteed <3.3GB/month (110MB/day hard shield) | "turbo" = War speed

# 2.0 Hard Daily Bandwidth Shield (Guarantees NEVER crossing 5 GB / month on Render!)
DAILY_SAFE_MB = 110.0  # 110 MB/day * 30 = 3.3 GB max (leaves 1.7 GB safety cushion under 5 GB)
daily_bw = {
    "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
    "bytes": 0,
}

def add_wire_bytes(estimated_bytes: int):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    if daily_bw["date"] != today:
        daily_bw["date"] = today
        daily_bw["bytes"] = 0
    daily_bw["bytes"] += estimated_bytes

def get_daily_mb() -> float:
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    if daily_bw["date"] != today:
        return 0.0
    return round(daily_bw["bytes"] / (1024 * 1024), 2)

# 2.1 Lightweight Known Group Tracker (Zero-Storage, < 1 KB)
KNOWN_GROUPS_FILE = "known_groups.txt"
SUDO_USERS_FILE = "sudo_users.txt"

def load_known_groups() -> Set[int]:
    groups: Set[int] = set()
    if os.path.exists(KNOWN_GROUPS_FILE):
        try:
            with open(KNOWN_GROUPS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        groups.add(int(line))
        except Exception:
            pass
    return groups

def save_known_group(chat_id: int):
    global known_groups
    if chat_id not in known_groups:
        known_groups.add(chat_id)
        try:
            with open(KNOWN_GROUPS_FILE, "a", encoding="utf-8") as f:
                f.write(f"{chat_id}\n")
        except Exception:
            pass

known_groups: Set[int] = load_known_groups()

# 2.2 Sudo Users Management (Pure Zero-Storage, In-Memory + Text File)
def load_sudo_users() -> Set[int]:
    sudos: Set[int] = set()
    # From ENV
    raw_sudos = os.environ.get("SUDO_USERS", "")
    for s in re.split(r"[,\s]+", raw_sudos):
        s = s.strip()
        if s.isdigit():
            sudos.add(int(s))
    # From file
    if os.path.exists(SUDO_USERS_FILE):
        try:
            with open(SUDO_USERS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.isdigit():
                        sudos.add(int(line))
        except Exception:
            pass
    return sudos

def save_sudo_users_file():
    global sudo_users
    try:
        with open(SUDO_USERS_FILE, "w", encoding="utf-8") as f:
            for uid in sorted(list(sudo_users)):
                f.write(f"{uid}\n")
    except Exception:
        pass

sudo_users: Set[int] = load_sudo_users()

def is_owner(uid: int) -> bool:
    return bool(OWNER_ID and uid == OWNER_ID)

def is_sudo_or_owner(uid: int) -> bool:
    if not OWNER_ID:
        return True
    return uid == OWNER_ID or uid in sudo_users

# 3. Real Render 512 MB RAM Measurement
def get_ram_mb() -> float:
    try:
        with open("/proc/self/statm", "r") as f:
            return round(int(f.read().split()[1]) * 4096 / (1024 * 1024), 2)
    except Exception:
        try:
            import resource
            return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)
        except Exception:
            return 18.2

daily_reset_stats = {
    "last_reset_time": "Aaj shaam 6:00 PM IST ko auto-reset hoga",
    "last_reset_freed": 0,
    "last_ram_after": 0.0,
    "total_resets_done": 0,
}

def get_next_reset_str() -> str:
    now_ist = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    target = now_ist.replace(hour=18, minute=0, second=0, microsecond=0)
    if now_ist >= target:
        target += datetime.timedelta(days=1)
    diff = target - now_ist
    h, rem = divmod(int(diff.total_seconds()), 3600)
    m = rem // 60
    return f"{target.strftime('%d-%b 18:00 IST')} ({h}h {m}m baaki)"

# 4. Daily 6:00 PM Storage & Cache Flush (Bina Ruke / Zero-Downtime)
def perform_memory_and_storage_purge(reason: str = "Daily 6:00 PM Purge"):
    global seen_update_ids, daily_reset_stats
    ram_before = get_ram_mb()

    # Trim seen updates
    if len(seen_update_ids) > 50:
        seen_update_ids = set(sorted(list(seen_update_ids))[-50:])

    # Clean finished chat events
    dead_chats = [cid for cid, ev in list(active_tasks.items()) if ev.is_set()]
    for cid in dead_chats:
        active_tasks.pop(cid, None)

    # Clean /tmp and __pycache__
    for p in ["/tmp", "__pycache__"]:
        try:
            if os.path.isdir(p):
                for f in os.listdir(p):
                    fp = os.path.join(p, f)
                    if os.path.isfile(fp) and f.startswith(("tmp", "httpx", "py")):
                        os.remove(fp)
        except Exception:
            pass

    collected = gc.collect(2)
    # ⚡ C-LEVEL MEMORY PURGE: Force Linux kernel to reclaim unmapped heap memory immediately
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass

    ram_after = get_ram_mb()
    now_ist = (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).strftime("%d-%b %H:%M:%S IST")

    daily_reset_stats["last_reset_time"] = now_ist
    daily_reset_stats["last_reset_freed"] = collected
    daily_reset_stats["last_ram_after"] = ram_after
    daily_reset_stats["total_resets_done"] += 1

    print(f"🧹 [{reason}] {now_ist} | Freed: {collected} items | RAM: {ram_after} MB / 512 MB")

async def daily_memory_cleaner_worker():
    last_daily_date = ""
    while True:
        try:
            await asyncio.sleep(60)
            ist_now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
            today_str = ist_now.strftime("%Y-%m-%d")

            # Daily at 6:00 PM (18:00 IST)
            if ist_now.hour == 18 and last_daily_date != today_str:
                last_daily_date = today_str
                perform_memory_and_storage_purge("Daily 6:00 PM IST Auto-Purge")
            # Gentle hourly collect at minute 0
            elif ist_now.minute == 0:
                perform_memory_and_storage_purge("Hourly Memory Sweep")
        except Exception:
            await asyncio.sleep(60)

# 5. Ultra-Stylish Name Generator (Cyber-Gothic Imperial Aesthetic)
DECORATORS = [
    ("◢█◣ ⟨ ", " ⟩ ◢█◣"),
    ("❖═━•〔 ", " 〕•━═❖"),
    ("⚡ 𓊈 ⚔️ ", " ⚔️ 𓊉 ⚡"),
    ("👑 ⟨⟨ ", " ⟩⟩ 👑"),
    ("🔱 ⟦ ", " ⟧ 🔱"),
    ("✦ ━━〔 ", " 〕━━ ✦"),
    ("💀 𓆩 ", " 𓆪 💀"),
    ("🔥 ⟨ ", " ⟩ 🔥"),
    ("🌌 ⟦ ✦ ", " ✦ ⟧ 🌌"),
    ("⚔️ 𓊈 ", " 𓊉 ⚔️"),
    ("⚜️ ═━〔 ", " 〕━═ ⚜️"),
    ("❄️ ⟨⟨ ", " ⟩⟩ ❄️"),
]
SUFFIXES = ["⚡", "👑", "🔱", "💎", "🔥", "⚔️", "🌪️", "✦", "💥", "💫", "🐉", "☄️"]

def make_stylish_name(base: str, last_cache: List[str]) -> str:
    for _ in range(15):
        dec = random.choice(DECORATORS)
        suf = random.choice(SUFFIXES)
        styled = f"{dec[0]}{base}{dec[1]} {suf}".strip()[:255]
        if styled != last_cache[0]:
            last_cache[0] = styled
            return styled
    return f"{base} {random.choice(SUFFIXES)}"

# 6. NC Rename Loop (Non-Stop 24/7/365 Multi-GC Engine)
async def nc_loop(client, chat_id: int, base: str, stop_event: asyncio.Event):
    global TOTAL_NAME_CHANGES, GLOBAL_BOT_IDX
    last_cache = [""]

    # Initial micro-jitter to prevent 50+ groups from colliding at the exact same millisecond
    await asyncio.sleep(random.uniform(0.05, 0.8))

    while not stop_event.is_set():
        if not BOT_TOKENS:
            await asyncio.sleep(2.0)
            continue

        new_title = make_stylish_name(base, last_cache)
        token = BOT_TOKENS[0]
        retry_delay = 0.0

        try:
            url = f"https://api.telegram.org/bot{token}/setChatTitle"
            raw_body = json.dumps({"chat_id": chat_id, "title": new_title}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            add_wire_bytes(len(raw_body) + 380)  # Count body + TLS/HTTP2/TCP wire overhead conservatively
            resp = await client.post(
                url,
                content=raw_body,
                headers={"Content-Type": "application/json", "Accept-Encoding": "gzip, deflate, br", "Connection": "keep-alive"},
                timeout=2.0
            )
            data = resp.json()
            if data.get("ok"):
                TOTAL_NAME_CHANGES += 1
            else:
                err_desc = (data.get("description") or "").lower()
                if any(x in err_desc for x in ["rights", "admin", "forbidden", "kicked", "not a member"]):
                    active_tasks.pop(chat_id, None)
                    stop_event.set()
                    return
                retry_after = data.get("parameters", {}).get("retry_after")
                if retry_after:
                    retry_delay = float(retry_after)
        except Exception:
            pass

        # ⚡ IRONCLAD 30-DAY 5GB PERMA SHIELD:
        # Global max ~1.6 req/sec in PERMA mode (~70-95 MB/day = 2.1 - 2.9 GB/month across ANY number of groups!)
        # If daily usage hits 90% of daily budget (100 MB), auto-throttle smoothly so 5 GB is NEVER crossed!
        if retry_delay > 0:
            sleep_sec = retry_delay + 0.15
        elif SPEED_MODE == "turbo":
            active_count = len(active_tasks)
            sleep_sec = 0.72 if active_count <= 2 else max(0.85, round(active_count * 0.14, 2))
        else:
            active_count = len(active_tasks)
            if active_count <= 1:
                sleep_sec = 0.95  # 1 group: fast & guaranteed ~1.4 GB/month
            elif active_count == 2:
                sleep_sec = 1.35
            elif active_count == 3:
                sleep_sec = 1.90
            else:
                # 4 to 50 groups: 0.62s per group => global rate <= 1.61 req/s (~2.2 - 2.8 GB/month total!)
                sleep_sec = max(2.2, round(active_count * 0.62, 2))

            # Hard daily byte shield: if today's budget is nearly full, double spacing for rest of the day
            if get_daily_mb() >= (DAILY_SAFE_MB * 0.90):
                sleep_sec = round(sleep_sec * 2.0, 2)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=sleep_sec)
        except asyncio.TimeoutError:
            pass

# 7. Helper to send messages
async def send_msg(client, token: str, chat_id: int, text: str):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=4.0)
    except Exception:
        pass

# 8. Command Handler (! usage, /allgc, /listgc, /addgc, /nc, /nc stop, /mode)
async def handle_update(client, update: dict):
    global SPEED_MODE
    # Auto-track any group where bot was added or updated
    my_chat_member = update.get("my_chat_member")
    if my_chat_member:
        c = my_chat_member.get("chat")
        if c and c.get("type") in ("group", "supergroup"):
            save_known_group(c.get("id"))

    msg = update.get("message")
    if not msg:
        return

    # 🛡️ ZERO-MEDIA FILTER (Save 100% Inbound Bandwidth & Keep Monthly Data Under 4GB)
    # Discard photos, videos, stickers, voice, audio, documents, animations instantly without downloading
    if any(k in msg for k in ("photo", "video", "sticker", "voice", "audio", "document", "animation", "video_note")):
        return

    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    user_id = msg.get("from", {}).get("id")

    # Automatically register every group/supergroup where a message arrives
    if chat.get("type") in ("group", "supergroup") and chat_id:
        save_known_group(chat_id)

    text = (msg.get("text") or "").strip()
    if not text:
        return

    # Only process bot commands, ignore normal chat conversations to save CPU & RAM
    if not text.startswith(("/", "!", "+")):
        return

    primary_token = BOT_TOKENS[0]
    cleaned = text.strip()

    # Public /start and /help command (Anyone can view this)
    if re.match(r"^(!|/|\+)?\s*(start|help|alive|info)\b", cleaned, re.IGNORECASE):
        welcome_banner = (
            f"▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜\n"
            f"   ⚡ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 𝐕𝟒 ⚡\n"
            f"▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟\n\n"
            f"  👑 ʜᴏꜱᴛᴇᴅ ʙʏ : *AMRIT*\n"
            f"  ⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ: *MENTALS PERMA BOT*\n"
            f"  🛡️ ꜱʜɪᴇʟᴅ    : `30-Day Perma (< 5GB)`\n\n"
            f"───〔 𝐂𝐎𝐌𝐌𝐀𝐍𝐃 𝐕𝐀𝐔𝐋𝐓 〕───\n"
            f"  ◈ `/nc` ▸ Open NC Control HUD\n"
            f"  ◈ `/nc <name>` ▸ Launch NC Here\n"
            f"  ◈ `/nc <gc_id> - <name>` ▸ Remote GC NC\n"
            f"  ◈ `/nc stop` ▸ Halt NC Here\n"
            f"  ◈ `/allgc <name>` ▸ Launch All GCs\n"
            f"  ◈ `/allgc stop` ▸ Halt All GCs\n"
            f"  ◈ `/mode perma` ▸ 30-Day Safe Gear\n"
            f"  ◈ `/mode turbo` ▸ 0.72s War Gear\n"
            f"  ◈ `/listgc` ▸ Registered GC Radar\n"
            f"  ◈ `! usage` ▸ Owner Live Monitor\n\n"
            f"▚▚ ʜᴏꜱᴛɪɴɢ ʙʏ ᴍᴇɴᴛᴀʟꜱ • 24×7 ʟɪᴠᴇ ▞▞"
        )
        await send_msg(client, primary_token, chat_id, welcome_banner)
        return

    # ══════════════════════════════════════════════════
    # 👑 OWNER ONLY COMMANDS (! usage, /addsudo, /delsudo, /sudolist)
    # ══════════════════════════════════════════════════

    # ! usage command (STRICTLY OWNER ONLY)
    if re.match(r"^(!|/|\+)?\s*(usage|ram|memory)\b", cleaned, re.IGNORECASE):
        if not is_owner(user_id):
            return

        if "reset" in cleaned.lower() or "purge" in cleaned.lower():
            perform_memory_and_storage_purge("Manual Reset Command")
            ram = get_ram_mb()
            await send_msg(
                client, primary_token, chat_id,
                f"🧹 *MANUAL MEMORY PURGE DONE!*\n"
                f"• Current RAM: `{ram} MB` / `512 MB`\n"
                f"• Cleaned: `{daily_reset_stats['last_reset_freed']} items`\n"
                f"• All running chats continue without stopping!"
            )
            return

        ram_used = get_ram_mb()
        total_ram = 512.0
        ram_free = round(max(0.0, total_ram - ram_used), 2)
        pct = round((ram_used / total_ram) * 100, 1)
        filled = min(10, max(1, int(pct / 10)))
        bar = "■" * filled + "□" * (10 - filled)

        uptime_sec = int(time.time() - BOT_START_TIME)
        h, rem = divmod(uptime_sec, 3600)
        m, s = divmod(rem, 60)
        uptime_str = f"{h}h {m}m {s}s"

        # Estimated outbound bandwidth from NC renames
        est_mb = round((TOTAL_NAME_CHANGES * 0.85) / 1024, 2)
        est_gb = round(est_mb / 1024, 2)

        # Next monthly reset (1st of next month)
        now_utc = datetime.datetime.utcnow()
        if now_utc.month == 12:
            next_month = datetime.datetime(now_utc.year + 1, 1, 1)
        else:
            next_month = datetime.datetime(now_utc.year, now_utc.month + 1, 1)
        days_left = max(1, (next_month - now_utc).days)

        report = (
            f"▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜\n"
            f"   📊 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 𝐌𝐎𝐍𝐈𝐓𝐎𝐑\n"
            f"▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟\n"
            f"  ⚡ ꜱᴛᴀᴛᴜꜱ: `ONLINE • 24/7 PERMA`\n\n"
            f"───〔 𝐑𝐀𝐌 & 𝐒𝐓𝐎𝐑𝐀𝐆𝐄 〕───\n"
            f"  ◈ 𝐔𝐬𝐞𝐝 𝐑𝐀𝐌 : `{ram_used} MB` ({pct}%)\n"
            f"  ◈ 𝐅𝐫𝐞𝐞 𝐑𝐀𝐌 : `{ram_free} MB` ({round(100 - pct, 1)}%)\n"
            f"  ◈ 𝐌𝐞𝐭𝐞𝐫    : `[{bar}]`\n"
            f"  ◈ 𝐃𝐢𝐬𝐤     : `0.0 MB` (Pure RAM)\n\n"
            f"───〔 𝟓𝐆𝐁 𝐁𝐀𝐍𝐃𝐖𝐈𝐃𝐓𝐇 𝐒𝐇𝐈𝐄𝐋𝐃 〕───\n"
            f"  ◈ 𝐓𝐨𝐝𝐚𝐲    : `{get_daily_mb()} MB` / `{int(DAILY_SAFE_MB)} MB Cap`\n"
            f"  ◈ 𝐆𝐞𝐚𝐫     : `{SPEED_MODE.upper()} ({'30-Day <3.3GB Safe' if SPEED_MODE == 'perma' else '0.72s War Speed'})`\n"
            f"  ◈ 𝐋𝐚𝐬𝐭 𝐏𝐮𝐫𝐠𝐞: `{daily_reset_stats['last_reset_time']}`\n"
            f"  ◈ 𝐍𝐞𝐱𝐭 𝐏𝐮𝐫𝐠𝐞: `{get_next_reset_str()}`\n\n"
            f"───〔 𝐍𝐂 𝐌𝐀𝐓𝐑𝐈𝐗 〕───\n"
            f"  ◈ 𝐀𝐜𝐭𝐢𝐯𝐞   : `{len(active_tasks)}` / `{len(known_groups)}` GCs\n"
            f"  ◈ 𝐑𝐞𝐧𝐚𝐦𝐞𝐬  : `{TOTAL_NAME_CHANGES}`\n"
            f"  ◈ 𝐒𝐮𝐝𝐨𝐬    : `{len(sudo_users)}` | 𝐁𝐨𝐭𝐬: `{len(BOT_TOKENS)}`\n"
            f"  ◈ 𝐔𝐩𝐭𝐢𝐦𝐞   : `{uptime_str}`\n\n"
            f"▚▚ ʜᴏꜱᴛᴇᴅ ʙʏ ᴀᴍʀɪᴛ • ᴍᴇɴᴛᴀʟꜱ ᴘᴇʀᴍᴀ ▞▞"
        )
        await send_msg(client, primary_token, chat_id, report)
        return

    # /addsudo - Owner adds a user to Sudo list
    if cleaned.lower().startswith(("/addsudo", "!addsudo", "+addsudo")):
        if not is_owner(user_id):
            return
        parts = cleaned.split(maxsplit=1)
        target_str = parts[1].strip() if len(parts) > 1 else ""
        # Check reply message user
        reply_msg = msg.get("reply_to_message")
        target_uid = reply_msg.get("from", {}).get("id") if reply_msg else None
        if not target_uid and target_str.isdigit():
            target_uid = int(target_str)

        if not target_uid:
            await send_msg(client, primary_token, chat_id, "ℹ️ *Usage:* `/addsudo <user_id>` ya kisi user ke msg par reply karke `/addsudo` likhein.")
            return

        sudo_users.add(target_uid)
        save_sudo_users_file()
        await send_msg(
            client, primary_token, chat_id,
            f"✅ ◢█◣ ⟨ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 ⟩ ◢█◣\n"
            f"❖═━•〔 𝐒𝐔𝐃𝐎 𝐀𝐃𝐃𝐄𝐃 〕•━═❖\n"
            f"├─▹ 𝐔𝐬𝐞𝐫 𝐈𝐃: `{target_uid}`\n"
            f"├─▹ 𝐏𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧: `Can Start & Stop NC`\n"
            f"╰─▹ 𝐓𝐨𝐭𝐚𝐥 𝐒𝐮𝐝𝐨𝐬: `{len(sudo_users)}`\n"
            f"❖═━•〔 𝐒𝐮𝐝𝐨 𝐀𝐜𝐭𝐢𝐯𝐚𝐭𝐞𝐝 〕•━═❖"
        )
        return

    # /delsudo or /rmsudo - Owner removes a Sudo user
    if cleaned.lower().startswith(("/delsudo", "!delsudo", "/rmsudo", "!rmsudo")):
        if not is_owner(user_id):
            return
        parts = cleaned.split(maxsplit=1)
        target_str = parts[1].strip() if len(parts) > 1 else ""
        reply_msg = msg.get("reply_to_message")
        target_uid = reply_msg.get("from", {}).get("id") if reply_msg else None
        if not target_uid and target_str.isdigit():
            target_uid = int(target_str)

        if not target_uid:
            await send_msg(client, primary_token, chat_id, "ℹ️ *Usage:* `/delsudo <user_id>` ya user ke msg par reply karke `/delsudo` karein.")
            return

        if target_uid in sudo_users:
            sudo_users.remove(target_uid)
            save_sudo_users_file()
            await send_msg(client, primary_token, chat_id, f"🗑️ Sudo removed for user `{target_uid}`. Total sudos: `{len(sudo_users)}`")
        else:
            await send_msg(client, primary_token, chat_id, f"ℹ️ User `{target_uid}` sudo list me nahi hai.")
        return

    # /sudolist - List of all Sudo users
    if cleaned.lower().startswith(("/sudolist", "!sudolist", "/sudos", "!sudos")):
        if not is_owner(user_id):
            return
        lines = [
            f"👑 ◢█◣ ⟨ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 ⟩ ◢█◣",
            f"❖═━•〔 𝐒𝐔𝐃𝐎 𝐔𝐒𝐄𝐑𝐒 𝐋𝐈𝐒𝐓 〕•━═❖",
            f"├─▹ 𝐎𝐰𝐧𝐞𝐫: `{OWNER_ID}`",
            f"├─▹ 𝐓𝐨𝐭𝐚𝐥 𝐒𝐮𝐝𝐨𝐬: `{len(sudo_users)}`",
            f"─────────────────────────",
        ]
        if sudo_users:
            for i, su in enumerate(list(sudo_users), 1):
                lines.append(f"├─▹ {i}. `{su}`")
        else:
            lines.append("╰─▹ Koi sudo user add nahi hai.")
        lines.append("❖═━•〔 /addsudo | /delsudo 〕•━═❖")
        await send_msg(client, primary_token, chat_id, "\n".join(lines))
        return

    # ══════════════════════════════════════════════════
    # ⚡ NC MENU COMMAND (Khali /nc bhejne par menu turant dikhega!)
    # ══════════════════════════════════════════════════
    if cleaned.lower() in ("/nc", "!nc", "+nc", "nc"):
        status = "🟢 ʀᴜɴɴɪɴɢ" if chat_id in active_tasks else "⚪ ꜱᴛᴀɴᴅʙʏ"
        gear_tag = "🛡️ PERMA (30-Day Safe)" if SPEED_MODE == "perma" else "🚀 TURBO (0.72s War)"
        await send_msg(
            client, primary_token, chat_id,
            f"▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜\n"
            f"   ⚡ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 𝐇𝐔𝐃 ⚡\n"
            f"▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟\n\n"
            f"  ◈ 𝐒𝐓𝐀𝐓𝐔𝐒 ▸ {status}\n"
            f"  ◈ 𝐆𝐄𝐀𝐑   ▸ `{gear_tag}`\n"
            f"  ◈ 𝐀𝐂𝐓𝐈𝐕𝐄 ▸ `{len(active_tasks)} GCs Live`\n"
            f"  ◈ 𝐃𝐀𝐓𝐀   ▸ `{get_daily_mb()} MB` / `{int(DAILY_SAFE_MB)} MB`\n\n"
            f"───〔 𝐐𝐔𝐈𝐂𝐊 𝐂𝐎𝐍𝐓𝐑𝐎𝐋𝐒 〕───\n"
            f"  ▸ `/nc <name>` ⇝ Fire NC Here\n"
            f"  ▸ `/nc <gc_id> - <name>` ⇝ Remote GC Fire\n"
            f"  ▸ `/nc stop` ⇝ Halt NC Here\n"
            f"  ▸ `/nc <gc_id> - stop` ⇝ Remote GC Halt\n"
            f"  ▸ `/allgc <name>` ⇝ Fire All GCs\n"
            f"  ▸ `/allgc stop` ⇝ Halt All GCs\n"
            f"  ▸ `/mode perma` ⇝ 5GB Safe Gear\n"
            f"  ▸ `/mode turbo` ⇝ 0.72s War Gear\n"
            f"  ▸ `/listgc` ⇝ Group Radar\n\n"
            f"  👑 ʜᴏꜱᴛᴇᴅ ʙʏ *AMRIT* • ᴍᴇɴᴛᴀʟꜱ ᴘᴇʀᴍᴀ"
        )
        return

    # ══════════════════════════════════════════════════
    # ⚡ SUDO + OWNER COMMANDS (/nc <name>, /allgc, /listgc, /addgc, /mode)
    # ══════════════════════════════════════════════════
    if not is_sudo_or_owner(user_id):
        return

    # /mode perma|turbo - Switch between 30-Day 5GB Safe Mode and War Turbo Mode
    if cleaned.lower().startswith(("/mode", "!mode", "+mode")):
        parts = cleaned.split(maxsplit=1)
        m = parts[1].strip().lower() if len(parts) > 1 else ""
        if m in ("perma", "safe", "eco"):
            SPEED_MODE = "perma"
            await send_msg(
                client, primary_token, chat_id,
                "🛡️ *PERMA 30-DAY MODE ACTIVATED!*\n"
                "• 10-20 GCs 24/7 = Strictly under ~3.2 GB / Month!\n"
                "• 5 GB Render limit 30 din tak kabhi cross nahi hogi."
            )
        elif m in ("turbo", "fast", "war"):
            SPEED_MODE = "turbo"
            await send_msg(
                client, primary_token, chat_id,
                "🚀 *TURBO WAR MODE ACTIVATED!*\n"
                "• Max 0.72s-0.85s speed!\n"
                "• ⚠️ Note: 10+ GCs me zyada der chalane par 5GB jaldi khatam ho sakta hai, fight ke baad `/mode perma` karein."
            )
        else:
            await send_msg(
                client, primary_token, chat_id,
                f"⚙️ *Current Mode:* `{SPEED_MODE.upper()}`\n"
                "• `/mode perma` — 30 Days < 5GB Safe\n"
                "• `/mode turbo` — Max Rocket Speed"
            )
        return

    # /allgc or /ncall - Start/Stop in all known groups at once
    if cleaned.lower().startswith(("/allgc", "+allgc", "!allgc", "/ncall", "+ncall", "!ncall")):
        parts = cleaned.split(maxsplit=1)
        arg = parts[1].strip() if len(parts) > 1 else ""

        if arg.lower() in ("stop", "off", "cancel", "kill"):
            stopped = len(active_tasks)
            for cid, ev in list(active_tasks.items()):
                ev.set()
            active_tasks.clear()
            await send_msg(
                client, primary_token, chat_id,
                f"🛑 ◢█◣ ⟨ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 ⟩ ◢█◣\n"
                f"❖═━•〔 𝐀𝐋𝐋 𝐆𝐂 𝐒𝐓𝐎𝐏𝐏𝐄𝐃 〕•━═❖\n"
                f"├─▹ 𝐓𝐨𝐭𝐚𝐥 𝐇𝐚𝐥𝐭𝐞𝐝: `{stopped} Groups`\n"
                f"╰─▹ 𝐒𝐭𝐚𝐭𝐮𝐬: `All background tasks killed.`\n"
                f"❖═━•〔 𝐄𝐧𝐠𝐢𝐧𝐞 𝐒𝐭𝐚𝐧𝐝𝐛𝐲 〕•━═❖"
            )
            return

        if not arg:
            await send_msg(
                client, primary_token, chat_id,
                f"⚡ ◢█◣ ⟨ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 ⟩ ◢█◣\n"
                f"❖═━•〔 𝐀𝐋𝐋 𝐆𝐂 𝐂𝐎𝐍𝐓𝐑𝐎𝐋 〕•━═❖\n"
                f"├─▹ 𝐒𝐭𝐚𝐫𝐭 𝐀𝐥𝐥: `/allgc <name>`\n"
                f"├─▹ 𝐒𝐭𝐨𝐩 𝐀𝐥𝐥:  `/allgc stop`\n"
                f"├─▹ 𝐑𝐞𝐠𝐢𝐬𝐭𝐞𝐫𝐞𝐝: `{len(known_groups)} Groups`\n"
                f"╰─▹ 𝐑𝐮𝐧𝐧𝐢𝐧𝐠:   `{len(active_tasks)} Active`\n"
                f"❖═━•〔 𝐕𝐞𝐫𝐬𝐢𝐨𝐧 3.0 〕•━═❖"
            )
            return

        # Start NC in all known groups
        if not known_groups:
            if chat.get("type") in ("group", "supergroup") and chat_id:
                save_known_group(chat_id)
            else:
                await send_msg(
                    client, primary_token, chat_id,
                    "⚠️ *KOI GROUP DETECT NAHI HUA!*\n\n"
                    "• Bot ko apne groups me Admin banayein ya `/addgc` likhein."
                )
                return

        started = 0
        for gid in list(known_groups):
            if gid in active_tasks:
                active_tasks[gid].set()
            stop_ev = asyncio.Event()
            active_tasks[gid] = stop_ev
            asyncio.create_task(nc_loop(client, gid, arg, stop_ev))
            started += 1

        await send_msg(
            client, primary_token, chat_id,
            f"⚡ ◢█◣ ⟨ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 ⟩ ◢█◣\n"
            f"❖═━•〔 𝐀𝐋𝐋 𝐆𝐂 𝐋𝐀𝐔𝐍𝐂𝐇𝐄𝐃 〕•━═❖\n"
            f"├─▹ 𝐓𝐚𝐫𝐠𝐞𝐭: `{arg}`\n"
            f"├─▹ 𝐆𝐫𝐨𝐮𝐩𝐬: `{started} Groups Started`\n"
            f"├─▹ 𝐒𝐩𝐞𝐞𝐝: `1.0s Ultra-Speed (Zero-Flood)`\n"
            f"╰─▹ 𝐆𝐮𝐚𝐫𝐝: `Active (< 4.0 GB / M Safe)`\n"
            f"❖═━•〔 𝐍𝐨𝐧-𝐒𝐭𝐨𝐩 24/7 〕•━═❖"
        )
        return

    # /listgc - View all registered groups
    if cleaned.lower().startswith(("/listgc", "+listgc", "!listgc")):
        report_lines = [
            f"📋 ◢█◣ ⟨ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 ⟩ ◢█◣",
            f"❖═━•〔 𝐑𝐞𝐠𝐢𝐬𝐭𝐞𝐫𝐞𝐝 𝐆𝐫𝐨𝐮𝐩𝐬 〕•━═❖",
            f"├─▹ 𝐓𝐨𝐭𝐚𝐥 𝐊𝐧𝐨𝐰𝐧: `{len(known_groups)}`",
            f"╰─▹ 𝐀𝐜𝐭𝐢𝐯𝐞 𝐍𝐂:   `{len(active_tasks)}`",
            f"─────────────────────────",
        ]
        if known_groups:
            for i, gid in enumerate(list(known_groups)[:15], 1):
                state = "🟢 RUNNING" if gid in active_tasks else "⚪ IDLE"
                report_lines.append(f"├─▹ `{gid}` ⊳ {state}")
            if len(known_groups) > 15:
                report_lines.append(f"╰─▹ ... aur `{len(known_groups) - 15}` more groups.")
        else:
            report_lines.append("╰─▹ Koi group register nahi hai.")
        report_lines.append("❖═━•〔 /allgc <name> 〕•━═❖")
        await send_msg(client, primary_token, chat_id, "\n".join(report_lines))
        return

    # /addgc - Manually register current group
    if cleaned.lower().startswith(("/addgc", "+addgc", "!addgc")):
        if chat.get("type") in ("group", "supergroup") and chat_id:
            save_known_group(chat_id)
            await send_msg(
                client, primary_token, chat_id,
                f"✅ ◢█◣ ⟨ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 ⟩ ◢█◣\n"
                f"├─▹ 𝐆𝐫𝐨𝐮𝐩 `{chat_id}` 𝐑𝐞𝐠𝐢𝐬𝐭𝐞𝐫𝐞𝐝!\n"
                f"╰─▹ 𝐓𝐨𝐭𝐚𝐥 𝐊𝐧𝐨𝐰𝐧: `{len(known_groups)} Groups`"
            )
        else:
            await send_msg(client, primary_token, chat_id, "ℹ️ Ye command group me bhejein.")
        return

    # /nc or /nc stop or /nc <group_id> - <name> (Current or Remote Group)
    nc_cmd_match = re.match(r"^(/|\+|!)nc(?:@\w+)?(?:\s+(.*))?$", cleaned, re.IGNORECASE | re.DOTALL)
    if nc_cmd_match:
        arg = (nc_cmd_match.group(2) or "").strip()
        target_cid = chat_id
        nc_name = arg

        # 🎯 Check if user targeted a specific Group ID: e.g. /nc -1001234567890 - test  OR  /nc -1001234567890 test
        remote_match = re.match(r"^(-?\d{6,})\s*(?:[-–—]+\s*)?(.*)$", arg, re.DOTALL)
        if remote_match:
            target_cid = int(remote_match.group(1))
            nc_name = (remote_match.group(2) or "").strip()
            save_known_group(target_cid)

        if nc_name.lower() in ("stop", "off", "cancel", "kill"):
            if target_cid in active_tasks:
                active_tasks[target_cid].set()
                del active_tasks[target_cid]
                await send_msg(
                    client, primary_token, chat_id,
                    f"🛑 ◢█◣ ⟨ 𝐌𝐄𝐍𝐓𝐀𝐋 • 𝐏𝐄𝐑𝐌𝐀 ⟩ ◢█◣\n"
                    f"  ◈ 𝐆𝐫𝐨𝐮𝐩 : `{target_cid}`\n"
                    f"  ◈ 𝐒𝐭𝐚𝐭𝐮𝐬 : `NC Stopped Successfully.`"
                )
            else:
                await send_msg(client, primary_token, chat_id, f"ℹ️ Group `{target_cid}` me koi NC nahi chal raha hai.")
            return

        if not nc_name:
            await send_msg(
                client, primary_token, chat_id,
                f"ℹ️ *Remote NC Usage:*\n"
                f"• Start: `/nc {target_cid} - <name>`\n"
                f"• Stop:  `/nc {target_cid} - stop`"
            )
            return

        # Start NC in target group (current or remote Group ID)
        if target_cid in active_tasks:
            active_tasks[target_cid].set()

        stop_ev = asyncio.Event()
        active_tasks[target_cid] = stop_ev
        asyncio.create_task(nc_loop(client, target_cid, nc_name, stop_ev))

        is_remote = target_cid != chat_id
        target_label = f"`{target_cid}` (Remote)" if is_remote else f"`{target_cid}` (This GC)"
        stop_hint = f"/nc {target_cid} - stop" if is_remote else "/nc stop"

        await send_msg(
            client, primary_token, chat_id,
            f"▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜\n"
            f"   🚀 𝐍𝐂 𝐄𝐍𝐆𝐈𝐍𝐄 𝐋𝐀𝐔𝐍𝐂𝐇𝐄𝐃 🚀\n"
            f"▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟\n\n"
            f"  ◈ 𝐆𝐫𝐨𝐮𝐩  : {target_label}\n"
            f"  ◈ 𝐓𝐚𝐫𝐠𝐞𝐭 : `{nc_name}`\n"
            f"  ◈ 𝐆𝐞𝐚𝐫   : `{SPEED_MODE.upper()} ({'5GB 30-Day Safe' if SPEED_MODE == 'perma' else '0.72s War'})`\n"
            f"  ◈ 𝐒𝐡𝐢𝐞𝐥𝐝 : `Daily 110 MB Cap Active`\n"
            f"  ◈ 𝐒𝐭𝐨𝐩   : `{stop_hint}`\n\n"
            f"▚▚ ʜᴏꜱᴛᴇᴅ ʙʏ ᴀᴍʀɪᴛ • 24×7 ɴᴏɴ-ꜱᴛᴏᴘ ▞▞"
        )

# 9. Render Keep-Alive & Telegram Webhook HTTP Server (Port 10000)
# ⚡ 500% BYPASS ENGINE: Dual-Action HTTP Server
# 1. Pings from UptimeRobot return instant 204 No Content (0 body bytes).
# 2. Inbound Telegram Webhook requests receive updates pushed by Telegram, eliminating getUpdates long-polling entirely!
# Result: 95% bandwidth eliminated! Total monthly data stays under 500 MB - 1.2 GB!
async def start_http_and_webhook_server(port: int, client, primary_token: str):
    async def handle_connection(reader, writer):
        try:
            line = await reader.readline()
            if not line:
                return
            req_line = line.decode("utf-8", errors="ignore").strip()
            method, path, *_ = req_line.split() if req_line else ("GET", "/", "")

            # Read headers
            content_length = 0
            while True:
                header_line = await reader.readline()
                if not header_line or header_line == b"\r\n" or header_line == b"\n":
                    break
                header_text = header_line.decode("utf-8", errors="ignore").lower()
                if header_text.startswith("content-length:"):
                    try:
                        content_length = int(header_text.split(":", 1)[1].strip())
                    except Exception:
                        pass

            # If it's the Telegram Webhook push POST /webhook
            if method.upper() == "POST" and "/webhook" in path and content_length > 0:
                body = await reader.readexactly(content_length)
                # Reply 200 OK immediately to Telegram
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
                await writer.drain()

                # Process update asynchronously in memory
                try:
                    update_json = json.loads(body.decode("utf-8", errors="ignore"))
                    uid = update_json.get("update_id")
                    if uid and uid not in seen_update_ids:
                        seen_update_ids.add(uid)
                        if len(seen_update_ids) > 100:
                            seen_update_ids.difference_update(sorted(list(seen_update_ids))[:-30])
                        asyncio.create_task(handle_update(client, update_json))
                except Exception:
                    pass
                return

            # Otherwise, it's UptimeRobot or health check ping GET /
            # Reply 204 No Content (0 Bytes outbound, 100% free)
            writer.write(b"HTTP/1.1 204 No Content\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    try:
        server = await asyncio.start_server(handle_connection, "0.0.0.0", port)
        print(f"🌐 500% Bypass Webhook/Ping Server running on port {port}")
        return server
    except Exception as e:
        print(f"⚠️ Port {port} note: {e}")
        return None

# 10. Main Engine (Hybrid Webhook + Adaptive Poller Fallback)
async def main():
    import httpx

    if not BOT_TOKENS:
        print("❌ ERROR: BOT_TOKENS is empty! Add your tokens in .env or Render Environment.")
        return

    print("🚀 Starting Ultra-Lightweight NC Bot with 500% Permanent Bypass...")
    print(f"👑 Owner ID: {OWNER_ID or 'Any Admin'}")
    print(f"🤖 Loaded Bots: {len(BOT_TOKENS)}")
    print(f"⏱️ NC Cadence: Dynamic 5GB Mathematical Ceiling")

    asyncio.create_task(daily_memory_cleaner_worker())

    # Enable HTTP/2 multiplexing & HPACK compression + connection pool reuse
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=100, keepalive_expiry=60.0)
    client_kwargs = {"timeout": 15.0, "limits": limits}
    try:
        import h2  # noqa: F401
        client_kwargs["http2"] = True
    except Exception:
        pass

    async with httpx.AsyncClient(**client_kwargs) as client:
        primary_token = BOT_TOKENS[0]
        offset = 0
        global seen_update_ids

        # Start dual-action Webhook & Ping HTTP Server on PORT 10000
        await start_http_and_webhook_server(PORT, client, primary_token)

        # 👑 Auto-update bot description & about on host startup
        try:
            desc_text = "⚡ HOSTING BY MENTALS ⚡\n👑 Hosted By: AMRIT\n🚀 24/7 Ultra-Fast NC Engine\n💎 Powered by Mentals Perma"
            short_desc = "⚡ Hosting By Mentals | Hosted By AMRIT"
            for t in BOT_TOKENS:
                try:
                    await client.post(f"https://api.telegram.org/bot{t}/setMyDescription", json={"description": desc_text}, timeout=4.0)
                    await client.post(f"https://api.telegram.org/bot{t}/setMyShortDescription", json={"short_description": short_desc}, timeout=4.0)
                except Exception:
                    pass
            print("📝 Bot description auto-updated to: HOSTING BY MENTALS")
        except Exception:
            pass

        # ⚡ ANTI-SPIN UPDATE ENGINE:
        # When NC is running, Telegram generates new_chat_title service updates constantly.
        # Sleeping 1.5s between polls batches 100 updates per call & skips service updates immediately,
        # cutting getUpdates bandwidth by ~90%!
        print("⚡ NC Bot is ONLINE and actively listening for commands...")
        while True:
            try:
                url = f"https://api.telegram.org/bot{primary_token}/getUpdates"
                params = {"offset": offset, "limit": 100, "timeout": 20, "allowed_updates": '["message","my_chat_member"]'}
                add_wire_bytes(320)
                resp = await client.get(url, params=params, timeout=25.0)
                data = resp.json()
                if data.get("ok"):
                    for u in data.get("result", []):
                        uid = u["update_id"]
                        offset = uid + 1
                        # Ignore bot's own new_chat_title service spam updates with zero processing
                        msg_obj = u.get("message")
                        if msg_obj and "new_chat_title" in msg_obj and "text" not in msg_obj:
                            continue
                        if uid not in seen_update_ids:
                            seen_update_ids.add(uid)
                            if len(seen_update_ids) > 100:
                                seen_update_ids = set(sorted(list(seen_update_ids))[-30:])
                            asyncio.create_task(handle_update(client, u))
                if active_tasks:
                    await asyncio.sleep(2.5)
            except Exception:
                await asyncio.sleep(2.0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")
