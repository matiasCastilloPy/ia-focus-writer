# IA Focus Writer

Write with AI anywhere you have focus, without leaving the app you're using. Integrated as an MCP server in LM Studio for automatic startup.

## Installation

### Requirements

- **LM Studio** installed (latest version)
- **Python 3.8+** installed
- Dependencies: `pip install -r requirements.txt`

### Configure MCP in LM Studio

1. Open LM Studio → **Developer tab** (lightning bolt icon ⚡)
2. Scroll down to the **"MCP Servers"** section
3. Click **"Add MCP Server"**
4. Fill in the fields:
   - **Name**: `ia-focus-writer`
   - **Command**: `C:\Python314\python.exe` (or your Python path)
   - **Arguments**: `server.py`
   - **Working Directory**: Path to the project folder (e.g., `C:\Users\Usuario\Desktop\Proyectos\ia-focus-writer`)
5. Click **"Save"**

> ✅ When LM Studio starts, the MCP server will run automatically and keyboard hooks will be active.

## How to Use

### Workflow

1. Write your prompt with the trigger `@` in any text field:
   - WhatsApp Web: `@ reply to this message being funny`
   - Gmail: `@ summarize the key points`
   - VS Code: `@ explain what this function does`
2. Press **Ctrl+Space** — the text is automatically replaced with the AI response

### Context Modifiers

You can add a modifier before the prompt to change how the AI responds:

| Modifier | Shortcut | Usage |
|-----------|----------|-------|
| `@[whatsapp]` | `@w` | Casual tone, like writing to a friend |
| `@[gmail]` | `@g` | Professional and formal emails |
| `@[codigo]` | `@c` | Technical responses with precise code |
| `@[instagram]` | `@i` | Relaxed tone with emojis |
| `@[exacto]` | `@x` | Only the response, no extra text (ideal for JSON, code, translations) |

### Examples:

```
@ respond to me as if you were my friend
@w tell me a joke                    → uses whatsapp profile
@g write an email to my boss          → uses professional gmail profile
@c refactor this function              → uses code profile
@x format this json: [json without formatting] → uses exacto profile (JSON only)
```

### Automatic Detection

If you don't use a modifier, the program automatically detects the active window and uses the corresponding profile. You can configure your profiles in `config.json` under `"app_profiles"`.

## Configuration

Uses `config.json`. Main options:

```json
{
    "lmstudio_url": "http://localhost:1234/v1/chat/completions",
    "model": "",
    "trigger": "@",
    "temperature": 0.7,
    "max_tokens": 2048,
    "ascii_only": true,

    "app_profiles": {
        "whatsapp": "Casual tone...",
        "gmail": "Professional emails..."
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
        "exacto": "Only return exactly what was requested, no extra text."
    }
}
```

- `trigger`: Word that activates the AI (default: `@`)
- `ascii_only`: `true` removes accents from the response (avoids issues with pyautogui in Spanish)
- `app_profiles`: Maps window names to automatic system prompts
- `shortcuts`: Quick shortcuts (`@w`, `@g`, etc.)
- `profile_prompts`: System prompts for each profile

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Ctrl+Space** | Process @ in active field |
| **Ctrl+Shift+Q** | Close IA Focus Writer |
| **ESC** | Also closes the app |

> Note: Keyboard hooks are registered automatically when LM Studio starts. To close the app use Ctrl+Shift+Q or ESC.

## How It Works

1. The MCP server runs in the background while LM Studio is open
2. Ctrl+Space is captured at the system level (global hook)
3. The text from the field you have focus on is read (Ctrl+A + Ctrl+C)
4. If it contains `@`, the prompt is extracted and context modifier is detected
5. The appropriate system prompt is selected (by modifier, active window, or default)
6. The response automatically replaces your original prompt in the field

## Troubleshooting

- **"Could not connect to LM Studio"**: Make sure the server is running (Developer tab → "Start Server")
- **Ctrl+Space doesn't respond**: Verify that LM Studio is open and the MCP server is connected (you should see "Connected · 0 tools ready" in the MCP section)
- **Doesn't read field text**: Works best on HTML inputs (browsers). In native apps it may not work if the field is not selectable.
- **Response sends itself**: Make sure `ascii_only` is set to `true` and `\n` are replaced with spaces.

## Project Structure

```
ia-focus-writer/
├── main.py          # Main logic (hooks, processing, writing)
├── server.py        # MCP server for LM Studio (auto-start)
├── config.json      # App configuration
├── requirements.txt # Python dependencies
└── README.md        # This documentation
```
