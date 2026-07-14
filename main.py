import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import requests
import traceback
import re

app = FastAPI()
font_config = FontConfiguration()

def get_gemini_content(data):
    # প্রম্পটে অত্যন্ত কঠোর নির্দেশ দেওয়া হয়েছে
    prompt = f"""তুমি একজন প্রফেশনাল HTML/CSS ডেভেলপার। 
    
    **অত্যন্ত জরুরি নির্দেশাবলি (অবশ্যই মানতে হবে):**
    ১. কোনো অবস্থাতেই প্রশ্নের আগে 'সঠিক উত্তরটি চিহ্নিত করুন:' বা 'সঠিক উত্তরটি চিহ্নিত করুন' বা এই জাতীয় কোনো কথা লিখবে না। সরাসরি প্রশ্ন নম্বর দিয়ে শুরু করবে (যেমন: ১. কোনো গোলকের...)।
    ২. কোনো অবস্থাতেই $,$$, বা LaTeX/MathJax কোড ব্যবহার করবে না। সমীকরণের জন্য HTML এর <sub>, <sup> ট্যাগ ব্যবহার করবে।
    ৩. সরাসরি HTML কোড দিবে, কোনো ```html ট্যাগ বা ব্যাখ্যামূলক টেক্সট দিবে না।
    
    HTML এর গঠন (অবশ্যই হুবহু এই স্ট্রাকচার ফলো করবে):
    <div class="header">
       <div class="top-row">
           <span>সময়ঃ {data.get('time')}</span>
           <span>পূর্ণমানঃ {data.get('marks')}</span>
       </div>
       <h1>{data.get('institute')}</h1>
       <p class="address">{data.get('address', 'আটোয়ারী, পঞ্চগড়')}</p>
       <h2>{data.get('class')} শ্রেণির {data.get('exam')}</h2>
       <h3>বিষয়ঃ {data.get('subject')}</h3>
    </div>
    
    <div class="instruction">
       [দ্রষ্টব্যঃ প্রশ্নপত্রে কোন প্রকার দাগ/চিহ্ন দেওয়া যাবে না। সরবরাহকৃত বহু নির্বাচনী অভীক্ষার উত্তরপত্রের ক্রমিক নম্বরের বিপরীতে প্রদত্ত বর্ণ সম্বলিত বৃত্ত সমূহ হতে সঠিক/ সর্বোৎকৃষ্ট উত্তরের বৃত্তটি বল পয়েন্ট কলম দ্বারা সম্পূর্ণ ভরাট কর। প্রতিটি প্রশ্নের মান ১]
    </div>
    
    <div class="questions-container">
       <div class="question">
          <p><b>১. [সরাসরি প্রশ্ন হবে, কোনো বাড়তি কথা নয়]</b></p>
          <div class="options">
             <span>(ক) [অপশন ১]</span>
             <span>(খ) [অপশন ২]</span><br>
             <span>(গ) [অপশন ৩]</span>
             <span>(ঘ) [অপশন ৪]</span>
          </div>
       </div>
       <!-- এভাবে বাকি প্রশ্নগুলো দিবে -->
    </div>
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
    
    # পাইথন ফিল্টার: এআই যদি ভুল করেও অপ্রয়োজনীয় টেক্সট দেয়, পাইথন তা মুছে ফেলবে
    clean_html = html.replace("```html", "").replace("```", "").replace("$", "").replace("\\", "")
    clean_html = re.sub(r'<p>.*?সঠিক উত্তরটি চিহ্নিত করুন.*?</p>', '', clean_html)
    clean_html = clean_html.replace("সঠিক উত্তরটি চিহ্নিত করুন:", "").replace("সঠিক উত্তরটি চিহ্নিত করুন", "")
    
    return clean_html.strip()

@app.post("/generate-pdf")
async def generate_pdf(data: dict):
    try:
        html_content = get_gemini_content(data)
        
        # PhysicsMCQ মডেল অনুযায়ী পারফেক্ট CSS
        css = CSS(string='''
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;600;700&display=swap');
            
            @page { 
                size: A4; 
                margin: 1.2cm 1.5cm 1.5cm 1.5cm; 
                @bottom-center {
                    content: "পৃষ্ঠা " counter(page);
                    font-family: 'Noto Sans Bengali', sans-serif;
                    font-size: 10pt;
                }
            }
            body { 
                font-family: 'Noto Sans Bengali', sans-serif; 
                font-size: 11pt; 
                color: #000;
            }
            .header { text-align: center; margin-bottom: 15px; }
            .top-row { display: flex; justify-content: space-between; font-weight: bold; font-size: 11pt; margin-bottom: -10px; }
            .header h1 { margin: 5px 0 0 0; font-size: 16pt; font-weight: bold; }
            .header p.address { margin: 0; font-size: 11pt; }
            .header h2 { margin: 5px 0; font-size: 13pt; font-weight: bold; }
            .header h3 { margin: 0; font-size: 12pt; font-weight: bold; }
            
            .instruction { 
                text-align: justify; 
                font-size: 10pt; 
                margin-bottom: 15px; 
                line-height: 1.4; 
            }
            
            .questions-container { 
                column-count: 2; 
                column-gap: 35px; 
            }
            .question {
                break-inside: avoid;
                margin-bottom: 12px;
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
                font-size: 10.5pt;
            }
            .uddipak {
                border: 1px solid #333;
                padding: 6px;
                margin: 12px 0;
                text-align: justify;
                font-size: 10.5pt;
                background-color: #fafafa;
                break-inside: avoid;
            }
        ''', font_config=font_config)

        full_html = f'<div>{html_content}</div>'
        pdf = HTML(string=full_html).write_pdf(stylesheets=[css], font_config=font_config)

        return Response(content=pdf, media_type="application/pdf")
        
    except Exception as e:
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=str(e))
