from setup import get_chat_response , login , rollback_conversation, refresh_session, config
from pdf import PDF
from revChatGPT.revChatGPT import Chatbot
import streamlit as st
import textwrap
import replicate
import os
from PyPDF2 import PdfMerger
import io
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


 

# Environment Variable for Replicate
os.environ["REPLICATE_API_TOKEN"] = "b3ea4715f5e3450de2093c2c82fd224208a069e3"

stability_api = client.StabilityInference(
    key='sk-fnorOAW5VL6WZElXjkFrKiCBolm0oJYAKky2obn9sqjkqyq4', 
    verbose=True,
)

# PDF Object
pdf = PDF()
cover_pdf = PDF()

chatbot = Chatbot(config, conversation_id=None)


st.title('BookAI')
st.image("https://imageio.forbes.com/blogs-images/bernardmarr/files/2019/03/AdobeStock_235115918-1200x800.jpeg?format=jpg&width=1200")


# Text Boxes
title = st.text_input('Title of the book')
author = st.text_input('Author of the book')

# Stable Diffusion
model_id = "stabilityai/stable-diffusion-2-1"



#Cover page image
if st.button('Get Cover Image'):
    
    
    answers = stability_api.generate(
        prompt= f"Minima book Illustration, ({title}), (story of {title})",
        width=768, # Generation width, defaults to 512 if not included.
        height=1088,
    )
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                img_name = str(artifact.seed)+ ".png"
                img.save(img_name)
                image = Image.open(img_name)
                
                # Custom font style and font size
                title_font = ImageFont.truetype('playfair/playfair-font.ttf', 50)
                title_text = f"{title}"
                image_editable = ImageDraw.Draw(image)
                image_editable.text((15,15), title_text, (237, 230, 211), font=title_font)
                image.save("cover.jpg")
                cover_pdf.add_page()
                cover_pdf.image("cover.jpg")

                cover_pdf.output('cover.pdf', 'F')
                st.image("cover.jpg")

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
    
    # Merge pdfs
    pdfs = ['cover.pdf', 'dummy.pdf']

    merger = PdfMerger()

    for pdf in pdfs:
        merger.append(pdf)

    merger.write("result.pdf")
    merger.close()

    # Download Button
    with open("result.pdf", "rb") as file:
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
