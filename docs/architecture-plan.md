# wikiguard-py — פרויקט Python מקביל ל-wiki-guard, בנוי סביב Kafka

## Context

wiki-guard (Java/Spring Boot) נבנה בקורס, אבל המשתמש לא שולט בו לעומק — נבנה עם עזרת AI בלי הבנה מלאה של ההחלטות. המטרה כאן: **פרויקט Python מקביל**, שמדגים ניטור יושרת עריכות ויקיפדיה בזמן אמת (מלחמות עריכה / ונדליזם), אבל הפעם בתהליך שבו ההבנה של המשתמש היא התוצר המרכזי — לא רק קוד עובד. שתי מטרות משיקות: (א) ללמוד לבנות אפליקציות backend בעצמו בעזרת AI כשותף-הוראה, (ב) תיק עבודות שני, שונה מהותית מה-Java (שם: WebFlux/reactor-kafka; כאן: FastAPI async + **Kafka כנושא הלימוד המרכזי** — "תור הודעות ל-data stream בסקייל גבוה", בחירה מודעת ומוצהרת של המשתמש).

הארכיטקטורה שלמטה **לא הועתקה** מה-Java — היא נגזרה מדיון סוקרטי ארוך (המשתמש ענה על שאלות הבנה בכל צומת החלטה: הגדרת event, event_id, Kafka key/value, partition key, יחס בין Kafka/Redis/Postgres). קוד הג'אווה משמש רק כרפרנס-קריאה נקודתי בזמן המימוש (למשל למנוע גילוי-מחדש של באגים שכבר תועדו שם), לא כתבנית להעתקה — כולל לתיעוד/סקילים, שייבנו מחדש לפרויקט הזה ולא יועתקו מהסקילים הישנים של הבוטקאמפ.

## החלטות שנסגרו בדיון

- **ריפו:** תיקיית-אחות חדשה ועצמאית תחת אותה תיקיית-אם (`wikiguard-py`, ליד `wiki-guard`), git נפרד, לא branch בתוך wiki-guard הקיים.
- **Stack:** Python + **FastAPI (async)** + **aiokafka** + **redis.asyncio** + **SQLAlchemy 2.0 async (asyncpg) + Pydantic schemas נפרדים** (לא SQLModel — נבחר כי משמר את ההפרדה בין "מה שמור ב-DB" ל"מה נחשף ב-API", וזה השם שנשאל עליו בראיונות).
- **תשתית מקומית:** Docker Compose — Postgres, Redis, Kafka (single broker, KRaft), בדומה למבנה שקיים כבר ב-`wiki-guard/docker-compose.yml` (רפרנס בלבד).
- **Kafka נבחר במודע** (לא Redis Streams, לא asyncio.Queue) — זו מטרת הלימוד המוצהרת של הפרויקט.
- **ניהול תלויות:** `uv` (לא `requirements.txt`+venv כמו ב-`nemiys-basicPython`) — כלי מודרני אחד ל-venv+dependencies+lockfile.

## אסטרטגיית תיעוד — שתי שכבות, בלי שכפול תוכן ביניהן

נחקר (ADR pattern) ואושר עם המשתמש; מתוכנן מאפס לפרויקט הזה (לא מועתק מהישן) — במפורש כדי למנוע את בעיית "יותר מדי מידע לא מסונן" שהייתה בסיכומי הפרויקטים הקודמים.

1. **ADR בריפו** (`docs/adr/NNNN-slug.md`) — קובץ קצר לכל החלטה טכנית **משמעותית**: הקשר / ההחלטה / אלטרנטיבות שנשקלו / משמעות (יש כבר תוכן גולמי מהדיון: partition key, event_id, ORM choice ועוד). **לא כל החלטה** — מבחן הסינון: קשה/יקר לשנות בעתיד, או משפיע על איך חלקים אחרים בפרויקט ייבנו (למשל: Kafka vs Redis Streams, partition key, event_id, SQLAlchemy vs SQLModel — כן; קצב polling של הדשבורד, שם משתנה, בחירת כלי venv — לא, אלה נרשמים ב-README/CLAUDE.md רגיל אם בכלל). נכתב **מיד כשההחלטה מתקבלת**, לא בדיעבד. גלוי בגיטהאב — חומר פורטפוליו בפני עצמו, בנפרד מהקוד. לא נערך אחרי אישור; שינוי החלטה = ADR חדש שמחליף ומפנה לקודם.
2. **Notion — 3 סעיפים קבועים בלבד, בלי לשכפל את תוכן ה-ADR:**
   - **על הפרויקט** — נכתב פעם אחת (אחרי Stage 0), מתעדכן רק אם ההיקף משתנה מהותית.
   - **טכנולוגיות + איך מיושמות** — טבלה מצטברת, שורה חדשה רק כשטכנולוגיה חדשה נכנסת בשלב מסוים.
   - **צמתי החלטה** — שורה לכל החלטה: משפט-שניים בעברית פשוטה ברמת לומד ("מה ולמה") + קישור ל-ADR המלא. לא פסקאות ארוכות, לא חזרה על הנימוק ההנדסי המלא.
   - **קצב:** עדכון **פעם אחת בסוף כל Stage** (לא כל שיחה, לא רק בסוף הפרויקט) — נקודת עצירה טבעית עם בדיוק שלושת הדברים למעלה מוכנים.
   - דף/מבנה Notion לפרויקט **עדיין לא קיים** — יוקם בסוף ה-Stage הראשון שמייצר תוכן לתיעוד (לא חלק מ-scaffolding טכני).
