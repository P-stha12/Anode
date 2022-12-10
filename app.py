from setup import get_chat_response , login , rollback_conversation, refresh_session, config
from revChatGPT.revChatGPT import Chatbot
import streamlit as st
import textwrap
from fpdf import FPDF
import replicate
import os
from PyPDF2 import PdfReader

os.environ["REPLICATE_API_TOKEN"] = "b3ea4715f5e3450de2093c2c82fd224208a069e3"




class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Calculate width of title and position
        w = self.get_string_width(title) + 6
        self.set_x((210 - w) / 2)
        # Colors of frame, background and text
        # Thickness of frame (1 mm)
        self.set_line_width(1)
        # Title
        self.cell(w, 9, title, 1, 1, 'C', 1)
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Text color in gray
        self.set_text_color(128)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def chapter_title(self, num, label):
        # Arial 12
        self.set_font('Arial', '', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, 'Chapter %d : %s' % (num, label), 0, 1, 'L', 1)
        # Line break
        self.ln(4)

    def chapter_body(self, name):
        # Read text file
        with open(name, 'rb') as fh:
            txt = fh.read().decode('latin-1')
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        self.multi_cell(0, 5, txt)
        # Line break
        self.ln()
        # Mention in italics
        self.set_font('', 'I')
        self.cell(0, 5, '(end of excerpt)')

    def print_chapter(self, num, title, name):
        self.add_page()
        self.chapter_title(num, title)
        self.chapter_body(name)

pdf = PDF()


chatbot = Chatbot(config, conversation_id=None)


st.title('BookAI')
st.image("https://imageio.forbes.com/blogs-images/bernardmarr/files/2019/03/AdobeStock_235115918-1200x800.jpeg?format=jpg&width=1200")


# title
title = st.text_input('Title of the book')
author = st.text_input('Author of the book')

# Stable Diffusion
model = replicate.models.get("stability-ai/stable-diffusion")
version = model.versions.get("27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478")



#Cover page image
if st.button('Get Cover Image'):
    output= version.predict(prompt=f"Minima book Illustration, ({title}), (story of {title})", width = 704, height = 1024)
    st.image(output, caption='Cover Page')

    pdf.add_page()
    pdf.image(output[0])


# Number of chapters
chapters = st.number_input('Enter Number of chapters.', min_value=1, max_value=100, value=5, step=1)

if st.button('Get PDF'):
    st.write('Processing')

    text = []
    response = chatbot.get_chat_response( f"Now, we begin to write a novel. I'll give you the chapter number. Please generate a coherent story with the title {title}. Each chapter is 250 words long. Let's start with chapter 1:", output="text")
    text.append(response['message'])

    for i in range(2,chapters+1):
        response = chatbot.get_chat_response( f"Chapter {i}", output="text")
        text.append(response['message'])

    print(text)
    # Text to TXT
    for i in range(0, chapters):
        with open (f'chapter{i+1}.txt', 'w') as file:  
            file.write(text[i])  



    pdf.set_title(title)
    pdf.set_author(author)
    for i in range(1, chapters+1):
        pdf.print_chapter(i, f"Chapter {i}", f'chapter{i}.txt')

    pdf.output('dummy.pdf', 'F')

    # Download Button
    with open("dummy.pdf", "rb") as file:
        btn=st.download_button(
        label="⬇️ Download PDF",
        data=file,
        file_name="mybook.pdf",
        mime="application/octet-stream"
    )



if st.button('Get Audio Book'):
    # pdf to audio
    audio_model = replicate.models.get("afiaka87/tortoise-tts")
    audio_version = audio_model.versions.get("e9658de4b325863c4fcdc12d94bb7c9b54cbfe351b7ca1b36860008172b91c71")
    reader = PdfReader("dummy.pdf")
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n" 
    output = audio_version.predict(text=text)
    st.audio(output, format='audio/ogg')
