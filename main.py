"""
IA Focus Writer - Escribe con IA donde tengas el foco
======================================================
Presioná Ctrl+Space en cualquier campo de texto que tenga "@" para que la IA
reemplace tu prompt con la respuesta del modelo local.

Uso:
    1. Escribí "@" seguido de tu pregunta en cualquier campo de texto
    2. Presioná Ctrl+Space
    3. El texto se reemplaza automáticamente con la respuesta de IA

Modificadores de contexto (opcionales):
    @[whatsapp]   - Tono casual, como escribir a un amigo
    @[gmail]      - Redacta emails profesionales
    @[codigo]     - Respuestas técnicas con código preciso
    @[instagram]  - Tono relajado con emojis
    @[exacto]     - Solo la respuesta, sin texto extra

Atajos rápidos: @w, @g, @c, @i, @x
"""

import sys
import io

# Forzar UTF-8 para stdout/stderr en Windows
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "buffer"):
            stream.reconfigure(encoding="utf-8")

import keyboard
import pyautogui
import unicodedata
import threading
import time
import requests
import json
import os
from pathlib import Path

# ─── Modo silencioso (pythonw.exe) ──────────────────────────────

IS_SILENT = sys.executable.endswith('pythonw.exe') or not sys.stdout.isatty()
LOG_FILE = Path(__file__).parent / "focus-writer.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB


def _rotate_log():
    """Rota el archivo de log si supera MAX_LOG_SIZE."""
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
        backup = LOG_FILE.with_suffix(".log.bak")
        LOG_FILE.rename(backup)


def _write_log(msg):
    """Escribe un mensaje en el archivo de log."""
    try:
        _rotate_log()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass


def _log(msg):
    """Escribe en consola y/o archivo segun el modo."""
    if IS_SILENT:
        _write_log(msg)
    else:
        print(msg)

# ─── Configuración ───────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "lmstudio_url": "http://localhost:1234/v1/chat/completions",
    "model": "",  # Dejar vacío para usar el modelo cargado actualmente en LM Studio
    "trigger": "@",
    "temperature": 0.7,
    "max_tokens": 2048,
    "system_prompt": "Eres un asistente util. Respondé de forma clara y concisa.",
    "ascii_only": False,

    # Perfiles de contexto por aplicación o uso
    "app_profiles": {
        "whatsapp": "REESCRIBE SOLO: Convertí el texto del usuario en un mensaje de WhatsApp para enviar a otra persona. REGLAS: 1) NO converses con el usuario. 2) NO uses primera persona (yo, mi, me). 3) SOLO devolvé el mensaje reescrito. EJEMPLOS: 'como estas' -> 'Hola, ¿como andas?' | 'hola como estas petisa' -> 'Ola! Como vas?' | 'te paso el archivo mañana' -> 'Te lo mando ma\u00f1ana'.",
        "gmail": "Eres un asistente profesional para redacción de emails. Respondé con tono formal y claro, listo para copiar y pegar en un email.",
        "outlook": "Eres un asistente profesional para redacción de emails. Respondé con tono formal y claro, listo para copiar y pegar en un email.",
        "correo": "Eres un asistente profesional para redacción de emails. Respondé con tono formal y claro, listo para copiar y pegar en un email.",
        "visual studio": "Eres un desarrollador senior experto. Respondé con código preciso, explicaciones técnicas breves y ejemplos prácticos.",
        "vs code": "Eres un desarrollador senior experto. Respondé con código preciso, explicaciones técnicas breves y ejemplos prácticos.",
        "codigo": "Eres un desarrollador senior experto. Respondé con código preciso, explicaciones técnicas breves y ejemplos prácticos.",
        "instagram": "Respondé en tono relajado y amigable. Usá emojis cuando corresponda. Sé breve y entretenido.",
    },

    # Atajos rápidos para perfiles: @@w = @[whatsapp], etc.
    "shortcuts": {
        "w": "whatsapp",
        "g": "gmail",
        "c": "codigo",
        "i": "instagram",
        "x": "exacto",
    },

    # System prompts para cada perfil especial
    "profile_prompts": {
        "whatsapp": "REESCRIBE SOLO: Convertí el texto del usuario en un mensaje de WhatsApp para enviar a otra persona. REGLAS: 1) NO converses con el usuario. 2) NO uses primera persona (yo, mi, me). 3) SOLO devolvé el mensaje reescrito. EJEMPLOS: 'como estas' -> 'Hola, ¿como andas?' | 'hola como estas petisa' -> 'Ola! Como vas?' | 'te paso el archivo mañana' -> 'Te lo mando ma\u00f1ana'.",
        "gmail": "Eres un asistente profesional para redacción de emails. Respondé con tono formal y claro, listo para copiar y pegar en un email.",
        "codigo": "Eres un desarrollador senior experto. Respondé con código preciso, explicaciones técnicas breves y ejemplos prácticos.",
        "instagram": "Respondé en tono relajado y amigable. Usá emojis cuando corresponda. Sé breve y entretenido.",
        "exacto": "IMPORTANT: Solo devolvé exactamente lo que el usuario pidió, sin ninguna explicación adicional, sin saludos, sin texto introductorio ni conclusivo. Si pide un JSON, solo el JSON. Si pide una traducción, solo la traducción. Si pide una definición, solo la definición.",
    },

    # Control de razonamiento: none (sin pensar), medium, high
    "reasoning_effort": "none",
}


