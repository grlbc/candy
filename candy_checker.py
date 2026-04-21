import itertools
import string
import os
import sys
import time
import requests
import datetime
import getpass
import webbrowser

PINK   = "\033[95m"
RED    = "\033[91m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def p(text, color=PINK):
    print(color + text + RESET)

def ask(prompt, color=CYAN):
    return input(color + "  " + prompt + " " + RESET).strip()

def banner():
    os.system("cls" if os.name == "nt" else "clear")
    p(r"""
  /*  ++----------------------------------------------------------++  */
  /*  ++----------------------------------------------------------++  */
  /*                                                                   */
  /*      #####    ###   ##   ##  ######  ##   ##                     */
  /*     ##   ##  ## ##  ###  ##  ##   ## ##   ##                     */
  /*     ##       ##   ## ## # ##  ##   ##  ## ##                     */
  /*     ##       ####### ##  ###  ##   ##   ###                      */
  /*     ##   ##  ##   ## ##   ##  ##   ##    ##                      */
  /*      #####   ##   ## ##   ##  ######     ##                      */
  /*                                                                   */
  /*                      [ by grib ]                                 */
  /*  ++----------------------------------------------------------++  */
  /*  ++----------------------------------------------------------++  */
    """)

# ════════════════════════════════════════════════
#  DISCORD API
# ════════════════════════════════════════════════

def validate_token(token):
    try:
        r = requests.get("https://discord.com/api/v9/users/@me",
                         headers={"Authorization": token}, timeout=8)
        if r.status_code == 200:
            d = r.json()
            return True, d.get("username","unknown")
    except:
        pass
    return False, None

def try_claim(token, password, username):
    try:
        r = requests.patch(
            "https://discord.com/api/v9/users/@me",
            headers={"Authorization": token, "Content-Type": "application/json"},
            json={"username": username, "password": password},
            timeout=8
        )
        if r.status_code == 200:
            return ("claimed", r.json().get("username", username))
        elif r.status_code == 429:
            return ("ratelimit", r.json().get("retry_after", 5))
        elif r.status_code in (400, 401):
            body = str(r.json()).lower()
            if "password" in body and any(x in body for x in ("incorrect","invalid","wrong")):
                return "bad_password"
            return "taken"
    except:
        pass
    return "error"

# ════════════════════════════════════════════════
#  DISCORD SETUP (token + password)
# ════════════════════════════════════════════════

def discord_setup():
    banner()
    p("  DISCORD LOGIN\n")
    p("  How to get your token:", YELLOW)
    p("  1. Open Discord in your browser (discord.com)", YELLOW)
    p("  2. Press Ctrl+Shift+I", YELLOW)
    p("  3. Go to Console tab and paste:", YELLOW)
    p('  webpackChunkdiscord_app.push([[0],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}])&&m.find(m=>m?.exports?.default?.getToken).exports.default.getToken()', CYAN)
    p("  4. Copy the result\n", YELLOW)

    token = input(PINK + "  Token: " + RESET).strip()
    p("\n  Validating...", CYAN)
    valid, uname = validate_token(token)
    if not valid:
        p("  Invalid token!", RED)
        input(PINK + "  Press Enter..." + RESET)
        return None, None, None

    p(f"  Logged in as: {uname}", GREEN)
    pw = getpass.getpass(PINK + "  Account Password: " + RESET)
    if not pw:
        p("  No password entered.", RED)
        input(PINK + "  Press Enter..." + RESET)
        return None, None, None

    p("  Ready!\n", GREEN)
    time.sleep(0.6)
    return token, pw, uname

# ════════════════════════════════════════════════
#  DISCORD USERNAME CLAIMER
# ════════════════════════════════════════════════

