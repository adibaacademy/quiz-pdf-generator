import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import requests

app = FastAPI()
font_config = FontConfiguration()

def get_gemini_content(data):
    prompt = f"""তুমি একজন প্রফেশনাল HTML কোডার এবং প্রশ্নকর্তা। নিচের তথ্যগুলো ব্যবহার করে একটি ডাবল-কলাম A4 সাইজের MCQ প্রশ্নপত্রের শুধুমাত্র <body> অংশের ভিতরের HTML কোড তৈরি করো। 

    সতর্কতা (Failure is not an option - কঠোরভাবে পালনীয়):
    ১. কোনোভাবেই তোমার নিজের সম্পর্কে কোনো কথা বা ব্যাখ্যামূলক কোনো শব্দ আউটপুটে লিখবে না। সরাসরি HTML ট্যাগ দিয়ে শুরু করবে।
    ২. গাণিতিক সমীকরণ, একক, বা বিজ্ঞানের মাত্রা (Dimension - যেমন: [MLT-2]) লেখার জন্য কোনো অবস্থাতেই $, $$, বা LaTeX কোড ব্যবহার করবে না। সমীকরণের জন্য শুধুমাত্র সাধারণ টেক্সট এবং HTML-এর <sub> ও <sup> ট্যাগ ব্যবহার করবে।
    ৩. প্রশ্নের নম্বর অবশ্যই ১ থেকে শুরু করে সঠিক সিরিয়ালে থাকবে।
    ৪. চিত্র বা গ্রাফ বোঝাতে কোনো ব্র্যাকেট [ ] ব্যবহার করবে না। HTML <table> বা CSS border-যুক্ত <div> ব্যবহার করে পরিষ্কার বাংলায় চিত্রের বর্ণনা লিখবে।
    ৫. আউটপুটটি শুধুমাত্র একটি প্রফেশনাল HTML কোড হবে, কোনো মার্কডাউন (```html) ব্যবহার করবে না।

    তথ্যসমূহ:
    ১. প্রতিষ্ঠান: {data.get('institute')}
    ২. পরীক্ষা: {data.get('exam')}
    ৩. শ্রেণি: {data.get('class')}
    ৪. বিষয়: {data.get('subject')}
    ৫. বিষয় কোড: {data.get('code')}
    ৬. অধ্যায়: {data.get('chapters')}
    ৭. প্রশ্ন: {data.get('q_count')}টি
    ৮. সময়: {data.get('time')}
    ৯. পূর্ণমান: {data.get('marks')}

    NCTB কাঠামো অনুসরণ করে জ্ঞানমূলক, অনুধাবনমূলক, প্রয়োগমূলক, সাধারণ বহুনির্বাচনি, বহুপদী সমাপ্তিসূচক এবং অভিন্ন তথ্যভিত্তিক প্রশ্ন রাখবে। প্রশ্নপত্রের শেষে পৃথক পৃষ্ঠায় উত্তরমালা ও ব্যাখ্যা যুক্ত করবে।
    """

    api_key = os.getenv("GEMINI_API_KEY")
    url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=){api_key}"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    
    html = response.json()['candidates'][0]['content']['parts'][0]['text']
    return html.replace("```html", "").replace("```", "").strip()

@app.post("/generate-pdf")
async def generate_pdf(data: dict):
    html_content = get_gemini_content(data)
    
    # ফন্টের লোকেশনটি ডাইনামিক এবং অ্যাবসলুট করা হলো যাতে লিনাক্স সার্ভার সহজেই খুঁজে পায়
    font_path = "file://" + os.path.abspath("fonts/Kalpurush.ttf").replace("\\", "/")
    
    css = CSS(string=f'''
        @font-face {{
            font-family: 'Kalpurush';
            src: url('{font_path}');
        }}
        @page {{ size: A4; margin: 1cm; }}
        body {{ font-family: 'Kalpurush', sans-serif; font-size: 11pt; }}
        .column-container {{ column-count: 2; column-gap: 30px; }}
        .diagram-box {{ border: 2px solid #333; padding: 10px; margin: 10px 0; background: #fdfdfd; text-align: center; }}
        .answer-key {{ page-break-before: always; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        td, th {{ border: 1px solid #000; padding: 6px; text-align: center; }}
        h1, h2 {{ text-align: center; }}
    ''', font_config=font_config)

    full_html = f'<div class="column-container">{html_content}</div>'
    
    pdf = HTML(string=full_html, base_url=os.getcwd()).write_pdf(
        stylesheets=[css], font_config=font_config
    )

    return Response(content=pdf, media_type="application/pdf")