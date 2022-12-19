import uuid
import zipfile

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

from bugs_generator.bugs_generation import BugGenerator

app = FastAPI()


@app.get("/main")
async def root():
    with open("templates/main.html") as file:
        html_content = file.read()

    response = HTMLResponse(content=html_content)
    response.charset = "UTF-8"
    return response


@app.get("/api/v1/generate_images")
async def generate_images(count: int):
    generator = BugGenerator("Example.svg")
    for i in range(count):
        generator.regenerateBug()
        generator.exportToPNG(f"bug_{i}.png")
    file_path = 'reportDir' + str(uuid.uuid4()) + '.zip'
    with zipfile.ZipFile(file_path, 'w') as myzip:
        for i in range(count):
            myzip.write(f"bug_{i}.png")
    return FileResponse(path=file_path, media_type='application/octet-stream', filename=file_path)


@app.get("/api/v1/generate_one_image")
async def generate_one_image():
    with open("Example.svg") as img:
        text = img.read()
    return PlainTextResponse(content=text)
