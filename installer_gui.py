"""
Forensic AI Platform - Complete Installer
Designed for fresh Windows systems
Every step checks prerequisites
"""
import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import webbrowser

class Installer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Forensic AI Platform Installer")
        self.root.geometry("600x500")
        
        self.path = tk.StringVar(value=r"D:\forensic-ai-platform")
        self.python_ok = False
        self.pip_ok = False
        self.git_ok = False
        
        self.build_ui()
        self.check_all()  # Check everything on start
        self.root.mainloop()
    
    def build_ui(self):
        # Title
        tk.Label(self.root, text="Forensic AI Platform Installer", 
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white', pady=10).pack(fill='x')
        
        # Status frame
        sf = tk.LabelFrame(self.root, text="System Check", padx=10, pady=10)
        sf.pack(fill='x', padx=20, pady=10)
        
        self.lbl_python = tk.Label(sf, text="⏳ Checking Python...", font=('Arial', 10), anchor='w')
        self.lbl_python.pack(fill='x')
        
        self.lbl_pip = tk.Label(sf, text="⏳ Checking pip...", font=('Arial', 10), anchor='w')
        self.lbl_pip.pack(fill='x')
        
        self.lbl_git = tk.Label(sf, text="⏳ Checking Git...", font=('Arial', 10), anchor='w')
        self.lbl_git.pack(fill='x')
        
        # Path frame
        pf = tk.LabelFrame(self.root, text="Install Path", padx=10, pady=10)
        pf.pack(fill='x', padx=20, pady=5)
        
        pf2 = tk.Frame(pf)
        pf2.pack(fill='x')
        tk.Entry(pf2, textvariable=self.path, width=45).pack(side='left', padx=(0,5))
        tk.Button(pf2, text="Browse", command=self.browse).pack(side='left')
        
        # Log
        self.log = tk.Text(self.root, height=12, width=60, font=('Consolas', 9))
        self.log.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Buttons
        bf = tk.Frame(self.root, pady=10)
        bf.pack(fill='x', padx=20, pady=(0,15))
        
        self.btn_install = tk.Button(bf, text="INSTALL", font=('Arial', 12, 'bold'),
                                    bg='#27ae60', fg='white', padx=30, state='disabled',
                                    command=self.do_install)
        self.btn_install.pack(side='left')
        
        self.btn_retry = tk.Button(bf, text="RETRY CHECK", font=('Arial', 10),
                                  padx=15, command=self.check_all)
        self.btn_retry.pack(side='left', padx=10)
        
        tk.Button(bf, text="EXIT", font=('Arial', 10), padx=15, command=self.root.quit).pack(side='right')
    
    def log_msg(self, msg):
        self.log.insert('end', msg + '\n')
        self.log.see('end')
        self.root.update()
    
    def check_all(self):
        """Check all prerequisites"""
        self.log.delete('1.0', 'end')
        self.log_msg("=" * 50)
        self.log_msg("Checking system requirements...")
        self.log_msg("=" * 50)
        
        # 1. Check Python
        self.lbl_python.config(text="⏳ Checking Python...", fg='black')
        self.root.update()
        
        python_cmd = self._find_python()
        if python_cmd:
            ver = self._run(f'"{python_cmd}" --version')
            self.lbl_python.config(text=f"✅ Python: {ver}", fg='green')
            self.log_msg(f"\n[OK] Python found: {ver}")
            self.log_msg(f"     Path: {python_cmd}")
            self.python_ok = True
        else:
            self.lbl_python.config(text="❌ Python NOT installed", fg='red')
            self.log_msg("\n[FAIL] Python not found!")
            self.log_msg("")
            self.log_msg("SOLUTION:")
            self.log_msg("1. Download Python from: https://www.python.org/downloads/")
            self.log_msg("2. Run installer")
            self.log_msg("3. CHECK 'Add Python to PATH'!")
            self.log_msg("4. Restart this installer")
            self.python_ok = False
        
        # 2. Check pip
        self.lbl_pip.config(text="⏳ Checking pip...", fg='black')
        self.root.update()
        
        if self.python_ok:
            pip_ok = self._run(f'"{python_cmd}" -m pip --version')
            if pip_ok:
                self.lbl_pip.config(text="✅ pip: installed", fg='green')
                self.log_msg("\n[OK] pip installed")
                self.pip_ok = True
            else:
                self.lbl_pip.config(text="❌ pip NOT working", fg='red')
                self.log_msg("\n[FAIL] pip not working!")
                self.log_msg("SOLUTION: Run: python -m ensurepip")
                self.pip_ok = False
        else:
            self.lbl_pip.config(text="⚠️ pip: skipped (no Python)", fg='orange')
            self.pip_ok = False
        
        # 3. Check Git
        self.lbl_git.config(text="⏳ Checking Git...", fg='black')
        self.root.update()
        
        git_ok = self._run("git --version")
        if git_ok:
            self.lbl_git.config(text="✅ Git: installed", fg='green')
            self.log_msg("\n[OK] Git installed")
            self.git_ok = True
        else:
            self.lbl_git.config(text="⚠️ Git: not installed (optional)", fg='orange')
            self.log_msg("\n[WARN] Git not installed")
            self.log_msg("       You can download ZIP manually instead")
            self.git_ok = False
        
        # 4. Summary
        self.log_msg("\n" + "=" * 50)
        self.log_msg("SUMMARY:")
        self.log_msg(f"  Python: {'OK' if self.python_ok else 'MISSING'}")
        self.log_msg(f"  pip:    {'OK' if self.pip_ok else 'MISSING'}")
        self.log_msg(f"  Git:    {'OK' if self.git_ok else 'MISSING'}")
        self.log_msg("=" * 50)
        
        # Enable/disable install button
        if self.python_ok and self.pip_ok:
            self.btn_install.config(state='normal')
            self.log_msg("\n✅ Ready to install!")
        else:
            self.btn_install.config(state='disabled')
            self.log_msg("\n❌ Cannot install - missing requirements")
            if not self.git_ok:
                self.log_msg("\nAlternative: Download ZIP manually:")
                self.log_msg("https://github.com/luyichen0704/forensic-ai-platform")
    
    def _find_python(self):
        """Find Python executable"""
        # Try common locations
        candidates = [
            "python",
            "python3",
            r"C:\Python312\python.exe",
            r"C:\Python311\python.exe",
            r"C:\Python310\python.exe",
            r"C:\Python39\python.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Python\Python312\python.exe"),
            os.path.expanduser(r"~\AppData\Local\Programs\Python\Python311\python.exe"),
            os.path.expanduser(r"~\AppData\Local\Programs\Python\Python310\python.exe"),
        ]
        
        for cmd in candidates:
            try:
                r = subprocess.run(f'"{cmd}" --version', shell=True, capture_output=True, timeout=5)
                if r.returncode == 0:
                    return cmd
            except:
                continue
        
        return None
    
    def _run(self, cmd):
        """Run command and return success"""
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            return r.returncode == 0
        except:
            return False
    
    def browse(self):
        d = filedialog.askdirectory()
        if d:
            self.path.set(os.path.join(d, "forensic-ai-platform"))
    
    def do_install(self):
        self.btn_install.config(state='disabled')
        threading.Thread(target=self._install, daemon=True).start()
    
    def _install(self):
        p = self.path.get()
        
        try:
            self.log_msg("\n" + "=" * 50)
            self.log_msg("STARTING INSTALLATION")
            self.log_msg("=" * 50)
            
            # Step 1: Create directory
            self.log_msg("\n[1/4] Creating directory...")
            self.log_msg(f"  Path: {p}")
            os.makedirs(p, exist_ok=True)
            self.log_msg("  ✓ Directory created")
            
            # Step 2: Download project
            self.log_msg("\n[2/4] Downloading project...")
            
            if self.git_ok:
                # Use git
                if os.path.exists(os.path.join(p, '.git')):
                    self.log_msg("  Existing project found, updating...")
                    subprocess.run(["git", "pull"], capture_output=True, cwd=p)
                    self.log_msg("  ✓ Updated")
                else:
                    self.log_msg("  Cloning from GitHub...")
                    r = subprocess.run(
                        ["git", "clone", "https://github.com/luyichen0704/forensic-ai-platform.git", "."],
                        capture_output=True, text=True, cwd=p
                    )
                    if r.returncode == 0:
                        self.log_msg("  ✓ Downloaded")
                    else:
                        self.log_msg(f"  ✗ Clone failed: {r.stderr[:100]}")
                        self.log_msg("")
                        self.log_msg("  Please download manually:")
                        self.log_msg("  1. Go to: https://github.com/luyichen0704/forensic-ai-platform")
                        self.log_msg("  2. Click Code -> Download ZIP")
                        self.log_msg(f"  3. Extract to: {p}")
                        return
            else:
                # No git - prompt manual download
                self.log_msg("  Git not available")
                self.log_msg("")
                self.log_msg("  Please download manually:")
                self.log_msg("  1. Go to: https://github.com/luyichen0704/forensic-ai-platform")
                self.log_msg("  2. Click Code -> Download ZIP")
                self.log_msg(f"  3. Extract to: {p}")
                self.log_msg("  4. Run this installer again")
                
                if messagebox.askyesno("Download Required", 
                    "Git not installed.\n\n"
                    "Open download page in browser?\n\n"
                    "(Download ZIP, extract, then run installer again)"):
                    webbrowser.open("https://github.com/luyichen0704/forensic-ai-platform")
                return
            
            # Step 3: Install Python dependencies
            self.log_msg("\n[3/4] Installing Python dependencies...")
            
            req_file = os.path.join(p, "requirements.txt")
            if os.path.exists(req_file):
                self.log_msg("  Running pip install...")
                
                # Find python
                python_cmd = self._find_python()
                r = subprocess.run(
                    f'"{python_cmd}" -m pip install -r "{req_file}" -q',
                    shell=True, capture_output=True, text=True
                )
                
                if r.returncode == 0:
                    self.log_msg("  ✓ Dependencies installed")
                else:
                    self.log_msg(f"  ⚠ Some failed: {r.stderr[:150]}")
                    self.log_msg("  Continuing anyway...")
            else:
                self.log_msg("  ⚠ requirements.txt not found, skipping")
            
            # Step 4: Create config
            self.log_msg("\n[4/4] Setting up config...")
            
            config_example = os.path.join(p, "config", "llm_config.example.json")
            config_file = os.path.join(p, "config", "llm_config.json")
            
            if os.path.exists(config_example) and not os.path.exists(config_file):
                shutil.copy2(config_example, config_file)
                self.log_msg("  ✓ Config created from template")
                self.log_msg("  ⚠ Edit config/llm_config.json to add your API key")
            else:
                self.log_msg("  Config already exists or template missing")
            
            # Done
            self.log_msg("\n" + "=" * 50)
            self.log_msg("✅ INSTALLATION COMPLETE!")
            self.log_msg("=" * 50)
            self.log_msg(f"\nInstalled to: {p}")
            self.log_msg("\nNEXT STEPS:")
            self.log_msg("1. Edit config/llm_config.json (add your API key)")
            self.log_msg(f"2. Run: {p}\\start.bat")
            self.log_msg(f"3. Or run: {p}\\create_shortcut.bat")
            
            messagebox.showinfo("Success", 
                f"Installation complete!\n\n"
                f"Path: {p}\n\n"
                f"Next steps:\n"
                f"1. Edit config/llm_config.json\n"
                f"2. Run start.bat")
            
        except Exception as e:
            self.log_msg(f"\n❌ ERROR: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_install.config(state='normal')

if __name__ == "__main__":
    Installer()
