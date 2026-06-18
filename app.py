import customtkinter as ctk
import base64
import os
import threading
import wave
from pathlib import Path
from tkinter import filedialog, messagebox
from openai import OpenAI

# ── Theme ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SCRIPT_DIR = Path(__file__).resolve().parent
KEY_FILE = SCRIPT_DIR / "key.txt"
VOICES = [
    ("MiMo-默认", "mimo_default"),
    ("冰糖 (中文·女)", "冰糖"),
    ("茉莉 (中文·女)", "茉莉"),
    ("苏打 (中文·男)", "苏打"),
    ("白桦 (中文·男)", "白桦"),
    ("Mia (英文·女)", "Mia"),
    ("Chloe (英文·女)", "Chloe"),
    ("Milo (英文·男)", "Milo"),
    ("Dean (英文·男)", "Dean"),
]


def load_api_key() -> str:
    env_key = os.getenv("MIMO_API_KEY")
    if env_key:
        return env_key
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    return ""


def save_api_key(key: str) -> None:
    KEY_FILE.write_text(key.strip(), encoding="utf-8")


def get_client(key: str) -> OpenAI:
    return OpenAI(api_key=key, base_url="https://api.xiaomimimo.com/v1")


def encode_audio(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode()
    mime = "audio/mpeg" if path.suffix.lower() == ".mp3" else "audio/wav"
    return f"data:{mime};base64,{b64}"


def save_pcm16_wav(path: Path, pcm_bytes: bytes, sr: int = 24000) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm_bytes)


