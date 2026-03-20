// DOM 요소들
const sendBtn = document.getElementById('send-btn');
const btnText = document.getElementById('btn-text');
const fetchLimitInput = document.getElementById('fetch-limit');
const notifyLimitInput = document.getElementById('notify-limit');
const resultArea = document.getElementById('result-area');
const loadingOverlay = document.getElementById('loading-overlay');

// 결과 표시 요소들
const totalFetchedEl = document.getElementById('total-fetched');
const newNotificationsEl = document.getElementById('new-notifications');
const executionStatusEl = document.getElementById('execution-status');
const resultMessageEl = document.getElementById('result-message');
const executionTimeEl = document.getElementById('execution-time');
const timestampEl = document.getElementById('timestamp');

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    updateServerStatus();
    setInterval(updateServerStatus, 30000); // 30초마다 서버 상태 업데이트
});

// 서버 상태 업데이트
async function updateServerStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.status === 'running') {
            const timestamp = new Date(data.timestamp).toLocaleString('ko-KR');
            timestampEl.textContent = timestamp;
        }
    } catch (error) {
        console.error('서버 상태 확인 실패:', error);
        timestampEl.textContent = '연결 실패';
    }
}

// 전송 버튼 클릭 이벤트
sendBtn.addEventListener('click', async function() {
    // 입력값 검증
    const fetchLimit = parseInt(fetchLimitInput.value);
    const notifyLimit = parseInt(notifyLimitInput.value);
    
    if (!fetchLimit || fetchLimit < 1 || fetchLimit > 1000) {
        showAlert('가져올 공고 수는 1~1000 사이의 값이어야 합니다.', 'danger');
        return;
    }
    
    if (!notifyLimit || notifyLimit < 1 || notifyLimit > 100) {
        showAlert('알림 전송 수는 1~100 사이의 값이어야 합니다.', 'danger');
        return;
    }
    
    // UI 상태 변경
    setLoadingState(true);
    
    const startTime = new Date();
    
    try {
        // API 호출
        const response = await fetch('/api/send-notifications', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                fetch_limit: fetchLimit,
                notify_limit: notifyLimit
            })
        });
        
        const result = await response.json();
        const endTime = new Date();
        const executionTime = Math.round((endTime - startTime) / 1000);
        
        // 결과 표시
        displayResult(result, executionTime);
        
    } catch (error) {
        console.error('API 호출 실패:', error);
        displayResult({
            success: false,
            message: '서버와의 통신 중 오류가 발생했습니다.',
            total_fetched: 0,
            new_notifications: 0
        }, 0);
    } finally {
        setLoadingState(false);
    }
});

// 로딩 상태 설정
function setLoadingState(isLoading) {
    if (isLoading) {
        loadingOverlay.classList.remove('d-none');
        sendBtn.disabled = true;
        btnText.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>처리 중...';
    } else {
        loadingOverlay.classList.add('d-none');
        sendBtn.disabled = false;
        btnText.innerHTML = '<i class="fas fa-paper-plane me-2"></i>1회 전송 실행';
    }
}

// 결과 표시
function displayResult(result, executionTime) {
    // 결과 영역 표시
    resultArea.classList.remove('d-none');
    
    // 통계 업데이트
    totalFetchedEl.textContent = result.total_fetched || 0;
    newNotificationsEl.textContent = result.new_notifications || 0;
    executionStatusEl.textContent = result.success ? '성공' : '실패';
    executionStatusEl.className = result.success ? 'stat-number text-success' : 'stat-number text-danger';
    
    // 실행 시간 표시
    executionTimeEl.textContent = `실행 시간: ${executionTime}초`;
    
    // 메시지 표시
    showAlert(result.message, result.success ? 'success' : 'danger');
    
    // 결과 영역으로 스크롤
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 알림 메시지 표시
function showAlert(message, type) {
    resultMessageEl.className = `alert alert-${type}`;
    resultMessageEl.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
        ${message}
    `;
}

// 입력 필드 실시간 검증
fetchLimitInput.addEventListener('input', function() {
    const value = parseInt(this.value);
    if (value && (value < 1 || value > 1000)) {
        this.classList.add('is-invalid');
    } else {
        this.classList.remove('is-invalid');
    }
});

notifyLimitInput.addEventListener('input', function() {
    const value = parseInt(this.value);
    if (value && (value < 1 || value > 100)) {
        this.classList.add('is-invalid');
    } else {
        this.classList.remove('is-invalid');
    }
});

// 키보드 단축키 (Enter 키로 전송)
document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
        if (!sendBtn.disabled) {
            sendBtn.click();
        }
    }
});

// 페이지 새로고침 방지 (전송 중일 때)
window.addEventListener('beforeunload', function(event) {
    if (!sendBtn.disabled) {
        return; // 전송 중이 아니면 그냥 나가기 허용
    }
    
    event.preventDefault();
    event.returnValue = '알림 전송이 진행 중입니다. 페이지를 나가시겠습니까?';
    return event.returnValue;
});

// 에러 핸들링
window.addEventListener('error', function(event) {
    console.error('JavaScript 오류:', event.error);
    showAlert('페이지에서 오류가 발생했습니다. 페이지를 새로고침해주세요.', 'danger');
});

// 네트워크 상태 모니터링
window.addEventListener('online', function() {
    showAlert('네트워크 연결이 복구되었습니다.', 'success');
});

window.addEventListener('offline', function() {
    showAlert('네트워크 연결이 끊어졌습니다. 연결을 확인해주세요.', 'danger');
});