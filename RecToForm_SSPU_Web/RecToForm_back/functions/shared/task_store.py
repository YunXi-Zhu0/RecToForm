from typing import List
from queue import Queue

#包含所属文件夹名, 文件名, 状态
uploaded_folder = {}

#文件夹队列(用于上传)
upload_folder_queue: Queue = Queue()

#文件夹队列(用于下载)
download_folder_queue: Queue = Queue()

#host, port
host = "10.100.1.202"
port = 56112