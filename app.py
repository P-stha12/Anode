from setup import get_chat_response , login , rollback_conversation, refresh_session, config
from revChatGPT.revChatGPT import Chatbot
import streamlit as st
from pdf import pdf
import textwrap
from fpdf import FPDF



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
pdf.alias_nb_pages()


chatbot = Chatbot(config, conversation_id=None)


st.title('BookAI')
st.image("https://imageio.forbes.com/blogs-images/bernardmarr/files/2019/03/AdobeStock_235115918-1200x800.jpeg?format=jpg&width=1200")


# title
title = st.text_input('Title of the book')
author = st.text_input('Author of the book')


chapters = st.number_input('Enter Number of chapters.', min_value=1, max_value=100, value=5, step=1)

if st.button('Get PDF'):
    st.write('Processing')

    text = []
    response = chatbot.get_chat_response( f"Now, we begin to write a novel. I'll give you the chapter number. Please generate a coherent story with the title {title}. Each chapter is 250 words long. Let's start with chapter 1:", output="text")
    text.append(response['message'])

    for i in range(2,chapters+2):
        response = chatbot.get_chat_response( f"Chapter {i}", output="text")
        text.append(response['message'])


    print(text)
    # Text to TXT
    for i in range(1, chapters+1):
        with open (f'chapter{i}.txt', 'w') as file:  
            for line_1 in text:  
                file.write(line_1)  



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
