# IA Focus Writer

Escribí con IA donde tengas el foco, sin salir de la app que estés usando. Integrado como servidor MCP en LM Studio para auto-inicio automático.

## Instalación

### Requisitos

- **LM Studio** instalado (última versión)
- **Python 3.8+** instalado
- Dependencias: `pip install -r requirements.txt`

### Configurar MCP en LM Studio

1. Abrí LM Studio → **Developer tab** (ícono de rayo ⚡)
2. Bajá a la sección **"MCP Servers"**
3. Hacé clic en **"Add MCP Server"**
4. Completá los campos:
   - **Name**: `ia-focus-writer`
   - **Command**: `C:\Python314\python.exe` (o tu ruta de Python)
   - **Arguments**: `server.py`
   - **Working Directory**: Ruta a la carpeta del proyecto (ej: `C:\Users\Usuario\Desktop\Proyectos\ia-focus-writer`)
5. Hacé clic en **"Save"**

> ✅ Cuando LM Studio inicie, el servidor MCP se ejecutará automáticamente y los hooks de teclado quedarán activos.

## Cómo usar

### Flujo de trabajo

1. Escribí tu prompt con el trigger `@` en cualquier campo de texto:
   - WhatsApp Web: `@ respondé este mensaje siendo gracioso`
   - Gmail: `@ resumí los puntos clave`
   - VS Code: `@ explicá qué hace esta función`
2. Presioná **Ctrl+Space** — el texto se reemplaza automáticamente con la respuesta de IA

### Modificadores de contexto

Podés agregar un modificador antes del prompt para cambiar cómo responde la IA:

| Modificador | Atajo | Uso |
|-------------|-------|-----|
| `@[whatsapp]` | `@w` | Tono casual, como escribir a un amigo |
| `@[gmail]` | `@g` | Emails profesionales y formales |
| `@[codigo]` | `@c` | Respuestas técnicas con código preciso |
| `@[instagram]` | `@i` | Tono relajado con emojis |
| `@[exacto]` | `@x` | Solo la respuesta, sin texto extra (ideal para JSON, código, traducciones) |

### Ejemplos:

```
@ respondeme como si fueras mi amigo
@w contame un chiste                    → usa perfil whatsapp
@g escribime un email para mi jefe      → usa perfil gmail profesional
@c refactorizá esta función              → usa perfil código
@x formateame este json: [json sin formato] → usa perfil exacto (solo JSON)
```

### Detección automática

Si no usás modificador, el programa detecta automáticamente la ventana activa y usa el perfil correspondiente. Podés configurar tus perfiles en `config.json` bajo `"app_profiles"`.

## Configuración

Se usa `config.json`. Principales opciones:

```json
{
    "lmstudio_url": "http://localhost:1234/v1/chat/completions",
    "model": "",
    "trigger": "@",
    "temperature": 0.7,
    "max_tokens": 2048,
    "ascii_only": true,

    "app_profiles": {
        "whatsapp": "Tono casual...",
        "gmail": "Emails profesionales..."
    },

    "shortcuts": {
        "w": "whatsapp",
        "g": "gmail",
        "c": "codigo",
        "i": "instagram",
        "x": "exacto"
    },

    "profile_prompts": {
        "whatsapp": "...",
        "gmail": "...",
        "codigo": "...",
        "instagram": "...",
        "exacto": "Solo devolvé exactamente lo pedido, sin texto extra."
    }
}
```

- `trigger`: Palabra que activa la IA (default: `@`)
- `ascii_only`: `true` quita acentos de la respuesta (evita problemas con pyautogui en español)
- `app_profiles`: Mapea nombres de ventana a system prompts automáticos
- `shortcuts`: Atajos rápidos (`@w`, `@g`, etc.)
- `profile_prompts`: System prompts para cada perfil

## Atajos

| Tecla | Acción |
|-------|--------|
| **Ctrl+Space** | Procesar @ en campo activo |
| **Ctrl+Shift+Q** | Cerrar IA Focus Writer |
| **ESC** | También cierra la app |

> Nota: Los hooks de teclado se registran automáticamente cuando LM Studio inicia. Para cerrar la app usá Ctrl+Shift+Q o ESC.

## Cómo funciona

1. El servidor MCP se ejecuta en segundo plano mientras LM Studio está abierto
2. Ctrl+Space se captura a nivel de sistema (hook global)
3. Se lee el texto del campo donde tenés el foco (Ctrl+A + Ctrl+C)
4. Si contiene `@`, se extrae el prompt y se detecta si hay modificador de contexto
5. Se selecciona el system prompt adecuado (por modificador, ventana activa o default)
6. La respuesta reemplaza automáticamente tu prompt en el campo original

## Solución de problemas

- **"No se pudo conectar con LM Studio"**: Asegurate de tener el server activo (Developer tab → "Start Server")
- **Ctrl+Space no responde**: Verificá que LM Studio esté abierto y el MCP server conectado (debería aparecer "Conectado · 0 herramientas listas" en la sección de MCP)
- **No lee el texto del campo**: Funciona mejor en inputs HTML (navegadores). En apps nativas puede no funcionar si el campo no es seleccionable.
- **La respuesta se envía sola**: Asegurate que `ascii_only` esté en `true` y los `\n` se reemplacen por espacios.

## Estructura del proyecto

```
ia-focus-writer/
├── main.py          # Lógica principal (hooks, procesamiento, escritura)
├── server.py        # Servidor MCP para LM Studio (auto-inicio)
├── config.json      # Configuración de la app
├── requirements.txt # Dependencias Python
└── README.md        # Esta documentación
```
