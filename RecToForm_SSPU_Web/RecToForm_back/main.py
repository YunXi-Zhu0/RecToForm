import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from functions.upload.upload import upload
from functions.analyze.analyze import analyze
from functions.download.download import download

from functions.shared.task_store import host, port
from functions.shared.cleaner import start_cleaner_scheduler

app = FastAPI(root_path="/rec2form/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],  # 只允许 POST 请求方法
    allow_headers=["*"],  # 允许所有请求头
)

app.include_router(upload, tags=["文件上传"])
app.include_router(analyze, tags=["程序调用"])
app.include_router(download, tags=["表格下载"])


#每日凌晨3点删除所有用户文件
@app.on_event("startup")
async def startup_event():
    start_cleaner_scheduler()


if __name__ == "__main__":
    uvicorn.run(app, host=host, port=port)