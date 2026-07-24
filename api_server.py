from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import threading

app = FastAPI()

# CORS для доступа из webview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальный экземпляр бэкенда (инициализируется в main.py)
backend_instance = None

class OptionsRequest(BaseModel):
    file_paths: str
    dse_order: bool = True
    bam_parser: bool = True
    generate_table: bool = True
    query_split: int = 1
    error_handler: bool = True

class LogEntry(BaseModel):
    message: str
    color: Optional[str] = None

@app.get("/api/check-dependencies")
def check_dependencies():
    return backend_instance.check_dependencies()

@app.get("/api/test-db")
def test_db():
    return backend_instance.test_db_connection()

@app.get("/api/resource-path")
def get_resource_path(relative_path: str):
    return {"path": backend_instance.get_resource_path(relative_path)}

@app.post("/api/select-files")
def select_files(name: str = "отчетов"):
    return backend_instance.select_files(name)

@app.post("/api/start-processing")
def start_processing(req: OptionsRequest):
    return backend_instance.start_processing(req.file_paths, req.dict())

@app.post("/api/stop-processing")
def stop_processing():
    return backend_instance.stop_processing()

@app.get("/api/open-result")
def open_result():
    return backend_instance.open_result_file()

@app.get("/api/toggle-table")
def toggle_table():
    return backend_instance.open_work_table()

@app.get("/api/table-data")
def get_table_data():
    return backend_instance.get_table_data()

@app.get("/api/help-text")
def get_help_text():
    return backend_instance.get_help_text()

@app.get("/api/logs")
def get_logs():
    return {"logs": backend_instance.log_messages}

@app.get("/api/status")
def get_status():
    return {
        "is_processing": backend_instance.current_thread is not None and backend_instance.current_thread.is_alive(),
        "path_outfile": backend_instance.path_outfile,
        "table_open": backend_instance._table_window_open
    }

def run_server(port=8765):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

def start_server(backend, port=8765):
    global backend_instance
    backend_instance = backend
    thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    thread.start()
    return port
