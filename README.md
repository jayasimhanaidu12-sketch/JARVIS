# JARVIS — Universal Voice-Controlled AI Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Android-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-purple.svg)]()

> *"Listen → Understand → Plan → Observe → Act → Verify → Respond"*

JARVIS is an autonomous, two-way voice-controlled personal computer and mobile assistant designed for Windows and Android. Rather than blindly executing commands, JARVIS observes device and screen states, plans multi-step workflows, executes actions via sandboxed tool interfaces, verifies results across system APIs and screen states, and communicates concisely through speech.

---

## Architecture Overview

JARVIS is engineered around a five-pillar biological analogy:
- **Ears (Voice Input)**: Speech-to-Text via microphone stream capture (`sounddevice` + `SpeechRecognition`) with wake word detection.
- **Brain (Reasoning & Planning)**: Central reasoning layer supporting dual-engine execution: cloud multimodal LLMs (Gemini / OpenAI / Anthropic) and a zero-configuration local semantic intent engine.
- **Eyes (Computer Vision & Accessibility)**: High-speed screen capture (GDI BitBlt + PyAutoGUI) and Win32 accessibility UI hierarchy extraction.
- **Hands (Device Automation)**: Controlled automation tools for Windows (mouse, keyboard, windows, applications, files, system) and Android (ADB shell, gestures, and UI hierarchy).
- **Voice (Voice Output)**: Natural, offline Text-to-Speech (`pyttsx3`) with queue prioritization and instant interruption on Emergency Stop.

```
                      +-------------------+
                      |    USER VOICE     |
                      +-------------------+
                                |
                                v
                      +-------------------+
                      |  SPEECH-TO-TEXT   |
                      |  (sounddevice/SR) |
                      +-------------------+
                                |
                                v
                      +-------------------+
                      | INTENT & MEMORY   |
                      | (Reference Res.)  |
                      +-------------------+
                                |
                                v
                      +-------------------+
                      |   TASK PLANNER    |
                      | (Multi-Step Plan) |
                      +-------------------+
                                |
                                v
        +-----------------------------------------------+
        |               EXECUTION CYCLE                 |
        |                                               |
        |  1. OBSERVE PRE-STATE  (Screen & Window)      |
        |  2. PERMISSION CHECK   (Low vs High Risk)     |
        |  3. EXECUTE ACTION     (Win32 / Browser / ADB)|
        |  4. OBSERVE POST-STATE (Process & Controls)   |
        |  5. VERIFY OUTCOME     (Process/File/DOM check|
        +-----------------------------------------------+
                     |                     |
               [Verification OK]     [Failed/Blocked]
                     |                     |
                     v                     v
            +-----------------+   +-----------------+
            | NATURAL SPEECH  |   |  AUTO-RECOVERY  |
            |   GENERATION    |   |   OR REPLAN     |
            +-----------------+   +-----------------+
                     |
                     v
            +-----------------+
            | TEXT-TO-SPEECH  |
            | (pyttsx3 Audio) |
            +-----------------+
                     |
                     v
            +-----------------+
            |  USER FEEDBACK  |
            +-----------------+
```

---

## Directory Structure

```
jarvis/
├── config/
│   ├── __init__.py
│   └── settings.py              # Environment settings, thresholds, API keys
├── logging_system/
│   ├── __init__.py
│   └── logger.py                # Structured timeline logging (Section 20)
├── core/
│   ├── __init__.py
│   ├── context.py               # Active device, foreground app, media state
│   ├── memory.py                # Short-term dialogue, anaphora ('it', '2nd one')
│   ├── permissions.py           # Risk gate (Low vs High) & 'JARVIS STOP'
│   ├── planner.py               # Dual-engine planner (LLM + Semantic rules)
│   └── agent.py                 # Core Agent Loop: Listen->Plan->Observe->Act->Verify
├── voice/
│   ├── __init__.py
│   ├── speech_to_text.py        # sounddevice mic capture + SpeechRecognition
│   ├── text_to_speech.py        # pyttsx3 offline natural TTS engine
│   └── wake_word.py             # Wake word detector ('Jarvis', 'Hey Jarvis')
├── vision/
│   ├── __init__.py
│   ├── screen_capture.py        # GDI BitBlt + PyAutoGUI multi-backend capture
│   ├── screen_parser.py         # Structured Win32 UI controls hierarchy
│   └── ui_detector.py           # Semantic button and input field locator
├── computer/
│   ├── __init__.py
│   ├── mouse.py                 # Smooth cursor movement, click, drag, scroll
│   ├── keyboard.py              # Typing, shortcuts, fail-safe key press
│   ├── windows.py               # Win32 window focus, minimize, maximize, close
│   ├── applications.py          # App launcher, switcher, and process verification
│   ├── files.py                 # File & directory manager with safety barrier
│   └── system.py                # Volume up/down/mute, screenshot, OS stats
├── browser/
│   ├── __init__.py
│   ├── browser_controller.py    # Cross-browser launcher, tab management, URL routing
│   └── web_actions.py           # Google/YouTube search, result selection, media controls
├── mobile/
│   ├── __init__.py
│   ├── adb.py                   # ADB connection manager & device discovery
│   ├── mobile_ui.py             # Android uiautomator dump XML element finder
│   └── android_controller.py    # Tap, swipe, type, navigation keys, app launcher
├── tools/
│   ├── __init__.py
│   ├── registry.py              # Unified tool registry & LLM schemas
│   └── executor.py              # Observe-Act-Verify executor with structured logs
├── ui/
│   ├── __init__.py
│   └── dashboard.py             # Desktop Control Panel (Tkinter dark-mode GUI)
├── tests/
│   ├── __init__.py
│   ├── test_tools.py            # Unit tests for computer, browser, mobile tools
│   ├── test_safety.py           # Unit tests for permissions & emergency stop
│   ├── test_agent.py            # Unit tests for task planner & context resolution
│   └── test_e2e_scenarios.py    # Real-world end-to-end scenarios (Section 22)
├── logs/                        # Structured action timeline records
├── screenshots/                 # Captured screen images
├── .env.example                 # Configuration template
├── requirements.txt             # Dependency specification
├── main.py                      # Unified CLI / GUI / Voice launcher
└── README.md                    # Documentation
```

