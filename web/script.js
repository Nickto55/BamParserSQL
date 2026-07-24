// === STATE ===
let isProcessing = false;
let isTableOpen = false;
let filePaths = [];

// === INIT ===
document.addEventListener('DOMContentLoaded', async () => {
    // Загрузка логотипа
    try {
        const logoPath = await eel.get_resource_path('static/png/bam-parcer-sql.png')();
        document.getElementById('logo-img').src = logoPath;
    } catch (e) {
        console.error('Logo load error:', e);
    }

    // Проверка зависимостей
    const deps = await eel.check_dependencies()();
    if (!deps.success) {
        addLog(deps.message, 'red');
        addLog(`Путь к файлу: ${deps.path}`, '#ff8d52');
    }

    // Проверка БД
    const dbTest = await eel.test_db_connection()();
    if (dbTest.success) {
        setTimeout(() => addLog('Готов к запуску...', 'green'), 500);
    }
});

// === FILE SELECTION ===
async function selectFiles() {
    const result = await eel.select_files('отчетов')();
    if (result.success) {
        filePaths = result.paths;
        document.getElementById('file-path').value = result.str_paths;
        document.getElementById('file-name').value = result.name;
        document.getElementById('file-name').style.color = '#fff';
        addLog('<Установлен путь для файла отчетов>', '#9aa5aa');
        document.getElementById('file-path').classList.remove('error');
        document.getElementById('file-name').classList.remove('error');
    }
}

// === PROCESSING ===
async function startProcessing() {
    const path = document.getElementById('file-path').value;
    
    if (!path) {
        addLog('Ошибка, укажите путь к файлу', 'red');
        document.getElementById('file-path').classList.add('error');
        return;
    }

    // Собираем опции
    const options = {
        dse_order: document.getElementById('chk-dse').checked,
        bam_parser: document.getElementById('chk-bam').checked,
        generate_table: document.getElementById('chk-result').checked,
        query_split: parseInt(document.querySelector('input[name="query-split"]:checked').value),
        error_handler: true
    };

    // Сброс UI
    document.getElementById('status-text').innerHTML = '';
    document.getElementById('btn-result').style.display = 'none';
    document.getElementById('btn-start').disabled = true;
    document.getElementById('btn-stop').style.display = 'inline-block';
    document.getElementById('progress-container').style.display = 'block';
    
    isProcessing = true;
    
    // Запуск
    await eel.start_processing(path, options)();
}

function stopProcessing() {
    eel.stop_processing()();
    document.getElementById('btn-stop').style.display = 'none';
}

// === RESULT ===
async function openResult() {
    const result = await eel.open_result_file()();
    if (!result.success) {
        addLog(result.error || 'Ошибка при открытии файла', 'red');
    }
}

// === TABLE ===
async function toggleWorkTable() {
    const modal = document.getElementById('table-modal');
    
    if (isTableOpen) {
        modal.style.display = 'none';
        isTableOpen = false;
    } else {
        const result = await eel.open_work_table()();
        if (result.success) {
            renderTable(result.headers, result.data);
            modal.style.display = 'flex';
            isTableOpen = true;
        }
    }
}

function renderTable(headers, data) {
    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');
    
    // Header
    thead.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
    
    // Body
    tbody.innerHTML = data.map(row => 
        `<tr>${headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>`
    ).join('');
}

// === HELP ===
async function openHelp() {
    const result = await eel.get_help_text()();
    document.getElementById('help-text').textContent = result.text;
    document.getElementById('help-modal').style.display = 'flex';
}

function closeHelp() {
    document.getElementById('help-modal').style.display = 'none';
}

// === LOGS ===
function addLog(message, color = null) {
    const container = document.getElementById('status-text');
    const line = document.createElement('div');
    line.className = 'log-line';
    if (color) line.classList.add(`log-${color}`);
    line.textContent = message;
    container.appendChild(line);
    container.scrollTop = container.scrollHeight;
}

// === EEL CALLBACKS (from Python) ===
eel.expose(receiveLog);
function receiveLog(message, color) {
    addLog(message, color);
}

eel.expose(receiveTableRow);
function receiveTableRow(rowData) {
    if (isTableOpen) {
        // Добавляем строку в существующую таблицу
        const tbody = document.getElementById('table-body');
        const headers = [
            "Дсе", "ТП не в архиве", "ДСЕ без маршрутов",
            "ДСЕ без основного материала", "Дсе без трудоемкости",
            "Всего нет УП", "Наименование изделия (ИС)"
        ];
        const tr = document.createElement('tr');
        tr.innerHTML = headers.map(h => `<td>${rowData[h] || ''}</td>`).join('');
        tbody.appendChild(tr);
    }
}

eel.expose(processingFinished);
function processingFinished(path, wasStopped) {
    isProcessing = false;
    document.getElementById('btn-start').disabled = false;
    document.getElementById('btn-stop').style.display = 'none';
    document.getElementById('progress-container').style.display = 'none';
    
    if (path) {
        document.getElementById('btn-result').style.display = 'inline-block';
    }
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
