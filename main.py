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
    # প্রম্পটে একদম হুবহু PhysicsMCQ.pdf এর মডেল ফলো করার নির্দেশ দেওয়া হয়েছে
    prompt = f"""তুমি একজন প্রফেশনাল HTML/CSS ডেভেলপার। সংযুক্ত মডেল প্রশ্নপত্রের হুবহু ডিজাইনে একটি MCQ প্রশ্নপত্রের সম্পূর্ণ HTML কোড (শুধুমাত্র <body> এর ভেতরের অংশ) তৈরি করো। 

    নির্দেশাবলি:
    ১. কোনো অবস্থাতেই $,$$, বা LaTeX/MathJax কোড ব্যবহার করবে না। সমীকরণের জন্য HTML এর <sub>, <sup> ট্যাগ ব্যবহার করবে।
    ২. நேரடியாக HTML কোড দিবে, কোনো ```html ট্যাগ বা ব্যাখ্যামূলক টেক্সট দিবে না।
    
    HTML এর গঠন (অবশ্যই হুবহু এই স্ট্রাকচার ফলো করবে):
    <div class="header" style="position: relative; text-align: center; margin-bottom: 10px;">
       <div style="position: absolute; left: 0; top: 0; font-weight: bold;">সময়ঃ {data.get('time')}</div>
       <div style="position: absolute; right: 0; top: 0; font-weight: bold;">পূর্ণমানঃ {data.get('marks')}</div>
       <h1 style="margin: 0; font-size: 18pt; font-weight: bold;">{data.get('institute')}</h1>
       <p style="margin: 2px 0; font-size: 12pt;">{data.get('address', 'আটোয়ারী, পঞ্চগড়')}</p>
       <h2 style="margin: 5px 0 2px 0; font-size: 14pt; font-weight: 600;">{data.get('class')} শ্রেণির {data.get('exam')}</h2>
       <h3 style="margin: 3px 0; font-size: 13pt;">বিষয়ঃ {data.get('subject')}</h3>
    </div>
    
    <p class="instruction" style="text-align: justify; font-size: 10.5pt; margin-bottom: 15px;">
       [দ্রষ্টব্যঃ প্রশ্নপত্রে কোন প্রকার দাগ/চিহ্ন দেওয়া যাবে না। সরবরাহকৃত বহু নির্বাচনী অভীক্ষার উত্তরপত্রের ক্রমিক নম্বরের বিপরীতে প্রদত্ত বর্ণ সম্বলিত বৃত্ত সমূহ হতে সঠিক/ সর্বোৎকৃষ্ট উত্তরের বৃত্তটি বল পয়েন্ট কলম দ্বারা সম্পূর্ণ ভরাট কর। প্রতিটি প্রশ্নের মান ১]
    </p>
    
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
       <!-- উদ্দীপক থাকলে <div class="uddipak">...</div> ব্যবহার করবে -->
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
    return html.replace("```html", "").replace("```", "").replace("$", "").replace("\\", "").strip()

@app.post("/generate-pdf")
async def generate_pdf(data: dict):
    try:
        html_content = get_gemini_content(data)
        
        # CSS এ পেজ নম্বর (পৃষ্ঠা 1, পৃষ্ঠা 2) এবং অন্যান্য স্টাইলিং যুক্ত করা হয়েছে
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
