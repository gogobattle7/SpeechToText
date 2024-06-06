import os
import torch
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize
from pyannote.audio import Pipeline
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


# Hugging Face 토큰
hf_auth_token = os.getenv("HF_AUTH_TOKEN")


# Pyannote 화자 분할 파이프라인 초기화 (프리트레인된 모델 사용)
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=hf_auth_token
)

# m4a 파일을 wav 파일로 변환
audio = AudioSegment.from_file("sample.m4a", format="m4a")
audio = normalize(audio)  # 볼륨 정규화
audio.export("converted_audio.wav", format="wav")

# 화자 분할 수행
diarization = pipeline("converted_audio.wav")

# 음성 파일 전체를 로드
audio = AudioSegment.from_wav("converted_audio.wav")
recognizer = sr.Recognizer()

# 시간 순서대로 화자별 텍스트 저장을 위한 리스트
transcript_segments = []

# 화자별로 음성 인식 수행
for turn, _, speaker in diarization.itertracks(yield_label=True):
    start_time = turn.start * 1000  # 시작 시간 (밀리초)
    end_time = turn.end * 1000  # 종료 시간 (밀리초)
    segment = audio[start_time:end_time]  # 화자 구간 추출
    segment = normalize(segment)  # 각 세그먼트의 볼륨 정규화
    segment.export("segment.wav", format="wav")
    
    with sr.AudioFile("segment.wav") as source:
        audio_listened = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_listened, language="ko-KR")
            transcript_segments.append((speaker, text))
        except sr.UnknownValueError:
            print(f"Segment from {start_time} to {end_time} could not be understood")

# PDF로 변환된 텍스트 저장
def save_transcript_to_pdf(transcript_segments, output_path):
    pdfmetrics.registerFont(TTFont("맑은고딕", "malgun.ttf"))  # 폰트 등록
    pdf = canvas.Canvas(output_path)
    pdf.setFont("맑은고딕", 12)
    
    # 페이지 마진 설정
    margin = 40
    width, height = pdf._pagesize
    max_width = width - 2 * margin
    y_position = height - margin
    
    for speaker, text in transcript_segments:
        lines = text.split('\n')
        pdf.drawString(margin, y_position, f"Speaker {speaker}:")
        y_position -= 14

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
        y_position -= 14
        if y_position < margin:
            pdf.showPage()
            pdf.setFont("맑은고딕", 12)
            y_position = height - margin

    pdf.save()

# 변환된 텍스트를 PDF로 저장
save_transcript_to_pdf(transcript_segments, "transcript.pdf")
print("Transcript saved to transcript.pdf")