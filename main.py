import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import requests

app = FastAPI()
font_config = FontConfiguration()

def get_gemini_content(data):
    # আপনার প্রদানকৃত পূর্ণাঙ্গ প্রম্পটটি এখানে ডাইনামিক ইনপুটসহ সাজানো হয়েছে
    prompt = f"""
    তুমি একজন অভিজ্ঞ শিক্ষক এবং প্রশ্নকর্তা। শিক্ষার্থীদের মান উন্নয়নের জন্য আমাকে একটি বোর্ড পরীক্ষার প্রশ্নকাঠামোর আদলে পূর্ণাঙ্গ বহুনির্বাচনি (MCQ) প্রশ্নপত্র তৈরি করে দাও। প্রশ্নপত্রটি এমনভাবে তৈরি করবে যেন সেটি সরাসরি এ-ফোর (A4) সাইজের কাগজে ডাবল-কলাম লেআউটে প্রিন্ট করা যায়। 

    নিচের তথ্যগুলোর ভিত্তিতে প্রশ্নপত্রটি তৈরি করো:
    ১. প্রতিষ্ঠানের নাম: {data.get('institute')}
    ২. পরীক্ষার নাম: {data.get('exam')}
    ৩. শ্রেণি: {data.get('class')}
    ৪. বিষয়ের নাম: {data.get('subject')}
    ৫. বিষয় কোড: {data.get('code')}
    ৬. অধ্যায়সমূহ: {data.get('chapters')}
    ৭. প্রশ্ন: {data.get('q_count')}টি
    ৮. সময়: {data.get('time')}
    ৯. পূর্ণমান: {data.get('marks')}


প্রশ্ন তৈরির ক্ষেত্রে নিচের শর্তগুলো কঠোরভাবে মেনে চলতে হবে:
* জাতীয় শিক্ষাক্রম ও পাঠ্যপুস্তক বোর্ড (NCTB) অনুমোদিত প্রশ্নকাঠামো অনুসরণ করতে হবে।
* তিন ধরনের প্রশ্নই থাকতে হবে:
   ১. জ্ঞানমূলক প্রশ্ন। 
   ২. অনুধাবনমূলক প্রশ্ন।
   ৩. প্রয়োগমূলক প্রশ্ন
   ৩. সাধারণ বহুনির্বাচনি প্রশ্ন।
   ৪. বহুপদী সমাপ্তিসূচক প্রশ্ন (i, ii, iii দিয়ে 'নিচের কোনটি সঠিক' ধরনের)।
   ৫. অভিন্ন তথ্যভিত্তিক প্রশ্ন (উদ্দীপক পড়ে একাধিক প্রশ্নের উত্তর)।

* অন্তত ১ থেকে ২ টি অভিন্ন তথ্যভিত্তিক উদ্দীপক অবশ্যই 'চিত্রভিত্তিক' (Diagram/Image based) হতে হবে। (যেহেতু তুমি টেক্সট এআই, তাই HTML/CSS ব্যবহার করে ছক, গ্রাফ, বা সাধারণ জ্যামিতিক চিত্র এঁকে দেবে অথবা টেক্সট বক্সের ভেতর পরিষ্কারভাবে চিত্রের বর্ণনা দিয়ে দেবে)। 
*অন্তত একটি বহুপদী সমপ্তিসূচক প্রশ্ন অবশ্যই 'চিত্রভিত্তিক' (Diagram/Image based) হতে হবে। (যেহেতু তুমি টেক্সট এআই, তাই HTML/CSS ব্যবহার করে ছক, গ্রাফ, বা সাধারণ জ্যামিতিক চিত্র এঁকে দেবে অথবা টেক্সট বক্সের ভেতর পরিষ্কারভাবে চিত্রের বর্ণনা দিয়ে দেবে)। 
 * প্রশ্নের মান হবে সৃজনশীল এবং চিন্তামূলক, যা শিক্ষার্থীদের দক্ষতা যাচাই করতে পারে। 
* বিজ্ঞানের গাণিতিক সমীকরণের জন্য সাধারণ HTML ট্যাগ (<sub>, <sup>) ব্যবহার করবে।
 * শুধুমাত্র প্রফেশনাল HTML কোড দিবে।
* পৃথক পৃষ্ঠায় শিক্ষকদের মূল্যায়নের সুবিধার্থে একটি উত্তরমালা (Answer Key) যুক্ত করবে এবং উত্তরের সপক্ষে ব্যাখ্যাও যুক্ত করবে।
সব শর্ত মেনে একটি প্রফেশনাল পিডিএফ (PDF) ফাইল তৈরি করে দাও।"
     """

    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    
    html = response.json()['candidates'][0]['content']['parts'][0]['text']
    return html.replace("```html", "").replace("```", "").strip()

@app.post("/generate-pdf")
async def generate_pdf(data: dict):
    # ডাটা ইনপুট উদাহরণ: {"institute": "ঢাকা কলেজ", "exam": "অর্ধবার্ষিকী '২০২৬", "class": "দশম", ...}
    html_content = get_gemini_content(data)
    
    # প্রফেশনাল CSS (ডাবল কলাম এবং বাংলা ফন্ট সাপোর্ট)
    css = CSS(string='''
        @page { size: A4; margin: 1cm; }
        body { font-family: 'Kalpurush', sans-serif; font-size: 11pt; }
        .column-container { column-count: 2; column-gap: 30px; }
        .diagram-box { border: 2px solid #333; padding: 10px; margin: 10px 0; background: #fdfdfd; text-align: center; }
        .answer-key { page-break-before: always; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        td, th { border: 1px solid #000; padding: 6px; text-align: center; }
        h1, h2 { text-align: center; }
    ''', font_config=font_config)

    # HTML র‍্যাপার
    full_html = f'<div class="column-container">{html_content}</div>'
    
    pdf = HTML(string=full_html, base_url=os.getcwd()).write_pdf(
        stylesheets=[css], font_config=font_config
    )

    return Response(content=pdf, media_type="application/pdf")