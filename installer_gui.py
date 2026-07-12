"""
Forensic AI Platform - Installer
"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

class Installer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Forensic AI Platform - Installer")
        self.root.geometry("600x550")
        
        self.install_path = tk.StringVar(value=r"D:\forensic-ai-platform")
        self.opt_project = tk.BooleanVar(value=True)
        self.opt_deps = tk.BooleanVar(value=True)
        self.opt_tools = tk.BooleanVar(value=True)
        
        self.create_ui()
    
    def create_ui(self):
        # Title
        tk.Label(self.root, text="Forensic AI Platform Installer", 
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white', pady=10).pack(fill='x')
        
        # Main frame with scrollbar
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        main = tk.Frame(scrollable_frame, padx=20, pady=10)
        main.pack(fill='both', expand=True)
        
        # Step 1
        tk.Label(main, text="Step 1: Install Path", font=('Arial', 11, 'bold')).pack(anchor='w')
        path_frame = tk.Frame(main)
        path_frame.pack(fill='x', pady=5)
        tk.Entry(path_frame, textvariable=self.install_path, width=40).pack(side='left', padx=(0,10))
        tk.Button(path_frame, text="Browse", command=self.browse).pack(side='left')
        
        # Quick buttons
        quick = tk.Frame(main)
        quick.pack(anchor='w', pady=5)
        for d in ['D', 'E', 'F']:
            if os.path.exists(f"{d}:\\"):
                tk.Button(quick, text=f"{d}:\\forensic-ai-platform",
                         command=lambda x=d: self.install_path.set(f"{x}:\\forensic-ai-platform")).pack(side='left', padx=3)
        
        ttk.Separator(main, orient='horizontal').pack(fill='x', pady=10)
        
        # Step 2
        tk.Label(main, text="Step 2: Components", font=('Arial', 11, 'bold')).pack(anchor='w')
        tk.Checkbutton(main, text="Project Files", variable=self.opt_project).pack(anchor='w')
        tk.Checkbutton(main, text="Python Dependencies", variable=self.opt_deps).pack(anchor='w')
        tk.Checkbutton(main, text="Forensic Tools", variable=self.opt_tools).pack(anchor='w')
        
        ttk.Separator(main, orient='horizontal').pack(fill='x', pady=10)
        
        # Step 3
        tk.Label(main, text="Step 3: Progress", font=('Arial', 11, 'bold')).pack(anchor='w')
        self.progress = ttk.Progressbar(main, mode='determinate', length=400)
        self.progress.pack(fill='x', pady=5)
        self.status = tk.Label(main, text="Ready", anchor='w')
        self.status.pack(fill='x')
        
        # Log
        self.log = tk.Text(main, height=10, width=60, font=('Consolas', 9))
        self.log.pack(fill='both', expand=True, pady=5)
        
        # Buttons - MUST BE VISIBLE
        btn_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        btn_frame.pack(fill='x', side='bottom')
        
        self.install_btn = tk.Button(btn_frame, text="START INSTALL", font=('Arial', 12, 'bold'),
                                    bg='#27ae60', fg='white', padx=20, pady=5, command=self.start_install)
        self.install_btn.pack(side='left', padx=20)
        
        tk.Button(btn_frame, text="EXIT", font=('Arial', 11), bg='#95a5a6', fg='white',
                 padx=15, pady=5, command=self.root.quit).pack(side='right', padx=20)
    
    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_path.set(os.path.join(path, "forensic-ai-platform"))
    
    def log_msg(self, msg):
        self.root.after(0, lambda: self._do_log(msg))
    
    def _do_log(self, msg):
        self.log.insert('end', msg + '\n')
        self.log.see('end')
    
    def update_ui(self, text, progress):
        self.root.after(0, lambda: self.status.configure(text=text))
        self.root.after(0, lambda: self.progress.configure(value=progress))
    
    def start_install(self):
        if not self.install_path.get():
            messagebox.showerror("Error", "Select install path!")
            return
        if not messagebox.askyesno("Confirm", f"Install to:\n{self.install_path.get()}\n\nContinue?"):
            return
        self.install_btn.configure(state='disabled')
        threading.Thread(target=self._install, daemon=True).start()
    
    def _install(self):
        path = self.install_path.get()
        try:
            self.log_msg("Starting installation...")
            self.log_msg(f"Path: {path}")
            
            # Create dir
            self.update_ui("Creating directory...", 10)
            self.log_msg("\n[1/4] Creating directory...")
            os.makedirs(path, exist_ok=True)
            self.log_msg("  OK")
            
            # Download
            if self.opt_project.get():
                self.update_ui("Downloading...", 25)
                self.log_msg("\n[2/4] Downloading project...")
                if os.path.exists(os.path.join(path, '.git')):
                    subprocess.run(["git", "pull"], capture_output=True, cwd=path)
                else:
                    r = subprocess.run(["git", "clone", "https://github.com/luyichen0704/forensic-ai-platform.git", "."],
                                      capture_output=True, cwd=path)
                    if r.returncode != 0:
                        raise Exception("Git failed - download manually from GitHub")
                self.log_msg("  OK")
            
            # Python deps
            if self.opt_deps.get():
                self.update_ui("Installing deps...", 50)
                self.log_msg("\n[3/4] Python dependencies...")
                req = os.path.join(path, "requirements.txt")
                if os.path.exists(req):
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req, "-q"], capture_output=True)
                self.log_msg("  OK")
            
            # Tools
            if self.opt_tools.get():
                self.update_ui("Installing tools...", 70)
                self.log_msg("\n[4/4] Forensic tools...")
                scoop = os.path.expanduser("~/scoop/shims/scoop.cmd")
                if not os.path.exists(scoop):
                    self.log_msg("  Installing Scoop...")
                    subprocess.run(["powershell", "-Command", "iwr -useb get.scoop.sh | iex"], capture_output=True)
                
                tools = ["sleuthkit", "wireshark", "yara", "hashcat", "7zip", "exiftool", "ffmpeg", "sqlite", "openssl"]
                for i, t in enumerate(tools):
                    self.update_ui(f"Installing {t}...", 70 + i*3)
                    self.log_msg(f"  {t}...")
                    subprocess.run([scoop, "install", t], capture_output=True)
                self.log_msg("  OK")
            
            self.update_ui("Done!", 100)
            self.log_msg("\n" + "="*40)
            self.log_msg("INSTALLATION COMPLETE!")
            self.log_msg(f"Path: {path}")
            self.log_msg("Run start.bat to begin")
            
            messagebox.showinfo("Success", f"Installed to:\n{path}\n\nRun start.bat to begin!")
            
        except Exception as e:
            self.log_msg(f"\nERROR: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.root.after(0, lambda: self.install_btn.configure(state='normal'))
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    Installer().run()
