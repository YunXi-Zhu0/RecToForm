import os
import shutil
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from functions.shared.task_store import download_folder_queue

download = APIRouter()


def delete_folder(folder_path: str):
    """
    后台删除文件夹
    """
    try:
        shutil.rmtree(folder_path)
        print(f"成功删除文件夹：{folder_path}")
    except Exception as e:
        print(f"删除文件夹失败：{str(e)}")


@download.get('/download')
async def download_file(background_tasks: BackgroundTasks):
    folder_name = download_folder_queue.get()
    folder_path = f"functions/download/downloading_files/{folder_name}"
    file_path = os.path.join(folder_path, "发票信息.xlsx")

    #标记完成, 删除文件夹
    background_tasks.add_task(delete_folder, folder_path)
    download_folder_queue.task_done()

    # 返回文件响应
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename="发票信息.xlsx"
    )