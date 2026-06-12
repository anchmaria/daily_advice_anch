import os
import json
import urllib.request
from datetime import datetime, date
import pytz

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"].strip()
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()
TIMEZONE         = "Europe/Dublin"

# Natal data: 戊午 day master, 丙戌 month, 癸亥 hour
NATAL_BRANCHES  = {"Horse", "Dog", "Pig"}   # day / month / hour
NOBLE_PEOPLE    = {"Ox", "Goat"}
LIFE_GUA        = 8

# ── Tables ────────────────────────────────────────────────────────────────────
STEMS      = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEMS_EN   = ["Jia","Yi","Bing","Ding","Wu","Ji","Geng","Xin","Ren","Gui"]
STEMS_EL   = ["Yang Wood","Yin Wood","Yang Fire","Yin Fire","Yang Earth",
               "Yin Earth","Yang Metal","Yin Metal","Yang Water","Yin Water"]

BRANCHES   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCHES_EN= ["Zi","Chou","Yin","Mao","Chen","Si","Wu","Wei","Shen","You","Xu","Hai"]
ANIMALS    = ["Rat","Ox","Tiger","Rabbit","Dragon","Snake",
              "Horse","Goat","Monkey","Rooster","Dog","Pig"]
CLASH      = {a: ANIMALS[(i+6)%12] for i, a in enumerate(ANIMALS)}

THREE_HARMONY = [
    {"Tiger","Horse","Dog"},
    {"Pig","Rabbit","Goat"},
    {"Monkey","Rat","Dragon"},
    {"Snake","Rooster","Ox"},
]
SIX_HARMONY = [
    {"Rat","Ox"},{"Tiger","Pig"},{"Rabbit","Dog"},
    {"Dragon","Rooster"},{"Snake","Monkey"},{"Horse","Goat"},
]

OFFICERS = [
    ("建","Establish",True),  ("除","Remove",True),
    ("满","Full",True),       ("平","Balance",True),
    ("定","Stable",True),     ("执","Initiate",True),
    ("破","Destruction",False),("危","Danger",True),
    ("成","Success",True),    ("收","Receive",True),
    ("开","Open",True),       ("闭","Close",False),
]

CONSTELLATIONS = [
    ("角","Horn","Wood",True),    ("亢","Neck","Metal",False),
    ("氐","Root","Earth",True),   ("房","Room","Sun",True),
    ("心","Heart","Moon",False),  ("尾","Tail","Fire",True),
    ("箕","Basket","Water",True), ("斗","Dipper","Wood",True),
    ("牛","Ox Star","Metal",False),("女","Girl","Earth",False),
    ("虚","Emptiness","Sun",False),("危","Rooftop","Moon",False),
    ("室","Encampment","Fire",True),("壁","Wall","Water",True),
    ("奎","Legs","Wood",False),   ("娄","Bond","Metal",True),
    ("胃","Stomach","Earth",True),("昴","Hairy Head","Sun",False),
    ("毕","Net","Moon",True),     ("觜","Beak","Fire",False),
    ("参","Orion","Water",True),  ("井","Well","Wood",True),
    ("鬼","Ghost","Metal",False), ("柳","Willow","Earth",False),
    ("星","Star","Sun",False),    ("张","Extended Net","Moon",True),
    ("翼","Wings","Fire",False),  ("轸","Chariot","Water",True),
]

FSTAR_NAMES = {
    1:"一白 Water",2:"二黑 Illness",3:"三碧 Conflict",
    4:"四绿 Romance/Study",5:"五黄 ⚠️ Danger",6:"六白 Metal",
    7:"七赤 Decline",8:"八白 Prosperity",9:"九紫 Future Wealth"
}

# Solar month → branch index (午月=June, etc.)
MONTH_BRANCH = {1:2,2:3,3:4,4:5,5:6,6:6,7:7,8:8,9:9,10:10,11:11,12:0}
# More precisely: solar month shifts around 6th of each month
# June = 午 (index 6) starting ~Jun 6 (Mang Zhong)

# ── Julian Day ────────────────────────────────────────────────────────────────
def jd(d: date) -> int:
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12*a - 3
    return d.day + (153*m+2)//5 + 365*y + y//4 - y//100 + y//400 - 32045

# ── Pillar ────────────────────────────────────────────────────────────────────
def day_pillar(d: date):
    # Calibrated: stem_offset=9, branch_offset=1 (verified Jun 8-9 2026)
    j = jd(d)
    return (j + 9) % 10, (j + 1) % 12

# ── Officer ───────────────────────────────────────────────────────────────────
def officer(d: date):
    _, bi = day_pillar(d)
    # Solar month branch (午=6 for June; adjust if day < ~6th for prev month)
    # Simplified: use Gregorian month mapping
    mb = MONTH_BRANCH[d.month]
    # For days 1-5 of month, may still be prev solar month — acceptable approximation
    return OFFICERS[(bi - mb) % 12]

