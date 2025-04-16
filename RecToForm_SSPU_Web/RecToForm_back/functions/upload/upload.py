from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
from datetime import datetime
import uuid
from functions.shared.task_store import uploaded_folder, upload_folder_queue
import pyclamd

upload = APIRouter()

# 文件头白名单
MAGIC_HEADERS = {
    b'%PDF': 'PDF',
    b'\x50\x4B\x03\x04': 'ZIP/OFD',
}

# 文件大小限制（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024

# 检查文件魔数
def check_magic_header(content: bytes) -> str:
    for magic, filetype in MAGIC_HEADERS.items():
        if content.startswith(magic):
            return filetype
    return "Unknown"

# 初始化 ClamAV
try:
    cd = pyclamd.ClamdAgnostic()
    if not cd.ping():
        cd = None
except Exception:
    cd = None

@upload.post('/upload')
async def upload_file(files: List[UploadFile] = File(...)):
    # 限制最多上传 50 个文件
    if len(files) > 50:
        raise HTTPException(status_code=400, detail="一次最多只能上传 50 个文件")


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{timestamp}_{uuid.uuid4().hex[:6]}"
    upload_dir = os.path.join("functions/upload/uploaded_files/", folder_name)
    os.makedirs(upload_dir, exist_ok=True)

    folder_files_info = []

    for file in files:
        # 检查文件大小
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"{file.filename} 文件过大，最大支持 10MB")
        await file.seek(0) # 重置文件指针

        # 读取文件前 512 字节进行魔数检查
        content = await file.read(512)
        file_type = check_magic_header(content)
        if file_type == "Unknown":
            raise HTTPException(status_code=400, detail=f"{file.filename} 文件类型不被支持")

        # 重置文件指针
        await file.seek(0)
        full_content = await file.read()

        # 写入文件
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(full_content)

        # 扫描病毒
        if cd:
            scan_result = cd.scan_file(file_path)
            if scan_result:
                os.remove(file_path)
                raise HTTPException(status_code=400, detail=f"{file.filename} 被检测为病毒，已拒绝上传")

        file_inf = {
            "file_name": file.filename,
            "type": file_type,
            "status": "finished"
        }
        folder_files_info.append(file_inf)

    # 更新 uploaded_folder，按文件夹名存储文件信息列表
    uploaded_folder[folder_name] = folder_files_info

    # 将文件夹名称加入队列
    upload_folder_queue.put(folder_name)

    return {
        "message": "上传完成",
        "folder_name": folder_name,
        "files": folder_files_info
    }
