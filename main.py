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
    # প্রম্পটে শিরোনাম এবং প্রশ্নের জন্য আলাদা সেকশন করার কঠোর নির্দেশ দেওয়া হয়েছে
    prompt = f"""তুমি একজন প্রফেশনাল HTML/CSS ডেভেলপার। বাংলাদেশের বোর্ড পরীক্ষার (যেমন SSC/HSC) প্রশ্নপত্রের হুবহু ডিজাইনে একটি MCQ প্রশ্নপত্রের সম্পূর্ণ HTML কোড (শুধুমাত্র <body> এর ভেতরের অংশ) তৈরি করো। 

    নির্দেশাবলি:
    ১. প্রথমে একটি <div class="header"> তৈরি করবে, যেখানে প্রতিষ্ঠানের নাম, পরীক্ষার নাম, বিষয়, সময়, পূর্ণমান ইত্যাদি থাকবে। এটি এক কলামে থাকবে।
    ২. এরপর <div class="questions-container"> তৈরি করবে, যার ভেতরে ১ থেকে {data.get('q_count')} পর্যন্ত সবগুলো বহুনির্বাচনি প্রশ্ন থাকবে। এটি দুই কলামে রেন্ডার হবে।
    ৩. প্রশ্নের ৪টি অপশন (ক, খ, গ, ঘ) সুন্দরভাবে সাজানো থাকবে। 
    ৪. কোনো অবস্থাতেই $,$$, বা LaTeX/MathJax কোড ব্যবহার করবে না। সমীকরণের জন্য HTML এর <sub>, <sup> ট্যাগ ব্যবহার করবে।
    ৫. সরাসরি HTML কোড দিবে, কোনো ```html ট্যাগ বা ব্যাখ্যামূলক টেক্সট দিবে না।

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
    
    HTML এর গঠন (অবশ্যই হুবহু এই স্ট্রাকচার ফলো করবে):
    <div class="header">
       <h1>{data.get('institute')}</h1>
       <h2>{data.get('exam')}</h2>
       <p>শ্রেণি: {data.get('class')} | বিষয়: {data.get('subject')} | অধ্যায়: {data.get('chapters')}</p>
       <div class="meta">
          <span>সময়: {data.get('time')}</span>
          <span>বিষয় কোড: <b>{data.get('code')}</b></span>
          <span>পূর্ণমান: {data.get('marks')}</span>
       </div>
       <p class="instruction">[সকল প্রশ্নের উত্তর দাও। প্রতিটি প্রশ্নের মান ১। প্রতিটি প্রশ্নের চারটি বিকল্প উত্তরের মধ্যে সঠিক উত্তরটি চিহ্নিত করো।]</p>
    </div>
    
    <div class="questions-container">
       <!-- প্রশ্নগুলো এখানে আসবে -->
       <div class="question">
          <p><b>১. [প্রশ্ন]</b></p>
          <div class="options">
             <span>(ক) [অপশন ১]</span>
             <span>(খ) [অপশন ২]</span><br>
             <span>(গ) [অপশন ৩]</span>
             <span>(ঘ) [অপশন ৪]</span>
          </div>
       </div>
       <!-- এভাবে বাকি প্রশ্নগুলো দিবে -->
    </div>
    
    <div class="footer">সর্বস্বত্ব সংরক্ষিত।</div>
    """

    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-latest:generateContent?key={api_key}"
    
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
        
        # CSS এ শুধুমাত্র questions-container কে দুই কলামে ভাগ করা হয়েছে
        css = CSS(string='''
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;600;700&display=swap');
            
            @page { 
                size: A4; 
                margin: 1.2cm 1.5cm; 
            }
            body { 
                font-family: 'Noto Sans Bengali', sans-serif; 
                font-size: 11.5pt; 
                color: #000;
            }
            .header {
                text-align: center;
                margin-bottom: 15px;
                /* হেডার এক কলামে থাকবে, তাই এখানে column-count দেওয়া হয়নি */
            }
            .header h1 { margin: 0; font-size: 18pt; font-weight: bold; }
            .header h2 { margin: 5px 0; font-size: 14pt; font-weight: 600; }
            .header p { margin: 3px 0; font-size: 12pt; }
            .header .meta {
                display: flex;
                justify-content: space-between;
                border-bottom: 2px solid #000;
                padding-bottom: 5px;
                margin-top: 10px;
                font-weight: bold;
                font-size: 12pt;
            }
            .instruction {
                text-align: left;
                font-size: 11pt;
                margin-top: 8px;
            }
            .questions-container { 
                column-count: 2; /* প্রশ্নগুলো দুই কলামে ভাগ করা হয়েছে */
                column-gap: 40px; 
            }
            .question {
                break-inside: avoid; /* প্রশ্ন যেন অর্ধেক এক পেজে, অর্ধেক অন্য পেজে না ভাঙে */
                margin-bottom: 15px;
            }
            .question p {
                margin: 0 0 5px 0;
                line-height: 1.3;
            }
            .options span {
                display: inline-block;
                width: 48%;
                vertical-align: top;
                margin-bottom: 3px;
                font-size: 11pt;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                font-size: 11pt;
                font-weight: bold;
                column-span: all;
            }
        ''', font_config=font_config)

        full_html = f'<div>{html_content}</div>'
        pdf = HTML(string=full_html).write_pdf(stylesheets=[css], font_config=font_config)

        return Response(content=pdf, media_type="application/pdf")
        
    except Exception as e:
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=str(e))
