// SocketIO Real-time Chat Integration
let socket;

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

    // Media File Upload Handler
    const mediaInput = document.getElementById('mediaInput');
    if (mediaInput) {
        mediaInput.addEventListener('change', () => {
            if (mediaInput.files.length > 0) {
                const formData = new FormData();
                formData.append('file', mediaInput.files[0]);
                formData.append('conversation_id', conversationId);

                fetch('/chat/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        socket.emit('send_message', data.message);
                        mediaInput.value = '';
                    } else {
                        alert(data.message || 'File upload failed');
                    }
                })
                .catch(err => console.error('Upload error:', err));
            }
        });
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
        contentHtml = `<img src="/static/${msg.file_path}" class="max-w-xs rounded-xl shadow-md mb-1" />`;
    } else if (msg.message_type === 'file' && msg.file_path) {
        contentHtml = `<a href="/static/${msg.file_path}" target="_blank" class="underline text-orange-600 font-medium">Download Attachment</a>`;
    } else {
        contentHtml = `<p class="text-sm font-medium">${msg.content}</p>`;
    }

    wrapper.innerHTML = `
        <div class="max-w-[75%] ${isSelf ? 'bg-orange-500 text-white rounded-t-2xl rounded-l-2xl' : 'bg-gray-100 text-gray-800 rounded-t-2xl rounded-r-2xl'} p-3 shadow-sm">
            ${contentHtml}
            <span class="block text-[10px] ${isSelf ? 'text-orange-200' : 'text-gray-400'} text-right mt-1">${msg.created_at}</span>
        </div>
    `;

    container.appendChild(wrapper);
}

function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}