def run_claimer(token, password, orig_uname, length, mode):
    charset = string.ascii_lowercase + (string.digits if mode == "char" else "")
    label   = "char" if mode == "char" else "letter"
    total   = len(charset) ** length
    outfile = f"{length}{label}_claimed_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    delay   = 0.3   # Start fast — auto-adjusts on rate limit

    p(f"\n  Checking {total:,} {length}-{label} combos...")
    p(f"  Will auto-claim and stop on first available username.", YELLOW)
    p(f"  CTRL+C to stop.\n", YELLOW)
    input(PINK + "  Press Enter to start..." + RESET)

    checked = 0
    try:
        with open(outfile, "w") as f:
            for combo in itertools.product(charset, repeat=length):
                username = "".join(combo)
                checked += 1
                sys.stdout.write(
                    f"\r  {PINK}[{checked}/{total}] Trying: {CYAN}{username}{PINK} | delay: {delay:.2f}s{RESET}  "
                )
                sys.stdout.flush()

                result = try_claim(token, password, username)

                if isinstance(result, tuple) and result[0] == "claimed":
                    p(f"\n\n  [CLAIMED] Your new username: {result[1]}", GREEN)
                    f.write(f"CLAIMED: {result[1]}\nPrevious: {orig_uname}\nTime: {datetime.datetime.now()}\n")
                    p(f"  Saved to {outfile}", GREEN)
                    input(PINK + "\n  Press Enter to return..." + RESET)
                    return
                elif isinstance(result, tuple) and result[0] == "ratelimit":
                    retry = float(result[1])
                    p(f"\n  [RATE LIMIT] Sleeping {retry:.1f}s...", YELLOW)
                    time.sleep(retry + 0.3)
                    delay = min(delay + 0.1, 5.0)
                elif result == "bad_password":
                    p(f"\n  [ERROR] Wrong password! Stopping.", RED)
                    break
                else:
                    time.sleep(delay)
    except KeyboardInterrupt:
        p(f"\n  Stopped at {checked} checked.", YELLOW)

    p(f"  Saved to {outfile}", GREEN)
    input(PINK + "\n  Press Enter to return..." + RESET)

# ════════════════════════════════════════════════
#  USERNAME LIST GENERATORS
# ════════════════════════════════════════════════

def gen_list(length, mode):
    charset = string.ascii_lowercase + (string.digits if mode == "char" else "")
    label   = "char" if mode == "char" else "letter"
    outfile = f"{length}{label}_usernames.txt"
    total   = len(charset) ** length
    p(f"\n  Generating {total:,} combos -> {outfile}...")
    with open(outfile, "w") as f:
        for combo in itertools.product(charset, repeat=length):
            f.write("".join(combo) + "\n")
    p(f"  Done! Saved to {outfile}", GREEN)
    input(PINK + "\n  Press Enter to return..." + RESET)

# ════════════════════════════════════════════════
#  VERIFICATION GENERATORS
# ════════════════════════════════════════════════

def save_app(platform, content):
    fname = f"{platform}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content)
    p(f"\n  Saved to: {fname}", GREEN)

def verify_tiktok():
    banner(); p("  TIKTOK VERIFICATION GENERATOR\n", CYAN)
    name     = ask("Full name / brand name:")
    username = ask("TikTok username (no @):")
    category = ask("Category (Musician, Gamer, Brand, etc):")
    followers= ask("Follower count:")
    desc     = ask("What is your account about?")
    notable  = ask("Why are you notable? (press, awards, etc):")
    news     = ask("News/media links (or N):")
    other    = ask("Verified on other platforms? (or N):")
    website  = ask("Website (or N):")
    out = f"""
========================================
  TIKTOK VERIFICATION APPLICATION
  Generated by Candy | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
========================================
NAME:     {name}
USERNAME: @{username}
CATEGORY: {category}
FOLLOWERS:{followers}
ABOUT:    {desc}
NOTABLE:  {notable}
MEDIA:    {news if news.upper()!='N' else 'N/A'}
OTHER VERIFIED: {other if other.upper()!='N' else 'N/A'}
WEBSITE:  {website if website.upper()!='N' else 'N/A'}
========================================
SUBMIT AT:
  In-app: Profile > Menu > Settings > Account > Verification
  Online: https://www.tiktok.com/legal/report/verification
========================================"""
    print(PINK + out + RESET)
    save_app("tiktok_verification", out)
    if ask("Open form in browser? (Y/N):").upper() == "Y":
        webbrowser.open("https://www.tiktok.com/legal/report/verification")
    input(PINK + "\n  Press Enter to return..." + RESET)

def verify_instagram():
    banner(); p("  INSTAGRAM VERIFICATION GENERATOR\n", CYAN)
    name     = ask("Full name / brand name:")
    username = ask("Instagram username (no @):")
    category = ask("Category (News, Sports, Music, Brand, etc):")
    followers= ask("Follower count:")
    desc     = ask("Who are you?")
    notable  = ask("Why are you a notable public figure?")
    news     = ask("News/media links (or N):")
    id_type  = ask("ID type (Passport, Drivers License, etc):")
    out = f"""
========================================
  INSTAGRAM VERIFICATION APPLICATION
  Generated by Candy | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
========================================
NAME:     {name}
USERNAME: @{username}
CATEGORY: {category}
FOLLOWERS:{followers}
ABOUT:    {desc}
NOTABLE:  {notable}
MEDIA:    {news if news.upper()!='N' else 'N/A'}
ID TYPE:  {id_type}
========================================
SUBMIT AT:
  App: Profile > Menu > Settings > Account > Request Verification
  OR Meta Verified (paid): https://www.facebook.com/verified
========================================"""
    print(PINK + out + RESET)
    save_app("instagram_verification", out)
    if ask("Open form in browser? (Y/N):").upper() == "Y":
        webbrowser.open("https://www.instagram.com/accounts/request_verification/")
    input(PINK + "\n  Press Enter to return..." + RESET)

