// === CONFIG ===
const API_BASE = 'http://127.0.0.1:8765/api';

// === STATE ===
let isProcessing = false;
let isTableOpen = false;
let filePaths = [];
let lastLogCount = 0;
let pollingInterval = null;

// === INIT ===
document.addEventListener('DOMContentLoaded', async () => {
    // Загрузка логотипа (base64 data URI — работает везде)
    try {
        const resp = await fetch(`${API_BASE}/logo`);
        const data = await resp.json();
        if (data.data_uri) {
            document.getElementById('logo-img').src = data.data_uri;
        }
    } catch (e) {
        console.error('Logo load error:', e);
    }

    // Проверка зависимостей
    try {
        const resp = await fetch(`${API_BASE}/check-dependencies`);
        const deps = await resp.json();
        if (!deps.success) {
            addLog(deps.message, 'red');
            addLog(`Путь к файлу: ${deps.path}`, 'orange');
        }
    } catch (e) {
        addLog('Ошибка подключения к серверу', 'red');
    }

    // Проверка БД
    try {
        const resp = await fetch(`${API_BASE}/test-db`);
        const dbTest = await resp.json();
        if (dbTest.success) {
            setTimeout(() => addLog('Готов к запуску...', 'green'), 500);
        } else if (dbTest.error) {
            addLog(`БД: ${dbTest.error}`, 'red');
        }
    } catch (e) {
        console.error('DB test error:', e);
    }

    // Запуск polling логов
    startLogPolling();
});

// === POLLING ===
function startLogPolling() {
    pollingInterval = setInterval(async () => {
        try {
            const resp = await fetch(`${API_BASE}/logs`);
            const data = await resp.json();

            // Добавляем только новые логи
            const newLogs = data.logs.slice(lastLogCount);
            newLogs.forEach(log => addLog(log.message, log.color));
            lastLogCount = data.logs.length;

            // Проверка статуса
            const statusResp = await fetch(`${API_BASE}/status`);
            const status = await statusResp.json();

            if (!status.is_processing && isProcessing) {
                isProcessing = false;
                document.getElementById('btn-start').disabled = false;
                document.getElementById('btn-stop').style.display = 'none';
                document.getElementById('progress-container').style.display = 'none';

                if (status.path_outfile) {
                    document.getElementById('btn-result').style.display = 'inline-block';
                }
            }
        } catch (e) {
            // Сервер может быть временно недоступен
        }
    }, 500);
}

// === HELPERS ===
async function apiPost(endpoint, body = null) {
    const options = { method: 'POST' };
    if (body !== null) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(body);
    }
    const resp = await fetch(`${API_BASE}${endpoint}`, options);
    return await resp.json();
}

// === FILE SELECTION ===
async function selectFiles() {
    try {
        const result = await apiPost('/select-files', { name: 'отчетов' });

        if (result.success) {
            filePaths = result.paths;
            document.getElementById('file-path').value = result.str_paths;
            document.getElementById('file-name').value = result.name;
            document.getElementById('file-name').style.color = '#e8fbfd';
            addLog('<Установлен путь для файла отчетов>', 'muted');
            document.getElementById('file-path').classList.remove('error');
            document.getElementById('file-name').classList.remove('error');
        }
    } catch (e) {
        addLog('Ошибка выбора файлов', 'red');
    }
}