def load_config():
    """Carga la configuracion desde config.json o crea una nueva."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        # Merge con defaults para nuevas keys
        for k, v in DEFAULT_CONFIG.items():
            config.setdefault(k, v)
        return config
    else:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print(f"[OK] Configuracion creada en {CONFIG_PATH}")
        return DEFAULT_CONFIG.copy()


# ─── Utilidades de sistema ──────────────────────────────────────

def get_active_window_title():
    """Obtiene el titulo de la ventana activa."""
    try:
        import pygetwindow as gw
        active = gw.getActiveWindow()
        return active.title if active else "Desconocida"
    except Exception:
        return "Desconocida"


def get_focused_element_text():
    """
    Intenta obtener el texto del elemento enfocado en la ventana activa.
    
    Estrategias (en orden):
    1. Clipboard approach - seleccionar todo y copiar desde campo enfocado
    """
    text = try_clipboard_copy()
    if text:
        return text
    return None


def try_clipboard_copy():
    """
    Intenta leer el texto del campo enfocado usando Ctrl+A + Ctrl+C.
    
    Solo funciona si el foco esta en un campo de texto seleccionable.
    Restaura el contenido original despues de leer.
    """
    old_clipboard = None
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            old_clipboard = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
    except Exception:
        pass

    try:
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.02)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.03)
        
        text = None
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except Exception:
            pass
        
        return text.strip() if text else None
    except Exception:
        return None
    finally:
        if old_clipboard is not None:
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(old_clipboard)
                win32clipboard.CloseClipboard()
            except Exception:
                pass


def set_clipboard_text(text):
    """Coloca texto en el portapapeles."""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
    except Exception:
        pass


def type_text_slowly(text, pause=0.003):
    """Escribe texto letra por letra (para campos con validacion).
    pause = delay entre letras en segundos (0.003 = casi instantaneo)."""
    pyautogui.typewrite(text, interval=pause)


def type_text_with_newlines(text, newline_hotkey=('shift', 'enter'), pause=0):
    """Escribe texto con saltos de linea sin enviar (Shift+Enter).
    Ideal para WhatsApp Web, Gmail, etc donde Enter envia el mensaje."""
    parts = text.split('\n')
    for i, part in enumerate(parts):
        if i > 0:
            # No pause entre partes al hacer Shift+Enter
            pyautogui.hotkey(*newline_hotkey)
            time.sleep(0.02)
        if part:  # Evita escribir lineas vacias
            pyautogui.typewrite(part, interval=pause)


def strip_accents(text):
    """Convierte caracteres acentuados a ASCII (á->a, é->e, etc.)."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


# ─── Log helpers (ASCII-safe) ──────────────────────────────────

def log_ok(msg):
    _log(f"[OK] {msg}")

def log_warn(msg):
    _log(f"[WARN] {msg}")

def log_error(msg):
    _log(f"[ERROR] {msg}")

def log_info(msg):
    _log(f"[*]  {msg}")


# ─── Perfiles de contexto ──────────────────────────────────────

