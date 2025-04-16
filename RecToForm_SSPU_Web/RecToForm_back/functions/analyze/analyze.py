import os
import shutil

from fastapi import APIRouter, WebSocket
import asyncio
from starlette.websockets import WebSocketState
from functions.RecToForm_SSPU_Web import RecToForm
from functions.shared.task_store import upload_folder_queue, download_folder_queue

from functions.shared.task_store import host, port

analyze = APIRouter()

@analyze.websocket("/analyze")
async def analyze_websocket(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    sender_task = None

    async def log_sender():
        while True:
            message = await queue.get()
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            try:
                await websocket.send_text(message)
            except Exception:
                break
            finally:
                queue.task_done()

    def log_callback(message: str):
        asyncio.run_coroutine_threadsafe(queue.put(message), loop)

    try:
        sender_task = asyncio.create_task(log_sender())

        #创建下载文件夹
        folder_name = upload_folder_queue.get()
        os.makedirs(f"functions/download/downloading_files/{folder_name}")

        # 初始化处理器
        processor = RecToForm(
            in_path=f'functions/upload/uploaded_files/{folder_name}',
            out_path=f'functions/download/downloading_files/{folder_name}/发票信息.xlsx',
            message="分析下列的发票文件，提取发票代码、发票号码、发票金额这些信息。只需要发票代码、发票号码、发票金额（价税合计中的小写金额），注意：发票代码（一定是该关键字，不要误判）与发票号码不一样，若没有数据，则将发票代码字段填入与发票号码一样的值(也是字符串)；同时，如果是乱码，请转换为可读格式；所有信息均是字符串，用双引号包裹；最后以python字典返回（只需要字典，其余多余字符串不需要）\n",
            api_key="skorqzpJyrb4BjZa0w27xGIjDf",
            base_url="https://ds.sspu.edu.cn/api/v1/chat/completions",
            max_threads=10,
            log_back=log_callback
        )

        #提示信息
        await queue.put("作者：Yunxi_Zhu")
        await queue.put("邮箱：20241130160@sspu.edu.cn")
        await queue.put("----------------发票信息自助填表---------------")


        # 文件处理流程
        await queue.put("开始读取发票文件...")
        await asyncio.to_thread(processor.getfile)
        await queue.put(f"发现{len(processor.pdf_names)}份发票文件")

        await queue.put("开始解析发票信息...")
        await asyncio.to_thread(processor.recognize)

        await queue.put("正在生成Excel表格...")
        await asyncio.to_thread(processor.fill)

        await queue.put("所有任务全部处理完成")

        #删除已完成的任务节点
        if os.path.exists(f"functions/upload/uploaded_files/{folder_name}"):
            shutil.rmtree(f"functions/upload/uploaded_files/{folder_name}")
        download_folder_queue.put(folder_name)
        upload_folder_queue.queue.clear()

        await queue.put(f"表格下载链接: http://{host}:{port}/download?folder_name={folder_name}")

    except Exception as e:
        await queue.put(f"处理出错: {str(e)}")
    finally:
        await queue.join()
        if sender_task and not sender_task.done():
            sender_task.cancel()
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()