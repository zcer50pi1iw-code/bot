import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ضع توكين البوت الخاص بك والـ Admin ID
TOKEN = "8642314131:AAEBHQLgKXBpN8d_VSh6tzIIzJrdOUoet78"
ADMIN_ID = 7400700935

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------- إعداد قاعدة البيانات -----------------
def init_db():
    conn = sqlite3.connect('university_archive.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            file_name TEXT,
            category TEXT,
            content_type TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ----------------- القوائم والأزرار -----------------

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💻 برمجة الحاسوب", callback_data="sub_prog"), InlineKeyboardButton("🖱️ مهارات الحاسوب", callback_data="sub_skills")],
        [InlineKeyboardButton("📖 لغة عربية", callback_data="sub_arabic"), InlineKeyboardButton("🔤 لغة إنجليزية", callback_data="sub_english")],
        [InlineKeyboardButton("🔢 الرياضيات المتقطعة", callback_data="sub_discrete"), InlineKeyboardButton("📐 رياضيات", callback_data="sub_math")],
        [InlineKeyboardButton("🔒 أمن سيبراني", callback_data="sub_cyber"), InlineKeyboardButton("⚡ تصميم منطقي", callback_data="sub_logic")],
        [InlineKeyboardButton("💡 قسم للفائدة", callback_data="sec_info"), InlineKeyboardButton("⚙️ برامج برمجة", callback_data="sec_apps")],
        [InlineKeyboardButton("📩 الطلبات والشكاوى والتواصل", callback_data="sec_contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

def theoretical_practical_keyboard(subject_code):
    keyboard = [
        [InlineKeyboardButton("📖 نظري", callback_data=f"{subject_code}_th"), InlineKeyboardButton("💻 عملي", callback_data=f"{subject_code}_pr")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def content_types_keyboard(parent_code):
    keyboard = [
        [InlineKeyboardButton("📚 المحاضرات", callback_data=f"{parent_code}_lec")],
        [InlineKeyboardButton("📝 الملخصات", callback_data=f"{parent_code}_sum")],
        [InlineKeyboardButton("📄 النماذج والامتحانات", callback_data=f"{parent_code}_exm")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ----------------- الدوال المعالجة -----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "أهلاً بك في البوت الأكاديمي الجامعي 🎓\nاختر القسم أو المادة المطلوبة من القائمة أدناه:"
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=main_menu_keyboard())

# استقبال الملفات المرفوعة من قبل المشرف حصراً
async def handle_admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("عذراً، هذا البوت مخصص للأرشفة ولا يقبل الرفع إلا من المشرف.")
        return

    document = update.message.document
    if not document:
        return

    # حفظ بيانات الملف المؤقتة في الـ context
    file_id = document.file_id
    file_name = document.file_name
    context.user_data['pending_file_id'] = file_id
    context.user_data['pending_file_name'] = file_name

    # طلب اختيار المادة من المشرف (تشمل المواد الجديدة)
    keyboard = [
        [InlineKeyboardButton("💻 برمجة الحاسوب", callback_data="adm_sub_prog"), InlineKeyboardButton("🖱️ مهارات الحاسوب", callback_data="adm_sub_skills")],
        [InlineKeyboardButton("📖 لغة عربية", callback_data="adm_sub_arabic"), InlineKeyboardButton("🔤 لغة إنجليزية", callback_data="adm_sub_english")],
        [InlineKeyboardButton("🔢 الرياضيات المتقطعة", callback_data="adm_sub_discrete"), InlineKeyboardButton("📐 رياضيات", callback_data="adm_sub_math")],
        [InlineKeyboardButton("🔒 أمن سيبراني", callback_data="adm_sub_cyber"), InlineKeyboardButton("⚡ تصميم منطقي", callback_data="adm_sub_logic")]
    ]
    await update.message.reply_text(
        f"📄 تم استلام الملف: `{file_name}`\nاختر المادة التابع لها هذا الملف:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# معالج ضغطات الأزرار
async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await start(update, context)

    # تفليت المواد للأرشفة الإدارية
    elif data.startswith("adm_sub_"):
        sub = data.replace("adm_sub_", "")
        context.user_data['pending_category'] = sub
        
        # إذا كانت المادة مزدوجة (نظري/عملي)
        if sub in ["prog", "skills"]:
            keyboard = [
                [InlineKeyboardButton("📖 نظري", callback_data="adm_type_th"), InlineKeyboardButton("💻 عملي", callback_data="adm_type_pr")]
            ]
            await query.edit_message_text("اختر الشق (نظري / عملي):", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            # انتقل مباشرة لاختيار نوع المحتوى
            await query.edit_message_text("اختر نوع المحتوى:", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 محاضرات", callback_data="adm_cnt_lec"), InlineKeyboardButton("📝 ملخصات", callback_data="adm_cnt_sum")],
                [InlineKeyboardButton("📄 نماذج وامتحانات", callback_data="adm_cnt_exm")]
            ]))

    elif data in ["adm_type_th", "adm_type_pr"]:
        part = "th" if "th" in data else "pr"
        context.user_data['pending_category'] += f"_{part}"
        await query.edit_message_text("اختر نوع المحتوى:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 محاضرات", callback_data="adm_cnt_lec"), InlineKeyboardButton("📝 ملخصات", callback_data="adm_cnt_sum")],
            [InlineKeyboardButton("📄 نماذج وامتحانات", callback_data="adm_cnt_exm")]
        ]))

    elif data.startswith("adm_cnt_"):
        cnt_type = data.replace("adm_cnt_", "")
        category = context.user_data.get('pending_category')
        file_id = context.user_data.get('pending_file_id')
        file_name = context.user_data.get('pending_file_name')

        # حفظ الملف في قاعدة البيانات
        conn = sqlite3.connect('university_archive.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (file_id, file_name, category, content_type) VALUES (?, ?, ?, ?)",
                       (file_id, file_name, category, cnt_type))
        conn.commit()
        conn.close()

        await query.edit_message_text(f"✅ تم أرشفة الملف بنجاح!\n📁 الاسم: {file_name}\n📂 التصنيف: {category} ({cnt_type})")

    # تصفح الطلاب للملفات (المواد المزدوجة)
    elif data == "sub_prog":
        await query.edit_message_text("مادة برمجة الحاسوب 💻\nاختر الشق (نظري / عملي):", reply_markup=theoretical_practical_keyboard("prog"))
    elif data == "sub_skills":
        await query.edit_message_text("مادة مهارات الحاسوب 🖱️\nاختر الشق (نظري / عملي):", reply_markup=theoretical_practical_keyboard("skills"))

    elif data in ["prog_th", "prog_pr", "skills_th", "skills_pr"]:
        await query.edit_message_text("اختر نوع المحتوى المطلوب:", reply_markup=content_types_keyboard(data))

    # تصفح الطلاب للملفات (المواد ذات المسار الواحد وتشمل المواد الجديدة)
    elif data in ["sub_arabic", "sub_english", "sub_discrete", "sub_math", "sub_cyber", "sub_logic"]:
        code = data.replace("sub_", "")
        subject_names = {
            "arabic": "اللغة العربية 📖",
            "english": "اللغة الإنجليزية 4",
            "discrete": "الرياضيات المتقطعة 🔢",
            "math": "الرياضيات 📐",
            "cyber": "مقدمة في الأمن السيبراني 🔒",
            "logic": "التصميم المنطقي الرقمي ⚡"
        }
        await query.edit_message_text(f"مادة {subject_names.get(code, '')}\nاختر نوع المحتوى المطلوب:", reply_markup=content_types_keyboard(code))

    # عرض الملفات عند اختيار (محاضرات / ملخصات / نماذج)
    elif data.endswith("_lec") or data.endswith("_sum") or data.endswith("_exm"):
        parts = data.rsplit("_", 1)
        category = parts[0]
        cnt_type = parts[1]

        conn = sqlite3.connect('university_archive.db')
        cursor = conn.cursor()
        cursor.execute("SELECT file_id, file_name FROM files WHERE category = ? AND content_type = ?", (category, cnt_type))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await query.message.reply_text("📭 عذراً، لا توجد ملفات مرفوعة في هذا القسم حتى الآن.")
        else:
            await query.message.reply_text(f"📂 قائمة الملفات المتاحة لهذا القسم:")
            for f_id, f_name in rows:
                await context.bot.send_document(chat_id=query.message.chat_id, document=f_id, caption=f"📄 {f_name}")

    # الأقسام العامة
    elif data == "sec_info":
        await query.edit_message_text("💡 **قسم للفائدة:**\nهنا يتم نشر النصائح والأدوات والمقالات المفيدة للطلاب.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")]]))
    elif data == "sec_apps":
        await query.edit_message_text("⚙️ **برامج البرمجة:**\nروابط وتطبيقات مفيدة (VS Code, Dev-C++, Python, MinGW)...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")]]))
    elif data == "sec_contact":
        await query.edit_message_text("📩 **الطلبات والشكاوى والتواصل:**\nلإرسال استفسار أو طلب ملخص، يرجى كتابة رسالتك مباشرة وسنقوم بالرد عليك.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")]]))

# ----------------- تشغيل البوت -----------------

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_click_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_admin_upload))
    
    print("البوت يعمل الآن بنجاح مع المواد الجديدة...")
    app.run_polling()