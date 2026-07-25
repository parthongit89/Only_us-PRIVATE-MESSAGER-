// SocketIO Real-time Chat Integration & Media/Voice Messaging
let socket;
let mediaRecorder;
let audioChunks = [];
let recordingTimerInterval;
let recordingSeconds = 0;

function initSocketChat(conversationId, currentUserId, currentUsername) {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to OnlyUs SocketIO Server');
        socket.emit('join_conversation', { conversation_id: conversationId });
    });

    socket.on('new_message', (msg) => {
        appendMessageToContainer(msg, currentUserId);
        scrollToBottom();
    });

    socket.on('typing_status', (data) => {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            if (data.is_typing) {
                indicator.innerText = `${data.user_name} is typing...`;
                indicator.style.display = 'block';
            } else {
                indicator.style.display = 'none';
            }
        }
    });

    // Send Message Button Handler
    const sendBtn = document.getElementById('sendMsgBtn');
    const msgInput = document.getElementById('msgInput');

    if (sendBtn && msgInput) {
        sendBtn.addEventListener('click', () => {
            sendMessage(conversationId, currentUserId, msgInput);
        });

        msgInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage(conversationId, currentUserId, msgInput);
            }
        });

        // Typing event handler
        let typingTimeout;
        msgInput.addEventListener('input', () => {
            socket.emit('typing', { conversation_id: conversationId, user_name: currentUsername, is_typing: true });
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                socket.emit('typing', { conversation_id: conversationId, user_name: currentUsername, is_typing: false });
            }, 2000);
        });
    }

    // Media File Upload Handler (Paperclip)
    const mediaInput = document.getElementById('mediaInput');
    if (mediaInput) {
        mediaInput.addEventListener('change', () => {
            if (mediaInput.files.length > 0) {
                uploadMediaFile(mediaInput.files[0], conversationId, mediaInput);
            }
        });
    }

    // Voice Message Feature Setup
    setupVoiceRecorder(conversationId);
}

function uploadMediaFile(fileObj, conversationId, inputElementToReset) {
    const formData = new FormData();
    formData.append('file', fileObj);
    formData.append('conversation_id', conversationId);

    fetch('/chat/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            if (inputElementToReset) inputElementToReset.value = '';
        } else {
            alert(data.message || 'File upload failed');
        }
    })
    .catch(err => console.error('Upload error:', err));
}

function setupVoiceRecorder(conversationId) {
    const micBtn = document.getElementById('micBtn');
    const voiceRecordingBar = document.getElementById('voiceRecordingBar');
    const standardInputBar = document.getElementById('standardInputBar');
    const cancelVoiceBtn = document.getElementById('cancelVoiceBtn');
    const sendVoiceBtn = document.getElementById('sendVoiceBtn');
    const timerDisplay = document.getElementById('recordingTimer');

    if (!micBtn) return;

    micBtn.addEventListener('click', async () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert('Voice recording requires a secure connection (HTTPS or http://localhost). Modern browsers restrict microphone access over plain HTTP IP addresses.');
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.start(100);
            recordingSeconds = 0;
            if (timerDisplay) timerDisplay.innerText = '00:00';

            clearInterval(recordingTimerInterval);
            recordingTimerInterval = setInterval(() => {
                recordingSeconds++;
                const mins = String(Math.floor(recordingSeconds / 60)).padStart(2, '0');
                const secs = String(recordingSeconds % 60).padStart(2, '0');
                if (timerDisplay) timerDisplay.innerText = `${mins}:${secs}`;
            }, 1000);

            if (standardInputBar) standardInputBar.classList.add('hidden');
            if (voiceRecordingBar) voiceRecordingBar.classList.remove('hidden');
        } catch (err) {
            console.error('Microphone access denied:', err);
            alert('Microphone access is required to send voice messages.');
        }
    });

    if (cancelVoiceBtn) {
        cancelVoiceBtn.addEventListener('click', () => {
            stopRecordingStream();
            resetVoiceUI();
        });
    }

    if (sendVoiceBtn) {
        sendVoiceBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const audioFile = new File([audioBlob], `voice_${Date.now()}.webm`, { type: 'audio/webm' });
                    uploadMediaFile(audioFile, conversationId);
                    stopRecordingStream();
                    resetVoiceUI();
                };
                mediaRecorder.stop();
            }
        });
    }

    function stopRecordingStream() {
        if (mediaRecorder && mediaRecorder.stream) {
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        clearInterval(recordingTimerInterval);
    }

    function resetVoiceUI() {
        if (voiceRecordingBar) voiceRecordingBar.classList.add('hidden');
        if (standardInputBar) standardInputBar.classList.remove('hidden');
        recordingSeconds = 0;
        audioChunks = [];
    }
}

function sendMessage(conversationId, senderId, inputElement) {
    const text = inputElement.value.trim();
    if (text === '') return;

    socket.emit('send_message', {
        conversation_id: conversationId,
        sender_id: senderId,
        content: text,
        message_type: 'text'
    });

    inputElement.value = '';
}

function appendMessageToContainer(msg, currentUserId) {
    const container = document.getElementById('messagesContainer');
    if (!container) return;

    const isSelf = msg.sender_id === currentUserId;
    const wrapper = document.createElement('div');
    wrapper.className = `flex ${isSelf ? 'justify-end' : 'justify-start'} mb-3 animate-fade-in`;

    let contentHtml = '';
    if (msg.message_type === 'image' && msg.file_path) {
        contentHtml = `<img src="/static/${msg.file_path}" class="max-w-xs rounded-xl shadow-md mb-1 object-cover" />`;
    } else if (msg.message_type === 'audio' && msg.file_path) {
        contentHtml = `
            <div class="flex flex-col gap-1">
                <span class="text-[11px] font-semibold opacity-80 flex items-center gap-1"><i data-lucide="mic" class="w-3.5 h-3.5"></i> Voice Note</span>
                <audio controls src="/static/${msg.file_path}" class="w-64 max-w-full my-1 rounded-lg"></audio>
            </div>
        `;
    } else if (msg.message_type === 'video' && msg.file_path) {
        contentHtml = `<video controls src="/static/${msg.file_path}" class="max-w-xs rounded-xl shadow-md my-1"></video>`;
    } else if (msg.message_type === 'file' && msg.file_path) {
        contentHtml = `<a href="/static/${msg.file_path}" target="_blank" class="flex items-center gap-2 underline ${isSelf ? 'text-orange-100' : 'text-orange-400'} font-medium"><i data-lucide="file-text" class="w-4 h-4"></i> Download Attachment</a>`;
    } else {
        contentHtml = `<p class="text-sm font-medium">${escapeHtml(msg.content)}</p>`;
    }

    wrapper.innerHTML = `
        <div class="max-w-[80%] ${isSelf ? 'bg-orange-600 text-white rounded-t-2xl rounded-l-2xl shadow-lg shadow-orange-600/20' : 'bg-gray-800 border border-gray-700 text-gray-100 rounded-t-2xl rounded-r-2xl'} p-3 shadow-sm">
            ${contentHtml}
            <span class="block text-[10px] ${isSelf ? 'text-orange-200' : 'text-gray-400'} text-right mt-1">${msg.created_at}</span>
        </div>
    `;

    container.appendChild(wrapper);
    if (window.lucide) {
        lucide.createIcons();
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}
