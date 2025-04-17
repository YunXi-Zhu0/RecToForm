import os
import subprocess
import shutil
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

#清理列表
TARGET_DIRS = [
    "./functions/upload/uploaded_files",
    "./functions/download/downloading_files",
]

def clean_upload_folders():
    print(f"[{datetime.now()}] 开始清理多个上传目录...")

    for dir_path in TARGET_DIRS:
        if not os.path.exists(dir_path):
            print(f"目录不存在，跳过清理：{dir_path}")
            continue

        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                    print(f"已删除文件：{item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"已删除文件夹：{item_path}")
            except Exception as e:
                print(f"删除失败：{item_path}，错误：{e}")

    #重启后端服务(依赖于pm2, 重启rec2form_back)
    subprocess.call(["pm2", "restart", "rec2form_back"])

def start_cleaner_scheduler():
    scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Shanghai'))  #上海时区
    scheduler.add_job(clean_upload_folders, 'cron', hour=3, minute=0)
    scheduler.start()
    print("定时清理任务已启动：每天凌晨 3 点")
