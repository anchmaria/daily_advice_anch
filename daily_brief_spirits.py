import os
import json
import urllib.request
from datetime import datetime, date
import pytz

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spirits_data import LIU_HE, ZHI_FU, TAI_YIN, JIU_TIAN, JIU_DI, SPIRIT_MEANING
from activations_data import NOBLE_HELPERS, QMDZ_ACTIVATIONS, PUSHING_PEOPLE, MONEY_STAR, LIGHT_DATES

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"].strip()
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()
TIMEZONE         = "Europe/Dublin"

WDAYS = {"Monday":"Понедельник","Tuesday":"Вторник","Wednesday":"Среда",
         "Thursday":"Четверг","Friday":"Пятница","Saturday":"Суббота","Sunday":"Воскресенье"}
MONTHS_RU = {1:"января",2:"февраля",3:"марта",4:"апреля",5:"мая",6:"июня",
             7:"июля",8:"августа",9:"сентября",10:"октября",11:"ноября",12:"декабря"}

SPIRIT_ORDER = [
    ("zhi_fu",   "Главный Дух",  ZHI_FU),
    ("tai_yin",  "Великий Инь",  TAI_YIN),
    ("liu_he",   "6 Союзов",     LIU_HE),
    ("jiu_tian", "9 Небес",      JIU_TIAN),
    ("jiu_di",   "9 Земель",     JIU_DI),
]

# ── Бог Богатства / Бог Счастья — 10-дневный цикл по Небесному Стволу дня ─────
STEMS    = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEMS_RU = ["Цзя","И","Бин","Дин","У","Цзи","Гэн","Синь","Жэнь","Гуй"]
WEALTH_GOD    = {0:"ЮВ",1:"ЮВ",2:"З",3:"З",4:"С",5:"С",6:"В",7:"В",8:"Ю",9:"Ю"}
HAPPINESS_GOD = {0:"СВ",1:"СЗ",2:"ЮЗ",3:"Ю",4:"ЮВ",5:"СВ",6:"СЗ",7:"ЮЗ",8:"Ю",9:"ЮВ"}
DIRECTION_RU  = {"С":"Север","Ю":"Юг","В":"Восток","З":"Запад",
                  "СВ":"Северо-Восток","СЗ":"Северо-Запад",
                  "ЮВ":"Юго-Восток","ЮЗ":"Юго-Запад"}

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
    today_str = today.isoformat()

    wd = WDAYS[now.strftime("%A")]
    dt = f"{today.day} {MONTHS_RU[today.month]}"

    # ── 1. Бог Богатства / Бог Счастья (всегда есть — циклическая система) ─────
    si = day_stem_idx(today)
    wealth_dir = WEALTH_GOD[si]
    happy_dir  = HAPPINESS_GOD[si]
    gods_block = (
        f"💰 Богатство: {DIRECTION_RU[wealth_dir]} ({wealth_dir})\n"
        f"🍀 Счастье: {DIRECTION_RU[happy_dir]} ({happy_dir})"
    )

    # ── 2. Духи Ци Мэнь (по часу — берём срез на момент отправки) ──────────────
    hour = now.hour
    h_idx = ((hour - 1) // 2) % 12 if hour >= 1 else 11

    spirit_lines = []
    for key, name, table in SPIRIT_ORDER:
        row = table.get(today_str)
        if row:
            direction = row[h_idx] if h_idx < len(row) else row[0]
            meaning = SPIRIT_MEANING.get(key, "")
            spirit_lines.append(f"• {name} — {direction} ({meaning})")
    if spirit_lines:
        spirits_block = "✅ Есть данные на сегодня:\n" + "\n".join(spirit_lines)
    else:
        spirits_block = "❌ Нет данных на сегодня."

    # ── 3. Благородные Помощники ────────────────────────────────────────────────
    if today_str in NOBLE_HELPERS:
        lines = []
        for animal, time_, sector, activator, note in NOBLE_HELPERS[today_str]:
            extra = f" · {note}" if note else ""
            lines.append(f"• {time_} ({animal}), сектор {sector}{extra}")
        helpers_block = "✅ Активация есть:\n" + "\n".join(lines)
    else:
        helpers_block = "❌ Активации нет."

    # ── 4. Активации Ци Мэнь (Птица / Три Генерала / Дракон) ───────────────────
    if today_str in QMDZ_ACTIVATIONS:
        lines = []
        for kind, animal, time_, direction, note in QMDZ_ACTIVATIONS[today_str]:
            lines.append(f"• {kind} — {time_} ({animal}), направление {direction} · {note}")
        qmdz_block = "✅ Активация есть:\n" + "\n".join(lines)
    else:
        qmdz_block = "❌ Активации нет."

    # ── 5. Вталкивание людей + Согревание денежной звезды (обе со свечой) ──────
    candle_lines = []
    if today_str in PUSHING_PEOPLE:
        for group, time_, sector, lz, unfit in PUSHING_PEOPLE[today_str]:
            candle_lines.append(f"🕯 Вталкивание людей (для {group}) — {time_}, сектор {sector}")
    if today_str in MONEY_STAR:
        for hr, time_, sector, fav, unfit, note in MONEY_STAR[today_str]:
            fav_txt = f", благоприятно для {fav}" if fav else ""
            candle_lines.append(f"💰 Согревание денежной звезды — {time_} ({hr}), сектор {sector}{fav_txt}")
    if candle_lines:
        candle_block = "✅ Активация есть:\n" + "\n".join(candle_lines)
    else:
        candle_block = "❌ Активации нет."

    # ── 6. Светящиеся даты / часы ───────────────────────────────────────────────
    if today_str in LIGHT_DATES:
        lines = []
        for animal, time_, traits, unfit in LIGHT_DATES[today_str]:
            traits_txt = ", ".join(traits)
            lines.append(f"• {time_} ({animal}): {traits_txt}")
        light_block = "✅ Есть на сегодня:\n" + "\n".join(lines)
    else:
        light_block = "❌ Нет на сегодня."

    msg = f"""<i>{wd}, {dt}</i>

<b>1. Бог Богатства / Бог Счастья</b>
{gods_block}

<b>2. Благородные Помощники</b>
{helpers_block}

<b>3. Активации Ци Мэнь (Птица/Дракон/Генералы)</b>
{qmdz_block}

<b>4. Вталкивание людей + Согревание денежной звезды</b>
{candle_block}

<b>5. Светящиеся даты/часы</b>
{light_block}

Дух дня: команда /spirit в боте 🔮

Maria Anch · Dublin"""

    tg_send(msg)
    print(f"Sent full categories brief for {today_str}")
    print(f"Message length: {len(msg)} chars")

if __name__ == "__main__":
    main()
