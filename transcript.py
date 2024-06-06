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

# AI를 통해 텍스트 수정 (폼 형식 유지)
def refine_text_with_form_gpt(form_text, transcript_text):
    formatted_text = f"형식:\n{form_text}\n\n대화:\n{transcript_text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"다음 대화를 형식을 참고하여 날짜를 명시하고, pdf의 끝을 언급하며 자연스럽고 어법에 맞게 수정해 주세요:\n\n{formatted_text}"}
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
    transcript_pdf_path = "transcript.pdf"
    form_pdf_path = "form.pdf"
    output_pdf_path = "refined_transcript.pdf"

    # Step 1: form.pdf에서 형식화된 텍스트 추출
    form_text = extract_text_from_pdf(form_pdf_path)
    print("Extracted Form Text:")
    print(form_text)

    # Step 2: transcript.pdf에서 텍스트 추출
    extracted_text = extract_text_from_pdf(transcript_pdf_path)
    print("Extracted Transcript Text:")
    print(extracted_text)

    # Step 3: 형식을 유지하며 AI를 통해 텍스트 수정
    refined_text = refine_text_with_form_gpt(form_text, extracted_text)
    print("Refined Text with Form:")
    print(refined_text)

    # Step 4: 수정된 텍스트를 새로운 PDF로 저장
    save_text_to_pdf(refined_text, output_pdf_path)
    print(f"Refined transcript saved to {output_pdf_path}")

if __name__ == "__main__":
    main()
