import json
import os
import subprocess
import shutil
import threading
import signal
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"ip": "", "port": "", "buffer": "200"}
    try:
        with open(CONFIG_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return {"ip": "", "port": "", "buffer": "200"}

def save_config(ip, port, buffer):
    with open(CONFIG_FILE, "w", encoding="utf8") as f:
        json.dump({"ip": ip, "port": port, "buffer": buffer}, f, indent=4)

def find_binary(name):
    return shutil.which(name)

adb_cmd = "adb"
scrcpy_cmd = find_binary("scrcpy")
config = load_config()

def run_adb(args, capture=True):
    try:
        if capture:
            res = subprocess.run([adb_cmd] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=False)
            return res.returncode, res.stdout.strip()
        else:
            res = subprocess.run([adb_cmd] + args, shell=False)
            return res.returncode, ""
    except FileNotFoundError:
        return 127, f"adb não encontrado: {adb_cmd}"
    except Exception as e:
        return 1, str(e)

class SaGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scrcpy Audio")
        self.geometry("360x300")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.scrcpy_proc = None
        self.adb_path = find_binary("adb")
        self.scrcpy_path = scrcpy_cmd

        self.ip_var = tk.StringVar(value=config.get("ip", ""))
        self.port_var = tk.StringVar(value=config.get("port", ""))
        self.buffer_var = tk.StringVar(value=config.get("buffer", "200"))

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="IP:").grid(row=0, column=0, sticky="w")
        self.ip_entry = ttk.Entry(frame, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=0, column=1, columnspan=2, sticky="w", padx=(6,0))

        ttk.Label(frame, text="Porta:").grid(row=1, column=0, sticky="w", pady=(8,0))
        self.port_entry = ttk.Entry(frame, textvariable=self.port_var, width=12)
        self.port_entry.grid(row=1, column=1, sticky="w", padx=(6,0), pady=(8,0))

        ttk.Label(frame, text="Audio Buffer (ms):").grid(row=2, column=0, sticky="w", pady=(8,0))
        self.buffer_entry = ttk.Entry(frame, textvariable=self.buffer_var, width=12)
        self.buffer_entry.grid(row=2, column=1, sticky="w", padx=(6,0), pady=(8,0))

        btn_quick = ttk.Button(frame, text="Quick Connect (porta=5555)", command=self.quick_connect)
        btn_quick.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(12,0))

        btn_set = ttk.Button(frame, text="Set 5555 via USB (adb tcpip 5555)", command=self.set_5555_usb)
        btn_set.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(6,0))

        btn_manual = ttk.Button(frame, text="Manual Connect", command=self.manual_connect)
        btn_manual.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(6,0))

        btn_disconnect = ttk.Button(frame, text="Desconectar", command=self.disconnect)
        btn_disconnect.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(10,0))

        ttk.Label(frame, text="Status:").grid(row=7, column=0, sticky="w", pady=(10,0))
        self.log = tk.Text(frame, width=44, height=8, state="disabled", bg="black", fg="white")
        self.log.grid(row=8, column=0, columnspan=3, pady=(6,0))

        self.log_message(f"adb: {self.adb_path or 'não encontrado'}  |  scrcpy: {self.scrcpy_path or 'não encontrado'}")

        signal.signal(signal.SIGINT, self._signal_handler)

    def log_message(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", f"{text}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def disable_buttons(self):
        for child in self.winfo_children():
            try:
                for w in child.winfo_children():
                    if isinstance(w, ttk.Button):
                        w.config(state="disabled")
            except:
                pass

    def enable_buttons(self):
        for child in self.winfo_children():
            try:
                for w in child.winfo_children():
                    if isinstance(w, ttk.Button):
                        w.config(state="normal")
            except:
                pass

    def quick_connect(self):
        ip = self.ip_var.get().strip()
        port = "5555"
        save_config(ip, port, self.buffer_var.get().strip())
        self.log_message(f"Tentando quick connect em {ip}:5555 ...")
        threading.Thread(target=self._connect_and_start, args=(ip, port), daemon=True).start()

    def set_5555_usb(self):
        ip = self.ip_var.get().strip()
        def job():
            self.disable_buttons()
            code, out = run_adb(["tcpip", "5555"])
            if code == 0:
                self.log_message("OK: porta 5555 setada via USB. Desconecte o cabo e use Quick/Manual.")
            else:
                self.log_message(f"Erro ao setar porta via USB: ({code}) {out}")
            self.enable_buttons()
        threading.Thread(target=job, daemon=True).start()

    def manual_connect(self):
        ip = self.ip_var.get().strip()
        port = self.port_var.get().strip()
        save_config(ip, port, self.buffer_var.get().strip())
        self.log_message(f"Tentando conectar manualmente em {ip}:{port} ...")
        threading.Thread(target=self._connect_and_start, args=(ip, port), daemon=True).start()

    def _connect_and_start(self, ip, port):
        self.disable_buttons()
        code, out = run_adb(["connect", f"{ip}:{port}"])
        self.log_message(f"[adb connect] retorno={code}. {out or ''}")
        if code == 0 and (("connected" in (out or "").lower()) or ("already" in (out or "").lower())):
            self.log_message("Conectado via adb → iniciando scrcpy (áudio)...")
            self._start_scrcpy_proc(ip, port)
        else:
            self.log_message("Falha ao conectar via adb. Verifique IP/Porta ou pareie o dispositivo.")
        self.enable_buttons()

    def _start_scrcpy_proc(self, ip, port):
        exe = self.scrcpy_path or find_binary("scrcpy")
        if not exe:
            self.log_message("scrcpy não encontrado no PATH.")
            return
        buffer = self.buffer_var.get().strip()
        if not buffer.isdigit():
            self.log_message("Buffer inválido.")
            return
        args = [
            exe,
            "--no-window",
            "--no-video",
            "--audio-source=playback",
            f"--audio-buffer={buffer}",
            f"--tcpip={ip}:{port}"
        ]
        try:
            creationflags = 0x08000000 if sys.platform.startswith("win") else 0
            proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)
            self.scrcpy_proc = proc
            self.log_message(f"scrcpy iniciado (áudio) em {ip}:{port} (pid={proc.pid})")
        except Exception as e:
            self.log_message(f"Erro ao iniciar scrcpy: {e}")

    def disconnect(self):
        ip = self.ip_var.get().strip()
        port = self.port_var.get().strip()
        if not ip or not port:
            self.log_message("IP/porta vazios — nada para desconectar.")
        else:
            self.log_message(f"Desconectando {ip}:{port} ...")
            code, out = run_adb(["disconnect", f"{ip}:{port}"])
            self.log_message(f"[adb disconnect] retorno={code}. {out or ''}")

        if self.scrcpy_proc:
            try:
                pid = self.scrcpy_proc.pid
                self.scrcpy_proc.terminate()
                self.scrcpy_proc.wait(timeout=3)
                self.log_message(f"scrcpy (pid={pid}) terminado.")
            except Exception:
                try:
                    self.scrcpy_proc.kill()
                    self.log_message("scrcpy morto (kill).")
                except Exception as e:
                    self.log_message(f"Falha ao terminar scrcpy: {e}")
            finally:
                self.scrcpy_proc = None

    def on_close(self):
        self.log_message("Fechando — realizando desconexão...")
        # chama disconnect e depois fecha janela
        try:
            self.disconnect()
        except Exception as e:
            self.log_message(f"Erro no disconnect: {e}")
        self.destroy()
        sys.exit(0)

    def _signal_handler(self, signum, frame):
        # tratado para Ctrl+C no console
        self.log_message("Sinal recebido (SIGINT). Executando desconexão...")
        try:
            self.disconnect()
        except Exception as e:
            self.log_message(f"Erro no disconnect: {e}")
        # fecha a GUI de forma segura
        try:
            self.quit()
        except:
            pass
        sys.exit(0)

def main():
    app = SaGui()
    app.mainloop()

if __name__ == "__main__":
    main()
