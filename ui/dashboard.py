"""
Desktop GUI for J.A.R.V.I.S. Personal AI Assistant.
Ultra-Clean, Minimal, Futuristic JARVIS-Inspired Interface.

Core Composition:
BLACK SPACE → ARC REACTOR → JARVIS → TIME + AI BRAIN

Features:
- Pure dark black / obsidian cinematic background (#010306) with abundant empty space
- Dominant central Mark VII / Mark VI Arc Reactor with realistic Iron Man energy-core
  (layered mechanical housing, 10 electromagnetic copper coils, counter-rotating telemetry,
   precision tachymeter teeth, inverted triangular core, cyan-white energy breath & shockwaves)
- Prominent futuristic "JARVIS" typography with multi-layered holographic cyan glow
- Discreet, clean digital clock & calendar timestamp
- Small, sophisticated digital AI Brain / neural-network visualization with interconnected synapses,
  pulsing data packets, and live neural impulses
- Clickable Arc Reactor for voice activation (or Spacebar / Enter for sleek floating HUD directive)
- 100% free of UI clutter, sidebars, cards, charts, panels, widgets, or extra buttons
"""

import math
import random
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from typing import Optional, List, Dict, Any, Tuple

from config.settings import ROOT_DIR
from core.context import context, DeviceType
from core.permissions import permission_manager
from core.agent import jarvis_agent
from voice.speech_to_text import stt
from logging_system.logger import jarvis_logger, JarvisActionRecord


