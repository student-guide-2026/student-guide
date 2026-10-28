# =============================================================================
#  Smart Student Guide - ط¯ظ„ظٹظ„ ط§ظ„ط·ط§ظ„ط¨ ط§ظ„ط°ظƒظٹ (Premium Edition)
#  ظ…ط´ط±ظˆط¹ ط¬ط§ظ…ط¹ظٹ ظ…طھظƒط§ظ…ظ„: ط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ + طھظ…ط«ظٹظ„ ط§ظ„ظ…ط¹ط±ظپط© + ط¥ط¯ط§ط±ط© ظ‚ظˆط§ط¹ط¯ ط§ظ„ط¨ظٹط§ظ†ط§طھ
#  ظˆط§ط¬ظ‡ط© طھظپط§ط¹ظ„ظٹط© ط§ط­طھط±ط§ظپظٹط© (Premium CLI) ظ…ط®طµطµط© ظ„ظƒظ„ظٹط§طھ ط§ظ„ط­ط§ط³ط¨ط§طھ ظˆط§ظ„ط°ظƒط§ط، ط§ظ„ط§طµط·ظ†ط§ط¹ظٹ
# =============================================================================

import os
import sys
import csv
import json
import logging
import datetime
from collections import defaultdict

# ط§ط³طھظٹط±ط§ط¯ ظ…ظƒطھط¨ط§طھ ط§ظ„ط°ظƒط§ط، ط§ظ„ط§طµط·ظ†ط§ط¹ظٹ ظˆط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ط§ط³طھظٹط±ط§ط¯ ظ…ظƒطھط¨ط§طھ ط§ظ„طھطµظ…ظٹظ… ط§ظ„ظ…طھظ‚ط¯ظ…
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box

# ط¯ط¹ظ… طھط´ط¨ظٹظƒ ط§ظ„ط­ط±ظˆظپ ط§ظ„ط¹ط±ط¨ظٹط© ظ„ظ„ط·ط±ظپظٹط§طھ (VS Code Terminal)
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False

# =============================================================================
#  ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ظ†ط¸ط§ظ… ط§ظ„ط¹ط§ظ…ط©
# =============================================================================
FIX_ARABIC_TERMINAL = True  # طھظپط¹ظٹظ„ ظ…ط¹ط§ظ„ط¬ط© ط§ظ„ط­ط±ظˆظپ ط§ظ„ط¹ط±ط¨ظٹط© ط¯ط§ط®ظ„ طھظٹط±ظ…ظ†ط§ظ„ VS Code
if os.name == "nt":
    os.system("")  # طھظپط¹ظٹظ„ ط¯ط¹ظ… VT100 ظˆط±ظ…ظˆط² ANSI ظپظٹ ط·ط±ظپظٹط© ظˆظٹظ†ط¯ظˆط²
console = Console()

COURSES_FILE   = "courses.csv"
PREREQ_FILE    = "prerequisites.json"
DOCS_DIR       = "docs"
LOG_FILE       = "queries.log"

ATTENDANCE_DOC = os.path.join(DOCS_DIR, "attendance_policy.txt")
GPA_DOC        = os.path.join(DOCS_DIR, "gpa_system.txt")
REG_DOC        = os.path.join(DOCS_DIR, "registration_rules.txt")

# =============================================================================
#  ط¯ط§ظ„ط© ظ…ط¹ط§ظ„ط¬ط© ط§ظ„ظ†طµظˆطµ ط§ظ„ط¹ط±ط¨ظٹط© ط§ظ„ط°ظƒظٹط©
# =============================================================================
def ar(text) -> str:
    """
    ظ…ط¹ط§ظ„ط¬ط© ط§ظ„ظ†طµظˆطµ ط§ظ„ط¹ط±ط¨ظٹط© طھظ„ظ‚ط§ط¦ظٹط§ظ‹ ظ„طھط¸ظ‡ط± ظ…طھطµظ„ط© ظˆظ…ظ†ط³ظ‚ط© ط¨ط§ظ„ط§طھط¬ط§ظ‡ ط§ظ„ط³ظ„ظٹظ…
    ط¯ط§ط®ظ„ طھظٹط±ظ…ظ†ط§ظ„ VS Code ظˆط£ظٹ ط·ط±ظپظٹط© ط£ط®ط±ظ‰.
    """
    if text is None:
        return ""
    text_str = str(text)
    if not FIX_ARABIC_TERMINAL or not HAS_BIDI:
        return text_str
    try:
        if any('\u0600' <= char <= '\u06FF' for char in text_str):
            return get_display(arabic_reshaper.reshape(text_str))
        return text_str
    except Exception:
        return text_str


def clear_screen():
    """ظ…ط³ط­ ط§ظ„ط´ط§ط´ط© ظ„ظ…ظ†ط­ ط§ظ„ظ…ط³طھط®ط¯ظ… طھط¬ط±ط¨ط© طھطµظپط­ ظ†ط¸ظٹظپط© ظˆظ…ظ†ط¸ظ…ط©."""
    os.system('cls' if os.name == 'nt' else 'clear')


def pause(message: str = "ط§ط¶ط؛ط· Enter ظ„ظ„ظ…طھط§ط¨ط¹ط©..."):
    """طھظˆظ‚ظپ ظ…ط¤ظ‚طھ ظ„ظ‚ط±ط§ط،ط© ط§ظ„ظ…ط®ط±ط¬ط§طھ ظ‚ط¨ظ„ ط§ظ„ط¹ظˆط¯ط© ظ„ظ„ظ‚ط§ط¦ظ…ط©."""
    try:
        input(f"\n  [Enter] {ar(message)}")
    except (EOFError, KeyboardInterrupt):
        pass


def get_arabic_input(prompt: str = "") -> str:
    """
    ط§ط³طھظ‚ط¨ط§ظ„ ظ…ط¯ط®ظ„ط§طھ ط§ظ„ظ…ط³طھط®ط¯ظ… ظ…ظ† ظ„ظˆط­ط© ط§ظ„ظ…ظپط§طھظٹط­ ظ…ط¹ طھط´ط¨ظٹظƒ ط§ظ„ط­ط±ظˆظپ ط§ظ„ط¹ط±ط¨ظٹط©
    ظ„ط­ط¸ظٹط§ظ‹ ظˆط¨ط´ظƒظ„ ط­ظٹ ط¹ظ„ظ‰ ط§ظ„ط´ط§ط´ط© ط¯ط§ط®ظ„ طھظٹط±ظ…ظ†ط§ظ„ VS Code.
    """
    formatted_prompt = prompt.strip()
    if not (formatted_prompt.endswith(":") or formatted_prompt.endswith(">")):
        formatted_prompt += ":"

    # ط¥ط°ط§ ظƒط§ظ† ط§ظ„ط¥ط¯ط®ط§ظ„ ط؛ظٹط± طھظپط§ط¹ظ„ظٹ (Piped/Testing)طŒ ظ†ط³طھط®ط¯ظ… ط¯ط§ظ„ط© ط§ظ„ط¥ط¯ط®ط§ظ„ ط§ظ„ط¹ط§ط¯ظٹط©
    if not sys.stdin.isatty():
        try:
            return input(f"\n  {formatted_prompt} ").strip()
        except EOFError:
            return ""

    # ط¹ظ„ظ‰ ظ†ط¸ط§ظ… ظˆظٹظ†ط¯ظˆط² ظˆط¨ط§ط³طھط®ط¯ط§ظ… msvcrt ظ„ظ„ط§ظ„طھظ‚ط§ط· ط§ظ„ط­ظٹ ظ„ظ„ط¶ط؛ط·ط§طھ
    if os.name == "nt":
        try:
            import msvcrt
            sys.stdout.write(f"\n  {formatted_prompt} ")
            sys.stdout.flush()
            buf = []
            while True:
                ch = msvcrt.getwch()
                if ch in ('\r', '\n'):
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    break
                elif ch == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                elif ch in ('\x00', '\xe0'):  # ظ…ظپط§طھظٹط­ ط§ظ„ط£ط³ظ‡ظ… ظˆط§ظ„ظˆط¸ط§ط¦ظپ ط§ظ„ط®ط§طµط©
                    msvcrt.getwch()
                    continue
                elif ch in ('\x08', '\x7f'):  # ط²ط± ط§ظ„ظ…ط³ط­ Backspace
                    if buf:
                        buf.pop()
                else:
                    buf.append(ch)

                # طھط´ط¨ظٹظƒ ظˆط¥ط¹ط§ط¯ط© ط±ط³ظ… ط§ظ„ط³ط·ط± ظ„ط­ط¸ظٹط§ظ‹
                cur = "".join(buf)
                display_text = ar(cur) if cur else ""
                sys.stdout.write(f"\r\033[K  {formatted_prompt} {display_text}")
                sys.stdout.flush()

            return "".join(buf).strip()
        except Exception:
            pass

    return input(f"\n  {formatted_prompt} ").strip()


def gui_arabic_input(title: str = "ط§ظ„ط¨ط­ط« ط§ظ„ط°ظƒظٹ", prompt: str = "ط£ط¯ط®ظ„ ط¹ط¨ط§ط±ط© ط§ظ„ط¨ط­ط« ط¨ط§ظ„ظ„ط؛ط© ط§ظ„ط¹ط±ط¨ظٹط©:") -> str:
    """
    ظپطھط­ ظ†ط§ظپط°ط© ط¥ط¯ط®ط§ظ„ ظˆظٹظ†ط¯ظˆط² طµط؛ظٹط±ط© (Native Windows Dialog)
    طھطھظٹط­ ط§ظ„ظƒطھط§ط¨ط© ظˆط§ظ„ظ„طµظ‚ ط¨ط§ظ„ط¹ط±ط¨ظٹط© ط¨ظƒظ„ ط³ظ„ط§ط³ط© ظˆظ…ط­ط§ط°ط§ط© ط·ط¨ظٹط¹ظٹط© ظ…ظ† ط§ظ„ظٹظ…ظٹظ† ظ„ظ„ظٹط³ط§ط±.
    """
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        res = simpledialog.askstring(title, prompt, parent=root)
        root.destroy()
        return res.strip() if res else ""
    except Exception:
        return ""



# =============================================================================
#  ط¥ط¹ط¯ط§ط¯ ظ†ط¸ط§ظ… طھط³ط¬ظٹظ„ ط§ظ„ط¹ظ…ظ„ظٹط§طھ (UTF-8 Logging)
# =============================================================================
logger = logging.getLogger("SmartGuide")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(_fh)

def log_query(action: str, details: str = ""):
    """طھط³ط¬ظٹظ„ ظƒظ„ ط§ط³طھظپط³ط§ط± ط£ظˆ ط¹ظ…ظ„ظٹط© ط¨ط­ط« ظپظٹ ظ…ظ„ظپ ط§ظ„ط³ط¬ظ„ queries.log ط¨طھط±ظ…ظٹط² UTF-8."""
    logger.info(f"[{action}] {details}")


