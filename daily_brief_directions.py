import os
import json
import urllib.request
from datetime import datetime, date
import pytz

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"].strip()
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()
TIMEZONE         = "Europe/Dublin"

STEMS    = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEMS_EN = ["Jia","Yi","Bing","Ding","Wu","Ji","Geng","Xin","Ren","Gui"]

# ── Бог Богатства / Бог Счастья — 10-дневный цикл по Небесному Стволу дня ─────
# Верифицировано построчно против infengi.ru на датах июнь-авг 2026, Дублин
WEALTH_GOD    = {0:"ЮВ",1:"ЮВ",2:"З",3:"З",4:"С",5:"С",6:"В",7:"В",8:"Ю",9:"Ю"}
HAPPINESS_GOD = {0:"СВ",1:"СЗ",2:"ЮЗ",3:"Ю",4:"ЮВ",5:"СВ",6:"СЗ",7:"ЮЗ",8:"Ю",9:"ЮВ"}
DIRECTION_RU  = {"С":"Север","Ю":"Юг","В":"Восток","З":"Запад",
                  "СВ":"Северо-Восток","СЗ":"Северо-Запад",
                  "ЮВ":"Юго-Восток","ЮЗ":"Юго-Запад"}

# ── Час Благородного Человека (Tian Yi Gui Ren) — по Небесному Стволу дня ─────
NOBLE_HOUR_BRANCHES = {
    0: ["Бык","Коза"], 1: ["Крыса","Обезьяна"], 2: ["Свинья","Петух"],
    3: ["Свинья","Петух"], 4: ["Бык","Коза"], 5: ["Крыса","Обезьяна"],
    6: ["Бык","Коза"], 7: ["Тигр","Лошадь"], 8: ["Кролик","Тигр"], 9: ["Кролик","Тигр"],
}

# ── Julian Day / day stem ──────────────────────────────────────────────────────
def jd(d: date) -> int:
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12*a - 3
    return d.day + (153*m+2)//5 + 365*y + y//4 - y//100 + y//400 - 32045

def day_stem_idx(d: date) -> int:
    return (jd(d) + 9) % 10

# ── Telegram ──────────────────────────────────────────────────────────────────
def tg_send(text: str):
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Telegram API error {e.code}: {body}")
        raise

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    tz  = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    today = now.date()

    WDAYS = {"Monday":"Понедельник","Tuesday":"Вторник","Wednesday":"Среда",
             "Thursday":"Четверг","Friday":"Пятница","Saturday":"Суббота","Sunday":"Воскресенье"}
    MONTHS_RU = {1:"января",2:"февраля",3:"марта",4:"апреля",5:"мая",6:"июня",
                 7:"июля",8:"августа",9:"сентября",10:"октября",11:"ноября",12:"декабря"}

    wd = WDAYS[now.strftime("%A")]
    dt = f"{today.day} {MONTHS_RU[today.month]}"

    si = day_stem_idx(today)
    day_zh = STEMS[si]
    day_py = STEMS_EN[si]

    wealth_dir = WEALTH_GOD[si]
    happy_dir  = HAPPINESS_GOD[si]
    noble_branches = NOBLE_HOUR_BRANCHES.get(si, [])
    noble_ru = ", ".join(noble_branches)

    msg = f"""<i>{wd}, {dt}</i> · {day_zh} ({day_py})

💰 <b>Бог Богатства: {DIRECTION_RU[wealth_dir]} ({wealth_dir})</b>
Направление, на которое стоит ориентироваться в денежных делах сегодня — переговоры об оплате, выставление счетов, важные финансовые решения.
Как активировать: садись лицом в эту сторону на встречах о деньгах, либо размести рабочее место/стол этим направлением, если решаешь сегодня финансовый вопрос.

🍀 <b>Бог Счастья: {DIRECTION_RU[happy_dir]} ({happy_dir})</b>
Направление, поддерживающее позитивные события — встречи, начало приятных дел, празднования.
Как активировать: выходи из дома или начинай важный разговор, повернувшись в эту сторону; хорошо проводить в этом направлении первую половину дня.

👑 <b>Час Благородного человека: {noble_ru}</b>
Часы дня (по животным), в которые выше шанс получить помощь, встретить нужного человека или нужную информацию.
Как использовать: если можешь выбирать время для важного звонка, встречи или письма — ставь его на один из этих часов.

Maria Anch · Dublin"""

    tg_send(msg)
    print(f"Sent directions brief for {today}: stem={day_zh}, wealth={wealth_dir}, happiness={happy_dir}")
    print(f"Message length: {len(msg)} chars")

if __name__ == "__main__":
    main()