class JarvisMinimalDashboard:
    """Ultra-clean, minimal, futuristic JARVIS HUD Dashboard."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("J.A.R.V.I.S.")
        self.root.geometry("1020x860")
        self.root.minsize(780, 680)
        self.root.configure(bg="#010306")

        # Set Window Icon if present
        try:
            ico_file = ROOT_DIR / "assets" / "jarvis_icon.ico"
            if ico_file.exists():
                self.root.iconbitmap(str(ico_file))
        except Exception:
            pass

        # Color Palette: Deep Black Void & Luminous Cyan/Blue-White Core
        self.c_bg = "#010306"             # Pure cosmic void / near-black
        self.c_white = "#F0FDFF"          # Brilliant core white
        self.c_cyan_bright = "#00F0FF"    # Electric Arc Cyan
        self.c_cyan_glow = "#38BDF8"      # Mid-frequency Sky Cyan
        self.c_cyan_dim = "#0284C7"       # Structural Cobalt
        self.c_blue_dark = "#031E38"      # Chassis Deep Navy
        self.c_blue_faint = "#061A2D"     # Faint Orbital Rings
        self.c_text_main = "#E0F7FF"      # High-contrast readable typography
        self.c_text_sub = "#7DD3FC"       # Secondary cyan captions
        self.c_text_dim = "#244D6E"       # Muted subtle HUD markings
        self.c_copper = "#38BDF8"         # High-tech coil windings
        self.c_rose = "#F43F5E"           # Halt / Warning state

        # Runtime Engine State
        self.hud_state = "IDLE"           # "IDLE", "LISTENING", "PROCESSING", "HALTED"
        self.reactor_angle = 0.0          # Outer mechanical ring rotation
        self.inner_angle = 0.0            # Counter-rotating gear rotation
        self.pulse_phase = 0.0            # Breathing energy pulse
        self.wave_energy = 0.20
        self.target_wave_energy = 0.20
        self.core_hovered = False
        self.last_cx = 510.0
        self.last_cy = 430.0
        self.reactor_radius = 250.0       # Dominant central arc reactor radius

        # Status text & spoken feedback
        self.status_caption = "SYSTEM ONLINE"
        self.response_text = ""
        self.response_clear_time = 0.0

        # Acoustic / shockwave ripples during listening
        self.shockwaves: List[Dict[str, float]] = []

        # Floating prompt input (discreet, appears only when typing/commanding)
        self.input_active = False
        self.input_text = ""
        self.is_running = True
        # DNA 3D helix angle
        self.dna_angle = 0.0

        # Background blue particles system
        self._init_particles()

        # Setup AI Brain Neural Network
        self._init_ai_brain()

        # Build Main Canvas
        self._build_viewport()

        # Bind Global Controls
        self._bind_interactions()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start Real-time Animation Pipeline
        self._start_animation_pipeline()

        # Connect Backend Callbacks
        jarvis_logger.register_ui_callback(self._on_action_logged)
        permission_manager.set_confirmation_callback(self._on_confirmation_requested)

    def _on_close(self):
        """Cleanly terminates animation cycle and destroys window."""
        self.is_running = False
        try:
            self.root.destroy()
        except Exception:
            pass

    # -------------------------------------------------------------
    # Cosmic Blue Particles Initialization
    # -------------------------------------------------------------
    def _init_particles(self):
        """Constructs 65 floating blue cosmic particles with subtle drift."""
        self.particles: List[Dict[str, Any]] = []
        blue_palette = ["#00F0FF", "#38BDF8", "#0284C7", "#60A5FA", "#93C5FD", "#0269A4"]
        for _ in range(65):
            self.particles.append({
                "x": random.uniform(10, 1010),
                "y": random.uniform(10, 850),
                "vx": random.uniform(-0.35, 0.35),
                "vy": random.uniform(-0.30, 0.30),
                "r": random.uniform(1.2, 2.8),
                "color": random.choice(blue_palette),
                "phase": random.uniform(0.0, 6.28),
                "speed": random.uniform(0.03, 0.07),
            })

    # -------------------------------------------------------------
    # AI Brain Neural Architecture Initialization
    # -------------------------------------------------------------
    def _init_ai_brain(self):
        """Constructs a sleek, anatomically inspired dual-hemisphere neural matrix."""
        # Normalized coordinates relative to brain center (-1.0 to +1.0)
        # 22 cerebral neural nodes outlining hemispheres, frontal, parietal, occipital, temporal lobes
        self.brain_nodes_norm = [
            # Left Hemisphere Profile
            (-0.35, -0.70),  # 0: Prefrontal
            (-0.62, -0.48),  # 1: Superior Frontal
            (-0.80, -0.18),  # 2: Motor / Parietal
            (-0.82, 0.15),   # 3: Sensory / Temporal
            (-0.68, 0.46),   # 4: Occipital upper
            (-0.42, 0.68),   # 5: Occipital / Cerebellar
            (-0.18, 0.48),   # 6: Midbrain lower left
            (-0.12, 0.18),   # 7: Thalamic hub left
            (-0.12, -0.22),  # 8: Cingulate left
            (-0.40, -0.15),  # 9: Internal cortex left A
            (-0.46, 0.18),   # 10: Internal cortex left B

            # Right Hemisphere Profile (Complementary)
            (0.35, -0.70),   # 11: Prefrontal
            (0.62, -0.48),   # 12: Superior Frontal
            (0.80, -0.18),   # 13: Motor / Parietal
            (0.82, 0.15),    # 14: Sensory / Temporal
            (0.68, 0.46),    # 15: Occipital upper
            (0.42, 0.68),    # 16: Occipital / Cerebellar
            (0.18, 0.48),    # 17: Midbrain lower right
            (0.12, 0.18),    # 18: Thalamic hub right
            (0.12, -0.22),   # 19: Cingulate right
            (0.40, -0.15),   # 20: Internal cortex right A
            (0.46, 0.18),    # 21: Internal cortex right B
        ]

        # Synaptic Axon Connections (Edges between nodes)
        self.brain_edges = [
            # Left Contour
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 0),
            (1, 9), (9, 2), (9, 10), (10, 3), (10, 4), (9, 8), (10, 7),
            # Right Contour
            (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 11),
            (12, 20), (20, 13), (20, 21), (21, 14), (21, 15), (20, 19), (21, 18),
            # Corpus Callosum Inter-Hemispheric Synapses
            (0, 11), (8, 19), (7, 18), (6, 17),
        ]

        # Active Data Packets (Pulsing impulses traveling along axons)
        self.data_pulses: List[Dict[str, Any]] = []
        for _ in range(6):
            edge = random.choice(self.brain_edges)
            direction = 1 if random.random() > 0.5 else -1
            u, v = (edge[0], edge[1]) if direction == 1 else (edge[1], edge[0])
            self.data_pulses.append({
                "u": u,
                "v": v,
                "progress": random.uniform(0.0, 1.0),
                "speed": random.uniform(0.025, 0.055),
            })

        # Node luminescence modulation
        self.node_intensities = [random.uniform(0.3, 0.8) for _ in self.brain_nodes_norm]

    # -------------------------------------------------------------
    # Viewport & Layout Construction
    # -------------------------------------------------------------
    def _build_viewport(self):
        """Creates the single full-bleed, clutter-free viewport canvas."""
        self.canvas = tk.Canvas(
            self.root,
            bg=self.c_bg,
            highlightthickness=0,
            cursor="arrow",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _bind_interactions(self):
        """Binds seamless user interactions (reactor click, spacebar, typing)."""
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.root.bind("<space>", lambda e: self._on_voice_trigger())
        self.root.bind("<v>", lambda e: self._on_voice_trigger())
        self.root.bind("<V>", lambda e: self._on_voice_trigger())
        self.root.bind("<Escape>", lambda e: self._on_escape_press())
        self.root.bind("<Return>", lambda e: self._on_return_press())
        self.root.bind("<Key>", self._on_keypress)

    # -------------------------------------------------------------
    # Event Handlers & Voice Automation
    # -------------------------------------------------------------
    def _on_canvas_click(self, event):
        """Clicking the central Arc Reactor triggers voice listening or clears halt."""
        dist = math.hypot(event.x - self.last_cx, event.y - self.last_cy)
        if dist <= self.reactor_radius:
            if self.hud_state == "HALTED":
                self.hud_state = "IDLE"
                self.status_caption = "SYSTEM ONLINE"
                self.response_text = "Systems restored, sir."
                self.response_clear_time = time.time() + 4.0
            else:
                self._on_voice_trigger()

    def _on_canvas_motion(self, event):
        """Hovering over the central Arc Reactor highlights cursor and core illumination."""
        dist = math.hypot(event.x - self.last_cx, event.y - self.last_cy)
        if dist <= self.reactor_radius:
            self.canvas.config(cursor="hand2")
            self.core_hovered = True
        else:
            self.canvas.config(cursor="arrow")
            self.core_hovered = False

    def _on_escape_press(self):
        """Escape halts current execution or closes active input."""
        if self.input_active:
            self.input_active = False
            self.input_text = ""
            return
        # Emergency Halt
        jarvis_agent.handle_emergency_stop()
        self.hud_state = "HALTED"
        self.status_caption = "EMERGENCY HALT"
        self.response_text = "Automation suspended. Click reactor to restore."
        self.response_clear_time = time.time() + 8.0

    def _on_return_press(self):
        """Enter activates floating HUD prompt or dispatches typed directive."""
        if not self.input_active:
            self.input_active = True
            self.input_text = ""
        else:
            cmd = self.input_text.strip()
            self.input_active = False
            self.input_text = ""
            if cmd:
                self._dispatch_command(cmd)

    def _on_keypress(self, event):
        """Handles subtle keyboard input without bulky form widgets."""
        if not self.input_active:
            # If user presses colon or alphanumeric key directly, auto-open sleek directive input
            if event.char and event.char.isalnum():
                self.input_active = True
                self.input_text = event.char
            return

        if event.keysym == "BackSpace":
            self.input_text = self.input_text[:-1]
        elif event.char and event.char.isprintable() and event.keysym != "Return":
            self.input_text += event.char

    def _on_voice_trigger(self):
        """Engages speech recognition with instant visual feedback."""
        if self.hud_state == "LISTENING":
            return
        self.hud_state = "LISTENING"
        self.status_caption = "LISTENING . . ."
        self.response_text = ""
        self.target_wave_energy = 0.95

        def listen_worker():
            try:
                heard = stt.listen_from_mic(duration_seconds=4.0)
                if heard:
                    self.root.after(0, lambda: self._dispatch_command(heard))
                else:
                    self.root.after(0, self._on_listening_timeout)
            except Exception:
                self.root.after(0, self._on_listening_timeout)

        threading.Thread(target=listen_worker, daemon=True).start()

    def _on_listening_timeout(self):
        if self.hud_state == "LISTENING":
            self.hud_state = "IDLE"
            self.status_caption = "SYSTEM ONLINE"
            self.target_wave_energy = 0.20

    def _dispatch_command(self, cmd_text: str):
        self.hud_state = "PROCESSING"
        self.status_caption = "PROCESSING DIRECTIVE"
        self.response_text = f'"{cmd_text.upper()}"'
        self.response_clear_time = time.time() + 12.0
        self.target_wave_energy = 0.70

        def worker():
            try:
                resp = jarvis_agent.process_command(cmd_text)
                self.root.after(0, lambda: self._on_command_finished(resp))
            except Exception as e:
                self.root.after(0, lambda: self._on_command_finished(f"Notice: {str(e)}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_command_finished(self, response: str):
        self.hud_state = "IDLE"
        self.status_caption = "SYSTEM ONLINE"
        self.target_wave_energy = 0.20
        # Voice-only mode: clear the display, let JARVIS speak it instead
        self.response_text = ""
        self.response_clear_time = 0

    def _on_action_logged(self, record: JarvisActionRecord):
        # Update transient status subtitle if relevant
        if record.tool:
            tool_name = record.tool.replace("_", " ").upper()
            self.status_caption = f"EXECUTING // {tool_name}"

    def _on_confirmation_requested(self, tool_name: str, params: dict) -> bool:
        """High-risk action confirmation modal."""
        return messagebox.askyesno(
            "STARK PROTOCOL // Authorization Required",
            f"JARVIS requires operator clearance to execute sensitive action:\n\n"
            f"Directive / Tool: {tool_name}\n"
            f"Parameters: {params}\n\n"
            f"Grant authorization, sir?",
            parent=self.root,
        )

    # -------------------------------------------------------------
    # Render & Animation Pipeline
    # -------------------------------------------------------------
    def _start_animation_pipeline(self):
        self._render_frame()

    def _render_frame(self):
        if not self.is_running:
            return
        try:
            self.canvas.delete("all")
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()

            if w <= 1 or h <= 1:
                w, h = 1020, 860

            cx, cy = w / 2.0, h / 2.0
            self.last_cx = cx
            self.last_cy = cy

            # Smooth Physics & Oscillators
            self.wave_energy += (self.target_wave_energy - self.wave_energy) * 0.08
            rot_speed = 0.012 if self.hud_state != "PROCESSING" else 0.038
            self.reactor_angle += rot_speed
            self.inner_angle -= rot_speed * 0.75
            self.dna_angle += 0.032 if self.hud_state != "PROCESSING" else 0.075
            self.pulse_phase += 0.045 + (self.wave_energy * 0.06)

            # Palette modulation according to HUD state
            if self.hud_state == "HALTED":
                glow_cyan = self.c_rose
                core_white = "#FFE4E6"
                primary_cyan = self.c_rose
                faint_ring = "#350E14"
            elif self.hud_state == "LISTENING":
                glow_cyan = "#00FFFF"
                core_white = "#FFFFFF"
                primary_cyan = "#00FFFF"
                faint_ring = "#062A48"
                # Emit acoustic shockwave ripples
                if len(self.shockwaves) < 5 and random.random() < 0.25:
                    self.shockwaves.append({"r": 60.0, "alpha": 1.0})
            elif self.hud_state == "PROCESSING":
                glow_cyan = "#38BDF8"
                core_white = "#FFFFFF"
                primary_cyan = "#38BDF8"
                faint_ring = "#0A2846"
            else:  # IDLE
                glow_cyan = self.c_cyan_glow
                core_white = self.c_white
                primary_cyan = self.c_cyan_bright
                faint_ring = self.c_blue_faint

            # ---------------------------------------------------------
            # 1. Background: Drifting Blue Cosmic Particles
            # ---------------------------------------------------------
            self._render_particles(w, h)

            # Subtle Deep Space Vignette & Ambient Radial Energy
            self.canvas.create_oval(
                cx - 380, cy - 380, cx + 380, cy + 380,
                outline="#020912", width=1,
            )
            self.canvas.create_oval(
                cx - 280, cy - 280, cx + 280, cy + 280,
                outline=faint_ring, width=1, dash=(3, 15),
            )

            # ---------------------------------------------------------
            # 2. Central Arc Reactor (Primary & Dominant Visual Element)
            # ---------------------------------------------------------
            self._render_arc_reactor(cx, cy, primary_cyan, glow_cyan, core_white)

            # ---------------------------------------------------------
            # 3. JARVIS Name (Prominent Futuristic Typography + Glow)
            # ---------------------------------------------------------
            self._render_jarvis_brand(cx, cy, primary_cyan, glow_cyan)

            # ---------------------------------------------------------
            # 4. Clean Digital Time (Discreetly Positioned Near Reactor)
            # ---------------------------------------------------------
            self._render_digital_time(cx, cy)

            # ---------------------------------------------------------
            # 5. AI Brain Visualization (Digital Neural Network)
            # ---------------------------------------------------------
            self._render_ai_brain(cx, cy, primary_cyan, glow_cyan)

            # ---------------------------------------------------------
            # 6. Blue 3D DNA Double-Helix Visualization
            # ---------------------------------------------------------
            self._render_dna_helix(cx, cy, primary_cyan, glow_cyan)

            # ---------------------------------------------------------
            # 7. Sleek Floating Directive Input (If Operator Types)
            # ---------------------------------------------------------
            self._render_floating_input(cx, cy, w)

        except Exception:
            pass

        # 60 FPS silky smooth loop
        if self.is_running:
            try:
                self.root.after(16, self._render_frame)
            except Exception:
                pass

    # -------------------------------------------------------------
    # Arc Reactor Component Rendering
    # -------------------------------------------------------------
    def _render_arc_reactor(self, cx: float, cy: float, primary_cyan: str, glow_cyan: str, core_white: str):
        """Renders the realistic Iron Man Arc Reactor with multi-tiered physical details."""
        R = self.reactor_radius
        pulse = math.sin(self.pulse_phase) * 0.5 + 0.5  # 0.0 to 1.0

        # Dynamic Listening Acoustic Ripples
        next_waves = []
        for sw in self.shockwaves:
            sw["r"] += 3.2
            if sw["r"] < R + 75:
                rw = sw["r"]
                self.canvas.create_oval(
                    cx - rw, cy - rw, cx + rw, cy + rw,
                    outline=glow_cyan, width=1, dash=(3, 6),
                )
                next_waves.append(sw)
        self.shockwaves = next_waves

        # Outer Subtle Telemetry Tick Ring (R + 24)
        r_tick_ring = R + 22
        self.canvas.create_oval(
            cx - r_tick_ring, cy - r_tick_ring, cx + r_tick_ring, cy + r_tick_ring,
            outline="#06223B", width=1,
        )
        # 36 Degree Ticks
        for i in range(36):
            ang = (i * 10) * (math.pi / 180.0) + self.reactor_angle * 0.35
            is_major = (i % 9 == 0)
            t_len = 8 if is_major else 4
            x1 = cx + (r_tick_ring - t_len) * math.cos(ang)
            y1 = cy + (r_tick_ring - t_len) * math.sin(ang)
            x2 = cx + r_tick_ring * math.cos(ang)
            y2 = cy + r_tick_ring * math.sin(ang)
            col = glow_cyan if is_major else "#0B385C"
            self.canvas.create_line(x1, y1, x2, y2, fill=col, width=1)

        # 3 Segmented Rotating Neon Arcs (Smooth outer orbital energy)
        for arc_idx in range(3):
            start_deg = (arc_idx * 120.0) + (self.reactor_angle * (180.0 / math.pi))
            self.canvas.create_arc(
                cx - (r_tick_ring + 6), cy - (r_tick_ring + 6),
                cx + (r_tick_ring + 6), cy + (r_tick_ring + 6),
                start=start_deg, extent=38, style=tk.ARC,
                outline=glow_cyan, width=2,
            )

        # Mechanical Outer Chassis Rings
        r_out = R + 2
        r_in = R - 36
        self.canvas.create_oval(cx - r_out, cy - r_out, cx + r_out, cy + r_out, outline=glow_cyan, width=2)
        self.canvas.create_oval(cx - r_in, cy - r_in, cx + r_in, cy + r_in, outline="#073B66", width=2)

        # 10 Symmetrical Electromagnetic Copper Coils (The Iconic Arc Reactor Detail)
        num_coils = 10
        for i in range(num_coils):
            theta = (i / num_coils) * 2 * math.pi
            d_th = (math.pi / num_coils) * 0.62

            # 4 polygon vertices of the trapezoid block
            c1_x = cx + (r_out - 1) * math.cos(theta - d_th)
            c1_y = cy + (r_out - 1) * math.sin(theta - d_th)
            c2_x = cx + (r_out - 1) * math.cos(theta + d_th)
            c2_y = cy + (r_out - 1) * math.sin(theta + d_th)
            c3_x = cx + (r_in + 1) * math.cos(theta + d_th)
            c3_y = cy + (r_in + 1) * math.sin(theta + d_th)
            c4_x = cx + (r_in + 1) * math.cos(theta - d_th)
            c4_y = cy + (r_in + 1) * math.sin(theta - d_th)

            # Metallic coil backing with crisp cyan outline
            self.canvas.create_polygon(
                [c1_x, c1_y, c2_x, c2_y, c3_x, c3_y, c4_x, c4_y],
                fill="#031A30",
                outline=primary_cyan,
                width=1,
            )

            # 3 High-density copper winding lines across the coil block
            for step in [0.35, 0.50, 0.65]:
                r_wire = r_in + (r_out - r_in) * step
                w1_x = cx + r_wire * math.cos(theta - d_th * 0.88)
                w1_y = cy + r_wire * math.sin(theta - d_th * 0.88)
                w2_x = cx + r_wire * math.cos(theta + d_th * 0.88)
                w2_y = cy + r_wire * math.sin(theta + d_th * 0.88)
                self.canvas.create_line(w1_x, w1_y, w2_x, w2_y, fill=glow_cyan, width=1)

        # Counter-Rotating Tachymeter Micro-Gear Ring (R_in - 8)
        r_gear = r_in - 8
        self.canvas.create_oval(cx - r_gear, cy - r_gear, cx + r_gear, cy + r_gear, outline="#052745", width=1)
        for g in range(60):
            g_ang = (g / 60.0) * 2 * math.pi + self.inner_angle
            g_len = 4 if g % 5 == 0 else 2
            gx1 = cx + (r_gear - g_len) * math.cos(g_ang)
            gy1 = cy + (r_gear - g_len) * math.sin(g_ang)
            gx2 = cx + r_gear * math.cos(g_ang)
            gy2 = cy + r_gear * math.sin(g_ang)
            g_col = primary_cyan if g % 5 == 0 else "#09365E"
            self.canvas.create_line(gx1, gy1, gx2, gy2, fill=g_col, width=1)

        # Translucent Inner Core Chamber (Deep Energy Well)
        r_core_chamber = r_in - 18
        self.canvas.create_oval(
            cx - r_core_chamber, cy - r_core_chamber,
            cx + r_core_chamber, cy + r_core_chamber,
            fill="#03162A",
            outline="#0D4675",
            width=2,
        )

        # The Iconic Mark VI Inverted Triangular Energy Core
        r_tri = (r_core_chamber - 12) + (3.0 * pulse)
        p_bottom = (cx, cy + r_tri)
        p_top_left = (cx - r_tri * 0.866025, cy - r_tri * 0.5)
        p_top_right = (cx + r_tri * 0.866025, cy - r_tri * 0.5)

        # Outer Glowing Energy Triangle
        self.canvas.create_polygon(
            [p_bottom[0], p_bottom[1], p_top_left[0], p_top_left[1], p_top_right[0], p_top_right[1]],
            fill="#04203B",
            outline=glow_cyan,
            width=2,
        )

        # Inner Beveled Core Triangle
        r_tri_in = r_tri * 0.68
        pi_bottom = (cx, cy + r_tri_in)
        pi_top_left = (cx - r_tri_in * 0.866025, cy - r_tri_in * 0.5)
        pi_top_right = (cx + r_tri_in * 0.866025, cy - r_tri_in * 0.5)
        self.canvas.create_polygon(
            [pi_bottom[0], pi_bottom[1], pi_top_left[0], pi_top_left[1], pi_top_right[0], pi_top_right[1]],
            fill="#062E54",
            outline=primary_cyan,
            width=1,
        )

        # 3 Radial Energy Conduits Connecting Center to Core Vertices
        for vp in [p_bottom, p_top_left, p_top_right]:
            self.canvas.create_line(cx, cy, vp[0], vp[1], fill=primary_cyan, width=2)

        # Harmonic Core Breathing Aura Rings (Layered Pulsing Illumination)
        r_glow_1 = 36.0 + (5.0 * pulse)
        r_glow_2 = 24.0 + (3.0 * pulse)
        r_center_core = 14.0 + (2.0 * pulse)

        if self.core_hovered:
            r_glow_1 += 4.0
            r_glow_2 += 3.0

        # Outer Soft Halo
        self.canvas.create_oval(
            cx - r_glow_1, cy - r_glow_1, cx + r_glow_1, cy + r_glow_1,
            outline=glow_cyan, width=1, dash=(2, 4),
        )
        # Inner Electric Ring
        self.canvas.create_oval(
            cx - r_glow_2, cy - r_glow_2, cx + r_glow_2, cy + r_glow_2,
            fill="#0A3C66",
            outline=primary_cyan,
            width=2,
        )
        # Intense Pure Core Light
        self.canvas.create_oval(
            cx - r_center_core, cy - r_center_core, cx + r_center_core, cy + r_center_core,
            fill=core_white,
            outline=primary_cyan,
            width=2,
        )

    # -------------------------------------------------------------
    # JARVIS Branding Component
    # -------------------------------------------------------------
    def _render_jarvis_brand(self, cx: float, cy: float, primary_cyan: str, glow_cyan: str):
        """Displays 'JARVIS' prominently near the Arc Reactor with sleek typography & glow."""
        # Positioned right above the Arc Reactor with plenty of breathing space
        brand_y = cy - self.reactor_radius - 75.0

        # Multi-layer subtle holographic glow (faint spread shadow offset)
        glow_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]
        for dx, dy in glow_offsets:
            self.canvas.create_text(
                cx + dx, brand_y + dy,
                text="J · A · R · V · I · S",
                font=("Segoe UI", 26, "bold"),
                fill="#052E52",
            )

        # Primary Crisp Futuristic Typography
        self.canvas.create_text(
            cx, brand_y,
            text="J · A · R · V · I · S",
            font=("Segoe UI", 26, "bold"),
            fill=self.c_text_main,
        )

        # Refined, minimal status subtitle line right under JARVIS
        sub_y = brand_y + 32.0

        # Minimal status indicator dot + caption
        pulse_alpha = math.sin(self.pulse_phase * 1.5) * 0.5 + 0.5
        caption_col = primary_cyan if self.hud_state != "IDLE" else self.c_text_sub

        self.canvas.create_text(
            cx, sub_y,
            text=f"•  {self.status_caption}  •",
            font=("Consolas", 8, "bold"),
            fill=caption_col,
        )

        # If there is active spoken response, display elegant single-line readout
        if self.response_text:
            if time.time() > self.response_clear_time and self.hud_state == "IDLE":
                self.response_text = ""
            else:
                disp_text = self.response_text
                if len(disp_text) > 85:
                    disp_text = disp_text[:82] + "..."
                self.canvas.create_text(
                    cx, sub_y + 20.0,
                    text=disp_text,
                    font=("Segoe UI", 9, "italic"),
                    fill=self.c_white,
                )

    # -------------------------------------------------------------
    # Digital Time Component
    # -------------------------------------------------------------
    def _render_digital_time(self, cx: float, cy: float):
        """Displays current time in a clean digital format discreetly near the Arc Reactor."""
        # Positioned beneath the Arc Reactor with balanced spacing
        time_y = cy + self.reactor_radius + 68.0

        now = datetime.now()
        time_str = now.strftime("%H : %M : %S")
        date_str = now.strftime("%A  •  %d %b %Y").upper()

        # Discreet digital clock
        self.canvas.create_text(
            cx, time_y,
            text=time_str,
            font=("Segoe UI", 16, "bold"),
            fill=self.c_text_sub,
        )

        # Clean calendar subtitle
        self.canvas.create_text(
            cx, time_y + 22.0,
            text=date_str,
            font=("Consolas", 8),
            fill=self.c_text_dim,
        )

    # -------------------------------------------------------------
    # AI Brain Neural Visualization Component
    # -------------------------------------------------------------
    def _render_ai_brain(self, cx: float, cy: float, primary_cyan: str, glow_cyan: str):
        """Renders small, sophisticated AI Brain neural network near the Arc Reactor."""
        # Positioned to the right of the Arc Reactor (or gracefully adjusted on smaller screens)
        # Width clearance check:
        w = self.canvas.winfo_width()
        if w >= 940:
            brain_cx = cx + self.reactor_radius + 155.0
            brain_cy = cy - 25.0
        else:
            brain_cx = cx + self.reactor_radius + 115.0
            brain_cy = cy - 20.0

        scale = 52.0  # Compact, refined size keeping it secondary to the Arc Reactor

        # Subtle Ambient Housing Orbit
        self.canvas.create_oval(
            brain_cx - 62, brain_cy - 62,
            brain_cx + 62, brain_cy + 62,
            outline="#031628", width=1, dash=(2, 8),
        )

        # Calculate actual (x, y) for all 22 neural nodes
        nodes_xy: List[Tuple[float, float]] = []
        for nx, ny in self.brain_nodes_norm:
            px = brain_cx + nx * scale
            py = brain_cy + ny * scale
            nodes_xy.append((px, py))

        # 1. Draw Axon Synapses (Edges)
        pulse_factor = 1.0 if self.hud_state != "PROCESSING" else 1.8
        for u, v in self.brain_edges:
            x1, y1 = nodes_xy[u]
            x2, y2 = nodes_xy[v]
            # Thin, delicate neural paths
            self.canvas.create_line(x1, y1, x2, y2, fill="#07223D", width=1)

        # 2. Update & Draw Dynamic Synaptic Data Pulses (Traveling Packets)
        for packet in self.data_pulses:
            packet["progress"] += packet["speed"] * pulse_factor
            if packet["progress"] >= 1.0:
                # Arrived at destination node: pick next adjacent edge
                packet["progress"] = 0.0
                curr_node = packet["v"]
                # Find neighboring edges
                neighbors = []
                for edge in self.brain_edges:
                    if edge[0] == curr_node:
                        neighbors.append(edge[1])
                    elif edge[1] == curr_node:
                        neighbors.append(edge[0])
                if neighbors:
                    packet["u"] = curr_node
                    packet["v"] = random.choice(neighbors)
                # Boost node intensity
                self.node_intensities[curr_node] = 1.0

            u_pos = nodes_xy[packet["u"]]
            v_pos = nodes_xy[packet["v"]]
            prog = packet["progress"]
            px = u_pos[0] + (v_pos[0] - u_pos[0]) * prog
            py = u_pos[1] + (v_pos[1] - u_pos[1]) * prog

            # Data packet head
            r_pkt = 1.8
            self.canvas.create_oval(
                px - r_pkt, py - r_pkt, px + r_pkt, py + r_pkt,
                fill=self.c_white, outline=primary_cyan, width=1,
            )

        # 3. Draw Neural Nodes (Neurons)
        for idx, (px, py) in enumerate(nodes_xy):
            # Decay intensity gently
            self.node_intensities[idx] = max(0.25, self.node_intensities[idx] - 0.02)
            intensity = self.node_intensities[idx]

            node_r = 2.2 + (1.2 * intensity)
            fill_col = self.c_white if intensity > 0.75 else (primary_cyan if intensity > 0.45 else "#0E4370")
            self.canvas.create_oval(
                px - node_r, py - node_r, px + node_r, py + node_r,
                fill=fill_col,
                outline="",
            )

        # Minimal AI Brain Caption
        self.canvas.create_text(
            brain_cx, brain_cy + 74.0,
            text="AI · NEURAL MATRIX",
            font=("Consolas", 7, "bold"),
            fill=self.c_text_dim,
        )

    # -------------------------------------------------------------
    # Cosmic Blue Particles Rendering
    # -------------------------------------------------------------
    def _render_particles(self, w: float, h: float):
        """Renders drifting blue cosmic particles with subtle constellation connections."""
        num_p = len(self.particles)
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["phase"] += p["speed"]

            # Wrap around boundaries smoothly
            if p["x"] < 0:
                p["x"] = w
            elif p["x"] > w:
                p["x"] = 0
            if p["y"] < 0:
                p["y"] = h
            elif p["y"] > h:
                p["y"] = 0

            r_anim = p["r"] + 0.45 * math.sin(p["phase"])
            self.canvas.create_oval(
                p["x"] - r_anim, p["y"] - r_anim,
                p["x"] + r_anim, p["y"] + r_anim,
                fill=p["color"],
                outline="",
            )

        # Faint constellation lines between close neighbors (optimized for high FPS)
        for i in range(0, min(num_p, 36), 2):
            p1 = self.particles[i]
            for j in range(i + 1, min(num_p, 36)):
                p2 = self.particles[j]
                dx = p1["x"] - p2["x"]
                dy = p1["y"] - p2["y"]
                if abs(dx) < 55 and abs(dy) < 55:
                    dist = math.hypot(dx, dy)
                    if dist < 55:
                        self.canvas.create_line(
                            p1["x"], p1["y"], p2["x"], p2["y"],
                            fill="#051D33", width=1,
                        )

    # -------------------------------------------------------------
    # 3D Rotating Blue DNA Double-Helix Visualization
    # -------------------------------------------------------------
    def _render_dna_helix(self, cx: float, cy: float, primary_cyan: str, glow_cyan: str):
        """Renders a rotating 3D holographic blue DNA double-helix on the left flank."""
        w = self.canvas.winfo_width()
        if w >= 940:
            dna_cx = cx - (self.reactor_radius + 155.0)
            dna_cy = cy - 25.0
        else:
            dna_cx = cx - (self.reactor_radius + 115.0)
            dna_cy = cy - 20.0

        # Subtle Ambient Housing Orbit
        self.canvas.create_oval(
            dna_cx - 52, dna_cy - 78,
            dna_cx + 52, dna_cy + 78,
            outline="#031628", width=1, dash=(2, 8),
        )

        amplitude = 26.0
        num_rungs = 17
        y_span = 130.0
        step = y_span / (num_rungs - 1)

        strand_a_pts: List[Tuple[float, float]] = []
        strand_b_pts: List[Tuple[float, float]] = []

        # Calculate all 3D coordinates for rungs and nodes
        rungs_data = []
        for i in range(num_rungs):
            y_rel = -(y_span / 2.0) + (i * step)
            theta = (y_rel * 0.046) + self.dna_angle

            x_off = math.cos(theta) * amplitude
            z_depth = math.sin(theta) * amplitude  # -amplitude (back) to +amplitude (front)
            norm_z = z_depth / amplitude           # -1.0 to +1.0

            pa = (dna_cx + x_off, dna_cy + y_rel)
            pb = (dna_cx - x_off, dna_cy + y_rel)

            strand_a_pts.append(pa)
            strand_b_pts.append(pb)
            rungs_data.append((pa, pb, norm_z))

        # 1. Draw Base-Pair Rungs with Depth Shading
        for pa, pb, norm_z in rungs_data:
            rung_col = glow_cyan if abs(norm_z) < 0.4 else (primary_cyan if norm_z > 0.0 else "#06294A")
            rung_w = 2 if norm_z > 0.3 else 1
            self.canvas.create_line(pa[0], pa[1], pb[0], pb[1], fill=rung_col, width=rung_w)

        # 2. Draw Helical Backbone Strands
        for i in range(len(strand_a_pts) - 1):
            p1_a, p2_a = strand_a_pts[i], strand_a_pts[i + 1]
            p1_b, p2_b = strand_b_pts[i], strand_b_pts[i + 1]
            self.canvas.create_line(p1_a[0], p1_a[1], p2_a[0], p2_a[1], fill="#0A3C6B", width=1)
            self.canvas.create_line(p1_b[0], p1_b[1], p2_b[0], p2_b[1], fill="#0A3C6B", width=1)

        # 3. Draw Base-Pair Spheres / Atoms with Depth Perception
        for pa, pb, norm_z in rungs_data:
            # Node A (Strand A)
            r_a = 2.4 + 1.2 * norm_z
            col_a = self.c_white if norm_z > 0.6 else (primary_cyan if norm_z > -0.1 else "#06294A")
            self.canvas.create_oval(
                pa[0] - r_a, pa[1] - r_a, pa[0] + r_a, pa[1] + r_a,
                fill=col_a, outline="",
            )

            # Node B (Strand B, inverse depth)
            norm_zb = -norm_z
            r_b = 2.4 + 1.2 * norm_zb
            col_b = self.c_white if norm_zb > 0.6 else (primary_cyan if norm_zb > -0.1 else "#06294A")
            self.canvas.create_oval(
                pb[0] - r_b, pb[1] - r_b, pb[0] + r_b, pb[1] + r_b,
                fill=col_b, outline="",
            )

        # Minimal DNA Helix Caption
        self.canvas.create_text(
            dna_cx, dna_cy + 74.0,
            text="DNA · GENOMIC CORE",
            font=("Consolas", 7, "bold"),
            fill=self.c_text_dim,
        )

    # -------------------------------------------------------------
    # Sleek Floating HUD Directive Input
    # -------------------------------------------------------------
    def _render_floating_input(self, cx: float, cy: float, w: float):
        """Displays an ultra-minimal, borderless floating directive line only when typing."""
        if not self.input_active:
            return

        input_y = cy + self.reactor_radius + 130.0
        prompt_w = min(540.0, w - 80.0)
        x1 = cx - prompt_w / 2.0
        x2 = cx + prompt_w / 2.0

        # Subtle glowing horizontal base line
        self.canvas.create_line(x1, input_y + 16.0, x2, input_y + 16.0, fill=self.c_cyan_bright, width=1)

        cursor_sym = "█" if int(time.time() * 2) % 2 == 0 else " "
        display_str = f"DIRECTIVE >  {self.input_text}{cursor_sym}"

        self.canvas.create_text(
            cx, input_y,
            text=display_str,
            font=("Consolas", 11),
            fill=self.c_text_main,
        )
        self.canvas.create_text(
            cx, input_y + 32.0,
            text="[ ENTER to transmit  •  ESC to dismiss ]",
            font=("Consolas", 7),
            fill=self.c_text_dim,
        )


# Aliases for backward compatibility
JarvisDashboard = JarvisMinimalDashboard
JarvisProDashboard = JarvisMinimalDashboard
JarvisHUDDashboard = JarvisMinimalDashboard


def launch_dashboard():
    """Initializes and runs the minimal futuristic JARVIS dashboard."""
    root = tk.Tk()
    app = JarvisMinimalDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    launch_dashboard()