# =============================================================================
#  ط¯ط§ظ„ط© ط§ظ„طھظ‡ظٹط¦ط© ط§ظ„طھظ„ظ‚ط§ط¦ظٹط© - Realistic Auto-Generated Data
# =============================================================================
def initialize_data():
    """
    طھظپط­طµ ظˆط¬ظˆط¯ ط§ظ„ظ…ظ„ظپط§طھ ط§ظ„ظ…ط·ظ„ظˆط¨ط©طŒ ظˆط¥ط°ط§ ظ„ظ… طھظƒظ† ظ…ظˆط¬ظˆط¯ط© طھظ‚ظˆظ… ط¨ط¥ظ†ط´ط§ط¦ظ‡ط§ ظپظˆط±ط§ظ‹
    ط¨ط¨ظٹط§ظ†ط§طھ ط¯ظ‚ظٹظ‚ط© ظˆظˆط§ظ‚ط¹ظٹط© طھط­ط§ظƒظٹ ظƒظ„ظٹط§طھ ط§ظ„ط°ظƒط§ط، ط§ظ„ط§طµط·ظ†ط§ط¹ظٹ ظˆط§ظ„ط­ط§ط³ط¨ط§طھ ط§ظ„ظ…طµط±ظٹط©.
    """
    created_any = False

    # 1. ط¥ظ†ط´ط§ط، ظ…ظ„ظپ ط§ظ„ظ…ظ‚ط±ط±ط§طھ courses.csv
    if not os.path.exists(COURSES_FILE):
        courses = [
            ["course_id", "course_name", "instructor", "room", "credit_hours"],
            ["CS101",   "مقدمة في البرمجة (Python & C++)",             "د. تامر مدحت",    "معمل الحاسب 1",          3],
            ["CS102",   "هياكل البيانات والخوارزميات",                   "د. محمود الصباغ", "مدرج 2",                 3],
            ["CS201",   "البرمجة كائنية التوجه (OOP & Design Patterns)", "د. تامر مدحت",    "معمل 2",                 3],
            ["CS202",   "تنظيم وعمارة الحاسب",                          "د. محمود يسن",    "مدرج 3",                 3],
            ["CS301",   "نظم التشغيل والبرمجة المتزامنة",                "د. محمود يسن",    "معمل 4",                 3],
            ["CS302",   "شبكات الحاسب وأمن الشبكات",                    "د. محمود الصباغ", "معمل الشبكات",           3],
            ["CS303",   "هندسة البرمجيات وإدارة المشاريع",             "د. زينب حسن",     "قاعة 204",               2],
            ["CS401",   "تطوير تطبيقات الويب المتكاملة (Full-Stack)",   "د. محمد عبده",    "معمل الويب",             3],
            ["CS402",   "أمن المعلومات واختبار الاختراق",               "د. محمود الصباغ", "معمل الأمان",            3],
            ["CS403",   "الحوسبة السحابية وDevOps",                     "د. محمد عبده",    "معمل السحابة",           3],
            ["MATH101", "تفاضل وتكامل 1",                                "د. فاطمة طلعت",   "مدرج 1",                 3],
            ["MATH102", "جبر خطي وإحصاء احتمالي",                       "د. فاطمة طلعت",   "قاعة 104",               3],
            ["MATH201", "رياضيات متقطعة ونظرية المخططات",               "د. زينب حسن",     "قاعة 105",               2],
            ["IS201",   "نظم قواعد البيانات وتصميمها",                   "د. فاطمة حسن",    "معمل 3",                 3],
            ["IS301",   "مستودعات البيانات وتنظيم ETL",                  "د. فاطمة حسن",    "معمل 2",                 2],
            ["AI201",   "أساسيات الذكاء الاصطناعي ونظم المعرفة",         "د. تامر مدحت",    "قاعة 201",               3],
            ["AI202",   "تعلم الآلة (Machine Learning)",                 "د. منال السيد",   "معمل الذكاء الاصطناعي",  3],
            ["AI301",   "التعلم العميق ورؤية الحاسب (Deep Learning)",    "د. منال السيد",   "معمل الرؤية",            3],
            ["AI302",   "معالجة اللغات الطبيعية (NLP & LLMs)",          "د. منى",          "معمل 1",                 2],
            ["ROB201",  "مقدمة في الروبوتات والأنظمة المدمجة",          "د. محمود يسن",    "معمل الروبوت",           2],
            ["ROB301",  "نظم الزمن الحقيقي وإنترنت الأشياء (RTOS & IoT)", "د. محمد عبده",    "معمل الأتمتة",           2],
        ]
        with open(COURSES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(courses)
        created_any = True

    # 2. ط¥ظ†ط´ط§ط، ط´ط¬ط±ط© ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ط³ط§ط¨ظ‚ط© prerequisites.json
    if not os.path.exists(PREREQ_FILE):
        prereqs = {
            "CS101":   [],
            "MATH101": [],
            "MATH201": ["MATH101"],
            "CS102":   ["CS101"],
            "CS201":   ["CS101"],
            "CS202":   ["CS101"],
            "MATH102": ["MATH101"],
            "IS201":   ["CS101"],
            "IS301":   ["IS201"],
            "AI201":   ["CS101", "MATH101"],
            "AI202":   ["AI201", "MATH102"],
            "AI301":   ["AI202"],
            "AI302":   ["AI202"],
            "ROB201":  ["CS101", "CS202"],
            "ROB301":  ["ROB201", "CS301"],
            "CS301":   ["CS102", "CS202"],
            "CS302":   ["CS301"],
            "CS303":   ["CS201"],
            "CS401":   ["CS201", "IS201"],
            "CS402":   ["CS302", "CS301"],
            "CS403":   ["CS301", "CS302"]
        }
        with open(PREREQ_FILE, "w", encoding="utf-8") as f:
            json.dump(prereqs, f, ensure_ascii=False, indent=4)
        created_any = True

    # 3. ط¥ظ†ط´ط§ط، ظ…ط¬ظ„ط¯ ط§ظ„ظˆط«ط§ط¦ظ‚ ظˆط§ظ„ظ„ظˆط§ط¦ط­ docs/
    os.makedirs(DOCS_DIR, exist_ok=True)

    # ظˆط«ظٹظ‚ط© ظ„ط§ط¦ط­ط© ط§ظ„ط­ط¶ظˆط± ظˆط§ظ„ط؛ظٹط§ط¨
    if not os.path.exists(ATTENDANCE_DOC):
        content = """ظ„ط§ط¦ط­ط© ط§ظ„ط­ط¶ظˆط± ظˆط§ظ„ط؛ظٹط§ط¨ - ظƒظ„ظٹط© ط§ظ„ط°ظƒط§ط، ط§ظ„ط§طµط·ظ†ط§ط¹ظٹ ظˆط§ظ„ط­ط§ط³ط¨ط§طھ

ط§ظ„ظ…ط§ط¯ط© ط§ظ„ط£ظˆظ„ظ‰: ط§ظ„ط­ط¶ظˆط± ط§ظ„ط¥ظ„ط²ط§ظ…ظٹ
ظٹظڈط¹ط¯ظ‘ ط­ط¶ظˆط± ط§ظ„ظ…ط­ط§ط¶ط±ط§طھ ظˆط§ظ„ط£ط¹ظ…ط§ظ„ ط§ظ„ط¹ظ…ظ„ظٹط© ظˆط§ظ„ظ…ظٹط¯ط§ظ†ظٹط© ط¥ظ„ط²ط§ظ…ظٹط§ظ‹ ظ„ط¬ظ…ظٹط¹ ط·ظ„ط§ط¨ ط§ظ„ظƒظ„ظٹط©.
ظٹط¬ط¨ ط¹ظ„ظ‰ ط§ظ„ط·ط§ظ„ط¨ ط­ط¶ظˆط± ظ…ط§ ظ„ط§ ظٹظ‚ظ„ ط¹ظ† 75% ظ…ظ† ط¥ط¬ظ…ط§ظ„ظٹ ط§ظ„ظ…ط­ط§ط¶ط±ط§طھ ط§ظ„ظ…ظ‚ط±ط±ط© ظ„ظƒظ„ ظ…ط§ط¯ط© ظپظٹ ط§ظ„ظپطµظ„ ط§ظ„ط¯ط±ط§ط³ظٹ.

ط§ظ„ظ…ط§ط¯ط© ط§ظ„ط«ط§ظ†ظٹط©: ط§ظ„ط­ط¯ ط§ظ„ط£ظ‚طµظ‰ ظ„ظ„ط؛ظٹط§ط¨
ط§ظ„ط­ط¯ ط§ظ„ط£ظ‚طµظ‰ ط§ظ„ظ…ط³ظ…ظˆط­ ط¨ظ‡ ظ„ظ„ط؛ظٹط§ط¨ ظ‡ظˆ 25% ظ…ظ† ط¥ط¬ظ…ط§ظ„ظٹ ط³ط§ط¹ط§طھ ط§ظ„ظ…ط§ط¯ط©.
ظٹظڈط­طھط³ط¨ ط§ظ„ط؛ظٹط§ط¨ ط¨ط¹ط°ط± ظˆط¨ط¯ظˆظ† ط¹ط°ط± ط¶ظ…ظ† ظ†ط³ط¨ط© ط§ظ„ط؛ظٹط§ط¨ ط§ظ„ط¥ط¬ظ…ط§ظ„ظٹط© ط­طھظ‰ ظٹطھظ… ط§ظ„ط¨طھ ظپظٹظ‡ ظ…ظ† ظ„ط¬ظ†ط© ط´ط¤ظˆظ† ط§ظ„ط·ظ„ط§ط¨.
ظپظٹ ط­ط§ظ„ط© طھط¬ط§ظˆط² ظ†ط³ط¨ط© ط§ظ„ط؛ظٹط§ط¨ 10% ظˆط­طھظ‰ 20%: ظٹظڈط±ط³ظ„ ظ„ظ„ط·ط§ظ„ط¨ ط¥ظ†ط°ط§ط± ط£ظƒط§ط¯ظٹظ…ظٹ ط£ظˆظ„ ط¹ط¨ط± ط§ظ„ط¨ظˆط§ط¨ط© ط§ظ„ط¥ظ„ظƒطھط±ظˆظ†ظٹط©.

ط§ظ„ظ…ط§ط¯ط© ط§ظ„ط«ط§ظ„ط«ط©: ط§ظ„ط­ط±ظ…ط§ظ† ظ…ظ† ط¯ط®ظˆظ„ ط§ظ„ط§ظ…طھط­ط§ظ† ط§ظ„ظ†ظ‡ط§ط¦ظٹ (ط§ظ„ط±ط³ظˆط¨ ط¨ط§ظ„ط؛ظٹط§ط¨)
ط¥ط°ط§ طھط¬ط§ظˆط² ط§ظ„ط·ط§ظ„ط¨ ظ†ط³ط¨ط© ط§ظ„ط؛ظٹط§ط¨ ط§ظ„ظ…ظ‚ط±ط±ط© (25%) ظپظٹ ط£ظٹ ظ…ط§ط¯ط© ط¯ظˆظ† ط¹ط°ط± ظ‚ظ‡ط±ظٹ ظ…ط¹طھظ…ط¯طŒ ظٹظڈط­ط±ظژظ… ط±ط³ظ…ظٹط§ظ‹ ظ…ظ† ط¯ط®ظˆظ„ ط§ظ„ط§ظ…طھط­ط§ظ† ط§ظ„ظ†ظ‡ط§ط¦ظٹ ظ„طھظ„ظƒ ط§ظ„ظ…ط§ط¯ط©.
طھظڈط±طµط¯ ظ„ظ„ط·ط§ظ„ط¨ ط¯ط±ط¬ط© طµظپط± ظپظٹ ط®ط§ظ†ط© ط§ظ„ط§ظ…طھط­ط§ظ† ط§ظ„ظ†ظ‡ط§ط¦ظٹ ظ…ط¹ طھط³ط¬ظٹظ„ طھظ‚ط¯ظٹط± (DN - ط­ط±ظ…ط§ظ†).
ظٹط­ظ‚ ظ„ظ„ط·ط§ظ„ط¨ طھظ‚ط¯ظٹظ… ط§ظ„طھظ…ط§ط³ طھط¸ظ„ظ… ط±ط³ظ…ظٹ ط¥ظ„ظ‰ ظˆظƒظٹظ„ ط§ظ„ظƒظ„ظٹط© ظ„ط´ط¤ظˆظ† ط§ظ„طھط¹ظ„ظٹظ… ظˆط§ظ„ط·ظ„ط§ط¨ ط®ظ„ط§ظ„ ط£ط³ط¨ظˆط¹ ظˆط§ط­ط¯ ظ…ظ† ط¥ط¹ظ„ط§ظ† ظƒط´ظˆظپ ط§ظ„ط­ط±ظ…ط§ظ†.

ط§ظ„ظ…ط§ط¯ط© ط§ظ„ط±ط§ط¨ط¹ط©: ط­ط§ظ„ط§طھ ط§ظ„ط؛ظٹط§ط¨ ط¨ط¹ط°ط± ظ…ظ‚ط¨ظˆظ„
طھظڈظ‚ط¨ظ„ ط§ظ„ط£ط¹ط°ط§ط± ظپظٹ ط§ظ„ط­ط§ظ„ط§طھ ط§ظ„ط§ط³طھط«ظ†ط§ط¦ظٹط© ط§ظ„طھط§ظ„ظٹط© ظپظ‚ط·:
1. ط§ظ„طھظ†ظˆظٹظ… ظپظٹ ط§ظ„ظ…ط³طھط´ظپظ‰ ط£ظˆ ط¥ط¬ط±ط§ط، ط¹ظ…ظ„ظٹط§طھ ط¬ط±ط§ط­ظٹط© ط¹ط§ط¬ظ„ط© ظ…ط¹ طھظ‚ط¯ظٹظ… طھظ‚ط±ظٹط± ط·ط¨ظٹ ظ…ط¹طھظ…ط¯ ظ…ظ† ط§ظ„ط¥ط¯ط§ط±ط© ط§ظ„ط·ط¨ظٹط© ط¨ط§ظ„ط¬ط§ظ…ط¹ط©.
2. ط­ط§ظ„ط§طھ ط§ظ„ظˆظپط§ط© ظ„ظ„ط£ظ‚ط§ط±ط¨ ظ…ظ† ط§ظ„ط¯ط±ط¬ط© ط§ظ„ط£ظˆظ„ظ‰ (ط§ظ„ط£ط¨طŒ ط§ظ„ط£ظ…طŒ ط§ظ„ط£ط®طŒ ط§ظ„ط£ط®طھ) ظ…ط¹ ط¥ط±ظپط§ظ‚ ط´ظ‡ط§ط¯ط© ط§ظ„ظˆظپط§ط©.
3. طھظ…ط«ظٹظ„ ط§ظ„ظƒظ„ظٹط© ط£ظˆ ط§ظ„ط¬ط§ظ…ط¹ط© ظپظٹ ط§ظ„ط¨ط·ظˆظ„ط§طھ ظˆط§ظ„ظ…ط¤طھظ…ط±ط§طھ ظˆط§ظ„ظ…ط³ط§ط¨ظ‚ط§طھ ط§ظ„ط±ط³ظ…ظٹط© ط¨ط®ط·ط§ط¨ طھظƒظ„ظٹظپ ظ…ط³ط¨ظ‚ ظ…ظ† ط±ط¹ط§ظٹط© ط§ظ„ط´ط¨ط§ط¨.
4. ط§ظ„ط¸ط±ظˆظپ ط§ظ„ظ‚ط§ظ‡ط±ط© ط؛ظٹط± ط§ظ„ظ…طھظˆظ‚ط¹ط© ط§ظ„طھظٹ ظٹظ‚ط±ط± ظ…ط¬ظ„ط³ ط§ظ„ظƒظ„ظٹط© ظ‚ط¨ظˆظ„ظ‡ط§.
"""
        with open(ATTENDANCE_DOC, "w", encoding="utf-8") as f:
            f.write(content)
        created_any = True

    # ظˆط«ظٹظ‚ط© ظ†ط¸ط§ظ… ط§ظ„طھظ‚ط¯ظٹط±ط§طھ ظˆط­ط³ط§ط¨ ط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„طھط±ط§ظƒظ…ظٹ
    if not os.path.exists(GPA_DOC):
        content = """ظ†ط¸ط§ظ… ط§ظ„طھظ‚ط¯ظٹط±ط§طھ ظˆط­ط³ط§ط¨ ط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„طھط±ط§ظƒظ…ظٹ (CGPA) - ظ†ط¸ط§ظ… ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط©

ط£ظˆظ„ط§ظ‹: ط¬ط¯ظˆظ„ طھظˆط²ظٹط¹ ط§ظ„طھظ‚ط¯ظٹط±ط§طھ ظˆط§ظ„ظ†ظ‚ط§ط·
ط§ظ„ط¯ط±ط¬ط© ط§ظ„ظ…ط¦ظˆظٹط©    ط§ظ„طھظ‚ط¯ظٹط± ط§ظ„ظ„ط§طھظٹظ†ظٹ    ط§ظ„ظ†ظ‚ط§ط· (Grade Points)    ط§ظ„طھظ‚ط¯ظٹط± ط§ظ„ظ…ظƒط§ظپط¦
------------------------------------------------------------------------
90% ظپط£ظƒط«ط±         A+                 4.0                      ظ…ظ…طھط§ط² ظ…ط±طھظپط¹
85% ط¥ظ„ظ‰ ط£ظ‚ظ„ ظ…ظ† 90% A                  3.7                      ظ…ظ…طھط§ط²
80% ط¥ظ„ظ‰ ط£ظ‚ظ„ ظ…ظ† 85% B+                 3.3                      ط¬ظٹط¯ ط¬ط¯ط§ظ‹ ظ…ط±طھظپط¹
75% ط¥ظ„ظ‰ ط£ظ‚ظ„ ظ…ظ† 80% B                  3.0                      ط¬ظٹط¯ ط¬ط¯ط§ظ‹
70% ط¥ظ„ظ‰ ط£ظ‚ظ„ ظ…ظ† 75% C+                 2.7                      ط¬ظٹط¯ ظ…ط±طھظپط¹
65% ط¥ظ„ظ‰ ط£ظ‚ظ„ ظ…ظ† 70% C                  2.3                      ط¬ظٹط¯
60% ط¥ظ„ظ‰ ط£ظ‚ظ„ ظ…ظ† 65% D+                 2.0                      ظ…ظ‚ط¨ظˆظ„ ظ…ط±طھظپط¹
55% ط¥ظ„ظ‰ ط£ظ‚ظ„ ظ…ظ† 60% D                  1.7                      ظ…ظ‚ط¨ظˆظ„ (ط§ظ„ط­ط¯ ط§ظ„ط£ط¯ظ†ظ‰ ظ„ظ„ظ†ط¬ط§ط­)
ط£ظ‚ظ„ ظ…ظ† 55%        F                  0.0                      ط±ط§ط³ط¨

ط«ط§ظ†ظٹط§ظ‹: ط´ط±ظˆط· ط§ظ„ظ†ط¬ط§ط­ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ
ط§ظ„ط­ط¯ ط§ظ„ط£ط¯ظ†ظ‰ ظ„ظ„ظ†ط¬ط§ط­ ظپظٹ ط£ظٹ ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ ظ‡ظˆ ط§ظ„ط­طµظˆظ„ ط¹ظ„ظ‰ طھظ‚ط¯ظٹط± (D) ط¨ظ†ط³ط¨ط© 55% ظ…ظ† ط¥ط¬ظ…ط§ظ„ظٹ ط§ظ„ط¯ط±ط¬ط© ط§ظ„ظ†ظ‡ط§ط¦ظٹط©.
ط§ظ„ظ…ظ‚ط±ط± ط§ظ„ط­ط§طµظ„ ظپظٹظ‡ ط§ظ„ط·ط§ظ„ط¨ ط¹ظ„ظ‰ طھظ‚ط¯ظٹط± (F) ظ„ط§ طھظڈط­طھط³ط¨ ط³ط§ط¹ط§طھظ‡ ط§ظ„ظ…ط¹طھظ…ط¯ط© ط¶ظ…ظ† ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ظ†ط¬ط²ط©طŒ ظˆظٹط¬ط¨ ط¹ظ„ظ‰ ط§ظ„ط·ط§ظ„ط¨ ط¥ط¹ط§ط¯ط© ط¯ط±ط§ط³طھظ‡ ظˆط§ظ„طھط³ط¬ظٹظ„ ظپظٹظ‡ ظ…ط±ط© ط£ط®ط±ظ‰.

ط«ط§ظ„ط«ط§ظ‹: ظ…ط¹ط§ط¯ظ„ط© ط­ط³ط§ط¨ ط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„طھط±ط§ظƒظ…ظٹ (GPA)
ط§ظ„ظ…ط¹ط¯ظ„ = ظ…ط¬ظ…ظˆط¹ (ظ†ظ‚ط§ط· ظƒظ„ ظ…ظ‚ط±ط± أ— ط¹ط¯ط¯ ط³ط§ط¹ط§طھظ‡ ط§ظ„ظ…ط¹طھظ…ط¯ط©) أ· ظ…ط¬ظ…ظˆط¹ ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط© ط§ظ„ط¥ط¬ظ…ط§ظ„ظٹ
ط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„طھط±ط§ظƒظ…ظٹ ط§ظ„طھط±ط§ظƒظ…ظٹ ط§ظ„ط¹ط§ظ… ط§ظ„ظ…ط·ظ„ظˆط¨ ظ„ظ„طھط®ط±ط¬ ظ‡ظˆ 2.0 ط¹ظ„ظ‰ ط§ظ„ط£ظ‚ظ„ ظ…ظ† 4.0.

ط±ط§ط¨ط¹ط§ظ‹: ط§ظ„طھط­ط°ظٹط± ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ ظˆظ„ظˆط§ط¦ط­ ط§ظ„ظپطµظ„
1. ظٹظˆط¶ط¹ ط§ظ„ط·ط§ظ„ط¨ طھط­طھ ط§ظ„ظ…ظ„ط§ط­ط¸ط© ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹط© (Academic Probation) ط¥ط°ط§ ط§ظ†ط®ظپط¶ ظ…ط¹ط¯ظ„ظ‡ ط§ظ„طھط±ط§ظƒظ…ظٹ ط¹ظ† 2.0 ظپظٹ ط£ظٹ ظپطµظ„ ط¯ط±ط§ط³ظٹ.
2. ط§ظ„ط·ط§ظ„ط¨ ط§ظ„ظ…ظ†ط°ط± ط£ظƒط§ط¯ظٹظ…ظٹط§ظ‹ ظٹظڈظ…ظ†ط¹ ظ…ظ† طھط³ط¬ظٹظ„ ط£ظƒط«ط± ظ…ظ† 12 ط³ط§ط¹ط© ظ…ط¹طھظ…ط¯ط© ظپظٹ ط§ظ„ظپطµظ„ ط§ظ„طھط§ظ„ظٹ ظ„ظ„طھط±ظƒظٹط² ط¹ظ„ظ‰ ط±ظپط¹ ظ…ط¹ط¯ظ„ظ‡.
3. ط¥ط°ط§ ط§ط³طھظ…ط± ط§ظ„ط·ط§ظ„ط¨ طھط­طھ ط§ظ„ظ…ظ„ط§ط­ط¸ط© ظ„ط«ظ„ط§ط«ط© ظپطµظˆظ„ ط¯ط±ط§ط³ظٹط© ظ…طھطھط§ظ„ظٹط© ظٹظڈط¹ط±ط¶ ظ…ظˆظ‚ظپظ‡ ط¹ظ„ظ‰ ظ…ط¬ظ„ط³ ط§ظ„ظƒظ„ظٹط© ظ„ظ„ظ†ط¸ط± ظپظٹ ظپطµظ„ظ‡ ط£ظƒط§ط¯ظٹظ…ظٹط§ظ‹ ط£ظˆ ظ…ظ†ط­ظ‡ ظپط±طµط© ط£ط®ظٹط±ط©.

ط®ط§ظ…ط³ط§ظ‹: ظ…ط±طھط¨ط© ط§ظ„ط´ط±ظپ ظˆط§ظ„طھظپظˆظ‚
طھظڈظ…ظ†ط­ ظ…ط±طھط¨ط© ط§ظ„ط´ط±ظپ ظ„ظ„ط·ط§ظ„ط¨ ط§ظ„ط°ظٹ ظٹطھط®ط±ط¬ ط¨ظ…ط¹ط¯ظ„ طھط±ط§ظƒظ…ظٹ 3.5 ظپط£ظƒط«ط± ط¨ط´ط±ط· ط£ظ„ط§ ظٹظƒظˆظ† ظ‚ط¯ ط±ط³ط¨ ظپظٹ ط£ظٹ ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ ط·ظˆط§ظ„ ط³ظ†ظˆط§طھ ط¯ط±ط§ط³طھظ‡ ط¨ط§ظ„ظƒظ„ظٹط©.
"""
        with open(GPA_DOC, "w", encoding="utf-8") as f:
            f.write(content)
        created_any = True

    # ظˆط«ظٹظ‚ط© ظ‚ظˆط§ط¹ط¯ ط§ظ„طھط³ط¬ظٹظ„ ظˆط§ظ„ط¥ط±ط´ط§ط¯ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ
    if not os.path.exists(REG_DOC):
        content = """ظ‚ظˆط§ط¹ط¯ ط§ظ„طھط³ط¬ظٹظ„ ظˆط§ظ„ط¥ط±ط´ط§ط¯ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ - ظƒظ„ظٹط© ط§ظ„ط­ط§ط³ط¨ط§طھ ظˆط§ظ„ط°ظƒط§ط، ط§ظ„ط§طµط·ظ†ط§ط¹ظٹ

ط£ظˆظ„ط§ظ‹: ط§ظ„ط¹ط¨ط، ط§ظ„ط¯ط±ط§ط³ظٹ (ط§ظ„ط­ط¯ ط§ظ„ط£ط¯ظ†ظ‰ ظˆط§ظ„ط£ظ‚طµظ‰ ظ„ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط©)
1. ط§ظ„ط­ط¯ ط§ظ„ط£ط¯ظ†ظ‰ ظ„ظ„طھط³ط¬ظٹظ„ ظپظٹ ط§ظ„ظپطµظ„ ط§ظ„ط¯ط±ط§ط³ظٹ ط§ظ„ط§ط¹طھظٹط§ط¯ظٹ: 12 ط³ط§ط¹ط© ظ…ط¹طھظ…ط¯ط©.
2. ط§ظ„ط­ط¯ ط§ظ„ط£ظ‚طµظ‰ ظ„ظ„ط¹ط¨ط، ط§ظ„ط¯ط±ط§ط³ظٹ ظ„ظ„ط·ط§ظ„ط¨ ط§ظ„ط¹ط§ط¯ظٹ (ظ…ط¹ط¯ظ„ 2.0 ط¥ظ„ظ‰ 3.49): 18 ط³ط§ط¹ط© ظ…ط¹طھظ…ط¯ط©.
3. ط§ط³طھط«ظ†ط§ط، ط§ظ„طھظپظˆظ‚ (ظ…ط¹ط¯ظ„ 3.5 ظپط£ظƒط«ط±): ظٹظڈط³ظ…ط­ ظ„ظ„ط·ط§ظ„ط¨ ط¨طھط³ط¬ظٹظ„ ط­طھظ‰ 21 ط³ط§ط¹ط© ظ…ط¹طھظ…ط¯ط© ط¨ط¹ط¯ ظ…ظˆط§ظپظ‚ط© ط§ظ„ظ…ط±ط´ط¯ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ ظˆط§ظ„ط¹ظ…ظٹط¯.
4. ط§ظ„ط·ظ„ط§ط¨ ط§ظ„ظ…ظ†ط°ط±ظˆظ† ط£ظƒط§ط¯ظٹظ…ظٹط§ظ‹ (ظ…ط¹ط¯ظ„ ط£ظ‚ظ„ ظ…ظ† 2.0): ط§ظ„ط­ط¯ ط§ظ„ط£ظ‚طµظ‰ ط§ظ„ظ…ط³ظ…ظˆط­ ط¨ظ‡ ظ‡ظˆ 12 ط³ط§ط¹ط© ظ…ط¹طھظ…ط¯ط© ظپظ‚ط·.
5. ط§ظ„ظپطµظ„ ط§ظ„طµظٹظپظٹ (Summer Semester): ط§ظ„ط­ط¯ ط§ظ„ط£ظ‚طµظ‰ ظ„ظ„طھط³ط¬ظٹظ„ ظ‡ظˆ 6 ط³ط§ط¹ط§طھ ظ…ط¹طھظ…ط¯ط© (ط£ظˆ 7 ط³ط§ط¹ط§طھ ط¥ط°ط§ ظƒط§ظ†طھ طھط´ظ…ظ„ ظ…ظ‚ط±ط± طھط¯ط±ظٹط¨ ط£ظˆ طھط®ط±ط¬).

ط«ط§ظ†ظٹط§ظ‹: ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ط³ط§ط¨ظ‚ط© ظ„ظ„ظ…ظ‚ط±ط±ط§طھ (Prerequisites)
ظ„ط§ ظٹط¬ظˆط² ظ„ظ„ط·ط§ظ„ط¨ ط¨ط£ظٹ ط­ط§ظ„ ظ…ظ† ط§ظ„ط£ط­ظˆط§ظ„ ط§ظ„طھط³ط¬ظٹظ„ ظپظٹ ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ ظ…ط§ ظ„ظ… ظٹظƒظ† ظ‚ط¯ ط§ط¬طھط§ط² ط§ظ„ظ…طھط·ظ„ط¨ ط§ظ„ط³ط§ط¨ظ‚ (Prerequisite) ط¨ظ†ط¬ط§ط­ (طھظ‚ط¯ظٹط± D ط¹ظ„ظ‰ ط§ظ„ط£ظ‚ظ„).
ظٹظڈظ„ط؛ظ‰ طھط³ط¬ظٹظ„ ط£ظٹ ظ…ظ‚ط±ط± ظٹطھظ… ط¨ط´ظƒظ„ ط®ط§ط·ط¦ ط¯ظˆظ† ط§ط³طھظٹظپط§ط، ظ…طھط·ظ„ط¨ظ‡ ط§ظ„ط³ط§ط¨ظ‚ ظپظˆط± ظ…ط±ط§ط¬ط¹ط© ط§ظ„ط¬ط¯ط§ظˆظ„ ظˆظ‚ط¨ظ„ ط¨ط¯ط، ط§ظ„ط£ط³ط¨ظˆط¹ ط§ظ„ط«ط§ظ„ط«.

ط«ط§ظ„ط«ط§ظ‹: ظ…ظ‡ط§ظ… ط§ظ„ظ…ط±ط´ط¯ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ
1. ظٹظڈط®طµطµ ظ„ظƒظ„ ط·ط§ظ„ط¨ ظ…ط±ط´ط¯ ط£ظƒط§ط¯ظٹظ…ظٹ ظ…ظ† ط£ط¹ط¶ط§ط، ظ‡ظٹط¦ط© ط§ظ„طھط¯ط±ظٹط³ ظ„ظ…ط³ط§ط¹ط¯طھظ‡ ظپظٹ ط¨ظ†ط§ط، ط®ط·طھظ‡ ط§ظ„ط¯ط±ط§ط³ظٹط© ظˆط§ط®طھظٹط§ط± ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…ظ†ط§ط³ط¨ط©.
2. ظ„ط§ ظٹظڈط¹طھظ…ط¯ ط§ظ„ط¬ط¯ظˆظ„ ط§ظ„ط¯ط±ط§ط³ظٹ ظ„ظ„ط·ط§ظ„ط¨ ط¥ظ„ط§ ط¨ط¹ط¯ ط§ظ„ط­طµظˆظ„ ط¹ظ„ظ‰ ط§ظ„ظ…ظˆط§ظپظ‚ط© ط§ظ„ط¥ظ„ظƒطھط±ظˆظ†ظٹط© ظ…ظ† ط§ظ„ظ…ط±ط´ط¯ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ.
3. ظٹطھظˆظ„ظ‰ ط§ظ„ظ…ط±ط´ط¯ ظ…طھط§ط¨ط¹ط© ط§ظ„ط·ظ„ط§ط¨ ط§ظ„ظ…طھط¹ط«ط±ظٹظ† ظˆطھظ‚ط¯ظٹظ… ط§ظ„ط¯ط¹ظ… ط§ظ„ط¥ط±ط´ط§ط¯ظٹ ط§ظ„ظ…ظ†ط§ط³ط¨ ظ„طھط­ط³ظٹظ† ظ…ط¹ط¯ظ„ط§طھظ‡ظ….

ط±ط§ط¨ط¹ط§ظ‹: ظپطھط±ط§طھ ط§ظ„ط­ط°ظپ ظˆط§ظ„ط¥ط¶ط§ظپط© ظˆط§ظ„ط§ظ†ط³ط­ط§ط¨ (Add & Drop)
1. ظپطھط±ط© ط§ظ„ط­ط°ظپ ظˆط§ظ„ط¥ط¶ط§ظپط©: ط®ظ„ط§ظ„ ط§ظ„ط£ط³ط¨ظˆط¹ظٹظ† ط§ظ„ط£ظˆظ„ ظˆط§ظ„ط«ط§ظ†ظٹ ظ…ظ† ط¨ط¯ط، ط§ظ„ظپطµظ„ ط§ظ„ط¯ط±ط§ط³ظٹطŒ ظˆظ„ط§ ظٹظڈط«ط¨طھ ط§ظ„ظ…ظ‚ط±ط± ظپظٹ ط§ظ„ط³ط¬ظ„ ط¹ظ†ط¯ ط­ط°ظپظ‡ ط®ظ„ط§ظ„ ظ‡ط°ظ‡ ط§ظ„ظپطھط±ط©.
2. ط§ظ„ط§ظ†ط³ط­ط§ط¨ ط¨ط¹ط°ط± (Withdrawal - W): ظٹط¬ظˆط² ظ„ظ„ط·ط§ظ„ط¨ ط§ظ„ط§ظ†ط³ط­ط§ط¨ ظ…ظ† ظ…ظ‚ط±ط± ط­طھظ‰ ظ†ظ‡ط§ظٹط© ط§ظ„ط£ط³ط¨ظˆط¹ ط§ظ„ط«ط§ظ…ظ†طŒ ظˆطھظڈط³ط¬ظ„ ظ„ظ‡ ط¹ظ„ط§ظ…ط© (W) ظˆظ„ط§ طھط¯ط®ظ„ ظپظٹ ط­ط³ط§ط¨ ط§ظ„ظ…ط¹ط¯ظ„.
3. ط§ظ„ط§ظ†ط³ط­ط§ط¨ ط§ظ„ط¥ط¬ط¨ط§ط±ظٹ/ط§ظ„ط±ط³ظˆط¨ (WF): ط§ظ„ط§ظ†ط³ط­ط§ط¨ ط¨ط¹ط¯ ط§ظ„ط£ط³ط¨ظˆط¹ ط§ظ„ط«ط§ظ…ظ† ظٹظڈط¹ط¯ ط±ط³ظˆط¨ط§ظ‹ ط¨ط§ظ„ط§ظ†ط³ط­ط§ط¨ (WF) ظˆظٹظڈط­ط³ط¨ ظƒطھظ‚ط¯ظٹط± F ط¨ظ†ظ‚ط§ط· طµظپط±ظٹط© ظپظٹ ط§ظ„ظ…ط¹ط¯ظ„.
"""
        with open(REG_DOC, "w", encoding="utf-8") as f:
            f.write(content)
        created_any = True

    return created_any


# =============================================================================
#  ظˆط­ط¯ط© ط§ظ„طھط¹ط§ظ…ظ„ ظ…ط¹ ط§ظ„ظ…ظ„ظپط§طھ (CSV / JSON / Docs)
# =============================================================================
def load_courses() -> list[dict]:
    """طھط­ظ…ظٹظ„ ط¨ظٹط§ظ†ط§طھ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ظ…ظ† ظ…ظ„ظپ CSV."""
    courses = []
    if not os.path.exists(COURSES_FILE):
        return courses
    with open(COURSES_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            courses.append(dict(row))
    return courses


def save_courses(courses: list[dict]):
    """ط­ظپط¸ ظ‚ط§ط¦ظ…ط© ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط¥ظ„ظ‰ ظ…ظ„ظپ CSV."""
    if not courses:
        return
    fieldnames = ["course_id", "course_name", "instructor", "room", "credit_hours"]
    with open(COURSES_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(courses)


def load_prerequisites() -> dict:
    """طھط­ظ…ظٹظ„ ط´ط¬ط±ط© ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ط³ط§ط¨ظ‚ط© ظ…ظ† ظ…ظ„ظپ JSON."""
    if not os.path.exists(PREREQ_FILE):
        return {}
    with open(PREREQ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_prerequisites(prereqs: dict):
    """ط­ظپط¸ ط´ط¬ط±ط© ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط¥ظ„ظ‰ ظ…ظ„ظپ JSON."""
    with open(PREREQ_FILE, "w", encoding="utf-8") as f:
        json.dump(prereqs, f, ensure_ascii=False, indent=4)


def load_doc_file(filepath: str) -> str:
    """ظ‚ط±ط§ط،ط© ظ…ط­طھظˆظ‰ ظ…ظ„ظپ ظ†طµظٹ ط¨طھط±ظ…ظٹط² UTF-8."""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# =============================================================================
#  ظˆط­ط¯ط© ط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ (Information Retrieval - IR)
# =============================================================================
def build_inverted_index(doc_texts: dict[str, str]) -> dict[str, list[str]]:
    """ط¨ظ†ط§ط، Inverted Index ظ…ظ† ط§ظ„ظˆط«ط§ط¦ظ‚ ط§ظ„ظ†طµظٹط©."""
    index = defaultdict(set)
    for doc_name, text in doc_texts.items():
        words = text.replace("\n", " ").replace(".", " ").replace("طŒ", " ").split()
        for word in words:
            clean = word.strip().lower()
            if len(clean) > 2:
                index[clean].add(doc_name)
    return {word: sorted(docs) for word, docs in index.items()}


class IREngine:
    """ظ…ط­ط±ظƒ ط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ ط¹ظ„ظ‰ TF-IDF ظˆ Cosine Similarity."""
    def __init__(self):
        self.doc_names: list[str] = []
        self.doc_texts: list[str] = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.inverted_index: dict = {}
        self.build()

    def build(self):
        self.doc_names.clear()
        self.doc_texts.clear()
        self.inverted_index.clear()

        doc_texts_map = {}
        if os.path.exists(DOCS_DIR):
            for fname in os.listdir(DOCS_DIR):
                if fname.endswith(".txt"):
                    fpath = os.path.join(DOCS_DIR, fname)
                    text = load_doc_file(fpath)
                    if text.strip():
                        self.doc_names.append(fname)
                        self.doc_texts.append(text)
                        doc_texts_map[fname] = text

        if not self.doc_texts:
            return

        self.inverted_index = build_inverted_index(doc_texts_map)
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"(?u)\b\w+\b",
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_texts)

    def search(self, query: str, top_n: int = 3) -> list[dict]:
        """ط§ظ„ط¨ط­ط« ظپظٹ ط§ظ„ظˆط«ط§ط¦ظ‚ ظˆط­ط³ط§ط¨ طھط´ط§ط¨ظ‡ ط¬ظٹط¨ ط§ظ„طھظ…ط§ظ…."""
        if self.vectorizer is None or self.tfidf_matrix is None or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        ranked_indices = similarities.argsort()[::-1]

        results = []
        for idx in ranked_indices[:top_n]:
            score = float(similarities[idx])
            if score > 0.01:
                # ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط£ظپط¶ظ„ ظپظ‚ط±ط© ظ…ط·ط§ط¨ظ‚ط© ظƒظ…ط¹ط§ظٹظ†ط©
                paragraphs = [p.strip() for p in self.doc_texts[idx].split("\n\n") if p.strip()]
                best_snippet = paragraphs[0] if paragraphs else self.doc_texts[idx][:250]
                results.append({
                    "file": self.doc_names[idx],
                    "score": round(score * 100, 1),
                    "snippet": best_snippet[:350],
                })
        return results


# =============================================================================
#  ظ…ط­ط±ظƒ ط§ظ„ط§ط³طھظ†طھط§ط¬ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ (Knowledge & Inference Engine)
# =============================================================================
def get_available_courses(passed_courses: list[str]) -> tuple[list[dict], list[dict]]:
    """
    ظ…ط­ط±ظƒ ط§ط³طھظ†طھط§ط¬ ظٹط­ط¯ط¯ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…طھط§ط­ط© ظˆط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…ظ‚ظپظ„ط© ظ„ظ„ط·ط§ظ„ط¨.
    ط§ظ„ظ…ط¯ط®ظ„ط§طھ: ظ‚ط§ط¦ظ…ط© ط±ظ…ظˆط² ط§ظ„ظ…ظˆط§ط¯ ط§ظ„ظ…ط¬طھط§ط²ط© (ظ…ط«ظ„ ['CS101', 'MATH101'])
    ط§ظ„ظ…ط®ط±ط¬ط§طھ: (ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…طھط§ط­ط© ظ„ظ„طھط³ط¬ظٹظ„, ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…ظ‚ظپظ„ط© ظ…ط¹ ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ظ†ط§ظ‚طµط©)
    """
    prereqs = load_prerequisites()
    all_courses = load_courses()
    passed_set = set(c.upper().strip() for c in passed_courses if c.strip())

    available = []
    locked = []

    for course in all_courses:
        cid = course["course_id"].upper().strip()

        # طھط®ط·ظٹ ط§ظ„ظ…ط§ط¯ط© ط¥ط°ط§ ظƒط§ظ† ط§ظ„ط·ط§ظ„ط¨ ظ‚ط¯ ط§ط¬طھط§ط²ظ‡ط§ ط¨ط§ظ„ظپط¹ظ„
        if cid in passed_set:
            continue

        reqs = prereqs.get(cid, [])
        missing_reqs = [r for r in reqs if r.upper() not in passed_set]

        if not missing_reqs:
            available.append(course)
        else:
            locked_info = dict(course)
            locked_info["missing_prereqs"] = missing_reqs
            locked.append(locked_info)

    return available, locked


# =============================================================================
#  ظ…ظƒظˆظ†ط§طھ ط§ظ„ظˆط§ط¬ظ‡ط© ط§ظ„ط¨طµط±ظٹط© ط§ظ„ظپط§ط®ط±ط© (UI Components)
# =============================================================================
def render_header(subtitle: str = ""):
    """ط¹ط±ط¶ ط§ظ„ط´ط¹ط§ط± ظˆط§ظ„طھط±ظˆظٹط³ط© ط§ظ„ط±ط¦ظٹط³ظٹط© ط¨طھطµظ…ظٹظ… ط¨ط·ط§ظ‚ط© ط¹طµط±ظٹط©."""
    clear_screen()
    
    title_text = f"[bold bright_yellow]ًںژ“ SMART STUDENT GUIDE[/bold bright_yellow]  |  [bold bright_cyan]{ar('ط¯ظ„ظٹظ„ ط§ظ„ط·ط§ظ„ط¨ ط§ظ„ط°ظƒظٹ')}[/bold bright_cyan]"
    desc_text = f"[dim white]{ar('ظ†ط¸ط§ظ… ط§ظ„ط¥ط±ط´ط§ط¯ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ ط§ظ„ط°ظƒظٹ ظˆط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ')}[/dim white]"
    
    if subtitle:
        desc_text += f"\n[bold bright_green]â—€ {ar(subtitle)} â–¶[/bold bright_green]"

    panel = Panel(
        f"{title_text}\n{desc_text}",
        box=box.ROUNDED,
        border_style="bright_blue",
        padding=(0, 2),
    )
    console.print(panel)


def render_dashboard_bar(ir_engine: IREngine):
    """ط¹ط±ط¶ ط´ط±ظٹط· ط§ظ„ط­ط§ظ„ط© ظˆط§ظ„ط¥ط­طµط§ط¦ظٹط§طھ ط§ظ„ط³ط±ظٹط¹ط© ظ„ظ„ظ†ط¸ط§ظ…."""
    courses_count = len(load_courses())
    docs_count = len(ir_engine.doc_names)
    terms_count = len(ir_engine.inverted_index)

    status_str = (
        f"[bright_cyan]ًں“ڑ {ar('ط§ظ„ظ…ظ‚ط±ط±ط§طھ')}: {courses_count}[/bright_cyan]   "
        f"[bright_magenta]ًں“„ {ar('ط§ظ„ظ„ظˆط§ط¦ط­')}: {docs_count}[/bright_magenta]   "
        f"[bright_yellow]ًں§  {ar('ط§ظ„ظƒظ„ظ…ط§طھ ط§ظ„ظ…ظپظ‡ط±ط³ط©')}: {terms_count}[/bright_yellow]   "
        f"[bright_green]âڑ، {ar('ط§ظ„ط­ط§ظ„ط©')}: {ar('ظ†ط´ط· ظˆظ…طھطµظ„')}[/bright_green]"
    )
    console.print(Panel(status_str, box=box.HORIZONTALS, border_style="dim blue", padding=(0, 1)))


def render_courses_table(courses: list[dict], title: str = "ط¯ظ„ظٹظ„ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ط¯ط±ط§ط³ظٹط©"):
    """ط¹ط±ط¶ ط¬ط¯ظˆظ„ ظ…ظ‚ط±ط±ط§طھ ط¯ط±ط§ط³ظٹط© ظ…ظ‚ط³ظ…ط© ط¨ط§ظ„طھط±طھظٹط¨ ظ…ط§ ط¨ظٹظ† 3 ط³ط§ط¹ط§طھ ظˆط³ط§ط¹طھظٹظ† ط¨طھظ†ط³ظٹظ‚ ظ…ظ„ظˆظ† ظˆط¹ط§ظ„ظٹ ط§ظ„ط¬ظˆط¯ط©."""
    if not courses:
        console.print(f"[yellow]{ar('ظ„ط§ طھظˆط¬ط¯ ظ…ظ‚ط±ط±ط§طھ ظ„ط¹ط±ط¶ظ‡ط§.')}[/yellow]")
        return

    prereqs = load_prerequisites()

    courses_3h = sorted([c for c in courses if str(c.get("credit_hours", "3")).strip() == "3"], key=lambda x: x.get("course_id", ""))
    courses_2h = sorted([c for c in courses if str(c.get("credit_hours", "")).strip() == "2"], key=lambda x: x.get("course_id", ""))
    courses_other = sorted([c for c in courses if str(c.get("credit_hours", "")).strip() not in ("2", "3")], key=lambda x: x.get("course_id", ""))

    def _build_table(items, group_title, border_color, hours_label):
        total_hrs = sum(int(c.get("credit_hours", 3)) for c in items)
        t = Table(
            title=f"[bold {border_color}]{ar(group_title)} ({len(items)} {ar('ظ…ظ‚ط±ط±ط§ظ‹')} | {total_hrs} {ar('ط³ط§ط¹ط© ظ…ط¹طھظ…ط¯ط©')})[/bold {border_color}]",
            box=box.ROUNDED,
            border_style=border_color,
            header_style="bold bright_yellow",
            expand=True,
        )
        t.add_column(ar("ط§ظ„ط±ظ…ط²"), style="bold cyan", justify="center", width=10)
        t.add_column(ar("ط§ط³ظ… ط§ظ„ظ…ط§ط¯ط©"), style="bold white", width=30)
        t.add_column(ar("ط§ظ„ظ…ط­ط§ط¶ط±"), style="green", width=18)
        t.add_column(ar("ط§ظ„ظ‚ط§ط¹ط© / ط§ظ„ظ…ط¹ظ…ظ„"), style="yellow", width=22)
        t.add_column(ar("ط§ظ„ط³ط§ط¹ط§طھ"), justify="center", style="magenta", width=8)
        t.add_column(ar("ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ط³ط§ط¨ظ‚ط©"), style="dim white", width=20)

        for c in items:
            cid = c.get("course_id", "")
            req_list = prereqs.get(cid, [])
            req_str = ", ".join(req_list) if req_list else ar("ط¨ط¯ظˆظ† ظ…طھط·ظ„ط¨")
            t.add_row(
                cid,
                ar(c.get("course_name", "")),
                ar(c.get("instructor", "")),
                ar(c.get("room", "")),
                str(c.get("credit_hours", "")),
                ar(req_str),
            )
        return t

    if courses_3h:
        console.print(_build_table(courses_3h, "ًں•’ ط£ظˆظ„ط§ظ‹: ظ…ظ‚ط±ط±ط§طھ 3 ط³ط§ط¹ط§طھ ظ…ط¹طھظ…ط¯ط© (ظ…ط±طھط¨ط© ط¨ط§ظ„طھط±طھظٹط¨)", "bright_cyan", "3"))
    if courses_2h:
        if courses_3h:
            console.print()
        console.print(_build_table(courses_2h, "ًں•‘ ط«ط§ظ†ظٹط§ظ‹: ظ…ظ‚ط±ط±ط§طھ ط³ط§ط¹طھط§ظ† ظ…ط¹طھظ…ط¯طھط§ظ† (ظ…ط±طھط¨ط© ط¨ط§ظ„طھط±طھظٹط¨)", "bright_magenta", "2"))
    if courses_other:
        console.print()
        console.print(_build_table(courses_other, "ًں“ڑ ظ…ظ‚ط±ط±ط§طھ ط£ط®ط±ظ‰", "yellow", "3"))


# =============================================================================
#  طµظپط­ط§طھ ظˆظ…ظٹط²ط§طھ ط¨ظˆط§ط¨ط© ط§ظ„ط·ط§ظ„ط¨ (Student Portal)
# =============================================================================
def student_course_catalog():
    """ط§ط³طھط¹ط±ط§ط¶ ط¯ظ„ظٹظ„ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظƒط§ظ…ظ„ ظ„ظ„ظƒظ„ظٹط©."""
    render_header("ط¯ظ„ظٹظ„ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ط¯ط±ط§ط³ظٹط©")
    courses = load_courses()
    render_courses_table(courses, "ط¬ظ…ظٹط¹ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط© ظپظٹ ط§ظ„ط®ط·ط© ط§ظ„ط¯ط±ط§ط³ظٹط©")
    log_query("STUDENT_VIEW_COURSES", f"ط§ط³طھط¹ط±ط§ط¶ {len(courses)} ظ…ظ‚ط±ط±ط§ظ‹")
    pause()


def student_advisor_check():
    """ظ…ط­ط±ظƒ ط§ظ„ط§ط³طھظ†طھط§ط¬ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ: ظپط­طµ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…طھط§ط­ط© ظ„ظ„طھط³ط¬ظٹظ„."""
    render_header("ظ…ط­ط±ظƒ ط§ظ„ط§ط³طھظ†طھط§ط¬ ط§ظ„ط°ظƒظٹ - ظپط­طµ ط§ظ„ظ…ظˆط§ط¯ ط§ظ„ظ…طھط§ط­ط© ظ„ظ„طھط³ط¬ظٹظ„")
    
    courses = load_courses()
    all_cids = [c["course_id"] for c in courses]

    info_panel = Panel(
        f"[bold bright_white]{ar('طھط¹ظ„ظٹظ…ط§طھ ط§ظ„ط¥ط±ط´ط§ط¯ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ:')}[/bold bright_white]\n"
        f"â€¢ {ar('ط£ط¯ط®ظ„ ط±ظ…ظˆط² ط§ظ„ظ…ظˆط§ط¯ ط§ظ„طھظٹ ط§ط¬طھط²طھظ‡ط§ ط¨ظ†ط¬ط§ط­ ظ…ظپطµظˆظ„ط© ط¨ظپط§طµظ„ط© (ظ…ط«ط§ظ„: CS101, MATH101)')}\n"
        f"â€¢ {ar('ط¥ط°ط§ ظƒظ†طھ ط·ط§ظ„ط¨ط§ظ‹ ظ…ط³طھط¬ط¯ط§ظ‹ ظˆظ„ظ… طھط¬طھط² ط£ظٹ ظ…ط§ط¯ط© ط¨ط¹ط¯طŒ ط§ط¶ط؛ط· Enter ظ…ط¨ط§ط´ط±ط©')}\n"
        f"â€¢ [dim cyan]{ar('ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…ط³ط¬ظ„ط© ظپظٹ ط§ظ„ظ†ط¸ط§ظ…')}: {', '.join(all_cids)}[/dim cyan]",
        box=box.ROUNDED,
        border_style="cyan",
    )
    console.print(info_panel)

    raw_input = get_arabic_input("[?] ط§ظ„ظ…ظˆط§ط¯ ط§ظ„ظ…ط¬طھط§ط²ط©")
    passed = [p.strip().upper() for p in raw_input.split(",") if p.strip()]

    available, locked = get_available_courses(passed)
    log_query("STUDENT_CHECK_COURSES", f"ظ…ط¬طھط§ط²: {passed} | ظ…طھط§ط­: {[c['course_id'] for c in available]}")

    # ط¹ط±ط¶ ظ…ظ„ط®طµ ط­ط§ظ„ط© ط§ظ„ط·ط§ظ„ط¨
    completed_hours = sum(int(c.get("credit_hours", 3)) for c in courses if c["course_id"].upper() in passed)
    summary_text = (
        f"[bold bright_green]âœ” {ar('ط§ظ„ظ…ظˆط§ط¯ ط§ظ„ظ…ط¬طھط§ط²ط©')}: {len(passed)} {ar('ظ…ط§ط¯ط©')} ({completed_hours} {ar('ط³ط§ط¹ط© ظ…ط¹طھظ…ط¯ط©')})[/bold bright_green]\n"
        f"[bold bright_cyan]âڑ، {ar('ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…طھط§ط­ط© ظ„ظ„طھط³ط¬ظٹظ„ ظپظˆط±ط§ظ‹')}: {len(available)} {ar('ظ…ظ‚ط±ط±')}[/bold bright_cyan]\n"
        f"[bold yellow]ًں”’ {ar('ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…ط؛ظ„ظ‚ط© ط­ط§ظ„ظٹط§ظ‹')}: {len(locked)} {ar('ظ…ظ‚ط±ط±')}[/bold yellow]"
    )
    console.print(Panel(summary_text, box=box.ROUNDED, border_style="green", title=f"ًں“ٹ {ar('ظ…ظ„ط®طµ ط§ظ„ط³ط¬ظ„ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ')}"))

    # ط¬ط¯ظˆظ„ ط§ظ„ظ…ظˆط§ط¯ ط§ظ„ظ…طھط§ط­ط©
    if available:
        render_courses_table(available, "ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„طھظٹ ظٹط­ظ‚ ظ„ظƒ ط§ظ„طھط³ط¬ظٹظ„ ظپظٹظ‡ط§ ط§ظ„ط¢ظ†")
    else:
        console.print(f"[yellow]{ar('ظ„ط§ طھظˆط¬ط¯ ظ…ظ‚ط±ط±ط§طھ ط¬ط¯ظٹط¯ط© ظ…طھط§ط­ط© ظ„ظ„طھط³ط¬ظٹظ„ ط­ط§ظ„ظٹط§ظ‹.')}[/yellow]")

    # ط¬ط¯ظˆظ„ ط§ظ„ظ…ظˆط§ط¯ ط§ظ„ظ…ط؛ظ„ظ‚ط© ظ…ط¹ ط³ط¨ط¨ ط§ظ„ظ‚ظپظ„
    if locked:
        locked_table = Table(
            title=f"[bold bright_yellow]{ar('ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…ط؛ظ„ظ‚ط© (طھطھط·ظ„ط¨ ظ…ظˆط§ط¯ ط³ط§ط¨ظ‚ط© ظ„ظ… طھط¬طھط²ظ‡ط§ ط¨ط¹ط¯)')}[/bold bright_yellow]",
            box=box.ROUNDED,
            border_style="yellow",
            header_style="bold red",
            expand=True,
        )
        locked_table.add_column(ar("ط§ظ„ط±ظ…ط²"), style="bold white", justify="center", width=10)
        locked_table.add_column(ar("ط§ط³ظ… ط§ظ„ظ…ط§ط¯ط©"), style="white", width=30)
        locked_table.add_column(ar("ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ظ…طھط¨ظ‚ظٹط© ط§ظ„ظ†ط§ظ‚طµط©"), style="bold red", width=35)
        locked_table.add_column(ar("ط§ظ„ط³ط§ط¹ط§طھ"), justify="center", style="magenta", width=8)

        for c in locked:
            missing_str = ", ".join(c.get("missing_prereqs", []))
            locked_table.add_row(
                c["course_id"],
                ar(c.get("course_name", "")),
                ar(f"ظٹظ†ظ‚طµظƒ ط§ط¬طھظٹط§ط²: {missing_str}"),
                str(c.get("credit_hours", "3")),
            )
        console.print(locked_table)

    pause()


def student_ir_search(ir_engine: IREngine):
    """
    ط§ظ„ط¨ط­ط« ط§ظ„ط¯ظ„ط§ظ„ظٹ ط§ظ„ط°ظƒظٹ ط§ظ„ظ…ط¨ط§ط´ط± ظپظٹ ظ„ظˆط§ط¦ط­ ظˆظ‚ظˆط§ظ†ظٹظ† ط§ظ„ظƒظ„ظٹط©.
    ظٹط³طھظ‚ط¨ظ„ ط§ط³طھظپط³ط§ط± ط§ظ„ط·ط§ظ„ط¨ ط¨ط­ط±ظٹط© ط¨ط§ظ„ظ„ط؛ط© ط§ظ„ط¹ط±ط¨ظٹط©طŒ ظˆظٹظ‚ظˆظ… ط¨طھط´ط¨ظٹظƒ ط§ظ„ط­ط±ظˆظپ ظ„ط­ط¸ظٹط§ظ‹
    ط£ط«ظ†ط§ط، ط§ظ„ظƒطھط§ط¨ط©طŒ ط«ظ… ظٹط·ط¨ظ‚ ط®ظˆط§ط±ط²ظ…ظٹط© TF-IDF ظˆظ…ظ‚ظٹط§ط³ Cosine Similarity ظ„طھط±طھظٹط¨ ط§ظ„ظ†طھط§ط¦ط¬.
    """
    while True:
        render_header("ظ…ط­ط±ظƒ ط§ظ„ط¨ط­ط« ط§ظ„ط°ظƒظٹ ظپظٹ ظ„ظˆط§ط¦ط­ ظˆظ‚ظˆط§ظ†ظٹظ† ط§ظ„ظƒظ„ظٹط© (IR Search Engine)")
        
        info_box = Panel(
            f"[bold bright_yellow]âڑ، {ar('ظ†ط¸ط§ظ… ط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ (Information Retrieval):')}[/bold bright_yellow]\n"
            f"â€¢ {ar('ط§ظƒطھط¨ ط§ط³طھظپط³ط§ط±ظƒ ط¨ط­ط±ظٹط© ط¨ط§ظ„ظ„ط؛ط© ط§ظ„ط¹ط±ط¨ظٹط© (ظ…ط«ط§ظ„: ط¹ظ‚ظˆط¨ط© ط§ظ„ط؛ظٹط§ط¨طŒ ط­ط³ط§ط¨ ط§ظ„ظ…ط¹ط¯ظ„طŒ ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط³ظ…ظˆط­ط©طŒ ط­ط±ظ…ط§ظ† ط§ظ„ط§ظ…طھط­ط§ظ†)')}\n"
            f"â€¢ {ar('ط³طھطھط´ط§ط¨ظƒ ط§ظ„ط­ط±ظˆظپ ط§ظ„ط¹ط±ط¨ظٹط© ظˆطھظ†طھط¸ظ… طھظ„ظ‚ط§ط¦ظٹط§ظ‹ ط£ظ…ط§ظ…ظƒ ط¹ظ„ظ‰ ط§ظ„ط´ط§ط´ط© ط£ط«ظ†ط§ط، ط§ظ„ظƒطھط§ط¨ط©')}\n"
            f"â€¢ [dim white]{ar('ط§ط¶ط؛ط· Enter ظ…ط¨ط§ط´ط±ط© ط¯ظˆظ† ظƒطھط§ط¨ط© ظ„ظ„ط¹ظˆط¯ط© ظ„ظ‚ط§ط¦ظ…ط© ط§ظ„ط·ط§ظ„ط¨')}[/dim white]",
            box=box.ROUNDED,
            border_style="bright_blue",
        )
        console.print(info_box)

        # ط§ط³طھظ‚ط¨ط§ظ„ ط§ظ„ط§ط³طھط¹ظ„ط§ظ… ظ…ط¨ط§ط´ط±ط© ط¨ط§ظ„ظƒطھط§ط¨ط© ط§ظ„ط­ط±ط© ظ…ط¹ طھط´ط¨ظٹظƒ ط§ظ„ط­ط±ظˆظپ ط§ظ„ظ„ط­ط¸ظٹ
        query = get_arabic_input(f"[ًں”چ] {ar('ط£ط¯ط®ظ„ ط§ط³طھظپط³ط§ط±ظƒ')} > ")

        # ط¥ط°ط§ ط¶ط؛ط· Enter ط¨ط¯ظˆظ† ظƒطھط§ط¨ط©طŒ ظٹط¹ظˆط¯ ظ„ظ„ظ‚ط§ط¦ظ…ط©
        if not query:
            break

        # طھط³ط¬ظٹظ„ ظˆطھظ†ظپظٹط° ط®ظˆط§ط±ط²ظ…ظٹط© ط§ظ„ط¨ط­ط« ط¨ظ€ TF-IDF ظˆ Cosine Similarity
        log_query("STUDENT_SEARCH", f"ط§ط³طھط¹ظ„ط§ظ… ط­ط±: {query}")
        results = ir_engine.search(query, top_n=3)

        if not results:
            console.print(f"\n[bold red]âœ– {ar('ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط£ظٹ طھط·ط§ط¨ظ‚ ظ…ط¹ ط§ط³طھظپط³ط§ط±ظƒ.')}[/bold red]")
            console.print(f"[dim white]{ar('ط¬ط±ط¨ طµظٹط§ط؛ط© ط£ط®ط±ظ‰ ظ…ط«ظ„: ط؛ظٹط§ط¨طŒ ظ…ط¹ط¯ظ„طŒ طھط³ط¬ظٹظ„طŒ ط³ط§ط¹ط§طھطŒ ظ…ط±ط´ط¯...')}[/dim white]")
        else:
            console.print(f"\n[bold bright_green]ًںژ¯ {ar('ظ†طھط§ط¦ط¬ ط§ظ„ط¨ط­ط« ط§ظ„ظ…ط·ط§ط¨ظ‚ط© ظ„ظ„ط§ط³طھط¹ظ„ط§ظ…:')} \"{ar(query)}\"[/bold bright_green]\n")
            
            for i, res in enumerate(results, 1):
                score_bar = "â–ˆ" * int(res["score"] / 10) + "â–‘" * (10 - int(res["score"] / 10))
                score_badge = f"[bold green]{res['score']}% {score_bar}[/bold green]"
                
                panel_content = (
                    f"[bold bright_yellow]ًں“„ {ar('ط§ظ„ظ…ظ„ظپ ط§ظ„ظ…طµط¯ط±')}:[/bold bright_yellow] [bold white]{res['file']}[/bold white]   "
                    f"[bold bright_yellow]ًں“ٹ {ar('ط¯ط±ط¬ط© ط§ظ„طھط´ط§ط¨ظ‡')}:[/bold bright_yellow] {score_badge}\n"
                    f"â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    f"[white]{ar(res['snippet'])}...[/white]"
                )
                console.print(Panel(panel_content, box=box.ROUNDED, border_style="cyan", title=f"[bold cyan]#{i}[/bold cyan]"))

        # ط®ظٹط§ط± ظپظˆط±ظٹ ظ„ظ„ط¨ط­ط« ظ…ط¬ط¯ط¯ط§ظ‹ ط£ظˆ ط§ظ„ط¹ظˆط¯ط©
        again = input(f"\n  [?] {ar('ط§ط¶ط؛ط· Enter ظ„ظ„ط¨ط­ط« ط¹ظ† ط´ظٹط، ط¢ط®ط± (ط£ظˆ ط§ظƒطھط¨ 0 ظ„ظ„ط¹ظˆط¯ط©)')}: ").strip()
        if again == "0":
            break




def student_view_full_docs():
    """ط§ط³طھط¹ط±ط§ط¶ ط§ظ„ظ„ظˆط§ط¦ط­ ط§ظ„ط¬ط§ظ…ط¹ظٹط© ط§ظ„ظ…ط¹طھظ…ط¯ط© ط¨ط§ظ„ظƒط§ظ…ظ„ ط¯ط§ط®ظ„ ظˆط§ط¬ظ‡ط© ط§ظ„ظ‚ط±ط§ط،ط©."""
    while True:
        render_header("ط§ط³طھط¹ط±ط§ط¶ ط§ظ„ظ„ظˆط§ط¦ط­ ظˆط§ظ„ط£ظ†ط¸ظ…ط© ط§ظ„ط¬ط§ظ…ط¹ظٹط© ط§ظ„ط±ط³ظ…ظٹط©")
        
        menu_text = (
            f"[bold cyan][1][/bold cyan] ًں“œ {ar('ظ„ط§ط¦ط­ط© ط§ظ„ط­ط¶ظˆط± ظˆط§ظ„ط؛ظٹط§ط¨ ظˆط§ظ„ط­ط±ظ…ط§ظ†')}\n"
            f"[bold cyan][2][/bold cyan] ًں“ٹ {ar('ظ†ط¸ط§ظ… ط§ظ„طھظ‚ط¯ظٹط±ط§طھ ظˆط­ط³ط§ط¨ ط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„طھط±ط§ظƒظ…ظٹ (GPA)')}\n"
            f"[bold cyan][3][/bold cyan] ًں“‹ {ar('ظ‚ظˆط§ط¹ط¯ ط§ظ„طھط³ط¬ظٹظ„ ظˆط§ظ„ط¥ط±ط´ط§ط¯ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ ظˆط§ظ„ط¹ط¨ط، ط§ظ„ط¯ط±ط§ط³ظٹ')}\n"
            f"[bold cyan][0][/bold cyan] â†©ï¸ڈ {ar('ط§ظ„ط¹ظˆط¯ط© ظ„ظ‚ط§ط¦ظ…ط© ط§ظ„ط·ط§ظ„ط¨')}"
        )
        console.print(Panel(menu_text, box=box.ROUNDED, border_style="bright_blue", title=f"ًں“– {ar('ط§ط®طھط± ط§ظ„ظ„ط§ط¦ط­ط© ط§ظ„ظ…ط·ظ„ظˆط¨ ظ‚ط±ط§ط،طھظ‡ط§')}"))

        try:
            choice = input(f"\n  [?] {ar('ط§ط®طھظٹط§ط±ظƒ')}: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        doc_map = {
            "1": ("ظ„ط§ط¦ط­ط© ط§ظ„ط­ط¶ظˆط± ظˆط§ظ„ط؛ظٹط§ط¨", ATTENDANCE_DOC),
            "2": ("ظ†ط¸ط§ظ… ط§ظ„طھظ‚ط¯ظٹط±ط§طھ ظˆط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„طھط±ط§ظƒظ…ظٹ", GPA_DOC),
            "3": ("ظ‚ظˆط§ط¹ط¯ ط§ظ„طھط³ط¬ظٹظ„ ظˆط§ظ„ط¥ط±ط´ط§ط¯ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ", REG_DOC),
        }

        if choice in doc_map:
            doc_title, doc_path = doc_map[choice]
            content = load_doc_file(doc_path)
            render_header(doc_title)
            console.print(Panel(ar(content), box=box.ROUNDED, border_style="bright_green", title=f"ًں“œ {ar(doc_title)}"))
            log_query("STUDENT_READ_DOC", f"ظ‚ط±ط§ط،ط©: {doc_title}")
            pause()
        elif choice == "0":
            break
        else:
            console.print(f"[red]{ar('ط§ط®طھظٹط§ط± ط؛ظٹط± طµط­ظٹط­.')}[/red]")
            pause()


def student_gpa_calculator():
    """ط­ط§ط³ط¨ط© ط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„ظپطµظ„ظٹ ظˆط§ظ„طھط±ط§ظƒظ…ظٹ ط­ط³ط¨ ظ†ط¸ط§ظ… ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط© ظپظٹ ط§ظ„ط¬ط§ظ…ط¹ط§طھ ط§ظ„ظ…طµط±ظٹط©."""
    render_header("ط­ط§ط³ط¨ط© ط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„طھط±ط§ظƒظ…ظٹ (GPA Calculator)")
    
    calc_intro = Panel(
        f"[bold bright_yellow]{ar('ظ…ظ‚ظٹط§ط³ ط§ظ„ظ†ظ‚ط§ط· ط§ظ„ظ…ط¹طھظ…ط¯ ظپظٹ ظƒظ„ظٹط© ط§ظ„ط°ظƒط§ط، ط§ظ„ط§طµط·ظ†ط§ط¹ظٹ:')}[/bold bright_yellow]\n"
        f"A+: 4.0 | A: 3.7 | B+: 3.3 | B: 3.0 | C+: 2.7 | C: 2.3 | D+: 2.0 | D: 1.7 | F: 0.0",
        box=box.ROUNDED,
        border_style="yellow",
    )
    console.print(calc_intro)

    grade_points = {
        "A+": 4.0, "A": 3.7, "B+": 3.3, "B": 3.0,
        "C+": 2.7, "C": 2.3, "D+": 2.0, "D": 1.7, "F": 0.0
    }

    try:
        count_str = input(f"\n  [?] {ar('ظƒظ… ط¹ط¯ط¯ ط§ظ„ظ…ظˆط§ط¯ ط§ظ„طھظٹ طھظˆط¯ ط­ط³ط§ط¨ ظ…ط¹ط¯ظ„ظ‡ط§طں')}: ").strip()
        if not count_str.isdigit() or int(count_str) <= 0:
            console.print(f"[red]{ar('ظٹط±ط¬ظ‰ ط¥ط¯ط®ط§ظ„ ط±ظ‚ظ… طµط­ظٹط­.')}[/red]")
            pause()
            return
        
        count = int(count_str)
        total_points = 0.0
        total_hours = 0
        details = []

        for i in range(1, count + 1):
            console.print(f"\n[bold cyan]â—€ {ar('ط§ظ„ظ…ط§ط¯ط© ط±ظ‚ظ…')} {i} â–¶[/bold cyan]")
            code = input(f"   {ar('ط±ظ…ط² ط£ظˆ ط§ط³ظ… ط§ظ„ظ…ط§ط¯ط© (ظ…ط«ط§ظ„: CS101)')}: ").strip() or f"Course_{i}"
            
            while True:
                grade = input(f"   {ar('ط§ظ„طھظ‚ط¯ظٹط± (A+, A, B+, B, C+, C, D+, D, F)')}: ").strip().upper()
                if grade in grade_points:
                    break
                console.print(f"   [red]{ar('طھظ‚ط¯ظٹط± ط؛ظٹط± طµط­ظٹط­طŒ ط§ط®طھط± ظ…ظ† ط§ظ„طھظ‚ط¯ظٹط±ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط©.')}[/red]")

            while True:
                hrs_str = input(f"   {ar('ط¹ط¯ط¯ ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط© (ط§ظ„ط§ظپطھط±ط§ط¶ظٹ 3)')}: ").strip() or "3"
                if hrs_str.isdigit() and int(hrs_str) > 0:
                    hrs = int(hrs_str)
                    break
                console.print(f"   [red]{ar('ظٹط±ط¬ظ‰ ط¥ط¯ط®ط§ظ„ ط¹ط¯ط¯ ط³ط§ط¹ط§طھ طµط­ظٹط­.')}[/red]")

            pts = grade_points[grade] * hrs
            total_points += pts
            total_hours += hrs
            details.append((code, grade, hrs, pts))

        # ط­ط³ط§ط¨ ظˆط¹ط±ط¶ ط§ظ„ظ†طھظٹط¬ط©
        final_gpa = total_points / total_hours if total_hours > 0 else 0.0

        if final_gpa >= 3.5:
            standing = "ظ…ظ…طھط§ط² ظ…ط±طھظپط¹ (ظ…ط±ط´ط­ ظ„ظ…ط±طھط¨ط© ط§ظ„ط´ط±ظپ)"
            standing_color = "bright_green"
        elif final_gpa >= 3.0:
            standing = "ط¬ظٹط¯ ط¬ط¯ط§ظ‹"
            standing_color = "green"
        elif final_gpa >= 2.5:
            standing = "ط¬ظٹط¯ ظ…ط±طھظپط¹"
            standing_color = "cyan"
        elif final_gpa >= 2.0:
            standing = "ظ…ظ‚ط¨ظˆظ„ (ظˆط¶ط¹ ط£ظƒط§ط¯ظٹظ…ظٹ ط³ظ„ظٹظ…)"
            standing_color = "yellow"
        else:
            standing = "ط¥ظ†ط°ط§ط± ط£ظƒط§ط¯ظٹظ…ظٹ (طھط­طھ ط§ظ„ظ…ظ„ط§ط­ط¸ط©)"
            standing_color = "bold red"

        result_panel = Panel(
            f"[bold white]{ar('ط¥ط¬ظ…ط§ظ„ظٹ ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط©')}:[/bold white] [bold cyan]{total_hours}[/bold cyan] {ar('ط³ط§ط¹ط©')}\n"
            f"[bold white]{ar('ظ…ط¬ظ…ظˆط¹ ط§ظ„ظ†ظ‚ط§ط· ط§ظ„ظ…ظƒطھط³ط¨ط©')}:[/bold white] [bold yellow]{round(total_points, 2)}[/bold yellow]\n"
            f"[bold white]{ar('ط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„ظ…ط­ط³ظˆط¨ (GPA)')}:[/bold white] [bold {standing_color}]{final_gpa:.2f} / 4.00[/bold {standing_color}]\n"
            f"[bold white]{ar('ط§ظ„ط­ط§ظ„ط© ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹط©')}:[/bold white] [{standing_color}]{ar(standing)}[/{standing_color}]",
            box=box.DOUBLE,
            border_style=standing_color,
            title=f"ًںژ¯ {ar('ظ†طھظٹط¬ط© ط­ط³ط§ط¨ ط§ظ„ظ…ط¹ط¯ظ„')}",
        )
        console.print(result_panel)
        log_query("STUDENT_GPA_CALC", f"ط­ط³ط§ط¨ ط§ظ„ظ…ط¹ط¯ظ„: {final_gpa:.2f} ظ„ط³ط§ط¹ط§طھ {total_hours}")

    except Exception as e:
        console.print(f"[red]{ar('ط­ط¯ط« ط®ط·ط£ ط£ط«ظ†ط§ط، ط§ظ„ط­ط³ط§ط¨')}: {e}[/red]")

    pause()


# =============================================================================
#  طµظپط­ط§طھ ظˆظ…ظٹط²ط§طھ ط¨ظˆط§ط¨ط© ط§ظ„ط¥ط¯ط§ط±ط© (Admin Portal)
# =============================================================================
def admin_add_course():
    """ط¥ط¶ط§ظپط© ظ…ظ‚ط±ط± ط¬ط¯ظٹط¯ ط¥ظ„ظ‰ ظ…ظ„ظپ courses.csv ظˆظ…ظ„ظپ prerequisites.json."""
    render_header("ط¥ط¶ط§ظپط© ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ ط¬ط¯ظٹط¯")
    courses = load_courses()
    prereqs = load_prerequisites()

    cid = input(f"\n  [?] {ar('ط±ظ…ط² ط§ظ„ظ…ظ‚ط±ط± (ظ…ط«ط§ظ„: CS205)')}: ").strip().upper()
    if not cid:
        console.print(f"[yellow]{ar('طھظ… ط¥ظ„ط؛ط§ط، ط§ظ„ط¥ط¶ط§ظپط©.')}[/yellow]")
        pause()
        return

    if any(c["course_id"].upper() == cid for c in courses):
        console.print(f"\n[bold red]âœ– {ar('ط§ظ„ظ…ظ‚ط±ط± ظ…ظˆط¬ظˆط¯ ط¨ط§ظ„ظپط¹ظ„ ظپظٹ ظ‚ط§ط¹ط¯ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ!')}[/bold red]")
        pause()
        return

    name = input(f"  [?] {ar('ط§ط³ظ… ط§ظ„ظ…ط§ط¯ط© ط¨ط§ظ„ط¹ط±ط¨ظٹط©')}: ").strip()
    inst = input(f"  [?] {ar('ط§ط³ظ… ط¹ط¶ظˆ ظ‡ظٹط¦ط© ط§ظ„طھط¯ط±ظٹط³ (ط§ظ„ظ…ط­ط§ط¶ط±)')}: ").strip()
    room = input(f"  [?] {ar('ط§ظ„ظ‚ط§ط¹ط© ط£ظˆ ط§ظ„ظ…ط¹ظ…ظ„')}: ").strip()
    hrs  = input(f"  [?] {ar('ط¹ط¯ط¯ ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط© (ط§ظ„ط§ظپطھط±ط§ط¶ظٹ 3)')}: ").strip() or "3"

    prereq_input = input(f"  [?] {ar('ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ط³ط§ط¨ظ‚ط© ظ…ظپطµظˆظ„ط© ط¨ظپط§طµظ„ط© (ط§طھط±ظƒظ‡ ظپط§ط±ط؛ط§ظ‹ ط¥ط°ط§ ظ„ظ… طھظˆط¬ط¯)')}: ").strip()
    prereq_list = [p.strip().upper() for p in prereq_input.split(",") if p.strip()]

    courses.append({
        "course_id": cid,
        "course_name": name,
        "instructor": inst,
        "room": room,
        "credit_hours": hrs,
    })
    save_courses(courses)

    prereqs[cid] = prereq_list
    save_prerequisites(prereqs)

    log_query("ADMIN_ADD_COURSE", f"ط¥ط¶ط§ظپط© ط§ظ„ظ…ط§ط¯ط© {cid} - {name} ظ…طھط·ظ„ط¨ط§طھ: {prereq_list}")
    console.print(f"\n[bold bright_green]âœ” {ar(f'طھظ…طھ ط¥ط¶ط§ظپط© ط§ظ„ظ…ظ‚ط±ط± {cid} ظˆطھط­ط¯ظٹط« ط´ط¬ط±ط© ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط¨ظ†ط¬ط§ط­.')}[/bold bright_green]")
    pause()


def admin_edit_course():
    """طھط¹ط¯ظٹظ„ ط¨ظٹط§ظ†ط§طھ ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ ظ‚ط§ط¦ظ…."""
    render_header("طھط¹ط¯ظٹظ„ ط¨ظٹط§ظ†ط§طھ ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ")
    courses = load_courses()
    render_courses_table(courses, "ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ط­ط§ظ„ظٹط© ط§ظ„ظ…ط³ط¬ظ„ط©")

    cid = input(f"\n  [?] {ar('ط£ط¯ط®ظ„ ط±ظ…ط² ط§ظ„ظ…ط§ط¯ط© ط§ظ„ظ…ط±ط§ط¯ طھط¹ط¯ظٹظ„ظ‡ط§')}: ").strip().upper()
    course = next((c for c in courses if c["course_id"].upper() == cid), None)

    if not course:
        console.print(f"\n[red]âœ– {ar(f'ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط§ظ„ظ…ظ‚ط±ط± {cid}')}[/red]")
        pause()
        return

    console.print(Panel(
        f"[bold cyan]{ar('ط§ظ„ظ‚ظٹظ… ط§ظ„ط­ط§ظ„ظٹط©')} (ط§ط¶ط؛ط· Enter ظ„ظ„ط¥ط¨ظ‚ط§ط، ط¹ظ„ظ‰ ظ†ظپط³ ط§ظ„ظ‚ظٹظ…ط© ط¯ظˆظ† طھط؛ظٹظٹط±):[/bold cyan]\n"
        f"â€¢ {ar('ط§ظ„ط§ط³ظ…')}: {course.get('course_name')}\n"
        f"â€¢ {ar('ط§ظ„ظ…ط­ط§ط¶ط±')}: {course.get('instructor')}\n"
        f"â€¢ {ar('ط§ظ„ظ‚ط§ط¹ط©')}: {course.get('room')}\n"
        f"â€¢ {ar('ط§ظ„ط³ط§ط¹ط§طھ')}: {course.get('credit_hours')}",
        box=box.ROUNDED,
        border_style="yellow",
    ))

    new_name = input(f"  [?] {ar('ط§ط³ظ… ط§ظ„ظ…ط§ط¯ط© ط§ظ„ط¬ط¯ظٹط¯')}: ").strip()
    new_inst = input(f"  [?] {ar('ط§ط³ظ… ط§ظ„ظ…ط­ط§ط¶ط± ط§ظ„ط¬ط¯ظٹط¯')}: ").strip()
    new_room = input(f"  [?] {ar('ط§ظ„ظ‚ط§ط¹ط© ط§ظ„ط¬ط¯ظٹط¯ط©')}: ").strip()
    new_hrs  = input(f"  [?] {ar('ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط¹طھظ…ط¯ط© ط§ظ„ط¬ط¯ظٹط¯ط©')}: ").strip()

    if new_name: course["course_name"] = new_name
    if new_inst: course["instructor"] = new_inst
    if new_room: course["room"] = new_room
    if new_hrs:  course["credit_hours"] = new_hrs

    save_courses(courses)
    log_query("ADMIN_EDIT_COURSE", f"طھط¹ط¯ظٹظ„ ط§ظ„ظ…ط§ط¯ط©: {cid}")
    console.print(f"\n[bold green]âœ” {ar(f'طھظ… ط­ظپط¸ ط§ظ„طھط¹ط¯ظٹظ„ط§طھ ط¹ظ„ظ‰ ط§ظ„ظ…ظ‚ط±ط± {cid} ط¨ظ†ط¬ط§ط­.')}[/bold green]")
    pause()


def admin_delete_course():
    """ط­ط°ظپ ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ ظ…ظ† ظ…ظ„ظپ CSV ظˆط´ط¬ط±ط© ط§ظ„ظ…طھط·ظ„ط¨ط§طھ."""
    render_header("ط­ط°ظپ ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ")
    courses = load_courses()
    render_courses_table(courses, "ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…ط³ط¬ظ„ط©")

    cid = input(f"\n  [?] {ar('ط£ط¯ط®ظ„ ط±ظ…ط² ط§ظ„ظ…ط§ط¯ط© ط§ظ„ظ…ط±ط§ط¯ ط­ط°ظپظ‡ط§ ظ†ظ‡ط§ط¦ظٹط§ظ‹')}: ").strip().upper()
    course = next((c for c in courses if c["course_id"].upper() == cid), None)

    if not course:
        console.print(f"\n[red]âœ– {ar(f'ط§ظ„ظ…ظ‚ط±ط± {cid} ط؛ظٹط± ظ…ظˆط¬ظˆط¯.')}[/red]")
        pause()
        return

    confirm = input(f"  [âڑ ï¸ڈ] {ar(f'ظ‡ظ„ ط£ظ†طھ ظ…طھط£ظƒط¯ ظ…ظ† ط­ط°ظپ ط§ظ„ظ…ظ‚ط±ط± {cid} ظ†ظ‡ط§ط¦ظٹط§ظ‹طں (y/n)')}: ").strip().lower()
    if confirm == "y":
        courses = [c for c in courses if c["course_id"].upper() != cid]
        save_courses(courses)

        prereqs = load_prerequisites()
        if cid in prereqs:
            del prereqs[cid]
        # ط¥ط²ط§ظ„ط© ظ‡ط°ط§ ط§ظ„ظ…ظ‚ط±ط± ظ…ظ† ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ظ…ظˆط§ط¯ ط§ظ„ط£ط®ط±ظ‰
        for k, v in prereqs.items():
            if cid in v:
                v.remove(cid)
        save_prerequisites(prereqs)

        log_query("ADMIN_DELETE_COURSE", f"ط­ط°ظپ ط§ظ„ظ…ط§ط¯ط©: {cid}")
        console.print(f"\n[bold green]âœ” {ar(f'طھظ… ط­ط°ظپ ط§ظ„ظ…ظ‚ط±ط± {cid} ط¨ظ†ط¬ط§ط­.')}[/bold green]")
    else:
        console.print(f"[yellow]{ar('طھظ… ط¥ظ„ط؛ط§ط، ط¹ظ…ظ„ظٹط© ط§ظ„ط­ط°ظپ.')}[/yellow]")
    
    pause()


def admin_add_document(ir_engine: IREngine):
    """ط¥ط¶ط§ظپط© ظˆط«ظٹظ‚ط©/ظ„ط§ط¦ط­ط© ط¬ط¯ظٹط¯ط© ظˆط¥ط¹ط§ط¯ط© ط¨ظ†ط§ط، ظپظ‡ط±ط³ ط§ظ„ط¨ط­ط« طھظ„ظ‚ط§ط¦ظٹط§ظ‹."""
    render_header("ط¥ط¶ط§ظپط© ظ„ط§ط¦ط­ط© ط£ظˆ ظ…ط³طھظ†ط¯ ط¬ط§ظ…ط¹ظٹ ط¬ط¯ظٹط¯")

    fname = input(f"\n  [?] {ar('ط§ط³ظ… ط§ظ„ظ…ظ„ظپ ط§ظ„ط¥ظ†ط¬ظ„ظٹط²ظٹ (ظ…ط«ط§ظ„: examination_rules.txt)')}: ").strip()
    if not fname:
        console.print(f"[yellow]{ar('طھظ… ط§ظ„ط¥ظ„ط؛ط§ط،.')}[/yellow]")
        pause()
        return

    if not fname.endswith(".txt"):
        fname += ".txt"

    console.print(f"\n[bold cyan]{ar('ط£ط¯ط®ظ„ ظ†طµ ط§ظ„ظ„ط§ط¦ط­ط©/ط§ظ„ظ…ط³طھظ†ط¯ (ط§ظƒطھط¨ ظƒظ„ظ…ط© END ظپظٹ ط³ط·ط± ظ…ط³طھظ‚ظ„ ط¹ظ†ط¯ ط§ظ„ط§ظ†طھظ‡ط§ط،):')}[/bold cyan]")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break

    content = "\n".join(lines).strip()
    if not content:
        console.print(f"[yellow]{ar('ظ„ظ… ظٹطھظ… ط¥ط¯ط®ط§ظ„ ظ†طµطŒ طھظ… ط§ظ„ط¥ظ„ط؛ط§ط،.')}[/yellow]")
        pause()
        return

    fpath = os.path.join(DOCS_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

    # ط¥ط¹ط§ط¯ط© ط¨ظ†ط§ط، ظپظ‡ط±ط³ TF-IDF
    ir_engine.build()
    log_query("ADMIN_ADD_DOC", f"ط¥ط¶ط§ظپط© ط§ظ„ظ…ط³طھظ†ط¯: {fname}")
    console.print(f"\n[bold green]âœ” {ar(f'طھظ… ط­ظپط¸ ط§ظ„ظ…ط³طھظ†ط¯ {fname} ظˆط¥ط¹ط§ط¯ط© ط¨ظ†ط§ط، ظپظ‡ط±ط³ ط§ظ„ط¨ط­ط« ط§ظ„ظ†طµظٹ ط¨ظ†ط¬ط§ط­.')}[/bold green]")
    pause()


def admin_view_logs():
    """ط§ط³طھط¹ط±ط§ط¶ ط³ط¬ظ„ ط§ظ„ط¹ظ…ظ„ظٹط§طھ ظˆط§ظ„ط¨ط­ط« queries.log ط¨طھظ†ط³ظٹظ‚ ط¬ط¯ظˆظ„ ظ…ظ„ظˆظ†."""
    render_header("ط³ط¬ظ„ ط§ظ„ط§ط³طھظپط³ط§ط±ط§طھ ظˆط§ظ„ط¹ظ…ظ„ظٹط§طھ (queries.log)")

    if not os.path.exists(LOG_FILE):
        console.print(f"[yellow]{ar('ظ…ظ„ظپ ط§ظ„ط³ط¬ظ„ ظپط§ط±ط؛ ط­ط§ظ„ظٹط§ظ‹.')}[/yellow]")
        pause()
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        console.print(f"[yellow]{ar('ظ„ط§ طھظˆط¬ط¯ ط³ط¬ظ„ط§طھ ظ„ط¹ط±ط¶ظ‡ط§.')}[/yellow]")
        pause()
        return

    recent_lines = lines[-25:]  # ط¹ط±ط¶ ط¢ط®ط± 25 ط¹ظ…ظ„ظٹط©
    table = Table(
        title=f"[bold bright_cyan]{ar(f'ط¢ط®ط± {len(recent_lines)} ط¹ظ…ظ„ظٹط© ظ…ط³ط¬ظ„ط© ظپظٹ ط§ظ„ظ†ط¸ط§ظ…')}[/bold bright_cyan]",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold yellow",
        expand=True,
    )
    table.add_column(ar("ط§ظ„طھط§ط±ظٹط® ظˆط§ظ„ظˆظ‚طھ"), style="cyan", width=20)
    table.add_column(ar("ط§ظ„ظ…ط³طھظˆظ‰"), justify="center", style="green", width=8)
    table.add_column(ar("ظ†ظˆط¹ ط§ظ„ط¹ظ…ظ„ظٹط© ظˆط§ظ„طھظپط§طµظٹظ„"), style="white")

    for line in recent_lines:
        parts = line.split(" | ")
        if len(parts) >= 3:
            time_str = parts[0]
            lvl = parts[1]
            msg = " | ".join(parts[2:])
            table.add_row(time_str, lvl, ar(msg))
        else:
            table.add_row("-", "LOG", ar(line))

    console.print(table)
    pause()


def admin_reset_data(ir_engine: IREngine):
    """ط¥ط¹ط§ط¯ط© طھظ‡ظٹط¦ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ ط§ظ„ط§ظپطھط±ط§ط¶ظٹط© ظ„ظ„ظƒظ„ظٹط©."""
    render_header("ط¥ط¹ط§ط¯ط© ط¶ط¨ط· ط§ظ„ط¨ظٹط§ظ†ط§طھ ط§ظ„ط§ظپطھط±ط§ط¶ظٹط©")
    console.print(f"[bold red]âڑ ï¸ڈ  {ar('طھط­ط°ظٹط±: ط³ظٹطھظ… ط­ط°ظپ ط§ظ„طھط¹ط¯ظٹظ„ط§طھ ط§ظ„ط­ط§ظ„ظٹط© ظˆط§ط³طھط¹ط§ط¯ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ ط§ظ„ظ†ظ…ظˆط°ط¬ظٹط© ط§ظ„ط£ظˆظ„ظٹط© ظ„ظ„ظƒظ„ظٹط©!')}[/bold red]")
    
    confirm = input(f"\n  [?] {ar('ظ‡ظ„ ط£ظ†طھ ظ…طھط£ظƒط¯طں ط§ظƒطھط¨ YES ظ„ظ„طھط£ظƒظٹط¯')}: ").strip()
    if confirm == "YES":
        for file in [COURSES_FILE, PREREQ_FILE, ATTENDANCE_DOC, GPA_DOC, REG_DOC]:
            if os.path.exists(file):
                os.remove(file)
        initialize_data()
        ir_engine.build()
        log_query("ADMIN_RESET_DATA", "ط§ط³طھط¹ط§ط¯ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ ط§ظ„ط§ظپطھط±ط§ط¶ظٹط© ظ„ظ„ظ…ط´ط±ظˆط¹")
        console.print(f"\n[bold green]âœ” {ar('طھظ…طھ ط§ط³طھط¹ط§ط¯ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ ط§ظ„ط§ظپطھط±ط§ط¶ظٹط© ظˆط¥ط¹ط§ط¯ط© ط¨ظ†ط§ط، ط§ظ„ظپظ‡ط§ط±ط³ ط¨ظ†ط¬ط§ط­.')}[/bold green]")
    else:
        console.print(f"[yellow]{ar('طھظ… ط¥ظ„ط؛ط§ط، ط¹ظ…ظ„ظٹط© ط¥ط¹ط§ط¯ط© ط§ظ„ط¶ط¨ط·.')}[/yellow]")
    
    pause()


# =============================================================================
#  ط§ظ„ظ‚ظˆط§ط¦ظ… ط§ظ„طھظپط§ط¹ظ„ظٹط© ط§ظ„ط±ط¦ظٹط³ظٹط© (Navigation Menus)
# =============================================================================
def student_menu(ir_engine: IREngine):
    """ظ‚ط§ط¦ظ…ط© ط¨ظˆط§ط¨ط© ط§ظ„ط·ط§ظ„ط¨ ط§ظ„طھظپط§ط¹ظ„ظٹط©."""
    while True:
        render_header("ط¨ظˆط§ط¨ط© ط§ظ„ط·ط§ظ„ط¨ - Student Portal")
        render_dashboard_bar(ir_engine)

        menu_card = (
            f"[bold bright_cyan][1][/bold bright_cyan]  ًں“‹  {ar('ط¯ظ„ظٹظ„ ظˆطھظپط§طµظٹظ„ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ط¯ط±ط§ط³ظٹط©')}\n"
            f"[bold bright_cyan][2][/bold bright_cyan]  ًںژ¯  {ar('ظ…ط­ط±ظƒ ط§ظ„ط§ط³طھظ†طھط§ط¬ ط§ظ„ط°ظƒظٹ: ظپط­طµ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…طھط§ط­ط© ظ„ظ„طھط³ط¬ظٹظ„')}\n"
            f"[bold bright_cyan][3][/bold bright_cyan]  ًں”چ  {ar('ط§ظ„ط¨ط­ط« ط§ظ„ط°ظƒظٹ ظپظٹ ظ„ظˆط§ط¦ط­ ظˆظ†طµظˆطµ ط§ظ„ظƒظ„ظٹط© (TF-IDF & Cosine)')}\n"
            f"[bold bright_cyan][4][/bold bright_cyan]  ًں“–  {ar('ظ‚ط±ط§ط،ط© ظˆط§ط³طھط¹ط±ط§ط¶ ط§ظ„ظ„ظˆط§ط¦ط­ ط§ظ„ط¬ط§ظ…ط¹ظٹط© ط§ظ„ظ…ط¹طھظ…ط¯ط© ط¨ط§ظ„ظƒط§ظ…ظ„')}\n"
            f"[bold bright_cyan][5][/bold bright_cyan]  ًں§®  {ar('ط­ط§ط³ط¨ط© ط§ظ„ظ…ط¹ط¯ظ„ ط§ظ„طھط±ط§ظƒظ…ظٹ ظˆط§ظ„ظپطµظ„ظٹ ط§ظ„طھظپط§ط¹ظ„ظٹط© (GPA Calculator)')}\n"
            f"â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"[bold bright_red][0][/bold bright_red]  â†©ï¸ڈ  {ar('ط§ظ„ط¹ظˆط¯ط© ط¥ظ„ظ‰ ط§ظ„ظ‚ط§ط¦ظ…ط© ط§ظ„ط±ط¦ظٹط³ظٹط©')}"
        )
        console.print(Panel(menu_card, box=box.ROUNDED, border_style="cyan", title=f"ًںژ“ {ar('ط§ظ„ط®ط¯ظ…ط§طھ ط§ظ„ط·ظ„ط§ط¨ظٹط© ط§ظ„ظ…طھط§ط­ط©')}"))

        try:
            choice = input(f"\n  [?] {ar('ط§ط®طھط± ط±ظ‚ظ… ط§ظ„ط®ط¯ظ…ط©')}: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "1":
            student_course_catalog()
        elif choice == "2":
            student_advisor_check()
        elif choice == "3":
            student_ir_search(ir_engine)
        elif choice == "4":
            student_view_full_docs()
        elif choice == "5":
            student_gpa_calculator()
        elif choice == "0":
            break
        else:
            console.print(f"[red]{ar('ط§ط®طھظٹط§ط± ط؛ظٹط± طµط­ظٹط­طŒ ط§ظ„ط±ط¬ط§ط، ط§ط®طھظٹط§ط± ط±ظ‚ظ… ظ…ظ† ط§ظ„ظ‚ط§ط¦ظ…ط©.')}[/red]")
            pause()


def admin_menu(ir_engine: IREngine):
    """ظ‚ط§ط¦ظ…ط© ظ„ظˆط­ط© طھط­ظƒظ… ط§ظ„ظ…ط³ط¤ظˆظ„ ط§ظ„طھظپط§ط¹ظ„ظٹط©."""
    while True:
        render_header("ظ„ظˆط­ط© طھط­ظƒظ… ط¥ط¯ط§ط±ط© ط§ظ„ظ†ط¸ط§ظ… - Admin Portal")
        render_dashboard_bar(ir_engine)

        menu_card = (
            f"[bold bright_yellow][1][/bold bright_yellow]  ًں“‹  {ar('ط§ط³طھط¹ط±ط§ط¶ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ط­ط§ظ„ظٹط© ظˆط§ظ„ط´ط¬ط±ط© ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹط©')}\n"
            f"[bold bright_yellow][2][/bold bright_yellow]  â‍•  {ar('ط¥ط¶ط§ظپط© ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ ط¬ط¯ظٹط¯ ظˆظ‚ط§ط¹طھظ‡ ظˆظ…طھط·ظ„ط¨ط§طھظ‡')}\n"
            f"[bold bright_yellow][3][/bold bright_yellow]  âœڈï¸ڈ   {ar('طھط¹ط¯ظٹظ„ ط¨ظٹط§ظ†ط§طھ ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ ظ‚ط§ط¦ظ…')}\n"
            f"[bold bright_yellow][4][/bold bright_yellow]  ًں—‘ï¸ڈ   {ar('ط­ط°ظپ ظ…ظ‚ط±ط± ط¯ط±ط§ط³ظٹ ظ…ظ† ط§ظ„ط®ط·ط©')}\n"
            f"[bold bright_yellow][5][/bold bright_yellow]  ًں“„  {ar('ط¥ط¶ط§ظپط© ظ„ط§ط¦ط­ط© / ظˆط«ظٹظ‚ط© ط¬ط¯ظٹط¯ط© (ظˆط¥ط¹ط§ط¯ط© ط¨ظ†ط§ط، ط§ظ„ظپظ‡ط±ط³ طھظ„ظ‚ط§ط¦ظٹط§ظ‹)')}\n"
            f"[bold bright_yellow][6][/bold bright_yellow]  ًں“œ  {ar('ط§ط³طھط¹ط±ط§ط¶ ط³ط¬ظ„ ط§ط³طھظپط³ط§ط±ط§طھ ظˆط¹ظ…ظ„ظٹط§طھ ط§ظ„ط·ظ„ط§ط¨ (Live Log)')}\n"
            f"[bold bright_yellow][7][/bold bright_yellow]  ًں”„  {ar('ط§ط³طھط¹ط§ط¯ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ ط§ظ„ظ†ظ…ظˆط°ط¬ظٹط© ط§ظ„ط§ظپطھط±ط§ط¶ظٹط© ظ„ظ„ظƒظ„ظٹط©')}\n"
            f"â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"[bold bright_red][0][/bold bright_red]  â†©ï¸ڈ  {ar('طھط³ط¬ظٹظ„ ط§ظ„ط®ط±ظˆط¬ ظˆط§ظ„ط¹ظˆط¯ط© ظ„ظ„ظ‚ط§ط¦ظ…ط© ط§ظ„ط±ط¦ظٹط³ظٹط©')}"
        )
        console.print(Panel(menu_card, box=box.ROUNDED, border_style="bright_yellow", title=f"ًں›،ï¸ڈ {ar('طµظ„ط§ط­ظٹط§طھ ط§ظ„ظ…ط³ط¤ظˆظ„ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ')}"))

        choice = input(f"\n  [?] {ar('ط§ط®طھط± ط±ظ‚ظ… ط§ظ„ط¥ط¬ط±ط§ط،')}: ").strip()

        if choice == "1":
            render_header("ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ظ…ط³ط¬ظ„ط©")
            render_courses_table(load_courses(), "ط§ظ„ظ…ظ‚ط±ط±ط§طھ ط§ظ„ط­ط§ظ„ظٹط© ظپظٹ ط§ظ„ط®ط·ط©")
            pause()
        elif choice == "2":
            admin_add_course()
        elif choice == "3":
            admin_edit_course()
        elif choice == "4":
            admin_delete_course()
        elif choice == "5":
            admin_add_document(ir_engine)
        elif choice == "6":
            admin_view_logs()
        elif choice == "7":
            admin_reset_data(ir_engine)
        elif choice == "0":
            break
        else:
            console.print(f"[red]{ar('ط§ط®طھظٹط§ط± ط؛ظٹط± طµط­ظٹط­طŒ ط§ظ„ط±ط¬ط§ط، ط§ط®طھظٹط§ط± ط±ظ‚ظ… ظ…ظ† ط§ظ„ظ‚ط§ط¦ظ…ط©.')}[/red]")
            pause()


def show_about():
    """ط¹ط±ط¶ ظ…ط¹ظ„ظˆظ…ط§طھ ط¹ظ† ط§ظ„ظ…ط´ط±ظˆط¹ ظˆط§ظ„ظ…ط¹ط§ظٹظٹط± ط§ظ„ط¨ط±ظ…ط¬ظٹط© ط§ظ„ظ…ظ†ظپط°ط©."""
    render_header("ط­ظˆظ„ ظ…ط´ط±ظˆط¹ ط¯ظ„ظٹظ„ ط§ظ„ط·ط§ظ„ط¨ ط§ظ„ط°ظƒظٹ")
    about_text = (
        f"[bold bright_yellow]Smart Student Guide (ط¯ظ„ظٹظ„ ط§ظ„ط·ط§ظ„ط¨ ط§ظ„ط°ظƒظٹ)[/bold bright_yellow]\n"
        f"[dim white]ظ…ط´ط±ظˆط¹ ط¬ط§ظ…ط¹ظٹ ظ…طھظƒط§ظ…ظ„ ظ„ظƒظ„ظٹط© ط§ظ„ط­ط§ط³ط¨ط§طھ ظˆط§ظ„ط°ظƒط§ط، ط§ظ„ط§طµط·ظ†ط§ط¹ظٹ[/dim white]\n\n"
        f"[bold bright_cyan]ط§ظ„ظ…ط­ط§ظˆط± ظˆط§ظ„طھظ‚ظ†ظٹط§طھ ط§ظ„ط¨ط±ظ…ط¬ظٹط© ط§ظ„ظ…ط·ط¨ظ‚ط©:[/bold bright_cyan]\n"
        f"1. [green]ط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ (Information Retrieval):[/green] ط¨ظ†ط§ط، Inverted Index ظˆطھط·ط¨ظٹظ‚ ط®ظˆط§ط±ط²ظ…ظٹط© TF-IDF ظˆظ…ظ‚ظٹط§ط³ Cosine Similarity.\n"
        f"2. [green]طھظ…ط«ظٹظ„ ط§ظ„ظ…ط¹ط±ظپط© ظˆظ…ط­ط±ظƒ ط§ظ„ط§ط³طھظ†طھط§ط¬ (Inference Engine):[/green] ط´ط¬ط±ط© ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ط³ط§ط¨ظ‚ط© (Prerequisites DAG) ظˆطھط­ط¯ظٹط¯ ط£ظ‡ظ„ظٹط§طھ ط§ظ„طھط³ط¬ظٹظ„.\n"
        f"3. [green]ط¥ط¯ط§ط±ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ ظˆط§ظ„ظ…ظ„ظپط§طھ (File Handling):[/green] ظ‚ط±ط§ط،ط© ظˆطھط¹ط¯ظٹظ„ ظ…ظ„ظپط§طھ CSV ظˆ JSON ظˆ TXT ظˆط³ط¬ظ„ ط§ظ„ط£ط­ط¯ط§ط« queries.log.\n"
        f"4. [green]ظˆط§ط¬ظ‡ط© ظ…ط³طھط®ط¯ظ… ط§ط­طھط±ط§ظپظٹط© (Premium CLI):[/green] ط¯ط¹ظ… ط§ظ„ط®ط· ط§ظ„ط¹ط±ط¨ظٹطŒ ط¨ط·ط§ظ‚ط§طھ طھظپط§ط¹ظ„ظٹط©طŒ ظˆط¬ط¯ط§ظˆظ„ ظ…ظ„ظˆظ†ط© ط¨ط§ط³طھط®ط¯ط§ظ… ظ…ظƒطھط¨ط© Rich."
    )
    console.print(Panel(ar(about_text), box=box.ROUNDED, border_style="bright_blue", title=f"â„¹ï¸ڈ {ar('ط¨ط·ط§ظ‚ط© ط§ظ„ظ…ط´ط±ظˆط¹')}"))
    pause()


def show_developers():
    """ط¹ط±ط¶ ظ‚ط§ط¦ظ…ط© ط§ظ„ظ…ط·ظˆط±ظٹظ† ط§ظ„ظ‚ط§ط¦ظ…ظٹظ† ط¹ظ„ظ‰ ط§ظ„ظ…ط´ط±ظˆط¹ ظˆط±ظˆط§ط¨ط· LinkedIn ط§ظ„ظ…ط®طµطµط© ظپظٹ ط¨ط·ط§ظ‚ط§طھ ظ…ط³طھظ‚ظ„ط©."""
    render_header("ظپط±ظٹظ‚ ط§ظ„ظ…ط·ظˆط±ظٹظ† ظˆط§ظ„ظ‚ط§ط¦ظ…ظٹظ† ط¹ظ„ظ‰ ط§ظ„ظ…ط´ط±ظˆط¹ â€” Smart Student Guide Team")
    
    devs = [
        {
            "name": "ط³ط§ظ…ظٹ ظ…ط­ظ…ط¯ ظƒط§ط³ط¨ (Sami Mohamed Kassap)",
            "id": "25181309",
            "role": "ظ‚ط§ط¦ط¯ ط§ظ„ظ…ط´ط±ظˆط¹ ظˆظ…ط·ظˆط± ط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ (Project Lead & IR Engineer)",
            "linkedin": "https://www.linkedin.com/in/samy-kassap-25181309",
            "tasks": "ط¨ظ†ط§ط، ط§ظ„ظپظ‡ط±ط³ ط§ظ„ظ…ط¹ظƒظˆط³ ظˆظ…ط­ط±ظƒ ط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ (TF-IDF & Cosine Similarity) ظˆظ‡ظ†ط¯ط³ط© ط§ظ„ظ†ط¸ظ…"
        },
        {
            "name": "ظ…ط·ظˆط± ظˆط§ط¬ظ‡ط§طھ ط§ظ„ظ…ط³طھط®ط¯ظ… ظˆط§ظ„طھظپط§ط¹ظ„ (Frontend & UI/UX Developer)",
            "id": "25181310",
            "role": "ظ…ظ‡ظ†ط¯ط³ ظˆط§ط¬ظ‡ط§طھ ط§ظ„ظˆظٹط¨ ظˆطھط¬ط±ط¨ط© ط§ظ„ط§ط³طھط®ط¯ط§ظ… ط§ظ„طھظپط§ط¹ظ„ظٹط©",
            "linkedin": "https://www.linkedin.com",
            "tasks": "طھطµظ…ظٹظ… ظˆطھط·ظˆظٹط± ط§ظ„ظˆط§ط¬ظ‡ط§طھ ط§ظ„طھظپط§ط¹ظ„ظٹط© ط§ظ„ظƒط§ظ…ظ„ط© ط¨ط¯ط¹ظ… ظ…طھظƒط§ظ…ظ„ ظ„ظ„ط؛ط© ط§ظ„ط¹ط±ط¨ظٹط© ظˆطھط¬ط±ط¨ط© ط§ظ„ظ…ط³طھط®ط¯ظ… ط§ظ„ط­ط¯ظٹط«ط©"
        },
        {
            "name": "ظ…ظ‡ظ†ط¯ط³ طھظ…ط«ظٹظ„ ط§ظ„ظ…ط¹ط±ظپط© ظˆظ‚ظˆط§ط¹ط¯ ط§ظ„ط¨ظٹط§ظ†ط§طھ (Knowledge Base & Data Engineer)",
            "id": "25181311",
            "role": "ظ‡ظ†ط¯ط³ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ ظˆظ‚ظˆط§ط¹ط¯ ط§ظ„ظ„ظˆط§ط¦ط­ ظˆط§ظ„ط£ظ†ط¸ظ…ط© ط§ظ„ط¬ط§ظ…ط¹ظٹط©",
            "linkedin": "https://www.linkedin.com",
            "tasks": "ظ‡ظٹظƒظ„ط© ظ„ظˆط§ط¦ط­ ط§ظ„ظƒظ„ظٹط© ظˆط¨ظ†ظƒ ط§ظ„ظ‚ظˆط§ظ†ظٹظ† ظˆط§ظ„ظ„ظˆط§ط¦ط­ ظˆط³ط¬ظ„ ط§ظ„ط¹ظ…ظ„ظٹط§طھ queries.log ظˆظ…ظ„ظپط§طھ CSV/JSON"
        },
        {
            "name": "ظ…ظ‡ظ†ط¯ط³ ط§ظ„ط§ط³طھظ†طھط§ط¬ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ ظˆط§ظ„ط°ظƒط§ط، ط§ظ„ط§طµط·ظ†ط§ط¹ظٹ (AI & Inference Engineer)",
            "id": "25181312",
            "role": "طھط·ظˆظٹط± ظ…ط­ط±ظƒ ط§ظ„ط§ط³طھظ†طھط§ط¬ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ ظˆط§ظ„ظ…ط³ط§ط±ط§طھ ط§ظ„ظ…ظ‡ظ†ظٹط©",
            "linkedin": "https://www.linkedin.com",
            "tasks": "ط¨ظ†ط§ط، ط´ط¬ط±ط© ط§ظ„ظ…طھط·ظ„ط¨ط§طھ ط§ظ„ط³ط§ط¨ظ‚ط© (Prerequisites DAG) ظˆظ…ط­ط±ظƒ ظپط­طµ ط§ظ„ط£ظ‡ظ„ظٹط© ظˆط§ظ„طھظˆطµظٹط§طھ"
        }
    ]

    for d in devs:
        dev_info = (
            f"[bold bright_cyan]ًں‘¤ {ar(d['name'])}[/bold bright_cyan]\n"
            f"[dim white]ًں†” {ar('ط§ظ„ظƒظˆط¯ ط§ظ„ط¬ط§ظ…ط¹ظٹ')}: {d['id']}[/dim white]\n"
            f"[bright_yellow]ًں’¼ {ar(d['role'])}[/bright_yellow]\n"
            f"[dim white]ًں“Œ {ar('ط§ظ„ظ…ظ‡ط§ظ… ظˆط§ظ„ظ…ط³ط¤ظˆظ„ظٹط§طھ')}: {ar(d['tasks'])}[/dim white]\n"
            f"â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"[bold #0a66c2]ًں”— ط±ط§ط¨ط· LinkedIn ظ…ط®طµطµ:[/bold #0a66c2] [underline #38bdf8]{d['linkedin']}[/underline #38bdf8]"
        )
        console.print(Panel(dev_info, box=box.ROUNDED, border_style="blue", title=f"ًںŒں {ar('ط¨ط·ط§ظ‚ط© ظ…ط·ظˆط±')}"))
    
    pause()


# =============================================================================
#  ظ†ظ‚ط·ط© ط§ظ„ط¯ط®ظˆظ„ ط§ظ„ط±ط¦ظٹط³ظٹط© ظ„ظ„طھط·ط¨ظٹظ‚
# =============================================================================
def main():
    """ط§ظ„ط¯ط§ظ„ط© ط§ظ„ط±ط¦ظٹط³ظٹط© ظ„طھط´ط؛ظٹظ„ ط§ظ„طھط·ط¨ظٹظ‚."""
    # 1. طھظ‡ظٹط¦ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ ط§ظ„طھظ„ظ‚ط§ط¦ظٹط©
    initialize_data()

    # 2. ط¨ظ†ط§ط، ظ…ط­ط±ظƒ ط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ط¹ظ„ظˆظ…ط§طھ ظˆط§ظ„ظپظ‡ط±ط³
    ir_engine = IREngine()

    # 3. طھط³ط¬ظٹظ„ ط¨ط¯ط، ط§ظ„ط¬ظ„ط³ط©
    log_query("SESSION_START", "طھط´ط؛ظٹظ„ ط§ظ„طھط·ط¨ظٹظ‚ ظˆطھظ‡ظٹط¦ط© ط§ظ„ظˆط§ط¬ظ‡ط© ط¨ظ†ط¬ط§ط­")

    while True:
        render_header()
        render_dashboard_bar(ir_engine)

        welcome_card = (
            f"[bold bright_cyan][1][/bold bright_cyan]  ًںژ“  [bold white]{ar('ط¯ط®ظˆظ„ ظƒط·ط§ظ„ط¨ (Student Portal)')}[/bold white]\n"
            f"       [dim white]{ar('ط§ط³طھط¹ط±ط§ط¶ ط§ظ„ظ…ظ‚ط±ط±ط§طھ ظ…ظ‚ط³ظ…ط© ط¨ط§ظ„ط³ط§ط¹ط§طھطŒ ظپط­طµ ط§ظ„ظ…ظˆط§ط¯طŒ ط§ظ„ط¨ط­ط« ظپظٹ ط§ظ„ظ„ظˆط§ط¦ط­طŒ ظˆط­ط³ط§ط¨ ط§ظ„ظ…ط¹ط¯ظ„')}[/dim white]\n\n"
            f"[bold bright_cyan][2][/bold bright_cyan]  ًں›،ï¸ڈ   [bold white]{ar('ط¯ط®ظˆظ„ ظƒظ…ط³ط¤ظˆظ„ (Admin Dashboard)')}[/bold white]\n"
            f"       [dim white]{ar('ط¥ط¯ط§ط±ط© ط§ظ„ظ…ظ‚ط±ط±ط§طھطŒ ط¥ط¶ط§ظپط© ظ„ظˆط§ط¦ط­طŒ ظˆظ…ط±ط§ظ‚ط¨ط© ط³ط¬ظ„ ط§ظ„ط¹ظ…ظ„ظٹط§طھ')}[/dim white]\n\n"
            f"[bold bright_cyan][3][/bold bright_cyan]  â„¹ï¸ڈ   [bold white]{ar('ط­ظˆظ„ ط§ظ„ظ…ط´ط±ظˆط¹ ظˆط§ظ„طھظ‚ظ†ظٹط§طھ ط§ظ„ظ…ط³طھط®ط¯ظ…ط© (About)')}[/bold white]\n\n"
            f"[bold bright_cyan][4][/bold bright_cyan]  ًں‘¥  [bold white]{ar('ظپط±ظٹظ‚ ط§ظ„ظ…ط·ظˆط±ظٹظ† ظˆط±ظˆط§ط¨ط· LinkedIn (Development Team)')}[/bold white]\n\n"
            f"â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"[bold bright_red][0][/bold bright_red]  ًںڑھ  [bold red]{ar('ط¥ظ†ظ‡ط§ط، ط§ظ„ط¨ط±ظ†ط§ظ…ط¬ ظˆط§ظ„ط®ط±ظˆط¬')}[/bold red]"
        )
        console.print(Panel(welcome_card, box=box.ROUNDED, border_style="bright_blue", title=f"ًںŒں {ar('ظ…ط±ط­ط¨ط§ظ‹ ط¨ظƒ - ط§ط®طھط± ظ†ظˆط¹ ط§ظ„ط¯ط®ظˆظ„')}"))

        try:
            choice = input(f"\n  [?] {ar('ط§ط®طھط± ط±ظ‚ظ…ط§ظ‹')}: ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "0"

        if choice == "1":
            student_menu(ir_engine)
        elif choice == "2":
            pwd = input(f"\n  [ًں”’] {ar('ط£ط¯ط®ظ„ ظƒظ„ظ…ط© ظ…ط±ظˆط± ط§ظ„ظ…ط³ط¤ظˆظ„')}: ").strip()
            if pwd == "admin123":
                log_query("ADMIN_LOGIN_SUCCESS", "طھط³ط¬ظٹظ„ ط¯ط®ظˆظ„ ظ†ط§ط¬ط­ ظ„ظ„ظ…ط³ط¤ظˆظ„")
                admin_menu(ir_engine)
            else:
                console.print(f"\n[bold red]âœ– {ar('ظƒظ„ظ…ط© ط§ظ„ظ…ط±ظˆط± ط؛ظٹط± طµط­ظٹط­ط©!')}[/bold red]")
                log_query("ADMIN_LOGIN_FAIL", "ظ…ط­ط§ظˆظ„ط© ط¯ط®ظˆظ„ ط®ط§ط·ط¦ط©")
                pause()
        elif choice == "3":
            show_about()
        elif choice == "4":
            show_developers()
        elif choice == "0":
            log_query("SESSION_END", "ط®ط±ظˆط¬ ظ…ظ† ط§ظ„طھط·ط¨ظٹظ‚")
            clear_screen()
            farewell = Panel(
                f"[bold bright_green]ًںژ“ {ar('ط´ظƒط±ط§ظ‹ ظ„ط§ط³طھط®ط¯ط§ظ…ظƒ ط¯ظ„ظٹظ„ ط§ظ„ط·ط§ظ„ط¨ ط§ظ„ط°ظƒظٹ.')}[/bold bright_green]\n"
                f"[dim white]{ar('ظ†طھظ…ظ†ظ‰ ظ„ظƒ ظپطµظ„ط§ظ‹ ط¯ط±ط§ط³ظٹط§ظ‹ ط­ط§ظپظ„ط§ظ‹ ط¨ط§ظ„ظ†ط¬ط§ط­ ظˆط§ظ„طھظپظˆظ‚ ط§ظ„ط£ظƒط§ط¯ظٹظ…ظٹ!')}[/dim white]",
                box=box.ROUNDED,
                border_style="green",
            )
            console.print(farewell)
            break
        else:
            console.print(f"[red]{ar('ط§ط®طھظٹط§ط± ط؛ظٹط± طµط­ظٹط­طŒ ط§ظ„ط±ط¬ط§ط، ط§ط®طھظٹط§ط± ط±ظ‚ظ… ظ…ظ† ط§ظ„ظ‚ط§ط¦ظ…ط©.')}[/red]")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nطھظ… ط¥ظ†ظ‡ط§ط، ط§ظ„ط¨ط±ظ†ط§ظ…ط¬.")
        sys.exit(0)