# ── Constellation ─────────────────────────────────────────────────────────────
def constellation(d: date):
    # const_offset=12 (verified Jun 8-9 2026)
    return CONSTELLATIONS[(jd(d) + 12) % 28]

# ── Flying star ───────────────────────────────────────────────────────────────
def flying_star(d: date) -> int:
    # star_offset=1 (verified Jun 8-9 2026), stars increase daily
    return (jd(d) + 1) % 9 + 1

# ── Combinations ─────────────────────────────────────────────────────────────
def combinations(day_animal: str) -> list:
    result = []
    for g in THREE_HARMONY:
        if day_animal in g:
            result.extend(g & NATAL_BRANCHES - {day_animal})
    for p in SIX_HARMONY:
        if day_animal in p:
            result.extend(p & NATAL_BRANCHES - {day_animal})
    return list(set(result))

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

    wd  = WDAYS[now.strftime("%A")]
    dt  = f"{today.day} {MONTHS_RU[today.month]} {today.year}"

    # Pillar
    si, bi = day_pillar(today)
    animal   = ANIMALS[bi]
    day_zh   = f"{STEMS[si]}{BRANCHES[bi]}"
    day_py   = f"{STEMS_EN[si]} {BRANCHES_EN[bi]}"
    elem     = STEMS_EL[si]

    # Officer
    off_zh, off_en, off_ok = officer(today)
    off_icon = "✅" if off_ok else "⚠️"
    off_hint = {
        "Establish":"Хорошо начинать новое, закладывать основы",
        "Remove":   "День для расчистки, завершения старого",
        "Full":     "День изобилия — торговля, праздники, получение",
        "Balance":  "Переговоры, подписание, поиск баланса",
        "Stable":   "Стабильность — хорошо для долгосрочных решений",
        "Initiate": "Хорошо для старта, первых контактов",
        "Destruction":"🚫 Избегай важных начинаний",
        "Danger":   "Осознанные шаги, духовные практики, завершение",
        "Success":  "Один из лучших дней — запуски, публикации, действия",
        "Receive":  "Хорошо принимать, получать, закрывать циклы",
        "Open":     "Отличный день для новых начинаний и встреч",
        "Close":    "День завершения — закрывай дела, отдыхай",
    }.get(off_en, "")

    # Constellation
    c_zh, c_en, c_planet, c_ok = constellation(today)
    c_icon = "✅" if c_ok else "⚠️"

    # Flying star
    fs = flying_star(today)
    fs_name = FSTAR_NAMES.get(fs, str(fs))
    fs_icon = "✅" if fs in {1,4,6,8,9} else ("🚫" if fs == 5 else "⚪️")

    # Personal
    lines = []
    clash = CLASH[animal]
    if clash not in NATAL_BRANCHES:
        lines.append("✅ Нет столкновений с твоей картой — день чистый")
    else:
        lines.append(f"⚠️ Столкновение с натальной ветвью: {clash}")

    for c in combinations(animal):
        labels = {"Pig":"Кабан (час) → Direct Wealth 正財 активирована",
                  "Horse":"Лошадь (день) → Day Master активирован",
                  "Dog":"Собака (месяц) → Indirect Resource активирован"}
        lines.append(f"⭐️ Комбинация: {labels.get(c, c)}")

    if animal in NOBLE_PEOPLE:
        lines.append("👑 День Благородного Человека (贵人) — высокий шанс нужных встреч")

    if fs == LIFE_GUA:
        lines.append(f"🎯 Звезда дня ({fs}) = твоя Life Gua 8 — день в резонансе с тобой")

    personal = "\n".join(lines) if lines else "⚪️ Нейтральный день"

    msg = f"""🗓 <b>{wd}, {dt}</b>

<b>{day_zh} ({day_py})</b>
{elem} · {animal}

━━━━━━━━━━━━━━━
📋 <b>КАЧЕСТВО ДНЯ</b>

{off_icon} <b>Офицер: {off_zh} {off_en}</b>
{off_hint}

{c_icon} <b>Созвездие: {c_zh} {c_en}</b>
Планета: {c_planet}

{fs_icon} <b>Летящая звезда: {fs} {fs_name}</b>

━━━━━━━━━━━━━━━
👤 <b>ЛИЧНО ДЛЯ ТЕБЯ</b>

{personal}

━━━━━━━━━━━━━━━
<i>戊午 · Life Gua 8 · Dublin 🍀</i>"""

    tg_send(msg)
    print(f"✅ Sent for {today}: {day_zh}, officer={off_en}, star={fs}")

if __name__ == "__main__":
    main()
