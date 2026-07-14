import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import requests
import traceback

app = FastAPI()
font_config = FontConfiguration()

def get_gemini_content(data):
    prompt = f"""তুমি একজন প্রফেশনাল HTML কোডার। নিচের তথ্যগুলো দিয়ে একটি A4 সাইজের ডাবল-কলাম MCQ প্রশ্নপত্রের HTML (শুধুমাত্র <body> এর ভেতরের অংশ) তৈরি করো। 

    নির্দেশাবলি:
    ১. কোনো অবস্থাতেই $,$$, বা LaTeX/MathJax কোড ব্যবহার করবে না। সমীকরণের জন্য শুধু সাধারণ টেক্সট এবং HTML এর <sub>, <sup> ট্যাগ ব্যবহার করবে।
    ২. প্রশ্নের নম্বর ১ থেকে {data.get('q_count')} পর্যন্ত সঠিক সিরিয়ালে থাকবে।
    ৩. চিত্র বা গ্রাফের জন্য কোনো ব্র্যাকেট বা অদ্ভুত টেক্সট আর্ট ব্যবহার করবে না। HTML <table> বা CSS border-যুক্ত <div> দিয়ে বক্স তৈরি করে তার ভেতর পরিষ্কার বাংলায় বর্ণনা লিখবে।
    ৪. কোনো ব্যাখ্যামূলক টেক্সট বা ```html ট্যাগ দিবে না। সরাসরি HTML কোড দিবে।

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
    """

    api_key = os.getenv("GEMINI_API_KEY")
    url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=){api_key}"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Gemini API Error: {response.text}")
        
    response_data = response.json()
    if 'candidates' not in response_data:
        raise Exception(f"Invalid API response: {response_data}")
        
    html = response_data['candidates'][0]['content']['parts'][0]['text']
    return html.replace("```html", "").replace("```", "").replace("$", "").replace("\\", "").strip()

@app.post("/generate-pdf")
async def generate_pdf(data: dict):
    try:
        html_content = get_gemini_content(data)
        
        # এখানে ফন্টের লিংকটি একদম পরিষ্কার করে দেওয়া হয়েছে, কোনো ব্র্যাকেট নেই
        css = CSS(string='''
            @import url('[https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;600;700&display=swap](https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;600;700&display=swap)');
            
            @page { size: A4; margin: 1cm; }
            body { font-family: 'Noto Sans Bengali', sans-serif; font-size: 11pt; }
            .column-container { column-count: 2; column-gap: 30px; }
            .diagram-box { border: 2px solid #333; padding: 10px; margin: 10px 0; background: #fdfdfd; text-align: center; }
            .answer-key { page-break-before: always; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            td, th { border: 1px solid #000; padding: 6px; text-align: center; }
            h1, h2 { text-align: center; }
        ''', font_config=font_config)

        full_html = f'<div class="column-container">{html_content}</div>'
        pdf = HTML(string=full_html).write_pdf(stylesheets=[css], font_config=font_config)

        return Response(content=pdf, media_type="application/pdf")
        
    except Exception as e:
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=str(e))
