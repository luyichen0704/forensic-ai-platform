"""
取证AI平台 - 完整安装向导
一键安装：项目 + Python依赖 + 取证工具
"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import shutil
from pathlib import Path

class InstallerGUI:
    """安装向导GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("取证AI平台 - 安装向导")
        self.root.geometry("650x600")
        self.root.resizable(False, False)
        
        # 默认安装路径
        self.default_path = os.path.join(os.path.expanduser("~"), "forensic-ai-platform")
        self.install_path = tk.StringVar(value=self.default_path)
        
        # 安装选项
        self.install_project = tk.BooleanVar(value=True)
        self.install_python_deps = tk.BooleanVar(value=True)
        self.install_scoop = tk.BooleanVar(value=True)
        self.install_forensic_tools = tk.BooleanVar(value=True)
        
        # 状态
        self.is_installing = False
        self.install_log = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        # 标题
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="🔍 取证AI平台 - 一键安装",
            font=('微软雅黑', 16, 'bold'),
            fg='white',
            bg='#2c3e50'
        ).pack(expand=True)
        
        # 主内容区 - 使用Notebook实现分步安装
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 步骤1: 选择安装路径
        self.step1_frame = self._create_step1()
        self.notebook.add(self.step1_frame, text="  步骤1: 选择路径  ")
        
        # 步骤2: 选择安装组件
        self.step2_frame = self._create_step2()
        self.notebook.add(self.step2_frame, text="  步骤2: 选择组件  ")
        
        # 步骤3: 安装进度
        self.step3_frame = self._create_step3()
        self.notebook.add(self.step3_frame, text="  步骤3: 安装进度  ")
        
        # 底部按钮
        btn_frame = tk.Frame(self.root, bg='#f0f0f0')
        btn_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.prev_btn = tk.Button(
            btn_frame, text="上一步", font=('微软雅黑', 10),
            bg='#95a5a6', fg='white', padx=15, pady=5,
            command=self.prev_step
        )
        self.prev_btn.pack(side='left')
        
        self.next_btn = tk.Button(
            btn_frame, text="下一步", font=('微软雅黑', 10, 'bold'),
            bg='#3498db', fg='white', padx=20, pady=5,
            command=self.next_step
        )
        self.next_btn.pack(side='right')
        
        self.install_btn = tk.Button(
            btn_frame, text="🚀 开始安装", font=('微软雅黑', 12, 'bold'),
            bg='#27ae60', fg='white', padx=30, pady=8,
            command=self.start_install
        )
        
        # 初始化
        self.notebook.select(0)
        self.prev_btn.configure(state='disabled')
    
    def _create_step1(self):
        """创建步骤1: 选择安装路径"""
        frame = tk.Frame(self.notebook, bg='#f0f0f0', padx=20, pady=20)
        
        tk.Label(
            frame, text="选择安装路径",
            font=('微软雅黑', 14, 'bold'), bg='#f0f0f0'
        ).pack(anchor='w', pady=(0, 15))
        
        tk.Label(
            frame, text="请选择一个目录安装取证AI平台，建议安装到D盘或其他非系统盘：",
            font=('微软雅黑', 10), bg='#f0f0f0', wraplength=550
        ).pack(anchor='w', pady=(0, 10))
        
        # 路径选择
        path_frame = tk.Frame(frame, bg='#f0f0f0')
        path_frame.pack(fill='x', pady=(0, 10))
        
        tk.Entry(
            path_frame, textvariable=self.install_path,
            font=('微软雅黑', 11), width=45
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            path_frame, text="浏览...", font=('微软雅黑', 10),
            bg='#3498db', fg='white', command=self.browse_path
        ).pack(side='left')
        
        # 磁盘空间
        self.space_label = tk.Label(
            frame, text="", font=('微软雅黑', 10), bg='#f0f0f0'
        )
        self.space_label.pack(anchor='w', pady=(0, 20))
        
        # 快捷路径按钮
        quick_frame = tk.LabelFrame(
            frame, text="快捷选择", font=('微软雅黑', 10),
            bg='#f0f0f0', padx=10, pady=10
        )
        quick_frame.pack(fill='x')
        
        for drive in ['D', 'E', 'F']:
            if os.path.exists(f"{drive}:\\"):
                tk.Button(
                    quick_frame, text=f"{drive}:\\forensic-ai-platform",
                    font=('微软雅黑', 9), bg='#ecf0f1',
                    command=lambda d=drive: self.install_path.set(f"{d}:\\forensic-ai-platform")
                ).pack(side='left', padx=5)
        
        self.root.after(100, self.check_disk_space)
        return frame
    
    def _create_step2(self):
        """创建步骤2: 选择安装组件"""
        frame = tk.Frame(self.notebook, bg='#f0f0f0', padx=20, pady=20)
        
        tk.Label(
            frame, text="选择安装组件",
            font=('微软雅黑', 14, 'bold'), bg='#f0f0f0'
        ).pack(anchor='w', pady=(0, 15))
        
        tk.Label(
            frame, text="请选择要安装的组件（推荐全部安装）：",
            font=('微软雅黑', 10), bg='#f0f0f0'
        ).pack(anchor='w', pady=(0, 15))
        
        # 组件选择
        components = [
            (self.install_project, "📦 项目文件", "核心代码、Web界面、API接口", True),
            (self.install_python_deps, "🐍 Python依赖", "Gradio、FastAI、aiohttp等", True),
            (self.install_scoop, "🔧 Scoop包管理器", "Windows下的包管理工具", True),
            (self.install_forensic_tools, "🔍 取证工具", "tshark、volatility、sleuthkit等", True),
        ]
        
        for var, name, desc, recommended in components:
            item_frame = tk.Frame(frame, bg='#ffffff', relief='solid', bd=1)
            item_frame.pack(fill='x', pady=5)
            
            cb = tk.Checkbutton(
                item_frame, variable=var, font=('微软雅黑', 11),
                bg='#ffffff', anchor='w'
            )
            cb.pack(side='left', padx=10, pady=10)
            
            info_frame = tk.Frame(item_frame, bg='#ffffff')
            info_frame.pack(side='left', fill='x', expand=True, pady=10)
            
            tk.Label(
                info_frame, text=name,
                font=('微软雅黑', 11, 'bold'), bg='#ffffff', anchor='w'
            ).pack(anchor='w')
            
            tk.Label(
                info_frame, text=desc,
                font=('微软雅黑', 9), bg='#ffffff', fg='#666666', anchor='w'
            ).pack(anchor='w')
            
            if recommended:
                tk.Label(
                    item_frame, text="推荐",
                    font=('微软雅黑', 9), bg='#27ae60', fg='white',
                    padx=5, pady=2
                ).pack(side='right', padx=10)
        
        # 工具列表说明
        tools_info = tk.LabelFrame(
            frame, text="取证工具列表", font=('微软雅黑', 10),
            bg='#f0f0f0', padx=10, pady=10
        )
        tools_info.pack(fill='x', pady=(15, 0))
        
        tools_text = """
磁盘取证: sleuthkit, autopsy
网络分析: tshark (Wireshark), tcpdump  
内存取证: volatility3
密码破解: hashcat, john
隐写分析: steghide, zsteg, stegoveritas
逆向工程: radare2, jadx
文件处理: 7zip, exiftool, binwalk
其他工具: yara, sqlite, openssl, ffmpeg
        """
        tk.Label(
            tools_info, text=tools_text.strip(),
            font=('Consolas', 9), bg='#f0f0f0', justify='left', anchor='w'
        ).pack(anchor='w')
        
        return frame
    
    def _create_step3(self):
        """创建步骤3: 安装进度"""
        frame = tk.Frame(self.notebook, bg='#f0f0f0', padx=20, pady=20)
        
        tk.Label(
            frame, text="安装进度",
            font=('微软雅黑', 14, 'bold'), bg='#f0f0f0'
        ).pack(anchor='w', pady=(0, 15))
        
        # 进度条
        self.progress = ttk.Progressbar(frame, mode='determinate', length=500)
        self.progress.pack(fill='x', pady=(0, 10))
        
        # 当前步骤
        self.current_step_label = tk.Label(
            frame, text="准备开始安装...",
            font=('微软雅黑', 11), bg='#f0f0f0', anchor='w'
        )
        self.current_step_label.pack(fill='x', pady=(0, 15))
        
        # 安装日志
        log_frame = tk.LabelFrame(
            frame, text="安装日志", font=('微软雅黑', 10),
            bg='#f0f0f0', padx=10, pady=10
        )
        log_frame.pack(fill='both', expand=True)
        
        self.log_text = tk.Text(
            log_frame, height=15, font=('Consolas', 9),
            wrap='word', state='disabled'
        )
        self.log_text.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        return frame
    
    def browse_path(self):
        """浏览文件夹"""
        path = filedialog.askdirectory(
            title="选择安装路径",
            initialdir=os.path.dirname(self.install_path.get())
        )
        if path:
            self.install_path.set(os.path.join(path, "forensic-ai-platform"))
            self.check_disk_space()
    
    def check_disk_space(self):
        """检查磁盘空间"""
        try:
            path = self.install_path.get()
            drive = os.path.splitdrive(path)[0] + '\\' if os.name == 'nt' else '/'
            total, used, free = shutil.disk_usage(drive)
            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            
            if free_gb >= 5:
                self.space_label.configure(
                    text=f"✅ 可用空间: {free_gb:.1f} GB / {total_gb:.1f} GB (足够)",
                    fg='#27ae60'
                )
            else:
                self.space_label.configure(
                    text=f"⚠️ 可用空间: {free_gb:.1f} GB (建议至少5GB)",
                    fg='#e74c3c'
                )
        except Exception as e:
            self.space_label.configure(text=f"无法检查: {e}", fg='#e74c3c')
    
    def prev_step(self):
        """上一步"""
        current = self.notebook.index(self.notebook.select())
        if current > 0:
            self.notebook.select(current - 1)
            self.next_btn.configure(text="下一步")
            self.install_btn.pack_forget()
            
            if current - 1 == 0:
                self.prev_btn.configure(state='disabled')
    
    def next_step(self):
        """下一步"""
        current = self.notebook.index(self.notebook.select())
        if current < 2:
            self.notebook.select(current + 1)
            self.prev_btn.configure(state='normal')
            
            if current + 1 == 2:
                self.next_btn.pack_forget()
                self.install_btn.pack(side='right')
    
    def start_install(self):
        """开始安装"""
        path = self.install_path.get()
        
        if not path:
            messagebox.showerror("错误", "请选择安装路径!")
            return
        
        if not messagebox.askyesno("确认安装", 
            f"即将安装到:\n{path}\n\n是否继续?"):
            return
        
        self.is_installing = True
        self.install_btn.configure(state='disabled')
        self.prev_btn.configure(state='disabled')
        threading.Thread(target=self._install_thread, daemon=True).start()
    
    def _log(self, message):
        """添加日志"""
        self.root.after(0, lambda: self._append_log(message))
    
    def _append_log(self, message):
        """追加日志到界面"""
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message + '\n')
        self.log_text.see('end')
        self.log_text.configure(state='disabled')
    
    def _update_step(self, text, progress):
        """更新步骤"""
        self.root.after(0, lambda: self.current_step_label.configure(text=text))
        self.root.after(0, lambda: self.progress.configure(value=progress))
    
    def _install_thread(self):
        """安装线程"""
        path = self.install_path.get()
        
        try:
            # 步骤1: 创建目录
            self._update_step("📁 正在创建安装目录...", 5)
            self._log("=" * 50)
            self._log("开始安装取证AI平台")
            self._log("=" * 50)
            self._log(f"安装路径: {path}")
            
            os.makedirs(path, exist_ok=True)
            self._log("✅ 目录创建成功")
            
            # 步骤2: 克隆/下载项目
            if self.install_project.get():
                self._update_step("📦 正在下载项目文件...", 15)
                self._log("\n[1/4] 下载项目文件...")
                
                # 先检查是否已有git仓库
                if os.path.exists(os.path.join(path, '.git')):
                    self._log("检测到已有项目，执行更新...")
                    subprocess.run(["git", "pull", "origin", "main"], 
                                 capture_output=True, cwd=path)
                else:
                    self._log("正在克隆仓库...")
                    result = subprocess.run(
                        ["git", "clone", "https://github.com/luyichen0704/forensic-ai-platform.git", "."],
                        capture_output=True, text=True, cwd=path
                    )
                    if result.returncode != 0:
                        # 如果git失败，提示手动下载
                        self._log("⚠️ Git克隆失败，请手动下载:")
                        self._log("1. 访问 https://github.com/luyichen0704/forensic-ai-platform")
                        self._log("2. 点击 Code -> Download ZIP")
                        self._log(f"3. 解压到 {path}")
                        raise Exception("Git克隆失败")
                
                self._log("✅ 项目文件下载完成")
            
            # 步骤3: 安装Scoop包管理器
            if self.install_scoop.get():
                self._update_step("🔧 正在安装Scoop包管理器...", 30)
                self._log("\n[2/4] 安装Scoop包管理器...")
                
                # 检查scoop是否已安装
                scoop_path = os.path.expanduser("~/scoop/shims/scoop.cmd")
                if os.path.exists(scoop_path):
                    self._log("✅ Scoop已安装")
                else:
                    self._log("正在安装Scoop...")
                    self._log("（这可能需要几分钟，请耐心等待）")
                    
                    # 安装scoop
                    install_cmd = 'iwr -useb get.scoop.sh | iex'
                    result = subprocess.run(
                        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", install_cmd],
                        capture_output=True, text=True
                    )
                    
                    if os.path.exists(scoop_path):
                        self._log("✅ Scoop安装成功")
                    else:
                        self._log("⚠️ Scoop安装可能失败，继续安装其他组件...")
            
            # 步骤4: 安装Python依赖
            if self.install_python_deps.get():
                self._update_step("🐍 正在安装Python依赖...", 50)
                self._log("\n[3/4] 安装Python依赖...")
                
                req_file = os.path.join(path, "requirements.txt")
                if os.path.exists(req_file):
                    self._log("正在安装Python包...")
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", req_file, "-q"],
                        capture_output=True, text=True, cwd=path
                    )
                    if result.returncode == 0:
                        self._log("✅ Python依赖安装完成")
                    else:
                        self._log(f"⚠️ 部分依赖安装失败: {result.stderr[:200]}")
            
            # 步骤5: 安装取证工具
            if self.install_forensic_tools.get():
                self._update_step("🔍 正在安装取证工具...", 65)
                self._log("\n[4/4] 安装取证工具...")
                
                # 检查scoop
                scoop_cmd = os.path.expanduser("~/scoop/shims/scoop.cmd")
                if not os.path.exists(scoop_cmd):
                    scoop_cmd = "scoop"
                
                # 工具列表
                tools = [
                    ("sleuthkit", "磁盘取证"),
                    ("wireshark", "网络分析"),
                    ("yara", "恶意代码检测"),
                    ("hashcat", "密码破解"),
                    ("7zip", "压缩解压"),
                    ("ripgrep", "内容搜索"),
                    ("exiftool", "元数据提取"),
                    ("ffmpeg", "音视频处理"),
                    ("sqlite", "数据库"),
                    ("openssl", "加密解密"),
                    ("jadx", "APK逆向"),
                    ("radare2", "二进制逆向"),
                ]
                
                self._log("安装取证工具:")
                total = len(tools)
                
                for i, (tool, desc) in enumerate(tools):
                    progress = 65 + (i / total) * 25
                    self._update_step(f"🔍 正在安装 {tool} ({desc})...", progress)
                    self._log(f"  安装 {tool} ({desc})...")
                    
                    result = subprocess.run(
                        [scoop_cmd, "install", tool],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode == 0:
                        self._log(f"    ✅ {tool} 安装成功")
                    else:
                        self._log(f"    ⚠️ {tool} 安装失败（可能已存在）")
                
                # 安装Python取证包
                self._log("\n安装Python取证包...")
                pip_tools = [
                    "volatility3",
                    "dissect-evidence",
                    "oletools",
                    "pycryptodome",
                    "stegoveritas"
                ]
                
                for tool in pip_tools:
                    self._log(f"  安装 {tool}...")
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", tool, "-q"],
                        capture_output=True
                    )
                
                self._log("✅ 取证工具安装完成")
            
            # 完成
            self._update_step("✅ 安装完成!", 100)
            self._log("\n" + "=" * 50)
            self._log("🎉 安装完成!")
            self._log("=" * 50)
            self._log(f"\n安装位置: {path}")
            self._log("\n启动方式:")
            self._log(f"  1. 双击 {path}\\start.bat")
            self._log(f"  2. 或双击 {path}\\更新工具.bat")
            
            # 创建桌面快捷方式
            self._create_desktop_shortcut(path)
            
            self.root.after(0, lambda: messagebox.showinfo("安装完成", 
                f"🎉 安装成功!\n\n"
                f"安装路径: {path}\n\n"
                f"启动方式:\n"
                f"1. 双击桌面快捷方式\n"
                f"2. 运行 {path}\\start.bat"))
            
        except Exception as e:
            self._log(f"\n❌ 安装失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("安装失败", f"安装失败:\n{e}"))
        
        finally:
            self.root.after(0, lambda: self.install_btn.configure(state='normal'))
            self.is_installing = False
    
    def _create_desktop_shortcut(self, install_path):
        """创建桌面快捷方式"""
        try:
            if os.name == 'nt':
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_path = os.path.join(desktop, "取证AI平台.bat")
                
                with open(shortcut_path, 'w', encoding='utf-8') as f:
                    f.write(f'@echo off\n')
                    f.write(f'chcp 65001 >nul\n')
                    f.write(f'cd /d "{install_path}"\n')
                    f.write(f'start.bat\n')
                
                self._log(f"\n✅ 已创建桌面快捷方式")
        except Exception as e:
            self._log(f"⚠️ 创建快捷方式失败: {e}")
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()

def main():
    """主函数"""
    app = InstallerGUI()
    app.run()

if __name__ == "__main__":
    main()