def verify_youtube():
    banner(); p("  YOUTUBE VERIFICATION GENERATOR\n", CYAN)
    name     = ask("Channel name:")
    handle   = ask("Channel URL / handle:")
    subs     = ask("Subscriber count:")
    category = ask("Category (Gaming, Music, Education, etc):")
    desc     = ask("What is your channel about?")
    notable  = ask("Why should YouTube verify you?")
    website  = ask("Official website (or N):")
    out = f"""
========================================
  YOUTUBE VERIFICATION APPLICATION
  Generated by Candy | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
========================================
CHANNEL:  {name}
HANDLE:   {handle}
SUBS:     {subs}
CATEGORY: {category}
ABOUT:    {desc}
NOTABLE:  {notable}
WEBSITE:  {website if website.upper()!='N' else 'N/A'}
========================================
SUBMIT AT:
  Automatic at 100K subs.
  Channel verification tick: https://www.youtube.com/verify
  Official Artist Channel: contact your music distributor
========================================"""
    print(PINK + out + RESET)
    save_app("youtube_verification", out)
    if ask("Open in browser? (Y/N):").upper() == "Y":
        webbrowser.open("https://www.youtube.com/verify")
    input(PINK + "\n  Press Enter to return..." + RESET)

def verify_twitter():
    banner(); p("  X / TWITTER VERIFICATION GENERATOR\n", CYAN)
    name     = ask("Full name / brand name:")
    username = ask("X username (no @):")
    followers= ask("Follower count:")
    category = ask("Category (Journalist, Brand, Government, etc):")
    desc     = ask("Who are you?")
    notable  = ask("Why are you notable?")
    website  = ask("Official website (or N):")
    out = f"""
========================================
  X / TWITTER VERIFICATION APPLICATION
  Generated by Candy | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
========================================
NAME:     {name}
USERNAME: @{username}
FOLLOWERS:{followers}
CATEGORY: {category}
ABOUT:    {desc}
NOTABLE:  {notable}
WEBSITE:  {website if website.upper()!='N' else 'N/A'}
========================================
SUBMIT AT:
  Blue (personal): https://x.com/i/premium_sign_up
  Gold (org):      https://x.com/i/verified-orgs-signup
  Government:      https://help.x.com/forms
========================================"""
    print(PINK + out + RESET)
    save_app("twitter_verification", out)
    if ask("Open in browser? (Y/N):").upper() == "Y":
        webbrowser.open("https://x.com/i/premium_sign_up")
    input(PINK + "\n  Press Enter to return..." + RESET)

def verify_twitch():
    banner(); p("  TWITCH PARTNER APPLICATION GENERATOR\n", CYAN)
    p("  Requirements: 25hrs streamed, 12 stream days, 75 avg viewers (last 30 days)\n", YELLOW)
    name     = ask("Name / brand:")
    username = ask("Twitch username:")
    viewers  = ask("Avg concurrent viewers (last 30 days):")
    hours    = ask("Hours streamed (last 30 days):")
    days     = ask("Unique stream days (last 30 days):")
    followers= ask("Follower count:")
    category = ask("Main game / category:")
    desc     = ask("What makes your stream unique?")
    notable  = ask("Achievements / press (or N):")
    out = f"""
========================================
  TWITCH PARTNER APPLICATION
  Generated by Candy | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
========================================
NAME:       {name}
USERNAME:   {username}
AVG VIEWERS:{viewers}
HRS STREAMED:{hours}
STREAM DAYS:{days}
FOLLOWERS:  {followers}
CATEGORY:   {category}
ABOUT:      {desc}
NOTABLE:    {notable if notable.upper()!='N' else 'N/A'}
========================================
SUBMIT AT:
  https://www.twitch.tv/partner/signup
  OR: Dashboard > Achievements > Path to Partner
========================================"""
    print(PINK + out + RESET)
    save_app("twitch_partner", out)
    if ask("Open in browser? (Y/N):").upper() == "Y":
        webbrowser.open("https://www.twitch.tv/partner/signup")
    input(PINK + "\n  Press Enter to return..." + RESET)

