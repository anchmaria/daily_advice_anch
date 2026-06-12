import os
import json
import urllib.request
from datetime import datetime, date
import pytz

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"].strip()
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()
TIMEZONE         = "Europe/Dublin"

NATAL_BRANCHES  = {"Horse", "Dog", "Pig"}   # day / month / hour
NOBLE_PEOPLE    = {"Ox", "Goat"}
LIFE_GUA        = 8

# ── Tables ────────────────────────────────────────────────────────────────────
STEMS      = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEMS_EN   = ["Jia","Yi","Bing","Ding","Wu","Ji","Geng","Xin","Ren","Gui"]
STEM_BASE_ELEMENT = ["Wood","Wood","Fire","Fire","Earth","Earth","Metal","Metal","Water","Water"]

BRANCHES   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCHES_EN= ["Zi","Chou","Yin","Mao","Chen","Si","Wu","Wei","Shen","You","Xu","Hai"]
ANIMALS    = ["Rat","Ox","Tiger","Rabbit","Dragon","Snake",
              "Horse","Goat","Monkey","Rooster","Dog","Pig"]
CLASH      = {a: ANIMALS[(i+6)%12] for i, a in enumerate(ANIMALS)}

ANIMAL_EMOJI = {
    "Rat":"🐀","Ox":"🐂","Tiger":"🐯","Rabbit":"🐰","Dragon":"🐉","Snake":"🐍",
    "Horse":"🐴","Goat":"🐐","Monkey":"🐵","Rooster":"🐓","Dog":"🐶","Pig":"🐷"
}
ANIMAL_RU_GEN = {  # genitive: "год ___"
    "Rat":"Крысы","Ox":"Быка","Tiger":"Тигра","Rabbit":"Кролика","Dragon":"Дракона","Snake":"Змеи",
    "Horse":"Лошади","Goat":"Козы","Monkey":"Обезьяны","Rooster":"Петуха","Dog":"Собаки","Pig":"Свиньи"
}

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

MONTH_BRANCH = {1:2,2:3,3:4,4:5,5:6,6:6,7:7,8:8,9:9,10:10,11:11,12:0}

# ── Officers: (zh, en, auspicious, title, subtitle, favorable, unfavorable) ────
OFFICERS = [
    ("建","Establish",True,
        "Закладка основания","Фундамент для роста",
        "Начинать, договариваться, закладывать структуру",
        "подведение итогов долгих процессов"),
    ("除","Remove",True,
        "Расчистка","Место для нового",
        "Наводить порядок, закрывать старые задачи",
        "начало принципиально нового"),
    ("满","Full",True,
        "Полнота результата","Результаты становятся видимыми",
        "Подводить итоги, получать оплаты",
        "точные и детальные процедуры"),
    ("平","Balance",True,
        "Баланс","Ровный период без перекосов",
        "Переговоры, повседневные дела, поездки",
        "резкие, кардинальные решения"),
    ("定","Stable",True,
        "Стабильность","Решения держатся надолго",
        "Подписывать договоры, фиксировать договорённости",
        "спонтанные эксперименты"),
    ("执","Initiate",True,
        "Сфокусированное действие","Внимание собирается в одной точке",
        "Встречи, события, структурированная работа",
        "длительные поездки"),
    ("破","Destruction",False,
        "Разрушение старого","Старое теряет устойчивость",
        "Завершать то, что исчерпало себя",
        "запуск нового, важные договоры"),
    ("危","Danger",True,
        "Внимательность","Период просит больше внимательности",
        "Закрывать дела, действовать обдуманно",
        "действия на автопилоте"),
    ("成","Success",True,
        "Успех","Один из самых сильных периодов цикла",
        "Запуски, публикации, важные шаги",
        "пассивность и ожидание"),
    ("收","Receive",True,
        "Получение","Время собирать плоды",
        "Получать оплаты, закрывать проекты",
        "масштабные новые инициативы"),
    ("开","Open",True,
        "Открытие","Один из самых открытых периодов цикла",
        "Открытия, поездки, новый этап",
        "пассивное ожидание"),
    ("闭","Close",False,
        "Закрытие цикла","Пауза перед новым этапом",
        "Закрывать дела, отдыхать, восстанавливаться",
        "новые проекты, крупные покупки"),
]

