from setup import get_chat_response , login , rollback_conversation, refresh_session, config
from revChatGPT.revChatGPT import Chatbot
import streamlit as st
from pdf import PDF
import textwrap
from fpdf import FPDF
import replicate
import os
from PyPDF2 import PdfReader

os.environ["REPLICATE_API_TOKEN"] = "b3ea4715f5e3450de2093c2c82fd224208a069e3"

audio_model = replicate.models.get("afiaka87/tortoise-tts")
audio_version = audio_model.versions.get("e9658de4b325863c4fcdc12d94bb7c9b54cbfe351b7ca1b36860008172b91c71")
reader = PdfReader("dummy.pdf")
text = ""
for page in reader.pages:
   text += page.extract_text() + "\n" 
output = audio_version.predict(text=text)
print(output)