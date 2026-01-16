// ORCA - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function () {
    const driveBtn = document.getElementById('drive-btn');
    const logConsole = document.getElementById('log-console');
    const driverStatus = document.getElementById('driver-status');
    const productCategory = document.getElementById('product-category');
    const supplierCategory = document.getElementById('supplier-category');

    let eventSource = null;

    // Add log entry to console
    function addLog(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        logConsole.appendChild(entry);
        logConsole.scrollTop = logConsole.scrollHeight;
    }

    // Update driver status badge
    function updateStatus(status, type) {
        driverStatus.textContent = status;
        driverStatus.className = `status-badge status-${type}`;
    }

    // Drive button click handler
    if (driveBtn) {
        driveBtn.addEventListener('click', function () {
            const product = productCategory.value;
            const supplier = supplierCategory.value;

            // Close existing connection
            if (eventSource) {
                eventSource.close();
            }

            // Clear console
            logConsole.innerHTML = '';
            addLog(`GLOP Driver 시작: Product=${product.toUpperCase()}, Supplier=${supplier}`, 'highlight');
            updateStatus('실행 중...', 'pending');

            // Disable button during execution
            driveBtn.disabled = true;
            driveBtn.textContent = '⏳ 실행 중...';

            // Connect to SSE endpoint
            eventSource = new EventSource(`/api/drive_glop?product=${product}&supplier=${supplier}`);

            eventSource.onmessage = function (event) {
                const data = JSON.parse(event.data);

                if (data.type === 'log') {
                    let logType = 'info';
                    if (data.message.includes('완료') || data.message.includes('성공')) {
                        logType = 'success';
                    } else if (data.message.includes('오류') || data.message.includes('실패')) {
                        logType = 'error';
                    } else if (data.message.includes('알림') || data.message.includes('>>>')) {
                        logType = 'highlight';
                    }
                    addLog(data.message, logType);
                } else if (data.type === 'status') {
                    updateStatus(data.message, data.status);
                } else if (data.type === 'complete') {
                    addLog('GLOP Driver 작업 완료', 'success');
                    updateStatus('완료', 'active');
                    eventSource.close();
                    driveBtn.disabled = false;
                    driveBtn.textContent = '🚀 Drive GLOP';
                } else if (data.type === 'error') {
                    addLog(`오류: ${data.message}`, 'error');
                    updateStatus('오류 발생', 'rejected');
                    eventSource.close();
                    driveBtn.disabled = false;
                    driveBtn.textContent = '🚀 Drive GLOP';
                }
            };

            eventSource.onerror = function () {
                addLog('연결이 끊어졌습니다.', 'error');
                updateStatus('연결 끊김', 'rejected');
                eventSource.close();
                driveBtn.disabled = false;
                driveBtn.textContent = '🚀 Drive GLOP';
            };
        });
    }
});
