"""
Task planning and intent understanding layer for JARVIS.
Features dual reasoning:
1. Cloud/Local LLM Planner (Gemini, OpenAI, Ollama) when API keys are configured.
2. Intelligent Semantic Rule & Intent Parser for zero-configuration, 100% offline out-of-the-box operation.
"""

import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from config.settings import settings
from core.context import context, DeviceType
from core.memory import memory
from tools.registry import tool_registry


@dataclass
class PlanStep:
    tool_name: str
    parameters: Dict[str, Any]
    description: str


class TaskPlanner:
    def plan(self, command: str) -> List[PlanStep]:
        """
        Decomposes user command into an ordered sequence of verified PlanSteps.
        Resolves anaphora ('it', 'the second one', 'again') before planning.
        """
        resolved_cmd = memory.resolve_references(command)

        # 1. Fast deterministic intercepts (Emergency Stop & About Me)
        if "jarvis stop" in resolved_cmd.lower() or resolved_cmd.lower().strip() == "stop":
            return [PlanStep(tool_name="emergency_stop", parameters={}, description="Trigger global emergency stop")]

        about_me_patterns = [
            r"\bsearch\s+(?:about\s+)?(?:me|myself)\b",
            r"\bsearch\s+for\s+me\b",
            r"\bgoogle\s+(?:about\s+)?(?:me|myself)\b",
            r"\bwho\s+am\s+i\b",
            r"\bsearch\s+my\s+name\b",
            r"\btell\s+me\s+about\s+me\b",
            r"\blook\s+up\s+me\b",
            r"\bsearch\s+(?:about\s+)?gudise\b",
            r"\bsearch\s+(?:about\s+)?jayasimha\b",
        ]
        if any(re.search(p, resolved_cmd.lower()) for p in about_me_patterns):
            target_name = getattr(settings, "USER_NAME", "Gudise Jayasimha Naidu")
            return [PlanStep("browser_search", {"query": target_name}, f"Search for {target_name}")]

        # 2. Local Intelligent Semantic Rule Engine (Instant < 2ms execution)
        local_plan = self._plan_with_local_engine(resolved_cmd)
        if local_plan:
            return local_plan

        # 3. LLM Planning for complex / open-ended requests
        if settings.OPENAI_API_KEY or settings.GEMINI_API_KEY:
            try:
                llm_plan = self._plan_with_llm(resolved_cmd)
                if llm_plan:
                    return llm_plan
            except Exception as e:
                print(f"[LLM Planner Notice]: {e}")

        return []

    def _plan_with_local_engine(self, command: str) -> List[PlanStep]:
        """
        Comprehensive rule and pattern decomposition engine.
        Handles multi-step compound requests, browser flows, media controls, and mobile actions.
        """
        steps: List[PlanStep] = []
        cmd = command.strip()
        cmd_lower = cmd.lower()

        # Target device check
        is_mobile = context.active_device == DeviceType.ANDROID

        # --- Emergency Stop ---
        if "stop" in cmd_lower and ("jarvis" in cmd_lower or cmd_lower == "stop"):
            return [PlanStep("emergency_stop", {}, "Stop automation immediately")]

        # --- Present Day News & Live Updates ---
        # e.g., "what is the news update today", "jarvis what is the news update today . jarvis search about the present day and give me the 7 updates in the voice format"
        is_news, news_count, news_topic = self._extract_news_intent(cmd_lower)
        if is_news:
            desc = f"Searching for today's news updates"
            return [PlanStep("get_news_updates", {"count": news_count, "topic": news_topic}, desc)]

        # --- High-Risk: Delete Folder/File ---
        if any(w in cmd_lower for w in ["delete", "remove"]) and any(w in cmd_lower for w in ["folder", "file", "path"]):
            target_match = re.search(r"(?:delete|remove)\s+(?:the\s+)?(?:folder|file|path)?\s*(?:called|named)?\s*['\"]?([^'\"]+)['\"]?", cmd_lower)
            target = target_match.group(1).strip() if target_match else (memory.active_file_or_folder or "this folder")
            return [PlanStep("delete_file", {"path": target}, f"Delete {target}")]

        # --- Mobile Commands ---
        if is_mobile:
            if "youtube" in cmd_lower:
                steps.append(PlanStep("mobile_launch_app", {"app_name": "youtube"}, "Launch YouTube on phone"))
                if "search" in cmd_lower:
                    q = self._extract_search_query(cmd_lower)
                    steps.append(PlanStep("mobile_tap", {"text": "Search"}, "Tap Search icon"))
                    steps.append(PlanStep("mobile_type", {"text": q}, f"Type search '{q}'"))
                return steps
            elif "volume up" in cmd_lower:
                return [PlanStep("mobile_media_play_pause", {}, "Volume up on phone")]
            elif "home" in cmd_lower:
                return [PlanStep("mobile_home", {}, "Press Home on phone")]
            elif "back" in cmd_lower:
                return [PlanStep("mobile_back", {}, "Press Back on phone")]
            elif "scroll down" in cmd_lower:
                return [PlanStep("mobile_scroll_down", {}, "Scroll down on phone")]
            elif "scroll up" in cmd_lower:
                return [PlanStep("mobile_scroll_up", {}, "Scroll up on phone")]
            elif "pause" in cmd_lower or "play" in cmd_lower:
                return [PlanStep("mobile_media_play_pause", {}, "Play/Pause media on phone")]

        # --- Multi-step: Compound Browser & Search workflows ---
        # Example: "Open Chrome and search for AI agents"
        compound_chrome_search = re.search(r"open\s+(chrome|edge|browser)\s+and\s+search\s+(?:for\s+)?(.+)", cmd_lower)
        if compound_chrome_search:
            browser = compound_chrome_search.group(1)
            query = compound_chrome_search.group(2).strip()
            steps.append(PlanStep("open_application", {"app_name": browser}, f"Open {browser}"))
            steps.append(PlanStep("browser_search", {"query": query}, f"Search for {query}"))
            return steps

        # Example: "Open YouTube" or compound YouTube workflows
        if "youtube" in cmd_lower:
            if "search" in cmd_lower or "play" in cmd_lower:
                steps.append(PlanStep("open_application", {"app_name": "chrome"}, "Open Chrome"))
                q = self._extract_search_query(cmd_lower)
                if q:
                    steps.append(PlanStep("youtube_search", {"query": q}, f"Search YouTube for {q}"))

                # Check if an ordinal selection is part of the command
                idx = self._extract_result_index(cmd_lower)
                if idx:
                    steps.append(PlanStep("select_result", {"index": idx}, f"Select video result #{idx}"))

                if "pause" in cmd_lower:
                    steps.append(PlanStep("pause_media", {}, "Pause video"))
                return steps
                # Direct "open youtube" -> open browser in guest mode searching youtube.com
                return [
                    PlanStep(
                        "open_url",
                        {"url": "https://www.youtube.com", "guest_mode": True},
                        "Open YouTube in guest mode",
                    )
                ]

        # "open browser and search [query]"
        browser_search_match = re.search(
            r"open\s+(?:browser|chrome)\s+(?:and\s+)?search\s+(?:for\s+)?(.+)",
            cmd_lower,
        )
        if browser_search_match:
            query = browser_search_match.group(1).strip()
            return [PlanStep("browser_search", {"query": query}, f"Search Chrome for {query}")]

        # --- Base44.app AI Web Builder Workflow ---
        # e.g., "open base44.app and create a website about a coffee shop"
        base44_match = re.search(
            r"open\s+(?:base44\.app|base44)\s+and\s+(?:create|build|make)\s+(?:a\s+)?(?:website|site)\s+(?:about|for|saying)?\s*(.+)",
            cmd_lower,
        )
        if base44_match:
            prompt = base44_match.group(1).strip()
            steps.append(PlanStep("open_url", {"url": "https://base44.app", "guest_mode": False}, "Open base44.app"))
            steps.append(PlanStep("type_text", {"text": f"create a website {prompt}"}, f"Type website prompt"))
            steps.append(PlanStep("press_key", {"key": "enter"}, "Submit prompt"))
            return steps

        # Search About Me / Who am I / User Profile
        about_me_patterns = [
            r"\bsearch\s+(?:about\s+)?(?:me|myself)\b",
            r"\bsearch\s+for\s+me\b",
            r"\bgoogle\s+(?:about\s+)?(?:me|myself)\b",
            r"\bwho\s+am\s+i\b",
            r"\bsearch\s+my\s+name\b",
            r"\btell\s+me\s+about\s+me\b",
            r"\blook\s+up\s+me\b",
            r"\bsearch\s+(?:about\s+)?gudise\b",
            r"\bsearch\s+(?:about\s+)?jayasimha\b",
        ]
        if any(re.search(p, cmd_lower) for p in about_me_patterns):
            target_name = getattr(settings, "USER_NAME", "Gudise Jayasimha Naidu")
            return [PlanStep("browser_search", {"query": target_name}, f"Search for {target_name}")]

        # Standalone search queries
        if cmd_lower.startswith(("search for", "search youtube", "search google", "search")):
            query = self._extract_search_query(cmd_lower)
            if "youtube" in cmd_lower:
                return [PlanStep("youtube_search", {"query": query}, f"Search YouTube for {query}")]
            return [PlanStep("browser_search", {"query": query}, f"Search for {query}")]

        # Standalone result selection: "open the second one", "open the first result"
        idx = self._extract_result_index(cmd_lower)
        if idx and ("open" in cmd_lower or "select" in cmd_lower or "play" in cmd_lower or "click" in cmd_lower):
            return [PlanStep("select_result", {"index": idx}, f"Select result #{idx}")]

        # Media Play / Pause
        if any(w in cmd_lower for w in ["pause", "stop playing"]):
            return [PlanStep("pause_media", {}, "Pause active media")]
        if any(w in cmd_lower for w in ["resume", "play", "unpause"]):
            return [PlanStep("play_media", {}, "Play/Resume media")]

        # --- Compound: Open App and Type/Write ---
        # e.g., "open notepad and type Hello World", "open notepad and write my name"
        open_and_type_match = re.search(
            r"open\s+([a-zA-Z0-9_\-\s]+?)\s+and\s+(?:type|write)\s+(.+)",
            cmd_lower,
        )
        if open_and_type_match:
            app_target = open_and_type_match.group(1).strip()
            text_to_type = open_and_type_match.group(2).strip()
            if text_to_type in ("my name", "my full name"):
                text_to_type = getattr(settings, "USER_NAME", "Gudise Jayasimha Naidu")
            text_to_type = text_to_type.strip("'\"")
            steps.append(PlanStep("open_application", {"app_name": app_target}, f"Open {app_target}"))
            steps.append(PlanStep("type_text", {"text": text_to_type}, f"Type '{text_to_type}'"))
            return steps

        # --- Direct Keyboard Typing ---
        # e.g., "type Hello World", "write Hello World", "type my name"
        type_match = re.search(r"^(?:type|write|enter text)\s+(.+)", cmd_lower)
        if type_match and not any(w in cmd_lower for w in ["file", "code in", "email to", "document called"]):
            raw_text = type_match.group(1).strip()
            press_enter = False
            if raw_text.endswith(("and press enter", "and hit enter")):
                raw_text = re.sub(r"\s+and\s+(?:press|hit)\s+enter$", "", raw_text).strip()
                press_enter = True

            if raw_text in ("my name", "my full name"):
                raw_text = getattr(settings, "USER_NAME", "Gudise Jayasimha Naidu")

            raw_text = raw_text.strip("'\"")
            steps.append(PlanStep("type_text", {"text": raw_text}, f"Type '{raw_text}'"))
            if press_enter:
                steps.append(PlanStep("press_key", {"key": "enter"}, "Press Enter"))
            return steps

        # --- Specific Key Presses ---
        # e.g., "press enter", "hit enter", "press space", "press tab", "press backspace", "press escape"
        press_key_match = re.search(r"^(?:press|hit)\s+(enter|space|tab|backspace|esc|escape|delete|up|down|left|right|home|end|f[1-9]|f1[0-2])\b", cmd_lower)
        if press_key_match:
            k = press_key_match.group(1).strip()
            return [PlanStep("press_key", {"key": k}, f"Press {k.upper()}")]

        # --- Common Keyboard Shortcuts ---
        if cmd_lower in ("copy", "copy this", "copy selection", "press ctrl c", "press ctrl+c"):
            return [PlanStep("keyboard_copy", {}, "Copy to clipboard (Ctrl+C)")]
        if cmd_lower in ("paste", "paste this", "paste here", "press ctrl v", "press ctrl+v"):
            return [PlanStep("keyboard_paste", {}, "Paste from clipboard (Ctrl+V)")]
        if cmd_lower in ("select all", "select everything", "press ctrl a", "press ctrl+a"):
            return [PlanStep("keyboard_select_all", {}, "Select all (Ctrl+A)")]
        if cmd_lower in ("save", "save this", "save file", "save document", "press ctrl s", "press ctrl+s"):
            return [PlanStep("keyboard_save", {}, "Save document (Ctrl+S)")]
        if cmd_lower in ("undo", "undo that", "press ctrl z", "press ctrl+z"):
            return [PlanStep("keyboard_undo", {}, "Undo last action (Ctrl+Z)")]
        if cmd_lower in ("redo", "redo that", "press ctrl y", "press ctrl+y"):
            return [PlanStep("hotkey", {"keys": "ctrl+y"}, "Redo action (Ctrl+Y)")]

        # Generic Key Combination: "press ctrl+alt+del", "press alt+tab", "press win+r", "press ctrl+w"
        shortcut_match = re.search(r"^(?:press|hit|shortcut)\s+([a-zA-Z0-9_\-+,\s]+)", cmd_lower)
        if shortcut_match and any(mod in cmd_lower for mod in ["ctrl", "alt", "shift", "win", "windows", "cmd"]):
            combo = shortcut_match.group(1).strip()
            return [PlanStep("hotkey", {"keys": combo}, f"Execute shortcut {combo}")]

        # App Launching: "open chrome", "launch notepad", "start vs code", "open calculator"
        open_match = re.search(r"(?:open|launch|start)\s+([a-zA-Z0-9_\-\s]+)", cmd_lower)
        if open_match and not any(w in cmd_lower for w in ["file", "folder", "url", "website"]):
            app = open_match.group(1).strip()
            # Clean common filler words
            app = re.sub(r"\b(my|the|a|app|application)\b", "", app).strip()
            return [PlanStep("open_application", {"app_name": app}, f"Launch {app}")]

        # App Switching: "switch to vs code", "switch to chrome"
        switch_match = re.search(r"switch\s+(?:to\s+)?([a-zA-Z0-9_\-\s]+)", cmd_lower)
        if switch_match:
            app = switch_match.group(1).strip()
            return [PlanStep("switch_application", {"app_name": app}, f"Switch to {app}")]

        # Close App: "close chrome", "close notepad"
        close_match = re.search(r"close\s+([a-zA-Z0-9_\-\s]+)", cmd_lower)
        if close_match:
            app = close_match.group(1).strip()
            return [PlanStep("close_application", {"app_name": app}, f"Close {app}")]

        # Windows Management: minimize, maximize
        if "minimize" in cmd_lower:
            return [PlanStep("minimize_window", {"window_title": context.current_application or ""}, "Minimize window")]
        if "maximize" in cmd_lower:
            return [PlanStep("maximize_window", {"window_title": context.current_application or ""}, "Maximize window")]

        # Volume Controls
        if "volume up" in cmd_lower or "louder" in cmd_lower:
            return [PlanStep("system_volume_up", {"steps": 5}, "Increase system volume")]
        if "volume down" in cmd_lower or "quieter" in cmd_lower:
            return [PlanStep("system_volume_down", {"steps": 5}, "Decrease system volume")]
        if "mute" in cmd_lower or "unmute" in cmd_lower:
            return [PlanStep("system_mute", {}, "Toggle system mute")]

        # Screenshots
        if "screenshot" in cmd_lower or "capture screen" in cmd_lower:
            return [PlanStep("take_screenshot", {"name": "screen"}, "Capture screenshot")]

        # Scrolling
        if "scroll down" in cmd_lower:
            return [PlanStep("scroll_down", {"amount": 5}, "Scroll down")]
        if "scroll up" in cmd_lower:
            return [PlanStep("scroll_up", {"amount": 5}, "Scroll up")]

        # File Creation
        if "create file" in cmd_lower or "make file" in cmd_lower:
            name_match = re.search(r"(?:file|named|called)\s+([a-zA-Z0-9_.\-]+)", cmd)
            filename = name_match.group(1) if name_match else "new_document.txt"
            return [PlanStep("create_file", {"path": filename, "content": ""}, f"Create file {filename}")]

        # Default fallback: If unrecognized, return empty to prompt user clarification
        return steps

    def _extract_search_query(self, text: str) -> str:
        """Extracts search query from phrases like 'search for python tutorials'."""
        patterns = [
            r"search\s+(?:youtube\s+|google\s+)?for\s+(.+?)(?:,\s*open|\s+and|\s*$)",
            r"search\s+(.+?)(?:,\s*open|\s+and|\s*$)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                q = m.group(1).strip()
                # Remove trailing words like 'on my phone' or 'on laptop'
                q = re.sub(r"\s+on\s+my\s+(phone|laptop|pc)", "", q)
                return q
        return text

    def _extract_result_index(self, text: str) -> Optional[int]:
        """Extracts ordinal index (first=1, second=2, etc.) or resolved index numbers."""
        idx_match = re.search(r"\b(?:index|result|item|number)\s+(\d+)\b", text, re.IGNORECASE)
        if idx_match:
            return int(idx_match.group(1))

        mapping = {
            "first": 1, "1st": 1,
            "second": 2, "2nd": 2,
            "third": 3, "3rd": 3,
            "fourth": 4, "4th": 4,
            "fifth": 5, "5th": 5,
        }
        for word, val in mapping.items():
            if re.search(rf"\b{word}\b", text):
                return val
        return None

    def _extract_news_intent(self, text: str) -> Tuple[bool, int, Optional[str]]:
        """
        Detects if the user is asking for news or present day updates.
        Returns: (is_news: bool, count: int, topic: Optional[str])
        """
        clean = text.lower()

        # Check for news or present-day update keywords and phrases
        has_news_word = bool(re.search(r"\bnews\b", clean))
        has_present_day_update = bool(
            re.search(r"\bpresent\s+day\b", clean) and re.search(r"\bupdate(?:s)?\b", clean)
        )
        has_voice_updates = bool(
            re.search(r"\bupdate(?:s)?\b", clean) and ("voice format" in clean or "voice" in clean)
        )
        has_news_phrases = bool(
            re.search(
                r"\b(?:what\s+(?:is|are)\s+(?:the\s+)?news|news\s+update(?:s)?|today(?:'s)?\s+news|latest\s+news|headline(?:s)?)\b",
                clean,
            )
        )

        if not (has_news_word or has_present_day_update or has_voice_updates or has_news_phrases):
            return False, 7, None

        # Extract number of updates requested (defaults to 7)
        count = 7
        count_match = re.search(r"\b(\d+)\s*(?:update|news|headline|item|story|stories)", clean)
        if count_match:
            try:
                count = max(1, min(15, int(count_match.group(1))))
            except ValueError:
                count = 7
        else:
            word_to_num = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
            }
            for word, val in word_to_num.items():
                if re.search(rf"\b{word}\s*(?:update|news|headline|item|story|stories)", clean):
                    count = val
                    break

        # Extract optional topic
        topic = None
        topic_match = re.search(
            r"\b(tech|technology|ai|business|finance|crypto|sports|cricket|football|world|politics|entertainment|health|science)\s+news\b",
            clean,
        )
        if topic_match:
            topic = topic_match.group(1)

        return True, count, topic

    def _plan_with_llm(self, command: str) -> Optional[List[PlanStep]]:
        """LLM Function-calling planner for OpenAI / Gemini when configured."""
        schemas = tool_registry.get_tool_schemas_for_llm()
        context_prompt = memory.get_conversation_context_prompt()

        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": f"You are JARVIS, an autonomous PC/Mobile voice agent.\n{context_prompt}"},
                        {"role": "user", "content": command},
                    ],
                    tools=schemas,
                    tool_choice="auto",
                )
                message = response.choices[0].message
                if message.tool_calls:
                    steps = []
                    for tc in message.tool_calls:
                        name = tc.function.name
                        args = json.loads(tc.function.arguments or "{}")
                        steps.append(PlanStep(tool_name=name, parameters=args, description=f"Execute {name}"))
                    return steps
            except Exception as e:
                print(f"[OpenAI Planner Notice]: {e}")

        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                tool_descriptions = "\n".join([
                    f"- {t.name}: {t.description} (params: {list(t.parameters.keys())})"
                    for t in tool_registry.list_tools()
                ])
                prompt = (
                    f"You are JARVIS task planner. Plan the steps to satisfy the user's command.\n"
                    f"User Profile: The user's name is {settings.USER_NAME}. If the user asks to 'search about me', 'who am I', or 'google me', search for '{settings.USER_NAME}'.\n"
                    f"{context_prompt}\n"
                    f"Available Tools:\n{tool_descriptions}\n\n"
                    f"User command: {command}\n\n"
                    f"Output ONLY a valid JSON array of objects with keys 'tool_name', 'parameters', and 'description'. "
                    f"Example:\n"
                    f"[{{\"tool_name\": \"open_application\", \"parameters\": {{\"app_name\": \"chrome\"}}, \"description\": \"Open Chrome\"}}]"
                )
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                )
                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                    raw_text = re.sub(r"\n?```$", "", raw_text)
                data = json.loads(raw_text)
                if isinstance(data, list):
                    steps = []
                    for item in data:
                        steps.append(
                            PlanStep(
                                tool_name=item["tool_name"],
                                parameters=item.get("parameters", {}),
                                description=item.get("description", f"Execute {item['tool_name']}"),
                            )
                        )
                    if steps:
                        return steps
            except Exception as e:
                print(f"[Gemini Planner Notice]: {e}")

        return None


task_planner = TaskPlanner()