def resolve_system_prompt(config, modifier_text):
    """
    Determina el system prompt a usar segun:
    1. Modificador explicito (ej: @[whatsapp] o @w)
    2. Default
    
    No usa deteccion automatica por ventana.
    Retorna (system_prompt, profile_name).
    """
    # 1. Ver si hay modificador explicito
    if modifier_text:
        clean = modifier_text.strip().lower()
        
        # Buscar en shortcuts (@w -> whatsapp, etc.)
        shortcuts = config.get("shortcuts", {})
        # Quitar @ al inicio si existe (modifier_text viene como '@w')
        clean_no_at = clean.lstrip('@').strip()
        if clean_no_at in shortcuts:
            profile_name = shortcuts[clean_no_at]
            return config["profile_prompts"].get(profile_name), profile_name
        if clean in shortcuts:
            profile_name = shortcuts[clean]
            return config["profile_prompts"].get(profile_name), profile_name
        
        # Limpiar corchetes si los tiene (@[whatsapp])
        clean_bracket = clean.lstrip('[').rstrip(']')
        if clean_bracket in shortcuts:
            profile_name = shortcuts[clean_bracket]
            return config["profile_prompts"].get(profile_name), profile_name
        
        # Buscar directo en profile_prompts
        if clean in config["profile_prompts"]:
            return config["profile_prompts"][clean], clean
        if clean_bracket in config["profile_prompts"]:
            return config["profile_prompts"][clean_bracket], clean_bracket
    
    # 2. Default (neutro)
    return config.get("system_prompt", ""), "default"


# ─── Lógica de IA ──────────────────────────────────────────────

def call_lm_studio(system_prompt, user_message, config):
    """Envia el prompt a LM Studio y devuelve la respuesta."""
    url = config["lmstudio_url"].rstrip("/")
    model = config.get("model") or None
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": config.get("temperature", 0.7),
        "max_tokens": config.get("max_tokens", 2048),
        "stream": False,
    }
    
    # Agregar reasoning_effort si tiene un valor valido
    effort = config.get("reasoning_effort")
    if effort:
        payload["reasoning_effort"] = effort
    
    if model:
        payload["model"] = model
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        elif "text" in data:
            return data["text"]
        else:
            return f"Error: respuesta inesperada de LM Studio\n{json.dumps(data, indent=2)}"
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        return f"Error al llamar a LM Studio: {e}"


# ─── Indicador de carga ────────────────────────────────────────

def show_loading_indicator():
    """Muestra 'Procesando...' en el campo activo."""
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.02)
    pyautogui.write('Procesando...')


def stop_loading_indicator():
    """No hace nada (indicador estatico)."""
    pass


# ─── Procesamiento principal ───────────────────────────────────

def process_trigger(config):
    """Se ejecuta cuando se presiona Ctrl+Space."""
    full_text = get_focused_element_text()
    
    if not full_text:
        return
    
    trigger = config["trigger"]
    if trigger not in full_text:
        return
    
    # Buscar la ultima ocurrencia del trigger
    trigger_pos = full_text.rfind(trigger)
    before_trigger = full_text[:trigger_pos]
    after_trigger = full_text[trigger_pos + len(trigger):].strip()
    
    if not after_trigger:
        return  # @ sin texto despues
    
    # Detectar si hay modificador de contexto al inicio del prompt
    modifier = None
    user_prompt = after_trigger
    
    # Detectar modificador al inicio del prompt despues del trigger @
    import re
    modifier_text = None
    
    # Formato 1: @[nombre] (ej: @[whatsapp])
    match_bracket = re.match(r'^\[([^\]]+)\]\s*', after_trigger)
    if match_bracket:
        modifier_text = '[' + match_bracket.group(1) + ']'
        user_prompt = after_trigger[match_bracket.end():].strip()
    # Formato 2: @letra (ej: @w, @g) - la letra sola al inicio
    else:
        match_shortcut = re.match(r'^(\w)\s+', after_trigger)
        if match_shortcut and match_shortcut.group(1).lower() in config.get('shortcuts', {}):
            modifier_text = '@' + match_shortcut.group(1)
            user_prompt = after_trigger[match_shortcut.end():].strip()
    
    if modifier_text:
        log_info(f"Modificador: {modifier_text}")
    
    if not user_prompt:
        return  # Solo modificador sin prompt
    
    window_title = get_active_window_title()
    system_prompt, profile_name = resolve_system_prompt(config, modifier_text=modifier_text)
    
    log_info(f"Perfil: {profile_name}")
    log_info(f"Campo activo: {window_title}")
    log_info(f"Prompt IA: {user_prompt[:80]}{'...' if len(user_prompt) > 80 else ''}")
    
    # Mostrar indicador de carga en el campo
    show_loading_indicator()
    
    response = call_lm_studio(system_prompt, user_prompt, config)
    
    if response is None:
        log_error("No se pudo conectar con LM Studio. ¿El servidor esta corriendo?")
        # Restaurar texto original
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.write(full_text, interval=0.01)
        return
    
    if response.startswith("Error"):
        log_error(response)
        # Restaurar texto original
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.write(full_text, interval=0.01)
        return
    
    # Procesar respuesta
    if config.get("ascii_only", False):
        response = strip_accents(response)
    response = response.replace('\r', '')  # Solo eliminar \r, conservar \n
    
    # Reconstruir: texto antes del @ + respuesta
    full_response = before_trigger.rstrip() + ' ' + response if before_trigger.strip() else response
    
    # Escribir respuesta final (reemplaza "Procesando..." directamente)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.05)
    type_text_with_newlines(full_response)
    
    log_ok(f"Respuesta escrita en {window_title}")


