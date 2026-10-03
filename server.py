#!/usr/bin/env python3
"""Servidor MCP para IA Focus Writer.
LM Studio lo lanza al iniciar y lo mantiene corriendo via stdio.
La app funciona en segundo plano con hooks globales activos."""

import json
import sys
import os
import time
import threading

# Agregar el directorio del proyecto al path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from main import process_trigger, load_config, IS_SILENT, log_ok, log_warn

# Cargar config para que process_trigger la use
config = load_config()


def send_response(id_, result):
    msg = {"jsonrpc": "2.0", "id": id_, "result": result}
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def send_error(id_, code, message):
    msg = {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle_request(data):
    try:
        msg = json.loads(data)
    except json.JSONDecodeError:
        return

    method = msg.get("method", "")
    rid = msg.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"listChanged": False, "subscribe": False},
                "prompts": {"listChanged": False}
            },
            "serverInfo": {"name": "ia-focus-writer", "version": "1.0.0"},
        })

    elif method == "tools/list":
        send_response(rid, {"tools": []})

    else:
        if rid is not None:
            send_error(rid, -32601, f"Method not found: {method}")


def on_trigger():
    """Callback para Ctrl+Space."""
    time.sleep(0.05)
    try:
        process_trigger(config)
    except Exception as e:
        log_warn(f"Error en trigger: {e}")


def exit_handler():
    """Callback para Ctrl+Shift+Q o ESC."""
    _log("[SALIR] Cerrando IA Focus Writer...")
    import keyboard
    keyboard.unhook_all()
    sys.exit(0)


def start_keyboard_hooks():
    """Registra los hotkeys globales en un hilo separado."""
    try:
        import keyboard
        
        # Verificar admin
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            is_admin = False
        
        if not is_admin:
            log_warn("No estas ejecutando como administrador. Los hotkeys globales pueden no funcionar.")
        
        keyboard.add_hotkey('ctrl+space', on_trigger, suppress=False)
        log_ok("Ctrl+Space registrado")
        
        keyboard.add_hotkey('ctrl+shift+q', exit_handler, suppress=False)
        log_ok("Ctrl+Shift+Q registrado")
        
        # ESC tambien cierra la app (en hilo separado para no bloquear)
        def wait_esc():
            try:
                keyboard.wait('esc')
                exit_handler()
            except Exception:
                pass
        
        esc_thread = threading.Thread(target=wait_esc, daemon=True)
        esc_thread.start()
        
        log_ok("ESC tambien cierra la app")
        
    except Exception as e:
        log_warn(f"Error al registrar hooks: {e}")


def _log(msg):
    """Escribe en consola y/o archivo segun el modo."""
    if IS_SILENT:
        try:
            from main import _write_log
            _write_log(msg)
        except Exception:
            pass
    else:
        print(msg)


def main():
    log_ok("MCP server iniciado - IA Focus Writer activo")
    
    # Iniciar hooks de teclado en hilo separado
    hook_thread = threading.Thread(target=start_keyboard_hooks, daemon=True)
    hook_thread.start()
    
    # Leer requests de LM Studio via stdio (hilo principal)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            handle_request(line)
        except Exception as e:
            log_warn(f"Error handling request: {e}")


if __name__ == "__main__":
    main()