3. **המנגנון: ישירות בתוך `CLAUDE.md` של הפרויקט** (לא סקיל/פקודה נפרדת) — Stage 0 כולל כתיבת סעיף "תיעוד בסוף כל Stage" בתוך ה-CLAUDE.md החדש, עם שלושת הסעיפים למעלה + הכלל "ADR מיד עם ההחלטה, עדכון Notion בסוף כל Stage" — כדי ש-Claude יפעל לפי זה אוטומטית בכל סשן עתידי, בלי תלות בהפעלת פקודה ידנית.

## תמונת הארכיטקטורה

```
Wikimedia EventStreams (SSE: https://stream.wikimedia.org/v2/stream/recentchange)
        │  data: {json} lines, מסננים heartbeats (":")
        ▼
[Producer] — מנרמל/מסנן בלבד, אף פעם לא לוגיקה עסקית
        │  מסנן: type != "edit" → discard, namespace != 0 → discard
        │  בונה WikiEditEvent + event_id = "{wiki}:{revision_id}"
        ▼
Kafka topic "wiki-edit-events" — 3 partitions (מספיק להדגמת מקביליות, בלי overhead מיותר)
        │  key = page_title (routing בלבד → מבטיח סדר עריכות לאותו עמוד)
        │  value = WikiEditEvent המלא (self-contained)
        ▼
[Consumer / Rule Engine] — consumer group, עותק אחד כברירת מחדל בפיתוח
        │  טוען כללים פעילים מ-Postgres כל ~10 שניות (רענון, לא push)
        ├─▶ Threshold rule: נבדק מיידית על ה-event הבודד (byte_change) — בלי Redis בכלל
        └─▶ Window-Count rule: פונה ל-Redis
                 │  Sorted Set per (rule_id, page): score = timestamp
                 │  1. ZADD  2. ZREMRANGEBYSCORE (חיתוך לפי חלון זמן)  3. ZCARD (ספירה)
                 ▼
        אם נחצה סף → כתיבת שורה ל-Postgres (fired_alerts)
        ▼
[FastAPI REST] — CRUD חוקים + קריאת התראות, מדבר רק מול Postgres (לא נוגע ב-Kafka/Redis)
        ▼
[Dashboard] — עמוד HTML+JS יחיד, polling כל ~4 שניות מול ה-API, בלי build step/framework
```

### עקרונות מפתח שהודגשו בדיון (חשוב לשמר בזמן המימוש, לא רק לזכור)

1. **הפרדת producer/consumer מוחלטת:** הפרודוסר לעולם לא מקבל החלטות עסקיות (מה נחשב "בעיה") — רק מנרמל ומסנן מבנית. כל הלוגיקה העסקית (כללים) חיה בקונסומר, נטענת דינמית מ-DB, ניתנת לשינוי בלי לגעת בפרודוסר.
2. **event_id דטרמיניסטי (`wiki:revision_id`), לא UUID אקראי** — נותן אידמפוטנטיות (retry לא יוצר "אירוע חדש"), ופותר את בעיית ה-revision_id שאינו ייחודי גלובלית (רק פר-wiki, וה-stream גלובלי).
3. **partition key = page_title, לא event_id** — תפקידו טכני-פנימי בלבד (routing ל-partition), לא "עוד מזהה". בחירה זו היא שנותנת את ערבות הסדר הדרושה ל-Window-Count.
4. **הרחבה עתידית (למשל כלל per-user) לא דורשת לגעת ב-Kafka** — רק evaluator/rule type חדש בקונסומר, עם מפתח Redis לפי `user` במקום `page`. שיקוף לכך שהלוגיקה העסקית מנותקת משכבת ה-streaming.
5. **שום event בודד לא נשמר לצמיתות.** Postgres שומר רק: (א) הגדרות חוקים, (ב) רשומת כל התראה שבאמת נדלקה — בשתי טבלאות נפרדות (`alert_rules`, `fired_alerts`, קשר FK דרך `rule_id`). מבנה העמודות המדויק — **מוגדר בזמן המימוש** (Stage 5 למטה), לא סוכם ברמת עמודות בדיון.
6. **סקייל היא שכבה נפרדת מ-Kafka.** Kafka רק מחלק עבודה בין consumers קיימים; ההחלטה "כמה consumers להריץ" שייכת לשכבת אורקסטרציה חיצונית (למשל Kubernetes autoscaling ב-production אמיתי — **לא** בסקופ הבנייה כאן, ידע מושגי בלבד). בפיתוח: consumer אחד. להדגמה: `docker compose up --scale consumer=N`.