# ─── Hook global ────────────────────────────────────────────────

def on_trigger(event=None):
    """Callback cuando se presiona Ctrl+Space."""
    try:
        process_trigger(config)
    except Exception as e:
        log_error(f"Error: {e}")


# ─── Inicialización ─────────────────────────────────────────────

def main():
    global config
    
    if IS_SILENT:
        _log("=" * 50)
        _log("  IA Focus Writer - Iniciando en segundo plano")
        _log("  Ctrl+Space = procesar @ | Ctrl+Shift+Q = salir | ESC = salir")
    
    print("=" * 50)
    print("  IA Focus Writer")
    print("  Presioná Ctrl+Space en un campo con '@' para escribir")
    print("  con la respuesta de tu modelo local.")
    print("  Usá @w, @g, @c, @i, @x para cambiar el contexto.")
    if IS_SILENT:
        _log("  Modo silencioso activado - logs en focus-writer.log")
        print("  [Modo silencioso - logs en focus-writer.log]")
    print("=" * 50)
    
    # Verificar admin (para hooks globales)
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
    
    if not is_admin:
        log_warn("No estas ejecutando como administrador. Los hotkeys globales pueden no funcionar.")
    
    # Cargar config
    config = load_config()
    
    # Verificar LM Studio
    url = config["lmstudio_url"].rstrip("/")
    try:
        r = requests.get(f"{url}/models", timeout=5)
        if r.status_code == 200:
            log_ok("LM Studio server conectado")
        else:
            log_warn(f"LM Studio respondió con {r.status_code}. ¿El servidor esta corriendo?")
    except Exception:
        log_warn("No se pudo conectar a LM Studio. ¿Corres 'lms server start'?")
    
    # Registrar hotkeys
    keyboard.add_hotkey('ctrl+space', on_trigger, suppress=False)
    print("[OK] Ctrl+Space registrado. Presionalo en un campo con '@'.")
    
    # Ctrl+Shift+Q para salir (no usamos Ctrl+C para no romper el copiar normal)
    def exit_handler():
        _log("[SALIR] Cerrando IA Focus Writer...")
        print("\n[SALIR] Cerrando IA Focus Writer...")
        keyboard.unhook_all()
        sys.exit(0)
    
    keyboard.add_hotkey('ctrl+shift+q', exit_handler, suppress=False)
    
    print("[OK] Ctrl+Shift+Q para salir.")
    if IS_SILENT:
        _log("Ctrl+Shift+Q registrado. ESC tambien cierra la app.")
    else:
        print()
        print("Modificadores disponibles:")
        print("  @ [whatsapp]   - Redacta mensajes para WhatsApp")
        print("  @ [gmail]      - Emails profesionales")
        print("  @ [codigo]     - Respuestas tecnicas")
        print("  @ [instagram]  - Tono relajado con emojis")
        print("  @ [exacto]     - Solo la respuesta, sin texto extra")
        print()
        print("Atajos rapidos: @w, @g, @c, @i, @x")
        print("-" * 50)
    
    try:
        keyboard.wait('esc')  # Presionar ESC para salir tambien
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.unhook_all()


if __name__ == "__main__":
    main()