# ── Main App ─────────────────────────────────────────────────────────────
class MiMoTTSApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MiMo TTS Studio")
        self.geometry("780x720")
        self.minsize(700, 680)
        self.api_key = load_api_key()
        self.audio_ref_path: str | None = None
        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # Top bar: API Key
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(top, text="🔑 API Key", font=("", 14, "bold")).pack(side="left")
        self.key_entry = ctk.CTkEntry(top, show="•", width=340, placeholder_text="输入 API Key 或留空读取 key.txt")
        self.key_entry.pack(side="left", padx=(10, 6))
        if self.api_key:
            self.key_entry.insert(0, self.api_key)
        ctk.CTkButton(top, text="保存", width=60, command=self._save_key).pack(side="left")

        # Tabview for 3 modes
        self.tabs = ctk.CTkTabview(self, segmented_button_fg_color="#1f538d",
                                    segmented_button_selected_color="#2a7de1",
                                    segmented_button_unselected_color="#1a3a5c")
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(8, 16))

        self.tab_preset = self.tabs.add("预置音色")
        self.tab_design = self.tabs.add("音色设计")
        self.tab_clone  = self.tabs.add("音色克隆")

        self._build_preset_tab()
        self._build_design_tab()
        self._build_clone_tab()

    # ── Tab 1: Preset Voice ──────────────────────────────────────────────
    def _build_preset_tab(self) -> None:
        f = self.tab_preset
        # Voice selector
        row1 = ctk.CTkFrame(f, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(16, 4))
        ctk.CTkLabel(row1, text="选择音色", font=("", 13, "bold")).pack(side="left")
        self.preset_voice = ctk.CTkComboBox(row1, values=[v[0] for v in VOICES], width=220, state="readonly")
        self.preset_voice.set(VOICES[0][0])
        self.preset_voice.pack(side="left", padx=(10, 0))

        # Style
        ctk.CTkLabel(f, text="风格指令（可选，自然语言描述语气/情绪）", font=("", 13, "bold"), anchor="w").pack(fill="x", padx=16, pady=(12, 2))
        self.preset_style = ctk.CTkTextbox(f, height=60, font=("", 13))
        self.preset_style.pack(fill="x", padx=16, pady=(0, 4))
        self.preset_style.insert("1.0", "用轻快上扬的语调说，语速稍快，声音明亮有活力。")

        # Text
        ctk.CTkLabel(f, text="合成文本", font=("", 13, "bold"), anchor="w").pack(fill="x", padx=16, pady=(8, 2))
        self.preset_text = ctk.CTkTextbox(f, height=120, font=("", 13))
        self.preset_text.pack(fill="x", padx=16, pady=(0, 4))
        self.preset_text.insert("1.0", "你好，欢迎使用 MiMo 语音合成系统！")

        # Output & Generate
        row2 = ctk.CTkFrame(f, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(8, 8))
        ctk.CTkButton(row2, text="📁", width=36, command=lambda: self._pick_output(self.preset_out)).pack(side="left")
        self.preset_out = ctk.CTkEntry(row2, placeholder_text="输出文件路径", width=300)
        self.preset_out.insert(0, str(SCRIPT_DIR / "preset_output.wav"))
        self.preset_out.pack(side="left", padx=(6, 10))
        self.preset_btn = ctk.CTkButton(row2, text="🚀 生成语音", width=120, fg_color="#2a7de1", hover_color="#1f538d",
                                         command=lambda: self._run(self._do_preset, self.preset_btn))
        self.preset_btn.pack(side="left")

    # ── Tab 2: Voice Design ──────────────────────────────────────────────
    def _build_design_tab(self) -> None:
        f = self.tab_design
        ctk.CTkLabel(f, text="音色描述（描述你想要的音色特征）", font=("", 13, "bold"), anchor="w").pack(fill="x", padx=16, pady=(16, 2))
        self.design_voice_desc = ctk.CTkTextbox(f, height=80, font=("", 13))
        self.design_voice_desc.pack(fill="x", padx=16, pady=(0, 4))
        self.design_voice_desc.insert("1.0", "A warm, friendly young female voice with a slight British accent, speaking in a calm and soothing tone.")

        ctk.CTkLabel(f, text="合成文本", font=("", 13, "bold"), anchor="w").pack(fill="x", padx=16, pady=(8, 2))
        self.design_text = ctk.CTkTextbox(f, height=120, font=("", 13))
        self.design_text.pack(fill="x", padx=16, pady=(0, 4))
        self.design_text.insert("1.0", "The quick brown fox jumps over the lazy dog.")

        row2 = ctk.CTkFrame(f, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(8, 8))
        ctk.CTkButton(row2, text="📁", width=36, command=lambda: self._pick_output(self.design_out)).pack(side="left")
        self.design_out = ctk.CTkEntry(row2, placeholder_text="输出文件路径", width=300)
        self.design_out.insert(0, str(SCRIPT_DIR / "design_output.wav"))
        self.design_out.pack(side="left", padx=(6, 10))
        self.design_btn = ctk.CTkButton(row2, text="🚀 生成语音", width=120, fg_color="#2a7de1", hover_color="#1f538d",
                                         command=lambda: self._run(self._do_design, self.design_btn))
        self.design_btn.pack(side="left")

    # ── Tab 3: Voice Clone ───────────────────────────────────────────────
    def _build_clone_tab(self) -> None:
        f = self.tab_clone
        # Reference audio
        row0 = ctk.CTkFrame(f, fg_color="transparent")
        row0.pack(fill="x", padx=16, pady=(16, 4))
        ctk.CTkLabel(row0, text="参考音频（mp3/wav，≤10MB）", font=("", 13, "bold")).pack(side="left")
        self.clone_ref_entry = ctk.CTkEntry(row0, width=320, placeholder_text="选择参考音频文件...")
        self.clone_ref_entry.pack(side="left", padx=(10, 6))
        ctk.CTkButton(row0, text="浏览...", width=70, command=self._pick_ref_audio).pack(side="left")

        # Style
        ctk.CTkLabel(f, text="风格指令（可选）", font=("", 13, "bold"), anchor="w").pack(fill="x", padx=16, pady=(8, 2))
        self.clone_style = ctk.CTkTextbox(f, height=60, font=("", 13))
        self.clone_style.pack(fill="x", padx=16, pady=(0, 4))

        # Text
        ctk.CTkLabel(f, text="合成文本", font=("", 13, "bold"), anchor="w").pack(fill="x", padx=16, pady=(8, 2))
        self.clone_text = ctk.CTkTextbox(f, height=120, font=("", 13))
        self.clone_text.pack(fill="x", padx=16, pady=(0, 4))
        self.clone_text.insert("1.0", "你好，这是克隆音色的测试。")

        # Stream toggle + output + generate
        row2 = ctk.CTkFrame(f, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(8, 8))
        self.clone_stream_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(row2, text="流式", variable=self.clone_stream_var, width=60).pack(side="left")
        ctk.CTkButton(row2, text="📁", width=36, command=lambda: self._pick_output(self.clone_out)).pack(side="left", padx=(10, 0))
        self.clone_out = ctk.CTkEntry(row2, placeholder_text="输出文件路径", width=260)
        self.clone_out.insert(0, str(SCRIPT_DIR / "clone_output.wav"))
        self.clone_out.pack(side="left", padx=(6, 10))
        self.clone_btn = ctk.CTkButton(row2, text="🚀 生成语音", width=120, fg_color="#2a7de1", hover_color="#1f538d",
                                        command=lambda: self._run(self._do_clone, self.clone_btn))
        self.clone_btn.pack(side="left")

    # ── Helpers ──────────────────────────────────────────────────────────
    def _save_key(self) -> None:
        key = self.key_entry.get().strip()
        if key:
            save_api_key(key)
            self.api_key = key
            messagebox.showinfo("成功", "API Key 已保存到 key.txt")
        else:
            messagebox.showwarning("提示", "请输入 API Key")

    def _pick_output(self, entry: ctk.CTkEntry) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")])
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _pick_ref_audio(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("音频文件", "*.mp3 *.wav")])
        if path:
            self.audio_ref_path = path
            self.clone_ref_entry.delete(0, "end")
            self.clone_ref_entry.insert(0, path)

    def _get_key(self) -> str:
        key = self.key_entry.get().strip() or self.api_key
        if not key:
            raise RuntimeError("请先填写 API Key（或在 key.txt 中配置）")
        return key

    def _set_status(self, btn: ctk.CTkButton, text: str, disabled: bool = True) -> None:
        btn.configure(text=text, state="disabled" if disabled else "normal")

    def _run(self, func, btn: ctk.CTkButton) -> None:
        self._set_status(btn, "⏳ 生成中...")
        threading.Thread(target=self._worker, args=(func, btn), daemon=True).start()

    def _worker(self, func, btn: ctk.CTkButton) -> None:
        try:
            func()
            self.after(0, lambda: messagebox.showinfo("完成", "语音生成成功！"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("错误", str(e)))
        finally:
            self.after(0, lambda: self._set_status(btn, "🚀 生成语音", disabled=False))

    # ── TTS Modes ────────────────────────────────────────────────────────
    def _do_preset(self) -> None:
        key = self._get_key()
        client = get_client(key)
        voice_name = self.preset_voice.get()
        voice_id = next(v[1] for v in VOICES if v[0] == voice_name)
        style = self.preset_style.get("1.0", "end").strip()
        text = self.preset_text.get("1.0", "end").strip()
        output = Path(self.preset_out.get())
        if not text:
            raise RuntimeError("合成文本不能为空")

        messages = [
            {"role": "user", "content": style},
            {"role": "assistant", "content": text},
        ]
        completion = client.chat.completions.create(
            model="mimo-v2.5-tts",
            messages=messages,
            audio={"format": "wav", "voice": voice_id},
        )
        audio_bytes = base64.b64decode(completion.choices[0].message.audio.data)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(audio_bytes)

    def _do_design(self) -> None:
        key = self._get_key()
        client = get_client(key)
        voice_desc = self.design_voice_desc.get("1.0", "end").strip()
        text = self.design_text.get("1.0", "end").strip()
        output = Path(self.design_out.get())
        if not voice_desc:
            raise RuntimeError("音色描述不能为空")
        if not text:
            raise RuntimeError("合成文本不能为空")

        messages = [
            {"role": "user", "content": voice_desc},
            {"role": "assistant", "content": text},
        ]
        completion = client.chat.completions.create(
            model="mimo-v2.5-tts-voicedesign",
            messages=messages,
            audio={"format": "wav", "optimize_text_preview": True},
        )
        audio_bytes = base64.b64decode(completion.choices[0].message.audio.data)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(audio_bytes)

    def _do_clone(self) -> None:
        key = self._get_key()
        client = get_client(key)
        ref_path_str = self.clone_ref_entry.get().strip()
        if not ref_path_str:
            raise RuntimeError("请选择参考音频文件")
        ref_path = Path(ref_path_str)
        if not ref_path.exists():
            raise RuntimeError(f"参考音频文件不存在: {ref_path}")

        style = self.clone_style.get("1.0", "end").strip()
        text = self.clone_text.get("1.0", "end").strip()
        output = Path(self.clone_out.get())
        stream = self.clone_stream_var.get()
        if not text:
            raise RuntimeError("合成文本不能为空")

        voice_uri = encode_audio(ref_path)
        messages = [
            {"role": "user", "content": style},
            {"role": "assistant", "content": text},
        ]

        if stream:
            completion = client.chat.completions.create(
                model="mimo-v2.5-tts-voiceclone",
                messages=messages,
                audio={"format": "pcm16", "voice": voice_uri},
                stream=True,
            )
            pcm_chunks: list[bytes] = []
            for chunk in completion:
                if not chunk.choices:
                    continue
                audio = getattr(chunk.choices[0].delta, "audio", None)
                if audio and isinstance(audio, dict) and "data" in audio:
                    pcm_chunks.append(base64.b64decode(audio["data"]))
            output.parent.mkdir(parents=True, exist_ok=True)
            save_pcm16_wav(output, b"".join(pcm_chunks))
        else:
            completion = client.chat.completions.create(
                model="mimo-v2.5-tts-voiceclone",
                messages=messages,
                audio={"format": "wav", "voice": voice_uri},
            )
            audio_bytes = base64.b64decode(completion.choices[0].message.audio.data)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(audio_bytes)


if __name__ == "__main__":
    app = MiMoTTSApp()
    app.mainloop()