// === PROCESSING ===
async function startProcessing() {
    const pathInput = document.getElementById('file-path').value.trim();

    // Приоритет — файлы из диалога, иначе парсим введённый путь
    let paths = filePaths.length ? filePaths : [];
    if (!paths.length && pathInput) {
        paths = pathInput.split(/[,;]+/).map(s => s.trim()).filter(Boolean);
    }

    if (!paths.length) {
        addLog('Ошибка, укажите путь к файлу', 'red');
        document.getElementById('file-path').classList.add('error');
        return;
    }

    const options = {
        file_paths: paths,
        dse_order: document.getElementById('chk-dse').checked,
        bam_parser: document.getElementById('chk-bam').checked,
        generate_table: document.getElementById('chk-result').checked,
        query_split: parseInt(document.querySelector('input[name="query-split"]:checked').value),
        error_handler: true
    };

    // Сброс UI
    document.getElementById('status-text').innerHTML = '';
    lastLogCount = 0;
    document.getElementById('btn-result').style.display = 'none';
    document.getElementById('btn-start').disabled = true;
    document.getElementById('btn-stop').style.display = 'inline-block';
    document.getElementById('progress-container').style.display = 'block';

    isProcessing = true;

    try {
        const result = await apiPost('/start-processing', options);

        if (!result.success) {
            addLog('Ошибка запуска обработки', 'red');
            resetProcessingUI();
        }
    } catch (e) {
        addLog('Ошибка запуска: ' + e.message, 'red');
        resetProcessingUI();
    }
}

function resetProcessingUI() {
    isProcessing = false;
    document.getElementById('btn-start').disabled = false;
    document.getElementById('btn-stop').style.display = 'none';
    document.getElementById('progress-container').style.display = 'none';
}

async function stopProcessing() {
    try {
        await apiPost('/stop-processing');
        document.getElementById('btn-stop').style.display = 'none';
    } catch (e) {
        addLog('Ошибка остановки', 'red');
    }
}

// === RESULT ===
async function openResult() {
    try {
        const resp = await fetch(`${API_BASE}/open-result`);
        const result = await resp.json();
        if (!result.success) {
            addLog(result.error || 'Ошибка при открытии файла', 'red');
        }
    } catch (e) {
        addLog('Ошибка открытия файла', 'red');
    }
}

// === TABLE ===
async function toggleWorkTable() {
    const modal = document.getElementById('table-modal');

    if (isTableOpen) {
        modal.style.display = 'none';
        isTableOpen = false;
    } else {
        try {
            const resp = await fetch(`${API_BASE}/table-data`);
            const result = await resp.json();
            renderTable(result.headers, result.data);
            modal.style.display = 'flex';
            isTableOpen = true;
        } catch (e) {
            addLog('Ошибка загрузки таблицы', 'red');
        }
    }
}

function renderTable(headers, data) {
    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');

    thead.innerHTML = `<tr>${headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}</tr>`;

    if (!data.length) {
        tbody.innerHTML = `<tr><td colspan="${headers.length}" style="text-align:center;color:var(--text-muted);padding:24px;">Нет данных</td></tr>`;
        return;
    }

    tbody.innerHTML = data.map(row =>
        `<tr>${headers.map(h => `<td>${escapeHtml(String(row[h] ?? ''))}</td>`).join('')}</tr>`
    ).join('');
}

function escapeHtml(str) {
    return str.replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
}

// === HELP ===
async function openHelp() {
    try {
        const resp = await fetch(`${API_BASE}/help-text`);
        const result = await resp.json();
        document.getElementById('help-text').textContent = result.text;
        document.getElementById('help-modal').style.display = 'flex';
    } catch (e) {
        addLog('Ошибка загрузки справки', 'red');
    }
}

function closeHelp() {
    document.getElementById('help-modal').style.display = 'none';
}

// === LOGS ===
function addLog(message, color = null) {
    const container = document.getElementById('status-text');
    const line = document.createElement('div');
    line.className = 'log-line';
    if (color) {
        const colorMap = {
            'red': 'log-red',
            'green': 'log-green',
            'orange': 'log-orange',
            '#ff8d52': 'log-orange',
            '#9aa5aa': 'log-muted',
            '#788084': 'log-muted',
            '#00aaff': 'log-blue',
            'blue': 'log-blue',
            'muted': 'log-muted'
        };
        line.classList.add(colorMap[color] || 'log-muted');
    }
    line.textContent = message;
    container.appendChild(line);
    container.scrollTop = container.scrollHeight;
}

// === CLOSE MODAL ON BACKDROP CLICK ===
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            if (modal.id === 'table-modal') isTableOpen = false;
        }
    });
});

// === CLEANUP ===
window.addEventListener('beforeunload', () => {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
});
