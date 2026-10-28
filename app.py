# =============================================================================
#  Smart Student Guide - Web Edition (تطبيق الويب المتكامل)
#  خادم Flask + محرك استرجاع المعلومات (TF-IDF) + محرك الاستنتاج الأكاديمي
# =============================================================================

import os
import sys
import csv
import json
import logging
import threading
import webbrowser
from collections import defaultdict

# إعداد دعم إخراج UTF-8 في طرفية ويندوز لتجنب أخطاء الترميز (cp1256 UnicodeEncodeError)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ضمان مسار المجلد الأساسي للتطبيق بشكل مطلق
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    os.chdir(BASE_DIR)
except Exception:
    pass

# pyrefly: ignore[missing-import]
from flask import Flask, render_template, request, jsonify, send_from_directory

# استيراد خوارزميات استرجاع المعلومات
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__, template_folder=BASE_DIR, static_folder=BASE_DIR)
app.config['JSON_AS_ASCII'] = False  # دعم العربية في مخرجات JSON

# =============================================================================
#  مسارات الملفات
# =============================================================================
COURSES_FILE   = os.path.join(BASE_DIR, "courses.csv")
PREREQ_FILE    = os.path.join(BASE_DIR, "prerequisites.json")
DOCS_DIR       = os.path.join(BASE_DIR, "docs")
LOG_FILE       = os.path.join(BASE_DIR, "queries.log")

# Career Path Engine
CAREER_TRACKS_FILE = os.path.join(BASE_DIR, "career_tracks.json")
COURSE_SKILLS_FILE = os.path.join(BASE_DIR, "course_skills.json")

ATTENDANCE_DOC = os.path.join(DOCS_DIR, "attendance_policy.txt")
GPA_DOC        = os.path.join(DOCS_DIR, "gpa_system.txt")
REG_DOC        = os.path.join(DOCS_DIR, "registration_rules.txt")

# =============================================================================
#  إعداد نظام السجل (UTF-8 Logging)
# =============================================================================
logger = logging.getLogger("SmartGuideWeb")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(_fh)

def log_query(action: str, details: str = ""):
    """تسجيل العمليات في queries.log."""
    logger.info(f"[{action}] {details}")


