"""
取证AI平台 - 安装向导
让用户选择安装路径，一键安装
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
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 默认安装路径
        self.default_path = os.path.join(os.path.expanduser("~"), "forensic-ai-platform")
        self.install_path = tk.StringVar(value=self.default_path)
        
        # 安装选项
        self.install_git = tk.BooleanVar(value=True)
        self.install_python = tk.BooleanVar(value=True)
        self.install_tools = tk.BooleanVar(value=True)
        
        # 状态
        self.is_installing = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        # 标题
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="🔍 取证AI平台 - 安装向导",
            font=('微软雅黑', 16, 'bold'),
            fg='white',
            bg='#2c3e50'
        ).pack(expand=True)
        
        # 主内容区
        main_frame = tk.Frame(self.root, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 步骤1: 选择安装路径
        step1_frame = tk.LabelFrame(
            main_frame,
            text="步骤 1: 选择安装路径",
            font=('微软雅黑', 10, 'bold'),
            bg='#f0f0f0',
            padx=10,
            pady=10
        )
        step1_frame.pack(fill='x', pady=(0, 15))
        
        path_frame = tk.Frame(step1_frame, bg='#f0f0f0')
        path_frame.pack(fill='x')
        
        tk.Label(
            path_frame,
            text="安装路径:",
            font=('微软雅黑', 10),
            bg='#f0f0f0'
        ).pack(side='left')
        
        path_entry = tk.Entry(
            path_frame,
            textvariable=self.install_path,
            font=('微软雅黑', 10),
            width=40
        )
        path_entry.pack(side='left', padx=(10, 10), fill='x', expand=True)
        
        browse_btn = tk.Button(
            path_frame,
            text="浏览...",
            font=('微软雅黑', 9),
            bg='#3498db',
            fg='white',
            command=self.browse_path
        )
        browse_btn.pack(side='right')
        
        # 路径提示
        tk.Label(
            step1_frame,
            text="💡 建议安装到D盘或其他非系统盘，例如: D:\\forensic-ai-platform",
            font=('微软雅黑', 9),
            fg='#666666',
            bg='#f0f0f0',
            anchor='w'
        ).pack(fill='x', pady=(5, 0))
        
        # 步骤2: 安装选项
        step2_frame = tk.LabelFrame(
            main_frame,
            text="步骤 2: 安装选项",
            font=('微软雅黑', 10, 'bold'),
            bg='#f0f0f0',
            padx=10,
            pady=10
        )
        step2_frame.pack(fill='x', pady=(0, 15))
        
        tk.Checkbutton(
            step2_frame,
            text="安装 Git (版本控制工具)",
            variable=self.install_git,
            font=('微软雅黑', 10),
            bg='#f0f0f0'
        ).pack(anchor='w')
        
        tk.Checkbutton(
            step2_frame,
            text="安装 Python 依赖包",
            variable=self.install_python,
            font=('微软雅黑', 10),
            bg='#f0f0f0'
        ).pack(anchor='w')
        
        tk.Checkbutton(
            step2_frame,
            text="安装取证工具 (sleuthkit, volatility等)",
            variable=self.install_tools,
            font=('微软雅黑', 10),
            bg='#f0f0f0'
        ).pack(anchor='w')
        
        # 步骤3: 磁盘空间
        step3_frame = tk.LabelFrame(
            main_frame,
            text="步骤 3: 磁盘空间检查",
            font=('微软雅黑', 10, 'bold'),
            bg='#f0f0f0',
            padx=10,
            pady=10
        )
        step3_frame.pack(fill='x', pady=(0, 15))
        
        self.space_label = tk.Label(
            step3_frame,
            text="正在检查磁盘空间...",
            font=('微软雅黑', 10),
            bg='#f0f0f0',
            anchor='w'
        )
        self.space_label.pack(fill='x')
        
        # 检查空间
        self.root.after(100, self.check_disk_space)
        
        # 按钮区
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x')
        
        # 安装按钮
        self.install_btn = tk.Button(
            button_frame,
            text="🚀 开始安装",
            font=('微软雅黑', 12, 'bold'),
            bg='#27ae60',
            fg='white',
            padx=30,
            pady=10,
            cursor='hand2',
            command=self.start_install
        )
        self.install_btn.pack(side='left', padx=(0, 10))
        
        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            font=('微软雅黑', 11),
            bg='#95a5a6',
            fg='white',
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.root.quit
        )
        cancel_btn.pack(side='right')
        
        # 进度条
        self.progress = ttk.Progressbar(
            main_frame,
            mode='determinate'
        )
        self.progress.pack(fill='x', pady=(10, 0))
        
        # 状态标签
        self.status_label = tk.Label(
            main_frame,
            text="准备安装...",
            font=('微软雅黑', 9),
            fg='#666666',
            bg='#f0f0f0',
            anchor='w'
        )
        self.status_label.pack(fill='x', pady=(5, 0))
    
    def browse_path(self):
        """浏览文件夹"""
        path = filedialog.askdirectory(
            title="选择安装路径",
            initialdir=os.path.dirname(self.install_path.get())
        )
        if path:
            # 添加子目录
            install_dir = os.path.join(path, "forensic-ai-platform")
            self.install_path.set(install_dir)
            self.check_disk_space()
    
    def check_disk_space(self):
        """检查磁盘空间"""
        try:
            path = self.install_path.get()
            # 获取磁盘根目录
            if os.name == 'nt':  # Windows
                drive = os.path.splitdrive(path)[0] + '\\'
            else:  # Linux/Mac
                drive = '/'
            
            # 获取磁盘空间
            total, used, free = shutil.disk_usage(drive)
            
            # 转换为GB
            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            
            # 更新显示
            if free_gb >= 2:
                self.space_label.configure(
                    text=f"✅ 可用空间: {free_gb:.1f} GB / {total_gb:.1f} GB (足够)",
                    fg='#27ae60'
                )
            else:
                self.space_label.configure(
                    text=f"⚠️ 可用空间: {free_gb:.1f} GB / {total_gb:.1f} GB (建议至少2GB)",
                    fg='#e74c3c'
                )
        except Exception as e:
            self.space_label.configure(
                text=f"无法检查磁盘空间: {e}",
                fg='#e74c3c'
            )
    
    def start_install(self):
        """开始安装"""
        # 检查路径
        path = self.install_path.get()
        
        if not path:
            messagebox.showerror("错误", "请选择安装路径!")
            return
        
        # 检查路径是否包含中文或空格
        if ' ' in path or any('\u4e00' <= c <= '\u9fff' for c in path):
            if not messagebox.askyesno("警告", 
                "安装路径包含空格或中文，可能导致某些工具无法正常工作。\n\n是否继续?"):
                return
        
        # 确认安装
        if not messagebox.askyesno("确认安装", 
            f"即将安装到:\n{path}\n\n是否继续?"):
            return
        
        # 开始安装
        self.is_installing = True
        self.install_btn.configure(state='disabled')
        threading.Thread(target=self._install_thread, daemon=True).start()
    
    def _install_thread(self):
        """安装线程"""
        path = self.install_path.get()
        
        try:
            # 步骤1: 创建目录
            self.root.after(0, lambda: self.status_label.configure(text="正在创建安装目录..."))
            self.root.after(0, lambda: self.progress.configure(value=10))
            
            os.makedirs(path, exist_ok=True)
            
            # 步骤2: 克隆仓库
            self.root.after(0, lambda: self.status_label.configure(text="正在下载项目文件..."))
            self.root.after(0, lambda: self.progress.configure(value=20))
            
            repo_url = "https://github.com/luyichen0704/forensic-ai-platform.git"
            result = subprocess.run(
                ["git", "clone", repo_url, "."],
                capture_output=True,
                text=True,
                cwd=path
            )
            
            if result.returncode != 0:
                raise Exception(f"克隆仓库失败: {result.stderr}")
            
            self.root.after(0, lambda: self.progress.configure(value=50))
            
            # 步骤3: 安装Python依赖
            if self.install_python.get():
                self.root.after(0, lambda: self.status_label.configure(text="正在安装Python依赖..."))
                self.root.after(0, lambda: self.progress.configure(value=60))
                
                requirements = os.path.join(path, "requirements.txt")
                if os.path.exists(requirements):
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", requirements, "-q"],
                        capture_output=True,
                        cwd=path
                    )
            
            self.root.after(0, lambda: self.progress.configure(value=80))
            
            # 步骤4: 创建快捷方式
            self.root.after(0, lambda: self.status_label.configure(text="正在创建快捷方式..."))
            
            # 创建桌面快捷方式
            self._create_shortcut(path)
            
            self.root.after(0, lambda: self.progress.configure(value=100))
            self.root.after(0, lambda: self.status_label.configure(text="✅ 安装完成!"))
            
            # 显示完成消息
            self.root.after(0, lambda: messagebox.showinfo("安装完成", 
                f"🎉 安装成功!\n\n"
                f"安装路径: {path}\n\n"
                f"启动方式:\n"
                f"1. 双击桌面快捷方式\n"
                f"2. 运行 {path}\\start.bat\n"
                f"3. 运行 {path}\\更新工具.bat"))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_label.configure(text=f"❌ 安装失败: {e}"))
            self.root.after(0, lambda: messagebox.showerror("安装失败", f"安装失败:\n{e}"))
        
        finally:
            self.root.after(0, lambda: self.install_btn.configure(state='normal'))
            self.is_installing = False
    
    def _create_shortcut(self, install_path):
        """创建桌面快捷方式"""
        try:
            if os.name == 'nt':  # Windows
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_path = os.path.join(desktop, "取证AI平台.bat")
                
                with open(shortcut_path, 'w') as f:
                    f.write(f'@echo off\ncd /d "{install_path}"\nstart.bat\n')
        except:
            pass
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()

def main():
    """主函数"""
    app = InstallerGUI()
    app.run()

if __name__ == "__main__":
    main()
