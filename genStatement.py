import openai
import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# PDF에서 텍스트 추출
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = []
        for page in pdf.pages:
            text = page.extract_text()
            full_text.append(text)
    return "\n".join(full_text)

def refine_text_with_form_gpt(transcript_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f" 1.당사자의 성명ㆍ명칭 또는 상호와 주소\n 2.대리인의 성명과 주소\n 3.사건의 표시\n 4.공격 또는 방어의 방법\n 5.상대방의 청구와 공격 또는 방어의 방법에 대한 진술\n 6.덧붙인 서류의 표시\n 7.작성한 날짜\n법원의 표시\n제4호 및 제5호의 사항에 대하여는 사실상 주장을 증명하기 위한 증거방법과 상대방의 증거방법에 대한 의견을 함께 적어야 한다. 이 내용을 바탕을 준비서면 써봐\n\n{transcript_text}"}
        ],
        max_tokens=1500,
        n=1,
        stop=None,
        temperature=0.7
    )
    return response.choices[0].message['content'].strip()

# 수정된 텍스트를 PDF로 저장
def save_text_to_pdf(text, output_path):
    pdfmetrics.registerFont(TTFont("맑은고딕", "malgun.ttf"))
    pdf = canvas.Canvas(output_path)
    pdf.setFont("맑은고딕", 12)
    
    margin = 40
    width, height = pdf._pagesize
    max_width = width - 2 * margin
    y_position = height - margin
    
    lines = text.split('\n')
    for line in lines:
        while pdf.stringWidth(line) > max_width:
            split_index = 0
            for i in range(len(line)):
                if pdf.stringWidth(line[:i]) > max_width:
                    split_index = i
                    break
            pdf.drawString(margin, y_position, line[:split_index])
            line = line[split_index:]
            y_position -= 14
            if y_position < margin:
                pdf.showPage()
                pdf.setFont("맑은고딕", 12)
                y_position = height - margin
        pdf.drawString(margin, y_position, line)
        y_position -= 14
        if y_position < margin:
            pdf.showPage()
            pdf.setFont("맑은고딕", 12)
            y_position = height - margin

    pdf.save()

# 메인 함수
def main():
    transcript_pdf_path = "example.pdf"
    output_pdf_path = "refined_transcript.pdf"

    # Step 2: transcript.pdf에서 텍스트 추출
    extracted_text = extract_text_from_pdf(transcript_pdf_path)
    print("Extracted Transcript Text:")
    print(extracted_text)

    # Step 3: 형식을 유지하며 AI를 통해 텍스트 수정
    refined_text = refine_text_with_form_gpt(extracted_text)
    print("Refined Text with Form:")
    print(refined_text)

    # Step 4: 수정된 텍스트를 새로운 PDF로 저장
    save_text_to_pdf(refined_text, output_pdf_path)
    print(f"Refined transcript saved to {output_pdf_path}")

if __name__ == "__main__":
    main()