# ── Constellations: (zh, en, auspicious, theme, focus) ─────────────────────────
CONSTELLATIONS = [
    ("角","Horn",True,        "движение вперёд",            "Фокус на инициативу и новые шаги"),
    ("亢","Neck",False,       "резкость",                   "Будь мягче в словах"),
    ("氐","Root",True,        "устойчивость",               "Фокус на обустройство и долгие решения"),
    ("房","Room",True,        "дом и близкие",              "Фокус на семью и личное пространство"),
    ("心","Heart",False,      "переменчивость",             "Решения — не на эмоциях"),
    ("尾","Tail",True,        "продолжение",                "Фокус на то, что уже начато"),
    ("箕","Basket",True,      "накопление",                 "Собирай и систематизируй"),
    ("斗","Dipper",True,      "благоприятный период",       "Хорош для любых важных шагов"),
    ("牛","Ox Star",False,    "детали договорённостей",     "Проверяй финансовые детали внимательнее"),
    ("女","Girl",False,       "отношения",                  "Не торопи решения про отношения"),
    ("虚","Emptiness",False,  "пауза",                       "Больше для размышлений, чем для старта"),
    ("危","Rooftop",False,    "риски",                       "Внимательность к деталям и рискам"),
    ("室","Encampment",True,  "обустройство",               "Фокус на пространство и новые структуры"),
    ("壁","Wall",True,        "знания",                      "Хорош для учёбы и систематизации"),
    ("奎","Legs",False,       "скрытые детали",             "Перепроверяй информацию"),
    ("娄","Bond",True,        "сбор",                        "Хорош для встреч и переговоров"),
    ("胃","Stomach",True,     "накопление",                  "Фокус на бюджет, вещи, пространство"),
    ("昴","Hairy Head",False, "мелкие потери",              "Будь внимательнее с вещами"),
    ("毕","Net",True,         "точность",                    "Хорош для завершения дел"),
    ("觜","Beak",False,       "поспешность",                 "Не спеши с выводами"),
    ("参","Orion",True,       "движение",                    "Хорош для поездок и переговоров"),
    ("井","Well",True,        "глубина",                     "Хорош для анализа и исследований"),
    ("鬼","Ghost",False,      "забота о себе",              "Время для здоровья и документов"),
    ("柳","Willow",False,     "переменчивость планов",      "Оставь запас времени"),
    ("星","Star",False,       "публичность",                 "Избегай резких публичных шагов"),
    ("张","Extended Net",True,"связи",                       "Хорош для новых знакомств"),
    ("翼","Wings",False,      "нестабильность в перемещениях","Планируй поездки с запасом"),
    ("轸","Chariot",True,     "логистика",                   "Хорош для поездок и переездов"),
]

# ── Flying stars: num → (en, color, advice) ────────────────────────────────────
FSTAR = {
    1: ("Water",      "🟢", "Действовать смело — хорош для начала нового"),
    2: ("Illness",    "🟡", "Беречь силы и здоровье"),
    3: ("Conflict",   "🟡", "Быть осторожнее в словах"),
    4: ("Study",      "🟢", "Хорош для учёбы и личных разговоров"),
    5: ("Caution",    "🔴", "Отложить крупные решения"),
    6: ("Authority",  "🟢", "Хорош для важных решений и поездок"),
    7: ("Risk",       "🟡", "Проверять траты и договоры внимательнее"),
    8: ("Prosperity", "🟢", "Хорош для финансов и клиентов"),
    9: ("Recognition","🟢", "Хорош для публичных шагов и запусков"),
}

# ── Five-element relations ─────────────────────────────────────────────────────
GENERATES = {"Wood":"Fire","Fire":"Earth","Earth":"Metal","Metal":"Water","Water":"Wood"}
CONTROLS  = {"Wood":"Earth","Earth":"Water","Water":"Fire","Fire":"Metal","Metal":"Wood"}
ELEMENT_RU = {"Wood":"Дерево","Fire":"Огонь","Earth":"Земля","Metal":"Металл","Water":"Вода"}
ELEMENT_EMOJI = {"Wood":"🌳","Fire":"🔥","Earth":"⛰️","Metal":"⚙️","Water":"💧"}

