const fileInput = document.getElementById('fileInput');
const uploadSuccessMessage = document.getElementById('uploadSuccessMessage');
const uploadButton = document.getElementById('uploadButton');
const analyzeButton = document.getElementById('analyzeButton');
const downloadButton = document.getElementById('downloadButton');

const validExts = ['.pdf', '.ofd'];
let websocket, progress = 0, downloadUrl = null;
let step = 'upload';

// 消息观察器
const messagesObserver = new MutationObserver(() => {
    scrollToBottom();
});

function updateButtonStates() {
    uploadButton.classList.remove('active');
    analyzeButton.classList.remove('active');
    downloadButton.classList.remove('active');

    uploadButton.disabled = step !== 'upload';
    analyzeButton.disabled = step !== 'analyze';
    downloadButton.disabled = step !== 'download';

    [uploadButton, analyzeButton, downloadButton].forEach(btn => {
        if (!btn.disabled) btn.classList.add('active');
    });
}

function addMessage(text, type = 'normal') {
    requestAnimationFrame(() => {
        const messageDiv = document.createElement("div");
        messageDiv.textContent = text;
        messageDiv.className = `message-${type}`;
        messages.appendChild(messageDiv);
    });
}

function addMessageSuccess(text, type = 'success') {
    requestAnimationFrame(() => {
        const messageDiv = document.createElement("div");
        messageDiv.textContent = text;
        messageDiv.className = `message-${type}`;
        messages.appendChild(messageDiv);
    });
}


function scrollToBottom() {
    const lastMessage = messages.lastElementChild;
    if (lastMessage) {
        lastMessage.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest'
        });
    }
}

fileInput.addEventListener('change', () => {
    handleFiles(Array.from(fileInput.files));
    fileInput.value = '';
});

async function handleFiles(files) {
    const legal = files.filter(file =>
        validExts.some(ext => file.name.toLowerCase().endsWith(ext))
    );
    if (legal.length === 0) {
        addMessage("错误：请上传 PDF 或 OFD 格式的文件");
        return;
    }
    await uploadFiles(legal);
}

async function uploadFiles(files) {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
        const response = await fetch('http://10.100.1.202:56112/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorDetail = '';
            try {
                const errorResponse = await response.json();
                errorDetail = errorResponse.detail || errorResponse.message || JSON.stringify(errorResponse);
            } catch (e) {
                errorDetail = await response.text();
            }
            // 400错误显示为红色
            addMessage(errorDetail, response.status === 400 ? 'error' : 'normal');
            return;
        }

        await response.text();
        showUploadSuccess();
        step = 'analyze';
        updateButtonStates();
    } catch (err) {
        addMessage(`上传失败: ${err.message}`, 'error');
    }
}

function startWebSocket() {
    if (step !== 'analyze') return;

    if (websocket?.readyState === WebSocket.OPEN) return;

    // 添加"制表中"动画效果
    analyzeButton.innerHTML = '<span class="analyzing">制表中<span class="dots">...</span></span>';
    analyzeButton.disabled = true;

    // 创建CSS动画
    const style = document.createElement('style');
    style.textContent = `
        @keyframes dotPulse {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }
        .analyzing .dots span {
            animation: dotPulse 1.4s infinite;
            display: inline-block;
        }
        .analyzing .dots span:nth-child(1) {
            animation-delay: 0s;
        }
        .analyzing .dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .analyzing .dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
    `;
    document.head.appendChild(style);

    // 将...转换为3个span以便单独动画
    const dots = analyzeButton.querySelector('.dots');
    dots.innerHTML = '<span>.</span><span>.</span><span>.</span>';

    websocket = new WebSocket("ws://10.100.1.202:56112/analyze");

    websocket.onopen = () => {
        console.log("WebSocket连接已建立");
        websocket.send("开始分析");
    };

    websocket.onmessage = (event) => {
        const message = event.data;

        if (message.includes('表格下载链接:')) {
            progress = 100;
            updateProgressBar(progress);
            downloadUrl = message.split('表格下载链接:')[1].trim();
            step = 'download';
            updateButtonStates();
            addMessageSuccess("分析完成，点击“下载表格”，获得Excel文件");

            // 恢复按钮文本
            analyzeButton.innerHTML = '开始制表';
            return;
        }

        addMessage(message);
        if (progress < 90) progress += 10;
        updateProgressBar(progress);
    };

    websocket.onclose = () => {
        console.log("WebSocket连接已关闭");
        // 恢复按钮文本
        analyzeButton.innerHTML = '开始制表';
    };

    websocket.onerror = (error) => {
        if (error.data) {
            try {
                const errorData = JSON.parse(error.data);
                addMessage(errorData.detail || errorData.message || error.data, 'error');
            } catch (e) {
                addMessage(error.data, 'error');
            }
        } else {
            addMessage('制表过程中发生错误', 'error');
        }
        analyzeButton.innerHTML = '开始制表';
    };
}

downloadButton.addEventListener('click', () => {
    if (step === 'download' && downloadUrl) {
        window.open(downloadUrl, '_blank');
        // 下载后重置状态，开始新的循环
        resetState();
    }
});

function resetState() {
    // 重置所有状态
    progress = 0;
    downloadUrl = null;
    step = 'upload';
    updateProgressBar(progress);
    updateButtonStates();
    addMessageSuccess("下载完成！可以继续上传 PDF 或 OFD 文件分析");
}

function updateProgressBar(value) {
    progressBar.style.width = `${value}%`;
    progressText.textContent = `${value}%`;
}

function showUploadSuccess() {
    uploadSuccessMessage.style.display = 'block';
    setTimeout(() => {
        uploadSuccessMessage.style.display = 'none';
    }, 3000);
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    messagesObserver.observe(messages, { childList: true });

    const initialMessages = [
        { text: "发票信息自助填表（提取发票代码、发票号、发票金额）", type: "warning" },
        { text: "作者：Yunxi_Zhu, Xinger", type: "warning" },
        { text: "邮箱：20241130160@sspu.edu.cn ；20241113537@sspu.edu.cn", type: "warning" },
        { text: "请上传 PDF 或 OFD 文件以开始分析（可多选文件）", type: "warning" },
        { text: "------------------------------------------------------------------------------------", type: "divider" }
    ];

    initialMessages.forEach(msg => addMessage(msg.text, msg.type));
    updateButtonStates();
});