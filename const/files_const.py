from fastapi.responses import JSONResponse


upload_files = JSONResponse({"status": True,
                             "message": "Success!",
                             "files_path": ["string"],
                             "files_type": [0]})