RELATION_ACTION = {
    "peer":      "действуй сама, без лишнего соперничества",
    "output":    "покажи то, что уже готово",
    "resource":  "учись и восстанавливайся",
    "authority": "наведи порядок, доведи формальности",
    "wealth":    "деньги, расчёты, ресурсы",
}

def relation(dm_element: str, day_element: str) -> str:
    if dm_element == day_element:
        return "peer"
    if GENERATES[dm_element] == day_element:
        return "output"
    if GENERATES[day_element] == dm_element:
        return "resource"
    if CONTROLS[dm_element] == day_element:
        return "wealth"
    return "authority"

# ── Julian Day ────────────────────────────────────────────────────────────────
def jd(d: date) -> int:
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12*a - 3
    return d.day + (153*m+2)//5 + 365*y + y//4 - y//100 + y//400 - 32045

def day_pillar(d: date):
    j = jd(d)
    return (j + 9) % 10, (j + 1) % 12

def officer(d: date):
    _, bi = day_pillar(d)
    mb = MONTH_BRANCH[d.month]
    return OFFICERS[(bi - mb) % 12]

def constellation(d: date):
    return CONSTELLATIONS[(jd(d) + 12) % 28]

def flying_star(d: date) -> int:
    return (jd(d) + 1) % 9 + 1

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
    dt  = f"{today.day} {MONTHS_RU[today.month]}"

    si, bi = day_pillar(today)
    animal      = ANIMALS[bi]
    day_zh      = f"{STEMS[si]}{BRANCHES[bi]}"
    day_element = STEM_BASE_ELEMENT[si]

    # Officer
    off_zh, off_en, off_ok, off_title, off_sub, off_fav, off_unfav = officer(today)

    # Constellation
    c_zh, c_en, c_ok, c_theme, c_focus = constellation(today)

    # Flying star
    fs = flying_star(today)
    fs_en, fs_color, fs_advice = FSTAR.get(fs, ("", "⚪️", ""))

    # ── Personal section ──────────────────────────────────────────────────────
    personal = None

    clash = CLASH[animal]
    if clash in NATAL_BRANCHES:
        personal = (
            f"Столкновение {animal} - {clash}\n"
            f"{ANIMAL_EMOJI[clash]}Быть внимательным рожденным в год {ANIMAL_RU_GEN[clash]}"
        )

    if personal is None:
        combo_phrase = {
            "Pig":   "тема ресурсов в фокусе",
            "Horse": "в фокусе ваш Day Master",
            "Dog":   "ресурс поддержки активен",
        }
        for c in combinations(animal):
            if c in combo_phrase:
                personal = (
                    f"Активация {animal} - {c}\n"
                    f"{ANIMAL_EMOJI[c]}Рождённым в год {ANIMAL_RU_GEN[c]} — {combo_phrase[c]}"
                )
                break

    if personal is None and animal in NOBLE_PEOPLE:
        personal = (
            "День Благородного Человека (贵人)\n"
            "👑Выше шанс встретить нужного человека"
        )

    # ── Five-element actions ──────────────────────────────────────────────────
    element_lines = []
    for el in ["Wood","Fire","Earth","Metal","Water"]:
        rel = relation(el, day_element)
        element_lines.append(f"{ELEMENT_EMOJI[el]} {ELEMENT_RU[el]} — {RELATION_ACTION[rel]}")
    elements_block = "\n".join(element_lines)

    personal_block = f"\n{personal}\n" if personal else ""

    msg = f"""{wd}, {dt} · {day_zh} · {animal}

🎖 Офицер дня: {off_zh} {off_en} — {off_title}.
{off_sub}

Что делать сегодня ?

* {off_fav}
* Отложить: {off_unfav}

✨ Созвездие: {c_zh} {c_en} — {c_theme}.

* {c_focus}

{fs_color} Звезда {fs} · {fs_en}

* {fs_advice}
{personal_block}
Если Ваш Господин Дня:
{elements_block}

Maria Anch · Dublin"""

    tg_send(msg)
    print(f"Sent for {today}: {day_zh}, officer={off_en}, constellation={c_zh}, star={fs}")
    print(f"Message length: {len(msg)} chars")

if __name__ == "__main__":
    main()
