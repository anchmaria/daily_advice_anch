import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
import pytz

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TIMEMAP_BASE    = "https://api.timemap.app"   # public REST endpoints

BIRTH_DATE = "1990-10-20"
BIRTH_TIME = "21:36"
GENDER     = "female"
TIMEZONE   = "Europe/Dublin"

# Noble People branches for this chart
NOBLE_PEOPLE = {"Ox", "Goat"}
# Life Gua
LIFE_GUA_NUMBER = 8

# ── Helpers ───────────────────────────────────────────────────────────────────
def fetch(path: str) -> dict:
    url = f"{TIMEMAP_BASE}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


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
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    dublin_tz = pytz.timezone(TIMEZONE)
    today = datetime.now(dublin_tz).strftime("%Y-%m-%d")
    weekdays_ru = {
        "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
        "Thursday": "Четверг", "Friday": "Пятница",
        "Saturday": "Суббота", "Sunday": "Воскресенье"
    }
    weekday_en = datetime.now(dublin_tz).strftime("%A")
    weekday_ru = weekdays_ru.get(weekday_en, weekday_en)
    date_display = datetime.now(dublin_tz).strftime("%-d %B %Y")

    # Fetch day quality
    dq = fetch(f"/day-quality?date={today}")
    # Fetch personal interactions
    di = fetch(
        f"/daily-interactions"
        f"?date={today}"
        f"&birth_date={BIRTH_DATE}"
        f"&birth_time={urllib.parse.quote(BIRTH_TIME)}"
        f"&timezone={urllib.parse.quote(TIMEZONE)}"
    )

    # ── Parse day quality ─────────────────────────────────────────────────────
    pillar      = dq["day_pillar"]
    stem        = pillar["stem"]
    branch      = pillar["branch"]
    officer     = dq["day_officer"]
    constellation = dq["constellation"]
    fstar       = dq["flying_star"]

    day_chinese  = f"{stem['chinese']}{branch['chinese']}"
    day_pinyin   = f"{stem['pinyin']} {branch['pinyin']}"
    day_animal   = branch["animal"]
    day_element  = f"{stem['element']} {'♂' if stem['polarity']=='yang' else '♀'}"

    officer_auspicious = "✅" if officer["auspicious"] else "⚠️"
    const_auspicious   = "✅" if constellation["auspicious"] else "⚠️"
    fstar_auspicious   = "✅" if fstar["number"] in {1, 4, 6, 8, 9} else "⚪️"

    # ── Parse personal interactions ───────────────────────────────────────────
    clash_animal  = di.get("clash_animal", "")
    combos        = di.get("combinations", [])
    natal_clashes = di.get("natal_clashes", [])
    is_mb         = di.get("is_month_breaker", False)
    is_yb         = di.get("is_year_breaker", False)

    personal_lines = []

    if not natal_clashes and not is_mb and not is_yb:
        personal_lines.append("✅ Нет столкновений с твоей картой — день чистый")
    if natal_clashes:
        personal_lines.append(f"⚠️ Столкновение с натальными ветвями: {', '.join(natal_clashes)}")
    if is_mb:
        personal_lines.append("🚫 День — Разрушитель Месяца. Избегай важных начинаний")
    if is_yb:
        personal_lines.append("🚫 День — Разрушитель Года. Избегай важных начинаний")
    if combos:
        for c in combos:
            if c == "Pig":
                personal_lines.append("⭐️ Комбинация с Кабаном (час рождения) — активирована Direct Wealth 正財")
            elif c == "Horse":
                personal_lines.append("⭐️ Комбинация с Лошадью (день рождения) — активирован Day Master")
            else:
                personal_lines.append(f"⭐️ Комбинация с {c}")
    if day_animal in NOBLE_PEOPLE:
        personal_lines.append("👑 Сегодня твой день Благородного Человека (贵人) — высокий шанс нужных встреч и помощи")
    if fstar["number"] == LIFE_GUA_NUMBER:
        personal_lines.append(f"🎯 Летящая звезда дня ({fstar['number']}) совпадает с твоей Life Gua 8 — день в резонансе с тобой")

    personal_section = "\n".join(personal_lines) if personal_lines else "⚪️ Нейтральный день без особых активаций"

    # ── Officer advice ────────────────────────────────────────────────────────
    officer_advice = {
        "Establish": "Хорошо начинать новое, закладывать основы, первые шаги",
        "Remove":    "День для уборки, расчистки, завершения старого",
        "Full":      "День изобилия — хорошо для торговли, праздников, получения",
        "Balance":   "Хорошо для переговоров, подписания, поиска баланса",
        "Stable":    "Стабильность и надёжность — хорошо для долгосрочных решений",
        "Initiate":  "Хорошо для старта проектов, первых контактов",
        "Destruction": "День разрушения — избегай важных начинаний",
        "Danger":    "Осознанные шаги, духовные практики, завершение дел",
        "Success":   "Один из лучших дней — запуски, публикации, важные действия",
        "Receive":   "Хорошо принимать, получать, завершать циклы",
        "Open":      "Отличный день для новых начинаний, встреч, путешествий",
        "Close":     "День завершения — хорошо закрывать дела, отдыхать",
    }.get(officer["english"], "Действуй осознанно")

    # ── Build message ─────────────────────────────────────────────────────────
    msg = f"""🗓 <b>{weekday_ru}, {date_display}</b>

<b>День {day_chinese} ({day_pinyin})</b>
{day_element} · {day_animal}

━━━━━━━━━━━━━━━
📋 <b>КАЧЕСТВО ДНЯ</b>

{officer_auspicious} <b>Офицер: {officer['chinese']} {officer['english']}</b>
{officer_advice}

{const_auspicious} <b>Созвездие: {constellation['chinese']} {constellation['english']}</b>
Планета: {constellation['luminary']}

{fstar_auspicious} <b>Летящая звезда: {fstar['number']} {fstar['chinese']}</b>

━━━━━━━━━━━━━━━
👤 <b>ЛИЧНО ДЛЯ ТЕБЯ</b>

{personal_section}

━━━━━━━━━━━━━━━
<i>戊午 · Life Gua 8 · Dublin 🍀</i>"""

    tg_send(msg)
    print(f"✅ Sent daily brief for {today}")


if __name__ == "__main__":
    main()
