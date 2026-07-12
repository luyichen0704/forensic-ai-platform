"""
Forensic AI Platform - Simple Installer
"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import shutil

class SimpleInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Forensic AI Platform - Installer")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Default path
        self.install_path = tk.StringVar(value=r"D:\forensic-ai-platform")
        
        # Options
        self.opt_project = tk.BooleanVar(value=True)
        self.opt_deps = tk.BooleanVar(value=True)
        self.opt_tools = tk.BooleanVar(value=True)
        
        self.create_ui()
    
    def create_ui(self):
        # Title
        title = tk.Label(
            self.root, text="Forensic AI Platform Installer",
            font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white', pady=15
        )
        title.pack(fill='x')
        
        # Main frame
        main = tk.Frame(self.root, padx=20, pady=15)
        main.pack(fill='both', expand=True)
        
        # Step 1: Path
        tk.Label(main, text="Step 1: Select Install Path", font=('Arial', 12, 'bold')).pack(anchor='w')
        
        path_frame = tk.Frame(main)
        path_frame.pack(fill='x', pady=(5, 15))
        
        tk.Entry(path_frame, textvariable=self.install_path, font=('Arial', 10), width=40).pack(side='left', padx=(0, 10))
        tk.Button(path_frame, text="Browse...", command=self.browse).pack(side='left')
        
        # Quick select
        quick = tk.Frame(main)
        quick.pack(anchor='w', pady=(0, 15))
        for d in ['D', 'E', 'F']:
            if os.path.exists(f"{d}:\\"):
                tk.Button(quick, text=f"{d}:\\forensic-ai-platform", 
                         command=lambda x=d: self.install_path.set(f"{x}:\\forensic-ai-platform")).pack(side='left', padx=5)
        
        # Step 2: Options
        tk.Label(main, text="Step 2: Select Components", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10, 5))
        
        tk.Checkbutton(main, text="Project Files (code, web UI, API)", variable=self.opt_project, font=('Arial', 10)).pack(anchor='w')
        tk.Checkbutton(main, text="Python Dependencies (gradio, fastapi, etc)", variable=self.opt_deps, font=('Arial', 10)).pack(anchor='w')
        tk.Checkbutton(main, text="Forensic Tools (tshark, volatility, etc)", variable=self.opt_tools, font=('Arial', 10)).pack(anchor='w')
        
        # Step 3: Progress
        tk.Label(main, text="Step 3: Installation Progress", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(15, 5))
        
        self.progress = ttk.Progressbar(main, mode='determinate', length=500)
        self.progress.pack(fill='x', pady=(0, 10))
        
        self.status = tk.Label(main, text="Ready to install...", font=('Arial', 10), anchor='w')
        self.status.pack(fill='x')
        
        # Log
        log_frame = tk.Frame(main)
        log_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        self.log = tk.Text(log_frame, height=8, font=('Consolas', 9), state='disabled')
        self.log.pack(fill='both', expand=True)
        
        # Buttons
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        self.install_btn = tk.Button(
            btn_frame, text="Install", font=('Arial', 12, 'bold'),
            bg='#27ae60', fg='white', padx=30, pady=8, command=self.start_install
        )
        self.install_btn.pack(side='left')
        
        tk.Button(
            btn_frame, text="Exit", font=('Arial', 11),
            bg='#95a5a6', fg='white', padx=20, pady=8, command=self.root.quit
        ).pack(side='right')
    
    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_path.set(os.path.join(path, "forensic-ai-platform"))
    
    def log_msg(self, msg):
        self.root.after(0, lambda: self._append_log(msg))
    
    def _append_log(self, msg):
        self.log.configure(state='normal')
        self.log.insert('end', msg + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')
    
    def update_status(self, text, progress):
        self.root.after(0, lambda: self.status.configure(text=text))
        self.root.after(0, lambda: self.progress.configure(value=progress))
    
    def start_install(self):
        path = self.install_path.get()
        if not path:
            messagebox.showerror("Error", "Please select install path!")
            return
        
        if not messagebox.askyesno("Confirm", f"Install to:\n{path}\n\nContinue?"):
            return
        
        self.install_btn.configure(state='disabled')
        threading.Thread(target=self._install, daemon=True).start()
    
    def _install(self):
        path = self.install_path.get()
        
        try:
            self.log_msg("=" * 50)
            self.log_msg("Starting installation...")
            self.log_msg(f"Path: {path}")
            self.log_msg("=" * 50)
            
            # 1. Create directory
            self.update_status("Creating directory...", 10)
            self.log_msg("\n[1/4] Creating directory...")
            os.makedirs(path, exist_ok=True)
            self.log_msg("  OK: Directory created")
            
            # 2. Download project
            if self.opt_project.get():
                self.update_status("Downloading project...", 25)
                self.log_msg("\n[2/4] Downloading project...")
                
                if os.path.exists(os.path.join(path, '.git')):
                    self.log_msg("  Existing project found, updating...")
                    subprocess.run(["git", "pull", "origin", "main"], capture_output=True, cwd=path)
                else:
                    self.log_msg("  Cloning repository...")
                    result = subprocess.run(
                        ["git", "clone", "https://github.com/luyichen0704/forensic-ai-platform.git", "."],
                        capture_output=True, text=True, cwd=path
                    )
                    if result.returncode != 0:
                        self.log_msg("  Git clone failed!")
                        self.log_msg("  Please download manually from GitHub")
                        raise Exception("Git clone failed")
                
                self.log_msg("  OK: Project downloaded")
            
            # 3. Install Python deps
            if self.opt_deps.get():
                self.update_status("Installing Python dependencies...", 50)
                self.log_msg("\n[3/4] Installing Python dependencies...")
                
                req_file = os.path.join(path, "requirements.txt")
                if os.path.exists(req_file):
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", req_file, "-q"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        self.log_msg("  OK: Dependencies installed")
                    else:
                        self.log_msg(f"  Warning: Some deps failed: {result.stderr[:100]}")
            
            # 4. Install forensic tools
            if self.opt_tools.get():
                self.update_status("Installing forensic tools...", 70)
                self.log_msg("\n[4/4] Installing forensic tools...")
                
                # Check scoop
                scoop = os.path.expanduser("~/scoop/shims/scoop.cmd")
                if not os.path.exists(scoop):
                    self.log_msg("  Installing Scoop...")
                    subprocess.run(
                        ["powershell", "-Command", "iwr -useb get.scoop.sh | iex"],
                        capture_output=True
                    )
                
                # Install tools
                tools = ["sleuthkit", "wireshark", "yara", "hashcat", "7zip", 
                        "ripgrep", "exiftool", "ffmpeg", "sqlite", "openssl", "jadx", "radare2"]
                
                for i, tool in enumerate(tools):
                    progress = 70 + (i / len(tools)) * 25
                    self.update_status(f"Installing {tool}...", progress)
                    self.log_msg(f"  Installing {tool}...")
                    subprocess.run([scoop, "install", tool], capture_output=True)
                
                self.log_msg("  OK: Forensic tools installed")
            
            # Done
            self.update_status("Installation complete!", 100)
            self.log_msg("\n" + "=" * 50)
            self.log_msg("INSTALLATION COMPLETE!")
            self.log_msg("=" * 50)
            self.log_msg(f"\nInstalled to: {path}")
            self.log_msg("\nTo start:")
            self.log_msg(f"  1. Run {path}\\start.bat")
            self.log_msg(f"  2. Or run {path}\\create_shortcut.bat")
            
            self.root.after(0, lambda: messagebox.showinfo("Success", 
                f"Installation complete!\n\nPath: {path}\n\nRun start.bat to begin."))
            
        except Exception as e:
            self.log_msg(f"\nERROR: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Installation failed:\n{e}"))
        
        finally:
            self.root.after(0, lambda: self.install_btn.configure(state='normal'))
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleInstaller()
    app.run()
