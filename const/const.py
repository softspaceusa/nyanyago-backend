from fastapi.responses import JSONResponse


success_answer = JSONResponse({"status": True,
                               "message": "Success!"}, 200)
uncorrect_phone = JSONResponse({"status": False,
                                     "message": "Phone number uncorrect!"}, 404)
uncorrect_code = JSONResponse({"status": False,
                                     "message": "Code of verify uncorrect!"}, 404)
user_already_creates = JSONResponse({"status": False,
                                     "message": "User with this phone already created!"}, 404)