# =============================================================================
#  تهيئة البيانات التلقائية
# =============================================================================
def initialize_data():
    """إنشاء الملفات ببيانات واقعية إذا لم تكن موجودة."""
    # 1. courses.csv
    if not os.path.exists(COURSES_FILE):
        courses = [
            ["course_id", "course_name", "instructor", "room", "credit_hours"],
            ["CS101",   "مقدمة في البرمجة (Python & C++)",             "د. أحمد محمد",    "معمل الحاسب 1",          3],
            ["CS102",   "هياكل البيانات والخوارزميات",                   "د. محمود حسن",    "مدرج 2",                 3],
            ["CS201",   "البرمجة كائنية التوجه (OOP & Design Patterns)", "د. يوسف شريف",    "معمل 2",                 3],
            ["CS202",   "تنظيم وعمارة الحاسب",                          "د. عماد كامل",    "مدرج 3",                 3],
            ["CS301",   "نظم التشغيل والبرمجة المتزامنة",                "د. منى سعيد",      "معمل 4",                 3],
            ["CS302",   "شبكات الحاسب وأمن الشبكات",                    "د. هاني مصطفى",   "معمل الشبكات",           3],
            ["CS303",   "هندسة البرمجيات وإدارة المشاريع",             "د. نادية إبراهيم", "قاعة 204",               2],
            ["CS401",   "تطوير تطبيقات الويب المتكاملة (Full-Stack)",   "د. هشام زكي",     "معمل الويب",             3],
            ["CS402",   "أمن المعلومات واختبار الاختراق",               "د. شريف عادل",    "معمل الأمان",            3],
            ["CS403",   "الحوسبة السحابية وDevOps",                     "د. باسل محمود",   "معمل السحابية",          3],
            ["MATH101", "تفاضل وتكامل 1",                                "د. إبراهيم علي",  "مدرج 1",                 3],
            ["MATH102", "جبر خطي وإحصاء احتمالي",                       "د. سارة خالد",    "قاعة 104",               3],
            ["MATH201", "رياضيات متقطعة ونظرية المخططات",               "د. ليلى نبيل",    "قاعة 105",               2],
            ["IS201",   "نظم قواعد البيانات وتصميمها",                   "د. منى رضا",      "معمل 3",                 3],
            ["IS301",   "مستودعات البيانات وتنظيم ETL",                  "د. تامر فاروق",   "معمل 2",                 2],
            ["AI201",   "أساسيات الذكاء الاصطناعي ونظم المعرفة",         "د. علي عبدالله",  "قاعة 201",               3],
            ["AI202",   "تعلم الآلة (Machine Learning)",                 "د. كريم وليد",    "معمل الذكاء الاصطناعي", 3],
            ["AI301",   "التعلم العميق ورؤية الحاسب (Deep Learning)",    "د. ياسمين طارق",  "معمل الأبحاث",           3],
            ["AI302",   "معالجة اللغات الطبيعية (NLP & LLMs)",          "د. رامي إلهامي",  "معمل 1",                 2],
            ["ROB201",  "مقدمة في الروبوتات والأنظمة المدمجة",          "د. طارق أحمد",    "معمل الروبوت",           2],
            ["ROB301",  "نظم الزمن الحقيقي وإنترنت الأشياء (RTOS & IoT)", "د. وليد فوزي",    "معمل المدمجة",           2],
        ]
        with open(COURSES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(courses)

    # 2. prerequisites.json
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

    # 3. docs/
    os.makedirs(DOCS_DIR, exist_ok=True)

    if not os.path.exists(ATTENDANCE_DOC):
        content = """لائحة الحضور والغياب - كلية الذكاء الاصطناعي والحاسبات

المادة الأولى: الحضور الإلزامي
يُعدّ حضور المحاضرات والأعمال العملية والميدانية إلزامياً لجميع طلاب الكلية.
يجب على الطالب حضور ما لا يقل عن 75% من إجمالي المحاضرات المقررة لكل مادة في الفصل الدراسي.

المادة الثانية: الحد الأقصى للغياب
الحد الأقصى المسموح به للغياب هو 25% من إجمالي ساعات المادة.
يُحتسب الغياب بعذر وبدون عذر ضمن نسبة الغياب الإجمالية حتى يتم البت فيه من لجنة شؤون الطلاب.
في حالة تجاوز نسبة الغياب 10% وحتى 20%: يُرسل للطالب إنذار أكاديمي أول عبر البوابة الإلكترونية.

المادة الثالثة: الحرمان من دخول الامتحان النهائي (الرسوب بالغياب)
إذا تجاوز الطالب نسبة الغياب المقررة (25%) في أي مادة دون عذر قهري معتمد، يُحرَم رسمياً من دخول الامتحان النهائي لتلك المادة.
تُرصد للطالب درجة صفر في خانة الامتحان النهائي مع تسجيل تقدير (DN - حرمان).
يحق للطالب تقديم التماس تظلم رسمي إلى وكيل الكلية لشؤون التعليم والطلاب خلال أسبوع واحد من إعلان كشوف الحرمان.

المادة الرابعة: حالات الغياب بعذر مقبول
تُقبل الأعذار في الحالات الاستثنائية التالية فقط:
1. التنويم في المستشفى أو إجراء عمليات جراحية عاجلة مع تقديم تقرير طبي معتمد من الإدارة الطبية بالجامعة.
2. حالات الوفاة للأقارب من الدرجة الأولى (الأب، الأم، الأخ، الأخت) مع إرفاق شهادة الوفاة.
3. تمثيل الكلية أو الجامعة في البطولات والمؤتمرات والمسابقات الرسمية بخطاب تكليف مسبق من رعاية الشباب.
4. الظروف القاهرة غير المتوقعة التي يقرر مجلس الكلية قبولها.
"""
        with open(ATTENDANCE_DOC, "w", encoding="utf-8") as f:
            f.write(content)

    if not os.path.exists(GPA_DOC):
        content = """نظام التقديرات وحساب المعدل التراكمي (CGPA) - نظام الساعات المعتمدة

أولاً: جدول توزيع التقديرات والنقاط
الدرجة المئوية    التقدير اللاتيني    النقاط (Grade Points)    التقدير المكافئ
------------------------------------------------------------------------
90% فأكثر         A+                 4.0                      ممتاز مرتفع
85% إلى أقل من 90% A                  3.7                      ممتاز
80% إلى أقل من 85% B+                 3.3                      جيد جداً مرتفع
75% إلى أقل من 80% B                  3.0                      جيد جداً
70% إلى أقل من 75% C+                 2.7                      جيد مرتفع
65% إلى أقل من 70% C                  2.3                      جيد
60% إلى أقل من 65% D+                 2.0                      مقبول مرتفع
55% إلى أقل من 60% D                  1.7                      مقبول (الحد الأدنى للنجاح)
أقل من 55%        F                  0.0                      راسب

ثانياً: شروط النجاح الأكاديمي
الحد الأدنى للنجاح في أي مقرر دراسي هو الحصول على تقدير (D) بنسبة 55% من إجمالي الدرجة النهائية.
المقرر الحاصل فيه الطالب على تقدير (F) لا تُحتسب ساعاته المعتمدة ضمن الساعات المنجزة، ويجب على الطالب إعادة دراسته والتسجيل فيه مرة أخرى.

ثالثاً: معادلة حساب المعدل التراكمي (GPA)
المعدل = مجموع (نقاط كل مقرر × عدد ساعاته المعتمدة) ÷ مجموع الساعات المعتمدة الإجمالي
المعدل التراكمي العام المطلوب للتخرج هو 2.0 على الأقل من 4.0.

رابعاً: التحذير الأكاديمي ولوائح الفصل
1. يوضع الطالب تحت الملاحظة الأكاديمية (Academic Probation) إذا انخفض معدله التراكمي عن 2.0 في أي فصل دراسي.
2. الطالب المنذر أكاديمياً يُمنع من تسجيل أكثر من 12 ساعة معتمدة في الفصل التالي للتركيز على رفع معدله.
3. إذا استمر الطالب تحت الملاحظة لثلاثة فصول دراسية متتالية يُعرض موقفه على مجلس الكلية للنظر في فصله أكاديمياً أو منحه فرصة أخيرة.

خامساً: مرتبة الشرف والتفوق
تُمنح مرتبة الشرف للطالب الذي يتخرج بمعدل تراكمي 3.5 فأكثر بشرط ألا يكون قد رسب في أي مقرر دراسي طوال سنوات دراسته بالكلية.
"""
        with open(GPA_DOC, "w", encoding="utf-8") as f:
            f.write(content)

    if not os.path.exists(REG_DOC):
        content = """قواعد التسجيل والإرشاد الأكاديمي - كلية الحاسبات والذكاء الاصطناعي

أولاً: العبء الدراسي (الحد الأدنى والأقصى للساعات المعتمدة)
1. الحد الأدنى للتسجيل في الفصل الدراسي الاعتيادي: 12 ساعة معتمدة.
2. الحد الأقصى للعبء الدراسي للطالب العادي (معدل 2.0 إلى 3.49): 18 ساعة معتمدة.
3. استثناء التفوق (معدل 3.5 فأكثر): يُسمح للطالب بتسجيل حتى 21 ساعة معتمدة بعد موافقة المرشد الأكاديمي والعميد.
4. الطلاب المنذرون أكاديمياً (معدل أقل من 2.0): الحد الأقصى المسموح به هو 12 ساعة معتمدة فقط.
5. الفصل الصيفي (Summer Semester): الحد الأقصى للتسجيل هو 6 ساعات معتمدة (أو 7 ساعات إذا كانت تشمل مقرر تدريب أو تخرج).

ثانياً: المتطلبات السابقة للمقررات (Prerequisites)
لا يجوز للطالب بأي حال من الأحوال التسجيل في مقرر دراسي ما لم يكن قد اجتاز المتطلب السابق (Prerequisite) بنجاح (تقدير D على الأقل).
يُلغى تسجيل أي مقرر يتم بشكل خاطئ دون استيفاء متطلبه السابق فور مراجعة الجداول وقبل بدء الأسبوع الثالث.

ثالثاً: مهام المرشد الأكاديمي
1. يُخصص لكل طالب مرشد أكاديمي من أعضاء هيئة التدريس لمساعدته في بناء خطته الدراسية واختيار المقررات المناسبة.
2. لا يُعتمد الجدول الدراسي للطالب إلا بعد الحصول على الموافقة الإلكترونية من المرشد الأكاديمي.
3. يتولى المرشد متابعة الطلاب المتعثرين وتقديم الدعم الإرشادي المناسب لتحسين معدلاتهم.

رابعاً: فترات الحذف والإضافة والانسحاب (Add & Drop)
1. فترة الحذف والإضافة: خلال الأسبوعين الأول والثاني من بدء الفصل الدراسي، ولا يُثبت المقرر في السجل عند حذفه خلال هذه الفترة.
2. الانسحاب بعذر (Withdrawal - W): يجوز للطالب الانسحاب من مقرر حتى نهاية الأسبوع الثامن، وتُسجل له علامة (W) ولا تدخل في حساب المعدل.
3. الانسحاب الإجباري/الرسوب (WF): الانسحاب بعد الأسبوع الثامن يُعد رسوباً بالانسحاب (WF) ويُحسب كتقدير F بنقاط صفرية في المعدل.
"""
        with open(REG_DOC, "w", encoding="utf-8") as f:
            f.write(content)


# =============================================================================
#  إدارة الملفات (CSV / JSON)
# =============================================================================
def load_courses() -> list[dict]:
    courses = []
    if not os.path.exists(COURSES_FILE):
        return courses
    with open(COURSES_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            courses.append(dict(row))
    return courses


def save_courses(courses: list[dict]):
    if not courses:
        return
    fieldnames = ["course_id", "course_name", "instructor", "room", "credit_hours"]
    with open(COURSES_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(courses)


def load_prerequisites() -> dict:
    if not os.path.exists(PREREQ_FILE):
        return {}
    with open(PREREQ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_prerequisites(prereqs: dict):
    with open(PREREQ_FILE, "w", encoding="utf-8") as f:
        json.dump(prereqs, f, ensure_ascii=False, indent=4)


def load_career_tracks() -> dict:
    if not os.path.exists(CAREER_TRACKS_FILE):
        return {"tracks": []}
    with open(CAREER_TRACKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_course_skills() -> dict:
    if not os.path.exists(COURSE_SKILLS_FILE):
        return {}
    with open(COURSE_SKILLS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
#  محرك استرجاع المعلومات (IR Engine - TF-IDF & Cosine Similarity)
# =============================================================================
class WebIREngine:
    def __init__(self):
        self.doc_names = []
        self.doc_texts = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.inverted_index = {}
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
                    with open(fpath, "r", encoding="utf-8") as f:
                        text = f.read()
                    if text.strip():
                        self.doc_names.append(fname)
                        self.doc_texts.append(text)
                        doc_texts_map[fname] = text

        if not self.doc_texts:
            return

        # بناء الفهرس المعكوس
        idx = defaultdict(set)
        for doc_name, text in doc_texts_map.items():
            words = text.replace("\n", " ").replace(".", " ").replace("،", " ").split()
            for word in words:
                clean = word.strip().lower()
                if len(clean) > 2:
                    idx[clean].add(doc_name)
        self.inverted_index = {w: sorted(docs) for w, docs in idx.items()}

        # بناء نموذج TF-IDF
        self.vectorizer = TfidfVectorizer(analyzer="word", token_pattern=r"(?u)\b\w+\b")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_texts)

    def search(self, query: str, top_n: int = 3):
        if not self.vectorizer or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        ranked_indices = similarities.argsort()[::-1]

        results = []
        for idx in ranked_indices[:top_n]:
            score = float(similarities[idx])
            if score > 0.01:
                # استخراج أفضل فقرة مطابقة
                paragraphs = [p.strip() for p in self.doc_texts[idx].split("\n\n") if p.strip()]
                best_snippet = paragraphs[0] if paragraphs else self.doc_texts[idx][:300]
                results.append({
                    "file": self.doc_names[idx],
                    "score": round(score * 100, 1),
                    "snippet": best_snippet[:400]
                })
        return results


# تهيئة البيانات ومحرك البحث
initialize_data()
ir_engine = WebIREngine()


# =============================================================================
#  محرك الاستنتاج الأكاديمي (Inference Engine)
# =============================================================================
def get_available_courses(passed_courses: list[str]):
    prereqs = load_prerequisites()
    all_courses = load_courses()
    passed_set = set(c.upper().strip() for c in passed_courses if c.strip())

    available = []
    locked = []

    for course in all_courses:
        cid = course["course_id"].upper().strip()
        if cid in passed_set:
            continue

        reqs = prereqs.get(cid, [])
        missing_reqs = [r for r in reqs if r.upper() not in passed_set]

        if not missing_reqs:
            available.append(course)
        else:
            item = dict(course)
            item["missing_prereqs"] = missing_reqs
            locked.append(item)

    return available, locked


# =============================================================================
#  دوال Career Path Engine الحسابية
# =============================================================================
def compute_readiness(passed_courses: list[str], track_id: str) -> dict:
    """حاسبة الجاهزية لسوق العمل."""
    tracks_data = load_career_tracks()
    course_skills_data = load_course_skills()

    track = next((t for t in tracks_data["tracks"] if t["id"] == track_id), None)
    if not track:
        return {"error": "تراك غير موجود"}

    required_skills = set(track["required_skills"])
    acquired_skills = set()
    skills_by_course = {}

    for cid in passed_courses:
        cid_upper = cid.upper().strip()
        if cid_upper in course_skills_data:
            course_skills = course_skills_data[cid_upper]["skills"]
            skills_by_course[cid_upper] = course_skills
            acquired_skills.update(course_skills)

    covered = acquired_skills & required_skills
    missing = required_skills - acquired_skills

    score = round(len(covered) / len(required_skills) * 100) if required_skills else 0

    return {
        "track": track,
        "score": score,
        "covered_skills": sorted(covered),
        "missing_skills": sorted(missing),
        "acquired_extra": sorted(acquired_skills - required_skills),
        "skills_by_course": skills_by_course
    }


def recommend_electives(passed_courses: list[str], target_track_id: str) -> list[dict]:
    """مُوجِّه المواد الاختيارية الذكي."""
    tracks_data = load_career_tracks()
    course_skills_data = load_course_skills()
    courses = load_courses()
    prereqs = load_prerequisites()

    track = next((t for t in tracks_data["tracks"] if t["id"] == target_track_id), None)
    if not track:
        return []

    passed_set = set(c.upper().strip() for c in passed_courses if c.strip())
    required_skills = set(track["required_skills"])

    # المهارات المكتسبة حالياً
    acquired = set()
    for cid in passed_set:
        if cid in course_skills_data:
            acquired.update(course_skills_data[cid]["skills"])

    missing_skills = required_skills - acquired

    recommendations = []
    for course in courses:
        cid = course["course_id"].upper()
        if cid in passed_set:
            continue
        if cid not in course_skills_data:
            continue

        cd = course_skills_data[cid]
        if not cd.get("is_elective"):
            continue

        # فحص المتطلبات
        reqs = prereqs.get(cid, [])
        missing_reqs = [r for r in reqs if r.upper() not in passed_set]
        if missing_reqs:
            continue

        course_skills_set = set(cd["skills"])
        gains = course_skills_set & missing_skills

        if gains:
            recommendations.append({
                "course": course,
                "skills_gained": sorted(gains),
                "skills_gained_count": len(gains),
                "relevance_score": round(len(gains) / len(missing_skills) * 100) if missing_skills else 0
            })

    recommendations.sort(key=lambda x: x["skills_gained_count"], reverse=True)
    return recommendations


def generate_skill_gap_roadmap(passed_courses: list[str], track_id: str) -> dict:
    """كاشف الفجوة ومولد خطة المسار البديل."""
    readiness = compute_readiness(passed_courses, track_id)
    if "error" in readiness:
        return readiness

    BRIDGE_RESOURCES = {
        "Deep Learning": [
            {"name": "Deep Learning Specialization - Coursera", "url": "https://www.coursera.org/specializations/deep-learning", "duration": "3 أشهر", "free": False},
            {"name": "Practical Deep Learning - fast.ai", "url": "https://course.fast.ai/", "duration": "شهر", "free": True}
        ],
        "TensorFlow": [
            {"name": "TensorFlow Developer - Google", "url": "https://www.tensorflow.org/learn", "duration": "أسبوعان", "free": True}
        ],
        "PyTorch": [
            {"name": "PyTorch Official Tutorials", "url": "https://pytorch.org/tutorials/", "duration": "أسبوعان", "free": True}
        ],
        "Docker": [
            {"name": "Docker Getting Started", "url": "https://docs.docker.com/get-started/", "duration": "أسبوع", "free": True}
        ],
        "SQL": [
            {"name": "SQLZoo Interactive", "url": "https://sqlzoo.net/", "duration": "أسبوع", "free": True},
            {"name": "Mode Analytics SQL Tutorial", "url": "https://mode.com/sql-tutorial/", "duration": "أسبوع", "free": True}
        ],
        "Linux": [
            {"name": "Linux Command Line - Ryan's Tutorials", "url": "https://ryanstutorials.net/linuxtutorial/", "duration": "أسبوع", "free": True}
        ],
        "Git": [
            {"name": "Git & GitHub - freeCodeCamp", "url": "https://www.freecodecamp.org/news/git-and-github-for-beginners/", "duration": "3 أيام", "free": True}
        ],
        "Networking": [
            {"name": "Computer Networking - Coursera (Stanford)", "url": "https://www.coursera.org/learn/computer-networking", "duration": "شهران", "free": False}
        ],
        "Cryptography": [
            {"name": "Cryptography I - Stanford (Coursera)", "url": "https://www.coursera.org/learn/crypto", "duration": "شهران", "free": False}
        ],
        "JavaScript": [
            {"name": "JavaScript.info", "url": "https://javascript.info/", "duration": "شهر", "free": True}
        ],
        "NoSQL": [
            {"name": "MongoDB University (Free)", "url": "https://university.mongodb.com/", "duration": "أسبوعان", "free": True}
        ],
        "ETL": [
            {"name": "Data Engineering Zoomcamp", "url": "https://github.com/DataTalksClub/data-engineering-zoomcamp", "duration": "شهران", "free": True}
        ],
        "Pandas": [
            {"name": "Pandas Documentation Tutorials", "url": "https://pandas.pydata.org/docs/getting_started/tutorials.html", "duration": "أسبوع", "free": True}
        ],
        "Scikit-learn": [
            {"name": "Scikit-learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html", "duration": "أسبوعان", "free": True}
        ]
    }

    gap_roadmap = []
    for skill in readiness["missing_skills"]:
        resources = BRIDGE_RESOURCES.get(skill, [])
        gap_roadmap.append({
            "skill": skill,
            "resources": resources,
            "has_resources": len(resources) > 0
        })

    return {
        "track": readiness["track"],
        "score": readiness["score"],
        "covered_skills": readiness["covered_skills"],
        "missing_skills": readiness["missing_skills"],
        "gap_roadmap": gap_roadmap,
        "tools_gap": readiness["track"].get("tools", [])
    }


def generate_cv(passed_courses: list[str], student_name: str = "") -> dict:
    """مولّد السيرة الذاتية الأكاديمية."""
    course_skills_data = load_course_skills()
    all_courses = load_courses()
    courses_map = {c["course_id"].upper(): c for c in all_courses}

    COURSE_PROJECT_TEMPLATES = {
        "CS101": "تطوير تطبيقات console بلغة Python مع التحكم في تدفق البرنامج وبنية الكود",
        "CS102": "تطبيق هياكل بيانات (شجرة، قائمة، خريطة هاش) وتحليل تعقيد الخوارزميات Big-O",
        "MATH101": "نمذجة مسائل رياضية باستخدام التفاضل والتكامل وتطبيقها في تحسين الدوال",
        "MATH102": "تطبيقات الجبر الخطي: تحويلات المصفوفات، PCA، والإحصاء الوصفي والاستدلالي",
        "AI201": "تصميم وتطبيق نظام خبير Rule-Based وخوارزميات بحث (A*, BFS, DFS)",
        "AI202": "بناء نماذج تعلم آلة (تصنيف، انحدار، تجميع) باستخدام scikit-learn مع تقييم الأداء",
        "IS201": "تصميم قاعدة بيانات علائقية (ERD → SQL Schema) مع كتابة استعلامات SQL معقدة",
        "ROB201": "برمجة ميكروكنترولر Arduino للتحكم في Servo Motors وقراءة حساسات البيئة"
    }

    skills_all = set()
    cv_courses = []

    for cid in passed_courses:
        cid_upper = cid.upper().strip()
        if cid_upper not in course_skills_data:
            continue

        cd = course_skills_data[cid_upper]
        course_info = courses_map.get(cid_upper, {})
        skills_all.update(cd["skills"])

        cv_courses.append({
            "course_id": cid_upper,
            "course_name": course_info.get("course_name", cid_upper),
            "skills": cd["skills"],
            "project_template": COURSE_PROJECT_TEMPLATES.get(cid_upper, f"تطبيقات عملية في {course_info.get('course_name', cid_upper)}"),
            "credit_hours": course_info.get("credit_hours", "3")
        })

    return {
        "student_name": student_name,
        "cv_courses": cv_courses,
        "skills_summary": sorted(skills_all),
        "total_skills": len(skills_all),
        "total_courses": len(cv_courses)
    }


# =============================================================================
#  المسارات والواجهات (Routes & API Endpoints)
# =============================================================================

@app.route("/")
def index():
    """الصفحة الرئيسية للموقع."""
    index_file = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
    return render_template("index.html")


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    """خدمة ملفات الوسائط الثابتة (مثل صور المطورين)."""
    return send_from_directory(os.path.join(BASE_DIR, "assets"), filename)


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """إحصائيات النظام العامة."""
    courses = load_courses()
    return jsonify({
        "courses_count": len(courses),
        "docs_count": len(ir_engine.doc_names),
        "terms_count": len(ir_engine.inverted_index),
        "status": "Online"
    })


@app.route("/api/courses", methods=["GET"])
def api_courses():
    """الحصول على جميع المقررات وشجرة المتطلبات."""
    courses = load_courses()
    prereqs = load_prerequisites()
    for c in courses:
        cid = c.get("course_id", "")
        c["prereqs"] = prereqs.get(cid, [])
    return jsonify({"courses": courses})


@app.route("/api/search", methods=["POST"])
def api_search():
    """البحث الذكي باستخدام TF-IDF و Cosine Similarity."""
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"results": []})

    log_query("WEB_SEARCH", f"استعلام المستخدم: {query}")
    results = ir_engine.search(query, top_n=3)
    return jsonify({"results": results, "query": query})


@app.route("/api/advisor", methods=["POST"])
def api_advisor():
    """محرك الاستنتاج الأكاديمي."""
    data = request.get_json() or {}
    passed = data.get("passed", [])
    available, locked = get_available_courses(passed)
    
    log_query("WEB_ADVISOR", f"مجتاز: {passed} | متاح: {[c['course_id'] for c in available]}")
    return jsonify({
        "available": available,
        "locked": locked,
        "passed_count": len(passed)
    })


@app.route("/api/doc/<filename>", methods=["GET"])
def api_get_doc(filename):
    """قراءة نص لائحة كاملة."""
    # تأمين المسار ضد Directory Traversal
    safe_name = os.path.basename(filename)
    fpath = os.path.join(DOCS_DIR, safe_name)
    if not os.path.exists(fpath):
        return jsonify({"error": "المستند غير موجود"}), 404

    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    log_query("WEB_READ_DOC", f"قراءة المستند: {safe_name}")
    return jsonify({"filename": safe_name, "content": content})


@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    """التحقق من كلمة مرور المسؤول."""
    data = request.get_json() or {}
    pwd = data.get("password", "")
    if pwd == "admin123":
        log_query("ADMIN_LOGIN", "تسجيل دخول ناجح للوحة الإدارة")
        return jsonify({"success": True})
    log_query("ADMIN_LOGIN_FAIL", "محاولة دخول خاطئة")
    return jsonify({"success": False, "message": "كلمة المرور غير صحيحة"}), 401


@app.route("/api/admin/course/add", methods=["POST"])
def api_admin_add_course():
    """إضافة مقرر جديد."""
    data = request.get_json() or {}
    cid = data.get("course_id", "").strip().upper()
    name = data.get("course_name", "").strip()
    inst = data.get("instructor", "").strip()
    room = data.get("room", "").strip()
    hours = data.get("credit_hours", "3").strip()
    prereqs_list = data.get("prerequisites", [])

    if not cid or not name:
        return jsonify({"error": "رمز واسم المادة مطلوبان"}), 400

    courses = load_courses()
    if any(c["course_id"].upper() == cid for c in courses):
        return jsonify({"error": "المقرر موجود بالفعل"}), 400

    courses.append({
        "course_id": cid,
        "course_name": name,
        "instructor": inst,
        "room": room,
        "credit_hours": hours
    })
    save_courses(courses)

    prereqs = load_prerequisites()
    prereqs[cid] = [p.strip().upper() for p in prereqs_list if p.strip()]
    save_prerequisites(prereqs)

    log_query("ADMIN_ADD_COURSE", f"إضافة المادة: {cid} - {name}")
    return jsonify({"success": True, "message": f"تمت إضافة المقرر {cid} بنجاح"})


@app.route("/api/admin/course/delete", methods=["POST"])
def api_admin_delete_course():
    """حذف مقرر."""
    data = request.get_json() or {}
    cid = data.get("course_id", "").strip().upper()

    courses = load_courses()
    new_courses = [c for c in courses if c["course_id"].upper() != cid]
    save_courses(new_courses)

    prereqs = load_prerequisites()
    if cid in prereqs:
        del prereqs[cid]
    for k, v in prereqs.items():
        if cid in v:
            v.remove(cid)
    save_prerequisites(prereqs)

    log_query("ADMIN_DELETE_COURSE", f"حذف المادة: {cid}")
    return jsonify({"success": True, "message": f"تم حذف المقرر {cid}"})


@app.route("/api/admin/doc/add", methods=["POST"])
def api_admin_add_doc():
    """إضافة مستند جديد وإعادة بناء الفهرس."""
    data = request.get_json() or {}
    fname = data.get("filename", "").strip()
    content = data.get("content", "").strip()

    if not fname or not content:
        return jsonify({"error": "اسم الملف والمحتوى مطلوبان"}), 400

    if not fname.endswith(".txt"):
        fname += ".txt"

    safe_name = os.path.basename(fname)
    fpath = os.path.join(DOCS_DIR, safe_name)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

    ir_engine.build()
    log_query("ADMIN_ADD_DOC", f"إضافة المستند: {safe_name}")
    return jsonify({"success": True, "message": f"تم حفظ المستند {safe_name} وإعادة تدريب الفهرس"})


@app.route("/api/admin/logs", methods=["GET"])
def api_admin_logs():
    """عرض سجل العمليات."""
    if not os.path.exists(LOG_FILE):
        return jsonify({"logs": []})
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return jsonify({"logs": lines[-40:]})  # آخر 40 عملية


@app.route("/api/admin/reset", methods=["POST"])
def api_admin_reset():
    """استعادة البيانات الافتراضية."""
    for file in [COURSES_FILE, PREREQ_FILE, ATTENDANCE_DOC, GPA_DOC, REG_DOC]:
        if os.path.exists(file):
            os.remove(file)
    initialize_data()
    ir_engine.build()
    log_query("ADMIN_RESET_DATA", "استعادة البيانات الافتراضية")
    return jsonify({"success": True, "message": "تمت استعادة البيانات الافتراضية بنجاح"})


@app.route("/api/career/tracks", methods=["GET"])
def api_career_tracks():
    """جميع التراكات المهنية."""
    data = load_career_tracks()
    return jsonify(data)


@app.route("/api/career/readiness", methods=["POST"])
def api_career_readiness():
    """حاسبة الجاهزية لسوق العمل."""
    data = request.get_json() or {}
    passed = data.get("passed", [])
    track_id = data.get("track_id", "")
    result = compute_readiness(passed, track_id)
    log_query("CAREER_READINESS", f"Track: {track_id} | Score: {result.get('score', 0)}%")
    return jsonify(result)


@app.route("/api/career/electives", methods=["POST"])
def api_career_electives():
    """توصيات المواد الاختيارية."""
    data = request.get_json() or {}
    passed = data.get("passed", [])
    track_id = data.get("track_id", "")
    result = recommend_electives(passed, track_id)
    log_query("CAREER_ELECTIVES", f"Track: {track_id} | Recommendations: {len(result)}")
    return jsonify({"recommendations": result})


@app.route("/api/career/roadmap", methods=["POST"])
def api_career_roadmap():
    """خريطة الطريق لسد الفجوة المهارية."""
    data = request.get_json() or {}
    passed = data.get("passed", [])
    track_id = data.get("track_id", "")
    result = generate_skill_gap_roadmap(passed, track_id)
    log_query("CAREER_ROADMAP", f"Track: {track_id} | Missing: {len(result.get('missing_skills', []))} skills")
    return jsonify(result)


@app.route("/api/career/cv", methods=["POST"])
def api_career_cv():
    """مولد السيرة الذاتية الأكاديمية."""
    data = request.get_json() or {}
    passed = data.get("passed", [])
    name = data.get("student_name", "")
    result = generate_cv(passed, name)
    log_query("CAREER_CV", f"Courses: {len(passed)} | Skills: {result.get('total_skills', 0)}")
    return jsonify(result)


# =============================================================================
#  تشغيل الخادم مع فتح المتصفح التلقائي
# =============================================================================
def open_browser():
    """فتح المتصفح تلقائياً عند تشغيل الخادم."""
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("=" * 65)
    print("  Smart Student Guide - Web Edition")
    print("  Server: http://127.0.0.1:5000")
    print("  Opening browser automatically...")
    print("=" * 65)

    # تشغيل فتح المتصفح في خيط مستقل بعد ثانية واحدة
    threading.Timer(1.2, open_browser).start()

    # تشغيل تطبيق Flask
    app.run(host="127.0.0.1", port=5000, debug=False)
