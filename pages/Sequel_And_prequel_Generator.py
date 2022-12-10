from setup import get_chat_response , login , rollback_conversation, refresh_session, config
from pdf import PDF
import youtube_dl
import requests
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
import cohere



#function for getting transcription of audio from youtube video
def get_transcript(link):
    video_url = link
    video_info = youtube_dl.YoutubeDL().extract_info(url = video_url,download=False)
    options={
        'format':'bestaudio/best',
        'keepvideo':False,
        'outtmpl':"video.mp3",
    }

    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])
    token = "508792ff63d0478d8975224b345a32c4"
    filename = "video.mp3"
    
    def read_file(filename, chunk_size=5242880):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data

    #upload audio
    headers = {'authorization': token}
    response = requests.post('https://api.assemblyai.com/v2/upload',
                            headers=headers,
                            data=read_file(filename))

    #sending transcription request
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json = {
        "audio_url": response.json()['upload_url']
    }
    headers = {
        "authorization": token,
        "content-type": "application/json"
    }
    response = requests.post(endpoint, json=json, headers=headers)

    #get transcription
    endpoint = f"https://api.assemblyai.com/v2/transcript/{response.json()['id']}"
    headers = {
        "authorization": token,
    }

    while(response.json()['status'] != "completed"):
        response = requests.get(endpoint, headers=headers)

    text = response.json()['text']

    return text



# cohere api_key
co = cohere.Client("8XUN5KqdPmJOcrNEiI9kU9vjY8H4SWZIgqipfZlt")

 

# Environment Variable for Replicate
os.environ["REPLICATE_API_TOKEN"] = "b3ea4715f5e3450de2093c2c82fd224208a069e3"

stability_api = client.StabilityInference(
    key='sk-JdUA39qvtJ7rcsw4asLvVSPQMdGaha648nsbqZKIuMaGnJ4J', 
    verbose=True,
)

# PDF Object
pdf = PDF()
cover_pdf = PDF()
foreword_pdf = PDF()
summary_pdf = PDF()

chatbot = Chatbot(config, conversation_id=None)


st.title('Get Sequel/Prequel of your favourite Story')


# Text Boxes
link = st.text_input('Link to the video')
generate_video = st.checkbox('Generate Video')
if generate_video:
    story = get_transcript(link)
    st.text("Proceed to the next step")



preq_seq = st.selectbox(
    'Prequel or Sequel',
    ('Prequel', 'Sequel'))

generate_title = st.checkbox('Generate the title')
if generate_title:
    response = chatbot.get_chat_response( f'Generate a title for the following story: {story}', output="text")
    title = response['message']
    st.text(f"{title}")

author = "BookAI"

# Stable Diffusion
model_id = "stabilityai/stable-diffusion-2-1"


cover_pdf.add_page()
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
                W = 768
                title_font = ImageFont.truetype('playfair/playfair-font.ttf', 50)
                author_font = ImageFont.truetype('playfair/playfair-font.ttf', 20)
                title_text = f"{title}"
                if ':' in title_text:
                    temp = title_text.split(':')
                    title_text = temp[0] + '\n' + temp[1]
                image_editable = ImageDraw.Draw(image)
                w, h = image_editable.textsize(title)
                image_editable.text(((W-w)/3.7,25), title_text, (237, 230, 211), font=title_font)
                image_editable.text((630,1050), author, (237, 230, 211), font=author_font,align='left')
                image.save("cover.jpg")
                
                cover_pdf.image("cover.jpg",x=0, y=0, w= 210, h= 297)

                cover_pdf.output('cover.pdf', 'F')
                st.image("cover.jpg")

# Number of chapters
chapters = st.number_input('Enter Number of chapters.', min_value=1, max_value=100, value=5, step=1)

complete_text =''
## PDF Body
if st.button('Get PDF'):
    st.write('Processing')

    text = []
    response = chatbot.get_chat_response( f"Generate {chapters} chapter titles for the {preq_seq} of the story {title}", output="text")
    chaps= response['message'].rsplit("\n")
    

    for i in range(1,chapters+1):
        response = chatbot.get_chat_response( f"generate content for chapter {i}", output="text")
        text.append(response['message'])
        complete_text += text[0]

    # Text to TXT
    for i in range(0, chapters):
        with open (f'chapter{i+1}.txt', 'w') as file:  
            file.write(text[i])  
    


    pdf.set_title(title)
    pdf.set_author(author)
    for i in range(1, chapters+1):
        answers = stability_api.generate(
        prompt= f"Minimal Illustration, ({chaps[i-1][4:-1]}) (Van Gogh)",
        width=768, # Generation width, defaults to 512 if not included.
        height=384,
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
                
                title_font = ImageFont.load_default()
                title_text = f"{title}"
                image_editable = ImageDraw.Draw(image)
                image_editable.text((15,15), title_text, (237, 230, 211), font=title_font)
                image.save(f"{chaps[i-1][4:-1]}.jpg")
                
        
        pdf.print_chapter(i, f"{chaps[i-1][4:-1]}", f'chapter{i}.txt')
        pdf.image(f"{chaps[i-1][4:-1]}.jpg",x= 10, w=190, h = 80)
    pdf.output('dummy.pdf', 'F')
    
    #cohere text summarization
    #response = co.generate( 
    #model='xlarge', 
    #prompt = complete_text,
    #max_tokens=250, 
    #temperature=0.9)

    #summary = response.generations[0].text
    #pdf of summary
    #with open (f'about_{title}.txt', 'w') as file:  
    #        file.write(f"About {title}\n\n{summary}")
    #summary_pdf.print_chapter(i, f"About_{title}", f'about_{title}.txt')
    #summary_pdf.output(f'about_{title}.pdf', 'F')
    
    #Foreword generation
    foreword_response = chatbot.get_chat_response( f"write foreword for the book written by AI on the title {title}, 400 words", output="text")
    foreword = "FOREWORD\n\n\n\n" + foreword_response['message']
    with open (f'foreword.txt', 'w') as file:  
            file.write(foreword)
    foreword_pdf.print_chapter(i, f"Foreword", f'foreword.txt')
    foreword_pdf.output(f'foreword.pdf', 'F')

    # Merge pdfs
    pdfs = ['cover.pdf', 'foreword.pdf' ,'dummy.pdf']

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
        file_name="{title}.pdf",
        mime="application/octet-stream"
    )



##if st.button('Get Audio Book'):
##    # pdf to audio
##    audio_model = replicate.models.get("afiaka87/tortoise-tts")
##    audio_version = audio_model.versions.get("e9658de4b325863c4fcdc12d94bb7c9b54cbfe351b7ca1b36860008172b91c71")
##    reader = PdfReader("dummy.pdf")
##    text = ""
##    for page in reader.pages:
##        text += page.extract_text() + "\n" 
##    output = audio_version.predict(text=text)
##    st.audio(output, format='audio/ogg')