---

## Installation & Setup

### Prerequisites
1. **Windows 10 / 11** (64-bit)
2. **Python 3.10+** (Tested and verified up to Python 3.14)
3. **Microphone & Speakers / Headphones**
4. *(Optional for Android)*: **Android SDK Platform-Tools (`adb`)** with USB Debugging enabled on device.

### 1. Clone & Install Dependencies
Open PowerShell in the project directory:

```powershell
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
python -m pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:

```powershell
cp .env.example .env
```

Edit `.env` to set your desired AI Provider and options:
```env
# Cloud LLM Options (Optional - Works 100% offline out-of-the-box without keys)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Voice Settings
VOICE_ENABLED=true
WAKE_WORD=jarvis
CONTINUOUS_LISTENING=false

# Safety
REQUIRE_CONFIRMATION=true
```

> **Note**: Even without any API keys, JARVIS includes a complete **Local Semantic Intent Engine** capable of handling multi-step tasks, application control, browser search, YouTube playback, file management, volume, and mobile routing out-of-the-box!

---

## Running JARVIS

JARVIS provides 4 distinct runtime modes:

### 1. Desktop Control Panel (GUI Mode — Recommended)
```powershell
python main.py
# or
python main.py --gui
```
Launches the minimal, dark-themed Desktop Control Panel (Section 19):
* **Status Badge**: Real-time indication of Listening, Processing, Executing, Idle, or Stopped.
* **Last Command**: Live display of speech transcription or typed command.
* **Current Task**: Real-time progress tracker.
* **Target Device**: Shows `Windows PC` or `Android Phone` with one-click switcher.
* **Action History**: Chronological log of executed tools and verification outcomes.
* **[ STOP JARVIS ]**: Large red emergency stop button that immediately halts active automation.
* **Voice / Text Dock**: Push-to-talk microphone activation and manual command input bar.

### 2. Interactive Terminal (CLI Mode)
```powershell
python main.py --cli
```
Run JARVIS in terminal mode with full interactive dialogue, voice output, and command verification.

### 3. Continuous Voice Listening Mode
```powershell
python main.py --voice
```
Runs continuous background voice monitoring. Activate JARVIS by saying:
> *"Hey Jarvis, open Chrome"*  
> *"Jarvis, search for AI news"*  
> *"Jarvis, pause the video"*  
> *"JARVIS STOP"* (immediate emergency halt)

### 4. Automated Verification Suite
```powershell
python main.py --test
# or
python -m unittest discover tests
```
Runs all 19 automated unit and end-to-end integration tests.

---

## Supported Commands & Examples

### Windows Control
| Voice Command | Planned Actions | Verification |
|---|---|---|
| *"Open Chrome"* | `open_application(chrome)` | Verifies process `chrome.exe` is running |
| *"Launch Notepad"* | `open_application(notepad)` | Verifies process `notepad.exe` is active |
| *"Switch to VS Code"* | `switch_application(code)` | Brings VS Code window to front |
| *"Minimize window"* | `minimize_window()` | Verifies window minimized |
| *"Volume up"* / *"Volume down"* | `system_volume_up()` / `system_volume_down()` | Adjusts master hardware audio |
| *"Mute system"* | `system_mute()` | Toggles audio mute state |
| *"Take a screenshot"* | `take_screenshot()` | Captures and saves image to `screenshots/` |

### Browser Automation & Media
| Voice Command | Planned Actions | Verification |
|---|---|---|
| *"Open Chrome and search for AI agents"* | `open_application(chrome)` → `browser_search(ai agents)` | Verifies Chrome launched and search results rendered |
| *"Search YouTube for Python tutorials"* | `youtube_search(python tutorials)` | Verifies YouTube results page loaded |
| *"Open the second video"* | `select_result(index=2)` | Resolves ordinal, selects 2nd video, starts playback |
| *"Pause it"* | `pause_media()` | Resolves anaphora 'it' to current video, pauses stream |
| *"Resume"* | `play_media()` | Resumes video playback |

### Android Mobile Control
| Voice Command | Planned Actions | Target Device |
|---|---|---|
| *"Open YouTube on my phone"* | `mobile_launch_app(youtube)` | Android Device |
| *"Turn the volume up on my phone"* | `mobile_media_play_pause()` | Android Device |
| *"Tap Search on my phone"* | `mobile_tap(Search)` | Android Device |
| *"Scroll down on my phone"* | `mobile_scroll_down()` | Android Device |
| *"Press Home on my phone"* | `mobile_home()` | Android Device |

> **Device Disambiguation (Section 12)**: If a command does not specify the device and could apply to both (e.g. *"Open YouTube"*), JARVIS defaults to the currently active device toggle on the dashboard, or allows switching with *"on my phone"* / *"on my laptop"*.

---

## Safety, Permissions & Security

JARVIS adheres strictly to Section 13 and 14 safety guidelines:

### 1. Risk Tiering
* **Low-Risk Actions** (Execute automatically):
  * Open applications, search web, scroll, switch windows, play/pause media, type text, capture screen.
* **High-Risk Actions** (Require explicit user confirmation):
  * Delete files/folders (`delete_file`, `delete_directory`).
  * Shutdown/restart computer.
  * Shell execution.
  * Uninstalling mobile apps or factory reset.

### 2. Confirmation Protocol
When a high-risk tool is triggered:
* If running in **GUI Mode**, a native confirmation modal appears showing the tool name and exact target path.
* If running in **CLI Mode**, the user is prompted: `Do you confirm this action? (yes/no):`.
* Execution proceeds **only** upon explicit approval. If declined, JARVIS cleanly aborts and reports: *"Action canceled because confirmation was declined."*

### 3. Global Emergency Stop ("JARVIS STOP")
* Saying **"JARVIS STOP"**, typing **"stop"**, or clicking the **[ STOP JARVIS ]** button immediately:
  1. Sets the thread-safe `_emergency_stop` event.
  2. Cancels any currently executing sub-tasks.
  3. Flushes and silences the text-to-speech queue.
  4. Blocks subsequent tool execution until reset.
  5. Voices confirmation: *"Automation stopped immediately."*

---

## Verification & Error Handling Strategy

JARVIS does not claim success blindly (Section 15):

```
EXECUTE TOOL
     ↓
