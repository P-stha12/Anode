import youtube_dl
#uploading audio
import requests

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
