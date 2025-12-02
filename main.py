import os
import json
import subprocess
import sys
import signal
import customtkinter as ctk
from tkinter import filedialog, messagebox

CONFIG_FILE = "config.json"
DEFAULT_BUFFER = 200

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(scrcpy_exe, adb_exe):
    config = {"scrcpy": scrcpy_exe, "adb": adb_exe}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def ask_scrcpy_folder():
    folder = filedialog.askdirectory(title="Selecione a pasta raiz do scrcpy")
    if not folder:
        return None
    scrcpy_exe, adb_exe = None, None
    for root, dirs, files in os.walk(folder):
        if "scrcpy.exe" in files:
            scrcpy_exe = os.path.join(root, "scrcpy.exe")
        if "adb.exe" in files:
            adb_exe = os.path.join(root, "adb.exe")
        if scrcpy_exe and adb_exe:
            break
    if not scrcpy_exe or not adb_exe:
        messagebox.showerror("Erro", "Não foi possível localizar scrcpy.exe ou adb.exe na pasta selecionada.")
        return None
    save_config(scrcpy_exe, adb_exe)
    return scrcpy_exe, adb_exe

# --- AJUSTE AQUI: Função auxiliar para suprimir janelas no Windows ---
def get_subprocess_flags():
    """Retorna flags para não abrir janela de console no Windows."""
    if os.name == 'nt':
        return subprocess.CREATE_NO_WINDOW
    return 0

def run_adb_command(adb_path, args, log_widget):
    try:
        # --- AJUSTE AQUI: Adicionado creationflags ---
        result = subprocess.run(
            [adb_path] + args, 
            capture_output=True, 
            text=True, 
            creationflags=get_subprocess_flags() 
        )
        log_widget.insert(ctk.END, result.stdout + result.stderr + "\n")
        log_widget.see(ctk.END)
        return result.returncode == 0
    except Exception as e:
        log_widget.insert(ctk.END, f"Erro: {e}\n")
        log_widget.see(ctk.END)
        return False

class AudioDroidApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.title("AudioDroid")
        self.geometry("700x200")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close_app)

        self.config_data = load_config()
        if not self.config_data:
            res = ask_scrcpy_folder()
            if not res:
                self.destroy()
                return
            scrcpy_exe, adb_exe = res
            self.config_data = {"scrcpy": scrcpy_exe, "adb": adb_exe}

        self.scrcpy_path = self.config_data["scrcpy"]
        self.adb_path = self.config_data["adb"]

        self.ip_var = ctk.StringVar(value="")
        self.port_var = ctk.StringVar(value="")
        self.buffer_var = ctk.IntVar(value=DEFAULT_BUFFER)

        self.create_widgets()
        signal.signal(signal.SIGINT, lambda s,f: self.close_app())

    def create_widgets(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_frame, text="IP:").grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(top_frame, textvariable=self.ip_var, width=120).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(top_frame, text="Porta:").grid(row=0, column=2, sticky="w")
        ctk.CTkEntry(top_frame, textvariable=self.port_var, width=80).grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(top_frame, text="Buffer:").grid(row=0, column=4, sticky="w")
        ctk.CTkEntry(top_frame, textvariable=self.buffer_var, width=80).grid(row=0, column=5, sticky="w")

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="Conexão Rápida", command=self.quick_connect).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Parear", command=self.pair_adb).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Conexão Manual", command=self.manual_connect).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Fechar Conexão", command=self.close_connection).pack(side="left", padx=5)

        self.log = ctk.CTkTextbox(self, height=350)
        self.log.pack(fill="both", expand=True, padx=10, pady=10)
        self.log.insert(ctk.END, "🎵 AudioDroid iniciado\n")
        self.log.see(ctk.END)

    def log_print(self, msg):
        self.log.insert(ctk.END, msg + "\n")
        self.log.see(ctk.END)

    def quick_connect(self):
        ip = self.ip_var.get()
        port = self.port_var.get()
        buffer = self.buffer_var.get()
        if not ip or not port:
            self.log_print("❗ IP e Porta devem ser preenchidos")
            return
        self.log_print(f"🔌 Tentando conectar {ip}:{port}...")
        run_adb_command(self.adb_path, ["connect", f"{ip}:{port}"], self.log)
        self.start_scrcpy(ip, port, buffer)

    def pair_adb(self):
        self.log_print("🔑 Iniciando pareamento via ADB...")
        run_adb_command(self.adb_path, ["pair"], self.log)

    def manual_connect(self):
        ip = self.ip_var.get()
        port = self.port_var.get()
        buffer = self.buffer_var.get()
        if not ip or not port:
            self.log_print("❗ IP e Porta devem ser preenchidos")
            return
        self.log_print(f"🔍 Tentando conexão manual {ip}:{port}...")
        run_adb_command(self.adb_path, ["connect", f"{ip}:{port}"], self.log)
        self.start_scrcpy(ip, port, buffer)

    def start_scrcpy(self, ip, port, buffer):
        cmd = [
            self.scrcpy_path,
            "--no-window",
            "--no-control",
            "--no-video",
            "--audio-source=playback",
            f"--audio-buffer={buffer}",
            "--audio-bit-rate=128K",
            f"--tcpip={ip}:{port}"
        ]
        self.log_print(f"▶ Iniciando scrcpy: {cmd}")
        try:
            # --- AJUSTE AQUI: Adicionado creationflags ---
            subprocess.Popen(cmd, creationflags=get_subprocess_flags())
        except Exception as e:
            self.log_print(f"Erro ao iniciar scrcpy: {e}")

    def close_connection(self):
        self.log_print("✖ Fechando conexão...")
        run_adb_command(self.adb_path, ["disconnect"], self.log)

    def close_app(self):
        self.close_connection()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = AudioDroidApp()
    app.mainloop()