def verify_linkedin():
    banner(); p("  LINKEDIN VERIFICATION GENERATOR\n", CYAN)
    name   = ask("Full name:")
    url    = ask("LinkedIn profile URL:")
    job    = ask("Job title:")
    company= ask("Company / organization:")
    method = ask("Verification method (Work Email / Gov ID / Microsoft Entra):")
    out = f"""
========================================
  LINKEDIN VERIFICATION
  Generated by Candy | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
========================================
NAME:    {name}
PROFILE: {url}
JOB:     {job}
COMPANY: {company}
METHOD:  {method}
========================================
VERIFY AT:
  Profile > More > Verify
  https://www.linkedin.com/help/linkedin/answer/a1360744
========================================"""
    print(PINK + out + RESET)
    save_app("linkedin_verification", out)
    if ask("Open in browser? (Y/N):").upper() == "Y":
        webbrowser.open("https://www.linkedin.com/help/linkedin/answer/a1360744")
    input(PINK + "\n  Press Enter to return..." + RESET)

# ════════════════════════════════════════════════
#  MAIN MENU
# ════════════════════════════════════════════════

_discord_session = (None, None, None)   # token, pw, uname

def get_discord_session():
    global _discord_session
    token, pw, uname = _discord_session
    if token:
        return token, pw, uname
    token, pw, uname = discord_setup()
    if token:
        _discord_session = (token, pw, uname)
    return token, pw, uname

def main():
    global _discord_session
    while True:
        banner()
        p("         The All-In-One Discord Claimer & Verification Tool\n")

        # ── header row ──────────────────────────────────────────────────
        p("  |" + "─" * 26 + "||" + "─" * 26 + "||" + "─" * 26 + "|")
        p("  |{:^26}||{:^26}||{:^26}|".format("  CLAIMER","  GENERATOR","  VERIFY"))
        p("  |" + "─" * 26 + "||" + "─" * 26 + "||" + "─" * 26 + "|")

        rows = [
            (" [01] 2 Char  Claimer  ", " [07] 2 Char  List     ", " [13] TikTok           "),
            (" [02] 3 Char  Claimer  ", " [08] 3 Char  List     ", " [14] Instagram        "),
            (" [03] 4 Char  Claimer  ", " [09] 4 Char  List     ", " [15] YouTube          "),
            (" [04] 2 Letter Claimer ", " [10] 2 Letter List    ", " [16] X / Twitter      "),
            (" [05] 3 Letter Claimer ", " [11] 3 Letter List    ", " [17] Twitch Partner   "),
            (" [06] 4 Letter Claimer ", " [12] 4 Letter List    ", " [18] LinkedIn         "),
        ]
        for a, b, c in rows:
            p("  |- {:<23}|- {:<23}|- {:<23}".format(a, b, c))

        p("  |" + "─" * 26 + "||" + "─" * 26 + "||" + "─" * 26 + "|")
        p("")
        p("                              |- [E] Exit\n")

        c = input(PINK + "  Option: " + RESET).strip().lower()

        # ── Claimer options 01-06 ────────────────────────────────────────
        if c in ("01","1","02","2","03","3","04","4","05","5","06","6"):
            token, pw, uname = get_discord_session()
            if not token:
                continue
            map_ = {
                "01":"01","1":"01","02":"02","2":"02","03":"03","3":"03",
                "04":"04","4":"04","05":"05","5":"05","06":"06","6":"06",
            }
            n = map_[c]
            if   n == "01": run_claimer(token, pw, uname, 2, "char")
            elif n == "02": run_claimer(token, pw, uname, 3, "char")
            elif n == "03": run_claimer(token, pw, uname, 4, "char")
            elif n == "04": run_claimer(token, pw, uname, 2, "letter")
            elif n == "05": run_claimer(token, pw, uname, 3, "letter")
            elif n == "06": run_claimer(token, pw, uname, 4, "letter")

        # ── Generator options 07-12 ──────────────────────────────────────
        elif c in ("07","7"):  gen_list(2, "char")
        elif c in ("08","8"):  gen_list(3, "char")
        elif c in ("09","9"):  gen_list(4, "char")
        elif c in ("10"):      gen_list(2, "letter")
        elif c in ("11"):      gen_list(3, "letter")
        elif c in ("12"):      gen_list(4, "letter")

        # ── Verify options 13-18 ─────────────────────────────────────────
        elif c in ("13"): verify_tiktok()
        elif c in ("14"): verify_instagram()
        elif c in ("15"): verify_youtube()
        elif c in ("16"): verify_twitter()
        elif c in ("17"): verify_twitch()
        elif c in ("18"): verify_linkedin()

        elif c == "e":
            banner()
            p("  Thanks for using Candy! Bye~")
            p("  [ by grib ]\n")
            break
        else:
            p("  Invalid.", RED)
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        p("\n\n  Stopped. Bye!", RED)
