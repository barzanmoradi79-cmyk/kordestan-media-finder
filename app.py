
import re
import pandas as pd
import streamlit as st
from ddgs import DDGS

st.set_page_config(page_title="پایش رسانه‌های کردستان", page_icon="🔎", layout="wide")
st.markdown("""
<style>
html, body, [class*="css"] { direction: rtl; text-align: right; }
[data-testid="stAppViewContainer"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

st.title("🔎 پایش رسانه‌های مجازی استان کردستان")
st.caption("نسخه آزمایشی: جست‌وجوی وبِ عمومی و ثبت لینک‌های قابل مشاهده؛ نه خزنده داخلی پیام‌رسان‌ها.")

default_terms = "کردستان،سنندج،سقز،بانه،مریوان،قروه،بیجار،کامیاران،دیواندره،دهگلان،سروآباد"
terms_text = st.text_area("کلیدواژه‌ها (با ویرگول جدا کنید)", default_terms, height=100)
platforms = st.multiselect(
    "پیام‌رسان‌ها / دامنه‌های جست‌وجو",
    ["ایتا", "روبیکا", "بله", "سروش پلاس"],
    default=["ایتا", "روبیکا", "بله", "سروش پلاس"]
)
limit = st.slider("حداکثر نتیجه برای هر کلیدواژه و پیام‌رسان", 5, 30, 10)

domains = {
    "ایتا": ["eitaa.com"],
    "روبیکا": ["rubika.ir"],
    "بله": ["ble.ir"],
    "سروش پلاس": ["splus.ir", "splus.ir"]
}

def extract_metrics(text):
    members = None
    views = None
    m = re.search(r'([\d,٫٬]+)\s*(?:عضو|دنبال.?کننده|مشترک)', text)
    if m: members = m.group(1)
    v = re.search(r'([\d,٫٬]+)\s*(?:بازدید|ویو)', text)
    if v: views = v.group(1)
    return members, views

if st.button("شروع جست‌وجو", type="primary", use_container_width=True):
    terms = [x.strip() for x in terms_text.replace("،", ",").split(",") if x.strip()]
    if not terms or not platforms:
        st.warning("حداقل یک کلیدواژه و یک پیام‌رسان انتخاب کنید.")
    else:
        rows, seen = [], set()
        progress = st.progress(0)
        total = len(terms) * len(platforms)
        done = 0
        status = st.empty()
        try:
            with DDGS() as ddgs:
                for platform in platforms:
                    for term in terms:
                        for domain in domains[platform]:
                            query = f'site:{domain} "{term}"'
                            status.write(f"در حال جست‌وجو: {platform} — {term}")
                            try:
                                results = list(ddgs.text(query, max_results=limit))
                            except Exception:
                                results = []
                            for item in results:
                                url = item.get("href", "")
                                if not url or url in seen:
                                    continue
                                seen.add(url)
                                title = item.get("title", "")
                                body = item.get("body", "")
                                members, views = extract_metrics(title + " " + body)
                                rows.append({
                                    "کلیدواژه": term,
                                    "پیام‌رسان": platform,
                                    "عنوان نتیجه": title,
                                    "لینک": url,
                                    "تعداد اعضا (اگر در نتیجه درج شده)": members or "در دسترس نیست",
                                    "بازدید (اگر در نتیجه درج شده)": views or "در دسترس نیست",
                                    "شرح نتیجه": body
                                })
                        done += 1
                        progress.progress(min(done / total, 1.0))
            status.write("جست‌وجو تمام شد.")
            if rows:
                df = pd.DataFrame(rows)
                st.success(f"{len(df)} نتیجه یکتا پیدا شد. این نتایج فقط موارد نمایه‌شده در وب هستند.")
                st.dataframe(df, use_container_width=True, hide_index=True)
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("دانلود فایل CSV قابل باز شدن در Excel", csv,
                                   "kordestan_media_results.csv", "text/csv",
                                   use_container_width=True)
            else:
                st.warning("نتیجه‌ای دریافت نشد؛ ممکن است موتور جست‌وجو محدودیت موقت اعمال کرده باشد.")
        except Exception as e:
            st.error(f"خطا در جست‌وجو: {e}")

st.info("""
**محدودیت مهم:** این نسخه مستقیماً داخل اپلیکیشن‌های ایتا، روبیکا، بله یا سروش‌پلاس جست‌وجو نمی‌کند.
فقط صفحات عمومیِ نمایه‌شده در موتور جست‌وجو را پیدا می‌کند. تعداد اعضا و بازدید تنها وقتی ثبت می‌شود
که خودِ نتیجه جست‌وجو آن را نشان دهد. برای استخراج کامل‌تر باید دسترسی رسمی/مجاز و روش جداگانه
برای هر پیام‌رسان فراهم شود. رمز عبور، کد پیامکی یا فایل نشست خود را در این برنامه وارد نکنید.
""")
