from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import FileResponse, JSONResponse
from defs import generate_file_name
from const.files_const import *
from models.files_db import *
from typing import List
import json


router = APIRouter()


def generate_responses(answers: list):
    answer = {}
    for data in answers:
        description = json.loads(data.body.decode('utf-8'))
        if "message" in description:
            description = description["message"]
        elif "detail" in description:
            description = description["detail"]
        else:
            description = "Response"
        answer[data.status_code] = {
                                    "content": {
                                        "application/json": {
                                            "example": json.loads(data.body.decode("utf-8"))
                                        }
                                    },
                                    "description": description
        }
    return answer



@router.post("/upload_files",
             responses=generate_responses([upload_files]))
async def upload_files(request: Request, files: List[UploadFile] = File()):
    path=[]
    path_type=[]
    for file in files:
        file.filename= await generate_file_name(file.filename)
        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.heic', '.heif', '.svg')):
            path_type.append(2)
        elif file.filename.lower().endswith(('.mp4', '.mkv', '.mov', '.avi', '.gif', '.h264')):
            path_type.append(3)
        else:
            path_type.append(4)
        contents=await file.read()
        with open("/root/files/" + file.filename, "wb") as f:
            f.write(contents)
        path.append("https://nyanyago.ru/api/v1.0/files/" + file.filename)
        await DataUploadedFile.create(id_user=request.user,
                                      files_path="https://nyanyago.ru/api/v1.0/files/"+file.filename)
    return JSONResponse({"status": True,
                         "message": "Success!",
                         "files_path": path,
                         "files_type": path_type})


@router.get("/{file}",
            response_class=FileResponse)
async def send_files(file: str):
    return "/root/files/" + file