OBSERVE STATE
     ↓
[Process Running? / File on Disk? / Window Active?]
   ↙                    ↘
 YES                     NO
  ↓                      ↓
Success!           Inspect Error State
Respond to User          ↓
                   Retry up to N times?
                     ↙             ↘
                  RETRY       REPORT ISSUE
                            Ask user for assistance
```

* **Application Verification**: Verifies `tasklist` and window handles before confirming *"Chrome is open"*.
* **Filesystem Verification**: Inspects file existence and size after creation/deletion.
* **Corner Fail-Safe Guard**: Automatically detects cursor origin (0, 0) and prevents PyAutoGUI fail-safe crashes in background sessions.
* **Read-Only / Lock Recovery**: Uses `stat.S_IWRITE` error handlers for directory deletion across Windows/OneDrive environments.

---

## Structured Action Logging

All actions are logged in real-time to `logs/jarvis_actions.log` adhering to Section 20:

```text
[19:12:46]
Command:      Open Chrome and search for AI agents
Action:       Execute browser_search
Tool:         browser_search {'query': 'ai agents'}
Result:       Searched Google for 'ai agents'
Verification: Verified: Browser navigated to search results for 'ai agents'.
```

---

## Test Suite Execution

To run all automated unit and integration tests:

```powershell
python -m unittest discover tests
```

### Verified Test Cases:
1. `test_tools.py`: Unit tests for mouse, keyboard, windows, files, volume, screen capture, and mobile controller.
2. `test_safety.py`: Permission risk classification, confirmation barriers (declined & approved), and emergency stop.
3. `test_agent.py`: Single-step planning, compound multi-step workflows, anaphora reference resolution, and device selection.
4. `test_e2e_scenarios.py`: End-to-end scenarios covering Section 22 Tests 1 through 5.

---

## Future Roadmap

1. **Vision-Language Navigation**: Multimodal screen understanding with bounding-box element clicking via Gemini 2.5 Flash Vision.
2. **Local Whisper Speech Recognition**: Embedded offline `faster-whisper` model for air-gapped voice transcription.
3. **Smart Home Integration**: Adding Matter and Home Assistant adapters for controlling lights, thermostats, and IoT devices.
4. **iOS Bridge**: Support for iPhone via WebDriverAgent / Appium.
5. **Cross-Device Clipboard & File Sync**: Real-time push of screenshots and clipboard between Windows PC and Android phone over local Wi-Fi.