## שלבי בנייה מוצעים (כל שלב מניב משהו שרץ בפועל, לפני שמוסיפים מורכבות)

| שלב | מה נבנה | תלוי ב | קריטריון הצלחה |
|---|---|---|---|
| 0 — Scaffolding | ריפו חדש (`uv init`), מבנה תיקיות, `docker-compose.yml` (Postgres+Redis+Kafka), שלד FastAPI, תיקיית `docs/adr/`, `CLAUDE.md` לפרויקט (כולל סעיף "תיעוד בסוף כל Stage") | — | `docker compose up` מרים את כל התשתית |
| 1 — ליבת הדומיין | `WikiEditEvent` (Pydantic), Threshold evaluator — לוגיקה טהורה, בלי I/O | 0 | unit tests עוברים בלי שום תשתית חיה |
| 2 — Producer | SSE client מול Wikimedia, סינון `type`/`namespace`, בניית `event_id`, פרסום ל-Kafka (`aiokafka`, key=page_title) | 0, 1 | רואים הודעות אמיתיות נכנסות לטופיק (למשל דרך CLI consumer) |
| 3 — Consumer (Threshold בלבד) | קונסומר Kafka, מריץ רק Threshold evaluator end-to-end, כרגע רק log/print | 1, 2 | pipeline מלא רץ קצה-לקצה בלי Redis/DB עדיין |
| 4 — Redis sliding window | `WindowCountEvaluator` + Sorted Set operations, מחובר לקונסומר | 3 | חוק תדירות נבדק נכון מול Redis אמיתי |
| 5 — Postgres persistence | SQLAlchemy models (`AlertRuleModel`, `FiredAlertModel`) + Pydantic schemas, טעינת חוקים דינמית בקונסומר, כתיבת התראות | 3, 4 | חוק שנוצר ידנית ב-DB נטען ומופעל; התראה נכתבת בפועל |
| 6 — REST API | FastAPI CRUD לחוקים + endpoints לקריאת התראות | 5 | אפשר ליצור/לראות חוקים והתראות דרך HTTP |
| 7 — Dashboard | עמוד HTML+JS יחיד, polling מול ה-API | 6 | רואים חוקים+התראות מתעדכנים על מסך |
| 8 — הדגמת סקייל (אופציונלי) | תיעוד/סקריפט ל-`--scale`, בדיקה שרואים rebalance | 2–4 | מריצים 2-3 consumers ורואים חלוקת partitions |

## רפרנסים מ-wiki-guard (Java) — לקריאה נקודתית בזמן המימוש, לא להעתקה

- `wiki-guard/src/main/java/.../ingest/WikipediaEventStreamIngestClient.java` — פילטור heartbeat/type/namespace, retry-with-backoff על ניתוק SSE. לבדוק לפני מימוש Stage 2 כדי לא לפספס edge case שכבר תועד (כתובת singular "recentchange", timestamp בשניות לא במילישניות).
- `wiki-guard/src/main/java/.../redis/SlidingWindowService.java` — רצף הפעולות המדויק (ZADD/ZREMRANGEBYSCORE/EXPIRE/ZCARD) והבאג המתועד של key scoping גלובלי-מדי (רול גלובלי שלא כלל page ב-key קרס תחת עומס אמיתי). לבדוק לפני Stage 4.
- `wiki-guard/README.md`, סעיף "Notable bugs found during development" — שלושה כשלים אמיתיים שתועדו, שווה לבדוק שלא חוזרים עליהם.
- `wiki-guard/docker-compose.yml` — מבנה תשתית לרפרנס בלבד ל-Stage 0.

## נותר פתוח לזמן המימוש (לא הוכרע בדיון, ובכוונה)

- מבנה עמודות מדויק של `alert_rules`/`fired_alerts` (single-table inheritance כמו בג'אווה, או שתי טבלאות נפרדות לכל סוג חוק — יוחלט ב-Stage 5).
- מנגנון cooldown/דה-דופ להתראות חוזרות (קיים בג'אווה, לא נדון מחדש כאן — להחליט ב-Stage 4/5).
- אסטרטגיית טסטים (מוצע: pytest + pytest-asyncio, ואפשר testcontainers-python בדומה לגישת ה-Java, אך לא סוכם).
- הקמת דף/מבנה Notion לפרויקט בפועל (ראו "אסטרטגיית תיעוד" למעלה) — בסוף ה-Stage הראשון שמייצר תוכן לתיעוד.

## אימות ההתקדמות

כל שלב נבדק לפני מעבר לבא: Stage 1 — `pytest` ירוק בלי תלות בתשתית; Stage 2 — הודעות אמיתיות נראות בטופיק (CLI/Python consumer זמני); Stage 3 — לוג מציג הפעלת Threshold rule אמיתית מקצה-לקצה; Stage 4 — מספר עריכות חוזרות על אותו עמוד מפעיל את ה-Window-Count; Stage 5–7 — תרחיש מלא: יצירת חוק דרך ה-API → עריכה אמיתית/סינתטית מגיעה → התראה נכתבת ל-DB → מופיעה בדשבורד.
