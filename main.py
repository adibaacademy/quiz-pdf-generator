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
    ১. কোনোভাবেই তোমার নিজের সম্পর্কে কোনো কথা (যেমন: "আমি একটি প্রশ্নপত্র তৈরি করেছি...") বা ব্যাখ্যামূলক কোনো শব্দ আউটপুটে লিখবে না। সরাসরি <div>, <table> ইত্যাদি HTML ট্যাগ দিয়ে প্রশ্নপত্রের হেডিং থেকে শুরু করবে।
    ২. গাণিতিক সমীকরণ বা এককের জন্য কোনো অবস্থাতেই $ বা $$ বা LaTeX/MathJax কোড ব্যবহার করবে না। সমীকরণের জন্য শুধুমাত্র সাধারণ টেক্সট এবং HTML-এর <sub> ও <sup> ট্যাগ ব্যবহার করবে।
    ৩. প্রশ্নের নম্বর অবশ্যই ১ থেকে ৩০ পর্যন্ত সঠিক সিরিয়ালে থাকবে। কোনো অবস্থাতেই নম্বরের সিরিয়াল ভাঙা যাবে না।
    ৪. চিত্র বা গ্রাফ বোঝাতে কোনো ব্র্যাকেট [ ] বা অদ্ভুত টেক্সট ব্যবহার করবে না। সুন্দর করে HTML <table> বা CSS border-যুক্ত <div> ব্যবহার করে তার ভেতর পরিষ্কার বাংলায় চিত্রের বর্ণনা লিখবে।
    ৫. আউটপুটটি শুধুমাত্র একটি প্রফেশনাল HTML কোড হবে, কোনো মার্কডাউন (```html) ব্যবহার করবে না।

    তথ্যসমূহ:
    ১. প্রতিষ্ঠানের নাম: {data.get('institute')}
    ২. পরীক্ষার নাম: {data.get('exam')}
    ৩. শ্রেণি: {data.get('class')}
    ৪. বিষয়ের নাম: {data.get('subject')}
    ৫. বিষয় কোড: {data.get('code')}
    ৬. অধ্যায়সমূহ: {data.get('chapters')}
    ৭. প্রশ্ন: {data.get('q_count')}টি
    ৮. সময়: {data.get('time')}
    ৯. পূর্ণমান: {data.get('marks')}

    NCTB কাঠামো অনুসরণ করে জ্ঞানমূলক, অনুধাবনমূলক, প্রয়োগমূলক, সাধারণ বহুনির্বাচনি, বহুপদী সমাপ্তিসূচক এবং অভিন্ন তথ্যভিত্তিক প্রশ্ন রাখবে। প্রশ্নপত্রের শেষে পৃথক পৃষ্ঠায় উত্তরমালা ও ব্যাখ্যা যুক্ত করবে।
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