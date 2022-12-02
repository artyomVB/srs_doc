import uuid
import zipfile

from fastapi import FastAPI
from fastapi.responses import FileResponse

from bugs_generator.bugs_generation import generateRandomBug

app = FastAPI()


@app.get("/api/v1/generate_images")
async def root(count: int):
    for i in range(count):
        generateRandomBug("Example.svg", f"bug_{i}.png")
    file_path = 'reportDir' + str(uuid.uuid4()) + '.zip'
    with zipfile.ZipFile(file_path, 'w') as myzip:
        for i in range(count):
            myzip.write(f"bug_{i}.png")
    return FileResponse(path=file_path, media_type='application/octet-stream', filename=file_path)

