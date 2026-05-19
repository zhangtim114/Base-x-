# -*- coding: utf-8 -*-
"""
Base2文件加密器 - 图形界面模块
功能：将任意文件或文本转换为二进制字符串（0和1组成的字符串）
使用技术：tkinter GUI框架，支持多线程处理
整合底层模块：user（配置管理）、incode（编码）、decode（解码）
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import datetime
import threading
import time
from user import ConfigManager
import incode
import decode


class Base2Encryptor(tk.Tk):
    """
    Base2加密器主窗口类
    继承自tkinter.Tk，提供完整的图形用户界面
    功能包括：文件选择、文本输入、二进制转换、预览、导出等
    整合底层模块实现编码/解码功能
    """
    
    def __init__(self):
        """
        初始化主窗口
        设置窗口标题、大小、最小尺寸、字体样式等基本属性
        并初始化所有必要的实例变量
        """
        super().__init__()
        
        # 算法选择变量
        self.algorithm = tk.StringVar(value="Base64")
        
        # 设置窗口标题
        self.title("多功能Base编解码器")
        
        # 设置初始窗口尺寸（宽x高）
        self.geometry("1920x1080")
        
        # 设置窗口最小尺寸，防止用户缩放过小导致布局错乱
        self.minsize(800, 750)
        
        # 设置窗口内边距，使内容不贴边
        self.configure(padx=10, pady=10)
        
        # 设置全局默认字体为微软雅黑18号字
        self.option_add('*Font', '微软雅黑 18')
        
        # 存储转换后的二进制数据字符串
        self.binary_data = ""
        
        # 存储源文件的名称（用于导出时生成默认文件名）
        self.source_name = ""
        
        # 输入模式变量："file"表示文件模式，"text"表示文本输入模式
        # 使用StringVar实现与Radiobutton的双向绑定
        self.input_mode = tk.StringVar(value="file")
        
        # 文件路径变量，与文件路径输入框绑定
        self.file_path = tk.StringVar()
        
        # 进度条数值变量（0-100），与进度条控件绑定
        self.progress_var = tk.DoubleVar(value=0)
        
        # 处理状态标志位，用于防止重复操作和处理中的状态判断
        self.is_processing = False

        # 操作模式变量："encrypt"表示加密模式，"decrypt"表示解密模式
        self.operation_mode = tk.StringVar(value="encrypt")

        # 存储解密后的字节数据
        self.decrypted_bytes = None

        # 存储解密后的文本内容
        self.decrypted_text = ""

        # 解密模式的文件路径变量
        self.decrypt_file_path = tk.StringVar()

        # 解密模式的文本输入框引用
        self.binary_input_text = None

        # 解密模式的复制按钮引用
        self.decrypt_copy_btn = None

        # 处理统计信息
        self.total_bits = 0
        self.processed_bits = 0
        self.processing_start_time = None

        # 加密和解密输出的文件路径
        self.encrypt_output_path = ""
        self.decrypt_output_path = ""

        # 加密模式的复制按钮
        self.encrypt_copy_btn = None

        # 用户配置管理器（使用ConfigManager替代原ConfigParser）
        self.config_manager = ConfigManager()

        # 调用方法创建所有UI组件
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', padding=18)
        style.configure('TLabel', font=('微软雅黑', 18))
        style.configure('TButton', font=('微软雅黑', 18), padding=5)
        style.configure('Header.TLabel', font=('微软雅黑', 18, 'bold'))
        style.configure('TRadiobutton', font=('微软雅黑', 18))
        style.configure('TCombobox', font=('微软雅黑', 18))
        style.configure('TEntry', font=('微软雅黑', 18))
        style.configure('TNotebook.Tab', font=('微软雅黑', 18))
        style.configure('TLabelframe.Label', font=('微软雅黑', 18))
        style.configure('TNotebook', font=('微软雅黑', 18))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        encrypt_frame = ttk.Frame(self.notebook)
        decrypt_frame = ttk.Frame(self.notebook)
        self.notebook.add(encrypt_frame, text="  加密  ")
        self.notebook.add(decrypt_frame, text="  解密  ")

        self._create_encrypt_tab(encrypt_frame)
        self._create_decrypt_tab(decrypt_frame)

        self.on_mode_change()

    def _create_encrypt_tab(self, parent):
        input_frame = ttk.LabelFrame(parent, text="输入区", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.encrypt_input_frame = ttk.Frame(input_frame)
        self.encrypt_input_frame.pack(fill=tk.BOTH, expand=True)
        mode_frame = ttk.Frame(self.encrypt_input_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Radiobutton(mode_frame, text="选择文件", variable=self.input_mode, value="file",
                       command=self.on_mode_change).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="输入文本", variable=self.input_mode, value="text",
                       command=self.on_mode_change).pack(side=tk.LEFT)

        self.file_widget_frame = ttk.Frame(self.encrypt_input_frame)
        file_entry = ttk.Entry(self.file_widget_frame, textvariable=self.file_path, state='readonly')
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(self.file_widget_frame, text="选择文件",
                  command=self.select_file).pack(side=tk.RIGHT)

        self.text_widget_frame = ttk.Frame(self.encrypt_input_frame)
        self.text_input = scrolledtext.ScrolledText(
            self.text_widget_frame,
            height=6,
            wrap=tk.WORD,
            font=('Consolas', 18)
        )
        self.text_input.pack(fill=tk.BOTH, expand=True)
        self.text_input.bind('<KeyRelease>', self.on_text_change)

        button_frame = ttk.Frame(self.encrypt_input_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        self.convert_btn = ttk.Button(button_frame, text="转换后导出为文档",
                                     command=self.start_conversion)
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 5), pady=5)
        self.encrypt_copy_btn = ttk.Button(button_frame, text="复制到剪贴板",
                                           command=self.copy_encrypt_result,
                                           state='normal')
        self.encrypt_copy_btn.pack(side=tk.LEFT, pady=5)

        main_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        left_container = ttk.Frame(main_paned)
        main_paned.add(left_container)
        main_paned.pane(left_container, weight=1)

        preview_frame = ttk.LabelFrame(left_container, text="预览区（显示前100位二进制数据）", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            height=15,
            wrap=tk.NONE,
            font=('Consolas', 18),
            state='disabled',
            bg='#f0f0f0'
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        right_container = ttk.Frame(main_paned)
        main_paned.add(right_container)
        main_paned.pane(right_container, weight=3)

        processing_frame = ttk.LabelFrame(right_container, text="处理区", padding=10)
        processing_frame.pack(fill=tk.BOTH, expand=True)

        algorithm_frame = ttk.Frame(processing_frame)
        algorithm_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(algorithm_frame, text="算法:").pack(side=tk.LEFT, padx=(0, 5))
        self.encrypt_algorithm_combo = ttk.Combobox(
            algorithm_frame,
            textvariable=self.algorithm,
            values=["Base2 (二进制)", "Base8 (八进制)", "Base16 (十六进制)", "Base32", "Base64"],
            state="readonly",
            width=15
        )
        self.encrypt_algorithm_combo.pack(side=tk.LEFT)
        self.encrypt_algorithm_combo.bind("<<ComboboxSelected>>", self._on_algorithm_change)

        progress_frame = ttk.Frame(processing_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X)
        self.status_label = ttk.Label(progress_frame, text="就绪 - 请选择文件或输入文本")
        self.status_label.pack(fill=tk.X, pady=(5, 0))

        stats_frame = ttk.Frame(processing_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        self.encrypt_total_label = ttk.Label(stats_frame, text="原数据总大小: -- 位")
        self.encrypt_total_label.pack(anchor=tk.W, pady=2)
        self.encrypt_processed_label = ttk.Label(stats_frame, text="已处理: -- 位")
        self.encrypt_processed_label.pack(anchor=tk.W, pady=2)
        self.encrypt_remaining_label = ttk.Label(stats_frame, text="未处理: -- 位")
        self.encrypt_remaining_label.pack(anchor=tk.W, pady=2)
        self.encrypt_speed_label = ttk.Label(stats_frame, text="处理速度: -- 位/秒")
        self.encrypt_speed_label.pack(anchor=tk.W, pady=2)

    def _create_decrypt_tab(self, parent):
        input_frame = ttk.LabelFrame(parent, text="输入区", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.decrypt_input_frame = ttk.Frame(input_frame)
        self.decrypt_input_frame.pack(fill=tk.BOTH, expand=True)
        decrypt_file_frame = ttk.Frame(self.decrypt_input_frame)
        decrypt_file_frame.pack(fill=tk.X, pady=(0, 5))
        decrypt_file_entry = ttk.Entry(decrypt_file_frame, textvariable=self.decrypt_file_path, state='readonly')
        decrypt_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(decrypt_file_frame, text="选择二进制文件",
                  command=self.select_decrypt_file).pack(side=tk.RIGHT)

        self.binary_input_text = scrolledtext.ScrolledText(
            self.decrypt_input_frame,
            height=6,
            wrap=tk.NONE,
            font=('Consolas', 18)
        )
        self.binary_input_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.binary_input_text.bind('<KeyRelease>', self.on_decrypt_text_change)

        decrypt_button_frame = ttk.Frame(self.decrypt_input_frame)
        decrypt_button_frame.pack(fill=tk.X, pady=(10, 0))
        self.decrypt_btn = ttk.Button(decrypt_button_frame, text="导出解密为文档",
                                      command=self.start_decryption)
        self.decrypt_btn.pack(side=tk.LEFT, padx=(0, 5), pady=5)
        self.decrypt_copy_btn = ttk.Button(decrypt_button_frame, text="复制到剪贴板",
                                           command=self.copy_decrypt_result,
                                           state='normal')
        self.decrypt_copy_btn.pack(side=tk.LEFT, pady=5)

        main_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        left_container = ttk.Frame(main_paned)
        main_paned.add(left_container)
        main_paned.pane(left_container, weight=1)

        preview_frame = ttk.LabelFrame(left_container, text="预览区", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.decrypt_preview_text = scrolledtext.ScrolledText(
            preview_frame,
            height=15,
            wrap=tk.WORD,
            font=('Consolas', 18),
            state='disabled',
            bg='#f0f0f0'
        )
        self.decrypt_preview_text.pack(fill=tk.BOTH, expand=True)

        right_container = ttk.Frame(main_paned)
        main_paned.add(right_container)
        main_paned.pane(right_container, weight=3)

        decrypt_processing_frame = ttk.LabelFrame(right_container, text="处理区", padding=10)
        decrypt_processing_frame.pack(fill=tk.BOTH, expand=True)

        decrypt_algorithm_frame = ttk.Frame(decrypt_processing_frame)
        decrypt_algorithm_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(decrypt_algorithm_frame, text="算法:").pack(side=tk.LEFT, padx=(0, 5))
        self.decrypt_algorithm_combo = ttk.Combobox(
            decrypt_algorithm_frame,
            textvariable=self.algorithm,
            values=["Base2 (二进制)", "Base8 (八进制)", "Base16 (十六进制)", "Base32", "Base64"],
            state="readonly",
            width=15
        )
        self.decrypt_algorithm_combo.pack(side=tk.LEFT)

        progress_frame = ttk.Frame(decrypt_processing_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        self.decrypt_progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.decrypt_progress_bar.pack(fill=tk.X)
        self.decrypt_status_label = ttk.Label(progress_frame, text="就绪 - 请输入二进制数据或选择文件")
        self.decrypt_status_label.pack(fill=tk.X, pady=(5, 0))

        stats_frame = ttk.Frame(decrypt_processing_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        self.decrypt_total_label = ttk.Label(stats_frame, text="原数据总大小: -- 位")
        self.decrypt_total_label.pack(anchor=tk.W, pady=2)
        self.decrypt_processed_label = ttk.Label(stats_frame, text="已处理: -- 位")
        self.decrypt_processed_label.pack(anchor=tk.W, pady=2)
        self.decrypt_remaining_label = ttk.Label(stats_frame, text="未处理: -- 位")
        self.decrypt_remaining_label.pack(anchor=tk.W, pady=2)
        self.decrypt_speed_label = ttk.Label(stats_frame, text="处理速度: -- 位/秒")
        self.decrypt_speed_label.pack(anchor=tk.W, pady=2)

    def on_mode_change(self):
        """
        处理输入模式切换事件
        当用户在"选择文件"和"输入文本"之间切换时调用
        根据当前选择的模式显示/隐藏对应的输入控件
        """
        # 先隐藏两个输入控件组（防止同时显示）
        self.text_widget_frame.pack_forget()   # 隐藏文本输入框
        self.file_widget_frame.pack_forget()   # 隐藏文件选择框
        
        # 根据当前选中的模式显示对应的控件
        if self.input_mode.get() == "file":
            # 文件模式：显示文件选择控件
            self.file_widget_frame.pack(fill=tk.X, pady=5)
        else:
            # 文本模式：显示文本输入控件，允许垂直扩展
            self.text_widget_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 模式切换后重新验证输入有效性，更新按钮状态（包括复制按钮）
        self.validate_input()

    def _on_tab_changed(self, event):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            # 切换到加密标签页
            self.operation_mode.set("encrypt")
            self.decrypted_bytes = None
            self.decrypted_text = ""
            # 清空解密页面的统计信息
            self._reset_processing_stats(is_decrypt=True)

            # 新逻辑：根据输入有效性设置按钮状态（而非依赖输出结果）
            self.validate_input()
        else:
            # 切换到解密标签页
            self.operation_mode.set("decrypt")
            # 清空加密页面的统计信息
            self._reset_processing_stats(is_decrypt=False)

            # 新逻辑：根据输入有效性设置按钮状态（而非依赖输出结果）
            self.validate_decrypt_input()

    def _on_algorithm_change(self, event=None):
        """算法切换时的回调函数"""
        current_algo = self.algorithm.get()

        # 更新加密页面的预览区标题
        algo_short = current_algo.split(' ')[0]  # 取 "Base2" 等简称
        if hasattr(self, 'preview_text'):
            # 可以在这里动态更新预览区标题
            pass

    def select_file(self):
        """
        打开文件选择对话框
        让用户选择要转换的文件
        支持所有文件类型
        """
        # 弹出文件选择对话框
        # title: 对话框标题
        # filetypes: 文件类型过滤器（此处允许所有文件）
        file_path = filedialog.askopenfilename(
            title="选择要转换的文件", 
            filetypes=[("所有文件", "*.*")]
        )
        
        # 如果用户选择了文件（未取消）
        if file_path:
            # 将选中文件的完整路径设置到file_path变量（会自动更新到输入框显示）
            self.file_path.set(file_path)
            
            # 验证输入是否有效，决定是否启用"开始转换"按钮
            self.validate_input()

    def on_text_change(self, event=None):
        """
        文本输入框内容变化时的回调函数
        每次键盘按键释放后触发，实时验证输入内容
        参数event: 键盘事件对象（可选，未使用但需保留以符合tkinter接口规范）
        """
        self.validate_input()

    def validate_input(self):
        """
        验证当前输入是否有效
        根据：
        1. 是否正在处理中（is_processing标志）
        2. 当前模式下是否有有效输入内容
        来决定"开始转换"按钮的启用/禁用状态
        """
        # 如果正在处理中，禁用转换按钮防止重复操作
        if self.is_processing:
            self.convert_btn.config(state='disabled')
            return
        
        # 根据当前输入模式检查是否有有效输入
        if self.input_mode.get() == "file":
            # 文件模式：检查文件路径是否非空
            has_input = bool(self.file_path.get())
        else:
            # 文本模式：获取文本框全部内容（从第1行第0列到末尾）并去除首尾空白
            has_input = bool(self.text_input.get("1.0", tk.END).strip())
        
        # 根据是否有有效输入设置按钮状态
        self.convert_btn.config(state='normal' if has_input else 'disabled')
        # 新逻辑：复制按钮与导出按钮同步，基于输入有效性启用
        if self.encrypt_copy_btn:
            self.encrypt_copy_btn.config(state='normal' if has_input else 'disabled')

    def _make_progress_callback(self, is_decrypt=False):
        """
        创建进度回调函数用于包装GUI更新
        确保在后台线程中安全地更新GUI组件
        
        参数is_decrypt: 是否为解密模式（决定更新哪组状态标签）
        返回值: 回调函数(progress_percent, status_text)
        """
        def callback(progress_percent, status_text=None):
            # 通过after()在主线程更新进度条
            self.after(0, lambda p=progress_percent: self.progress_var.set(p))
            if status_text:
                # 根据模式更新对应的状态标签
                if is_decrypt:
                    self.after(0, lambda s=status_text: self.decrypt_status_label.config(text=s))
                else:
                    self.after(0, lambda s=status_text: self.status_label.config(text=s))
        return callback

    def _show_save_dialog_for_encrypt(self):
        """显示加密模式的保存对话框"""
        # 生成默认文件名（保持原有逻辑不变）
        if self.input_mode.get() == "file" and self.file_path.get():
            original_name = os.path.basename(self.file_path.get())
            default_filename = f"{original_name}.txt"
            fallback_dir = os.path.dirname(self.file_path.get())
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"text_input_{timestamp}.txt"
            fallback_dir = self._get_safe_save_directory()

        # 确定初始目录：优先使用配置文件中的路径，回退到原有逻辑
        initial_dir = self._get_initial_dir_for_encrypt(fallback_dir)

        file_path = filedialog.asksaveasfilename(
            title="保存二进制数据",
            defaultextension=".txt",
            initialfile=default_filename,
            initialdir=initial_dir if initial_dir else self._get_safe_save_directory(),
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        return file_path

    def _get_initial_dir_for_encrypt(self, fallback_dir):
        """
        获取加密保存对话框的初始目录
        优先级：配置文件路径 > 回退目录
        
        参数fallback_dir: 原有逻辑确定的回退目录
        返回值: 应该使用的初始目录路径
        """
        # 第一优先级：检查配置管理器中的加密保存路径
        config_path = self.config_manager.get_encrypt_last_path()
        if config_path:
            config_path = config_path.strip()
            # 验证路径非空且存在
            if config_path and os.path.exists(config_path) and os.path.isdir(config_path):
                return config_path
        
        # 第二优先级：使用原有的回退逻辑
        if fallback_dir and os.path.exists(fallback_dir):
            return fallback_dir
        
        # 最终回退到安全目录
        return self._get_safe_save_directory()

    def start_conversion(self):
        """
        开始转换流程的入口方法
        执行以下操作：
        1. 设置处理状态标志
        2. 禁用相关按钮防止重复操作
        3. 重置进度条和状态信息
        4. 启动后台线程执行实际转换工作
        使用多线程避免阻塞GUI主线程，保持界面响应
        """
        # 如果已经在处理中，直接返回（防止重复启动）
        if self.is_processing:
            return
        
        # 标记开始处理
        self.is_processing = True

        # 弹出保存对话框让用户选择输出路径
        output_path = self._show_save_dialog_for_encrypt()
        if not output_path:
            self.is_processing = False
            self.validate_input()
            return

        self.encrypt_output_path = output_path

        # 记录本次选择的保存路径到配置管理器
        self.config_manager.update_encrypt_path(output_path)

        # 禁用操作按钮，防止用户在处理过程中再次点击
        self.convert_btn.config(state='disabled')      # 禁用"开始转换"
        if self.encrypt_copy_btn:
            self.encrypt_copy_btn.config(state='disabled')  # 禁用"复制到剪贴板"

        # 重置进度条到0%
        self.progress_var.set(0)

        # 更新状态栏提示文字
        self.status_label.config(text="处理中...")
        
        # 创建并启动后台工作线程
        # target: 线程要执行的函数（实际的转换逻辑）
        # daemon=True: 设置为守护线程，主程序退出时自动结束
        thread = threading.Thread(target=self._convert_worker, daemon=True)
        thread.start()

    def _convert_worker(self):
        """
        后台工作线程的主函数
        在独立线程中执行耗时的文件读取和转换操作
        包含完整的异常处理机制
        注意：此方法在非主线程运行，不能直接操作GUI控件！
        必须通过self.after()方法将GUI更新操作调度回主线程
        """
        try:
            # 创建进度回调函数
            callback = self._make_progress_callback(is_decrypt=False)

            # 根据输入模式执行不同的转换逻辑
            if self.input_mode.get() == "file":
                # ===== 文件模式 =====
                # 获取文件路径
                file_path = self.file_path.get()
                
                # 验证文件是否存在
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"文件不存在: {file_path}")
                
                # 提取文件名（不含路径），用于后续导出命名
                self.source_name = os.path.basename(file_path)
                
                # 获取文件大小（字节）
                file_size = os.path.getsize(file_path)
                
                # 检查文件是否过大（超过100MB）
                # 大文件可能需要较长时间处理，需要用户确认
                if file_size > 100 * 1024 * 1024:
                    # 通过after()在主线程显示警告对话框
                    self.after(0, lambda: self._show_large_file_warning(file_path))
                    return  # 提前返回，等待用户确认后再继续
                
                # 正常大小的文件：直接执行转换（使用incode模块）
                current_algo = self.algorithm.get()
                preview_data, total_bits = incode.encode_file(
                    file_path, 
                    self.encrypt_output_path, 
                    current_algo,
                    callback
                )
                self.binary_data = preview_data  # 仅存储预览数据
            else:
                # ===== 文本模式 =====
                # 获取文本框中的全部内容
                text_content = self.text_input.get("1.0", tk.END).strip()
                
                # 验证文本内容不为空
                if not text_content:
                    raise ValueError("输入内容为空")
                
                # 设置源名称标识
                self.source_name = "手动输入文本"
                
                # 将文本转换为指定格式的编码字符串（使用incode模块）
                current_algo = self.algorithm.get()
                binary_data = incode.encode_data(text_content.encode('utf-8'), current_algo)

                # 直接写入输出文件
                decode.ensure_directory_exists(self.encrypt_output_path)
                with open(self.encrypt_output_path, 'w', encoding='utf-8') as f:
                    f.write(binary_data)

                # 仅保留前100位用于预览
                self.binary_data = binary_data[:100]

                # 更新文本模式的统计信息（瞬间完成）
                total_bits = len(binary_data)
                self.total_bits = total_bits
                self.processed_bits = total_bits
                self.processing_start_time = time.time()
                self._update_processing_stats(total_bits, total_bits, is_decrypt=False)
            
            # 转换完成：通过after()调度主线程执行完成后的UI更新
            self.after(0, self._on_conversion_complete)
            
        except Exception as e:
            # 捕获所有异常：通过after()调度主线程显示错误信息
            self.after(0, lambda: self._on_conversion_error(str(e)))

    def _show_large_file_warning(self, file_path):
        """
        显示大文件警告对话框
        当文件超过100MB时调用，让用户确认是否继续处理
        参数file_path: 要处理的文件路径
        """
        # 计算文件大小（GB或MB，保留1位小数）
        if os.path.getsize(file_path) > 1024 * 1024 * 1024 :
            size_xb = os.path.getsize(file_path) / 1024 / 1024 / 1024
            unit = "GB"
        else:
            size_xb = os.path.getsize(file_path) / 1024 / 1024
            unit = "MB"
        
        # 显示确认对话框
        # askyesno: 返回True（是）/False（否）
        result = messagebox.askyesno(
            "警告", 
            f"文件较大({size_xb:.1f} {unit})，处理可能需要较长时间。\n是否继续？"
        )
        
        if result:
            # 用户确认继续：启动新线程处理大文件
            thread = threading.Thread(
                target=lambda: self._process_large_file(file_path), 
                daemon=True
            )
            thread.start()
        else:
            # 用户取消：重置状态
            self.is_processing = False
            self.validate_input()          # 重新验证输入，恢复按钮状态
            self.status_label.config(text="已取消")
            self._reset_processing_stats(is_decrypt=False)  # 新增这行

    def _process_large_file(self, file_path):
        """
        处理大文件的专用方法
        在用户确认后调用，执行实际的文件转换操作
        与普通文件处理相同，但单独提取出来便于流程控制
        参数file_path: 要处理的大文件路径
        """
        try:
            # 创建进度回调函数
            callback = self._make_progress_callback(is_decrypt=False)

            # 执行文件到二进制的转换（使用incode模块）
            preview_data, total_bits = incode.file_to_binary(
                file_path, 
                self.encrypt_output_path,
                callback
            )
            self.binary_data = preview_data  # 仅存储预览数据

            # 转换完成：调度主线程更新UI
            self.after(0, self._on_conversion_complete)
        except Exception as e:
            # 出错：调度主线程显示错误
            self.after(0, lambda: self._on_conversion_error(str(e)))

    def _format_speed(self, bits_per_second):
        """
        将位/秒的速度值格式化为易读的字符串

        参数:
            bits_per_second: 速度值（位/秒）
        返回:
            str: 格式化后的速度字符串，如 "1,234,567.89 位/秒"
        """
        if bits_per_second >= 1000000:
            return f"{bits_per_second:,.0f} 位/秒"
        elif bits_per_second >= 1000:
            return f"{bits_per_second:,.2f} 位/秒"
        else:
            return f"{bits_per_second:.2f} 位/秒"

    def _update_processing_stats(self, total, processed, is_decrypt=False):
        """
        更新处理区的统计信息标签

        参数:
            total: 原数据总位数 (int)
            processed: 已处理位数 (int)
            is_decrypt: 是否为解密模式 (bool)，决定更新哪组标签
        """
        # 根据算法确定单位
        current_algo = getattr(self, 'algorithm', None)
        if current_algo:
            algo = current_algo.get() if hasattr(current_algo, 'get') else "Base2"
            if "Base2" in algo or "二进制" in algo:
                unit = "位"
            elif "Base8" in algo or "八进制" in algo:
                unit = "八位组"
            elif "Base16" in algo or "十六进制" in algo:
                unit = "字符"
            elif "Base32" in algo:
                unit = "字符"
            elif "Base64" in algo:
                unit = "字符"
            else:
                unit = "位"
        else:
            unit = "位"

        remaining = total - processed

        if self.processing_start_time and processed > 0:
            elapsed = time.time() - self.processing_start_time
            speed = processed / elapsed if elapsed > 0 else 0
        else:
            speed = 0

        total_str = f"{total:,}"
        processed_str = f"{processed:,}"
        remaining_str = f"{remaining:,}"
        speed_str = f"{speed:,.2f}"

        if is_decrypt:
            self.decrypt_total_label.config(text=f"原数据总大小: {total_str} {unit}")
            self.decrypt_processed_label.config(text=f"已处理: {processed_str} {unit}")
            self.decrypt_remaining_label.config(text=f"未处理: {remaining_str} {unit}")
            speed_formatted = self._format_speed(speed)
            self.decrypt_speed_label.config(text=f"处理速度: {speed_formatted}")
        else:
            self.encrypt_total_label.config(text=f"原数据总大小: {total_str} {unit}")
            self.encrypt_processed_label.config(text=f"已处理: {processed_str} {unit}")
            self.encrypt_remaining_label.config(text=f"未处理: {remaining_str} {unit}")
            speed_formatted = self._format_speed(speed)
            self.encrypt_speed_label.config(text=f"处理速度: {speed_formatted}")

    def _reset_processing_stats(self, is_decrypt=False):
        """
        重置处理区的统计信息标签到初始状态

        参数:
            is_decrypt: 是否为解密模式 (bool)
        """
        if is_decrypt:
            self.decrypt_total_label.config(text="原数据总大小: -- 位")
            self.decrypt_processed_label.config(text="已处理: -- 位")
            self.decrypt_remaining_label.config(text="未处理: -- 位")
            self.decrypt_speed_label.config(text="处理速度: -- 位/秒")
        else:
            self.encrypt_total_label.config(text="原数据总大小: -- 位")
            self.encrypt_processed_label.config(text="已处理: -- 位")
            self.encrypt_remaining_label.config(text="未处理: -- 位")
            self.encrypt_speed_label.config(text="处理速度: -- 位/秒")

        # 重置内部变量
        self.total_bits = 0
        self.processed_bits = 0
        self.processing_start_time = None

    def _on_conversion_complete(self):
        """转换完成后的UI更新方法"""
        # 重置处理状态标志
        self.is_processing = False
        
        # 进度条设为100%（完成）
        self.progress_var.set(100)
        
        # 获取预览数据（已经在前100位，无需再次截取）
        preview = self.binary_data if self.binary_data else ""
        
        # 启用预览文本框以便写入内容
        self.preview_text.config(state='normal')
        
        # 清空旧内容
        self.preview_text.delete(1.0, tk.END)
        
        # 插入新的预览数据
        self.preview_text.insert(tk.END, preview)
        
        # 再次设为只读状态
        self.preview_text.config(state='disabled')
        
        # 显示输出文件路径信息（而不是数据长度）
        if hasattr(self, 'encrypt_output_path') and self.encrypt_output_path:
            self.status_label.config(
                text=f"✓ 转换完成 | 文件已保存至: {self.encrypt_output_path}",
                foreground='green'
            )
        else:
            self.status_label.config(text="转换完成")
        
        # 更新最终统计信息（100%完成状态）
        final_total = self.total_bits
        self._update_processing_stats(final_total, final_total, is_decrypt=False)

        # 新逻辑：通过 validate_input() 恢复复制按钮和导出按钮状态
        self.validate_input()

    def _on_conversion_error(self, error_msg):
        """转换出错时的错误处理方法"""
        # 重置处理状态
        self.is_processing = False
        
        # 进度条归零
        self.progress_var.set(0)
        
        # 在状态栏显示错误信息（红色前景色）
        self.status_label.config(text=f"错误: {error_msg}", foreground='red')
        
        # 弹出错误提示对话框
        messagebox.showerror("转换错误", error_msg)
        
        # 重置统计信息
        self._reset_processing_stats(is_decrypt=False)

        # 新逻辑：通过 validate_input() 恢复按钮状态（输入仍然有效时启用）
        self.validate_input()

    def _get_safe_save_directory(self):
        """
        获取一个安全可写的保存目录
        按优先级依次检查以下目录：
        1. 桌面（Desktop）
        2. 文档（Documents）
        3. 下载（Downloads）
        4. 当前工作目录
        5. 用户主目录（最后保底）
        
        返回值: 第一个存在且可写的目录路径
        """
        # 定义候选目录列表（按优先级排序）
        safe_paths = [
            os.path.join(os.path.expanduser("~"), "Desktop"),     # 桌面
            os.path.join(os.path.expanduser("~"), "Documents"),    # 文档
            os.path.join(os.path.expanduser("~"), "Downloads"),   # 下载
            os.getcwd()                                           # 当前工作目录
        ]
        
        # 遍历候选目录，找到第一个存在且可写的
        for path in safe_paths:
            # os.path.exists: 目录是否存在
            # os.access(path, os.W_OK): 是否有写入权限
            if os.path.exists(path) and os.access(path, os.W_OK):
                return path
        
        # 所有候选目录都不可用时，返回用户主目录作为最后保底
        return os.path.expanduser("~")

    def _ensure_directory_exists(self, file_path):
        """
        确保文件所在的目录存在
        如果目录不存在则递归创建
        使用exist_ok=True避免目录已存在时报错
        
        参数file_path: 目标文件的完整路径
        """
        # 提取目录部分
        directory = os.path.dirname(file_path)
        
        # 如果目录非空且不存在
        if directory and not os.path.exists(directory):
            try:
                # 递归创建目录（包括所有父目录）
                # exist_ok=True: 目录已存在时不报错
                os.makedirs(directory, exist_ok=True)
            except Exception:
                # 创建失败时静默忽略（后续写文件时会报更具体的错误）
                pass

    def _handle_permission_error(self, default_filename):
        """
        处理文件写入权限错误
        当原路径无写入权限时：
        1. 提示用户改用备用目录
        2. 用户同意后尝试保存到备用位置
        3. 仍然失败则显示详细错误信息
        
        参数default_filename: 默认文件名（用于构建备用路径）
        """
        # 获取安全的备用保存目录
        fallback_dir = self._get_safe_save_directory()
        
        # 构建备用保存路径
        fallback_path = os.path.join(fallback_dir, default_filename)
        
        # 询问用户是否愿意保存到备用位置
        result = messagebox.askyesno(
            "权限错误", 
            f"原路径无写入权限。\n\n"
            f"是否改为保存到:\n{fallback_path}"
        )
        
        if result:
            # 用户同意：尝试保存到备用位置
            try:
                with open(fallback_path, 'w', encoding='utf-8') as f:
                    f.write(self.binary_data)

                # 显示成功信息
                messagebox.showinfo("导出成功", f"文件已成功导出到:\n{fallback_path}")
            except Exception as e:
                # 备用位置也失败了
                messagebox.showerror("导出失败", f"无法导出文件:\n{str(e)}")

    def _copy_to_clipboard(self, text):
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            return True
        except Exception:
            return False

    def _show_copy_success_feedback(self, label_widget, original_text):
        label_widget.config(text="✓ 已复制到剪贴板", foreground='green')
        self.after(2000, lambda: label_widget.config(text=original_text))

    def _format_file_size(self, size_bytes):
        if size_bytes >= 1024 * 1024 * 1024:
            return f"{size_bytes / 1024 / 1024 / 1024:.2f} GB"
        elif size_bytes >= 1024 * 1024:
            return f"{size_bytes / 1024 / 1024:.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} B"

    def _show_size_limit_error(self, label_widget, actual_size, limit_size=1024, mode="文件"):
        actual_str = self._format_file_size(actual_size)
        limit_str = self._format_file_size(limit_size)
        label_widget.config(
            text=f'⚠️ {mode}过大({actual_str} > {limit_str})，无法直接复制到剪贴板。请使用"导出为文档"功能保存完整数据。',
            foreground='red'
        )

    def copy_encrypt_result(self):
        if self.input_mode.get() == "text":
            text_content = self.text_input.get("1.0", tk.END).strip()
            if not text_content:
                self.status_label.config(text="错误: 没有可复制的内容", foreground='red')
                return
            try:
                current_algo = self.algorithm.get()
                # 使用incode模块进行编码
                binary_data = incode.encode_data(text_content.encode('utf-8'), current_algo)
                if len(binary_data) > 8 * 1024:
                    self._show_size_limit_error(self.status_label, len(binary_data), 8 * 1024, "生成的二进制数据")
                    return
                if self._copy_to_clipboard(binary_data):
                    original_text = self.status_label.cget("text")
                    self._show_copy_success_feedback(self.status_label, original_text)
                else:
                    self.status_label.config(text="错误: 复制到剪贴板失败", foreground='red')
            except Exception as e:
                self.status_label.config(text=f"错误: {str(e)}", foreground='red')
        elif self.input_mode.get() == "file":
            file_path = self.file_path.get()
            if not file_path:
                self.status_label.config(text="错误: 没有可复制的内容", foreground='red')
                return
            if not os.path.exists(file_path):
                self.status_label.config(text=f"错误: 文件不存在 - {file_path}", foreground='red')
                return
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 1024:
                    self._show_size_limit_error(self.status_label, file_size, 1024, "文件")
                    return
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                current_algo = self.algorithm.get()
                # 使用incode模块进行编码
                binary_data = incode.encode_data(file_bytes, current_algo)
                if self._copy_to_clipboard(binary_data):
                    original_text = self.status_label.cget("text")
                    self._show_copy_success_feedback(self.status_label, original_text)
                else:
                    self.status_label.config(text="错误: 复制到剪贴板失败", foreground='red')
            except Exception as e:
                self.status_label.config(text=f"错误: 读取文件失败 - {str(e)}", foreground='red')
        else:
            self.status_label.config(text="错误: 没有可复制的内容", foreground='red')

    def copy_decrypt_result(self):
        binary_str = self.binary_input_text.get("1.0", tk.END).strip()
        if binary_str:
            binary_str = binary_str.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
            if not binary_str:
                self.decrypt_status_label.config(text="错误: 没有可复制的解密数据", foreground='red')
                return
            # 根据当前算法验证输入数据
            current_algo = self.algorithm.get()
            if "Base2" in current_algo or "二进制" in current_algo:
                if not all(c in '01' for c in binary_str):
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法字符（仅允许0和1）", foreground='red')
                    return
            elif "Base8" in current_algo or "八进制" in current_algo:
                if not all(c in '01234567' for c in binary_str):
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法字符（仅允许0-7）", foreground='red')
                    return
            elif "Base16" in current_algo or "十六进制" in current_algo:
                clean_check = binary_str.lower()
                if not all(c in '0123456789abcdef' for c in clean_check):
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法字符（仅允许0-9, a-f, A-F）", foreground='red')
                    return
            elif "Base32" in current_algo:
                clean_check = binary_str.upper().replace('=', '')
                if not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567' for c in clean_check):
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法的Base32字符", foreground='red')
                    return
            elif "Base64" in current_algo:
                import base64
                try:
                    base64.b64decode(binary_str)
                except Exception:
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法的Base64字符", foreground='red')
                    return
            try:
                # 使用decode模块进行解码
                bytes_data = decode.decode_data(binary_str, current_algo)
            except ValueError as e:
                self.decrypt_status_label.config(text=f"错误: {str(e)}", foreground='red')
                return
            if len(bytes_data) > 8 * 1024:
                self._show_size_limit_error(self.decrypt_status_label, len(bytes_data), 8 * 1024, "解密后的数据")
                return
            try:
                text_to_copy = bytes_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_to_copy = bytes_data.decode('latin-1')
                except Exception:
                    text_to_copy = bytes_data.hex()
        else:
            file_path = self.decrypt_file_path.get()
            if not file_path:
                self.decrypt_status_label.config(text="错误: 没有可复制的解密数据", foreground='red')
                return
            if not os.path.exists(file_path):
                self.decrypt_status_label.config(text=f"错误: 文件不存在 - {file_path}", foreground='red')
                return
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 1024:
                    self._show_size_limit_error(self.decrypt_status_label, file_size, 1024, "二进制文件")
                    return
            except Exception as e:
                pass
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    binary_str = f.read()
            except Exception as e:
                self.decrypt_status_label.config(text=f"错误: 文件读取失败 - {str(e)}", foreground='red')
                return
            binary_str = binary_str.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
            if not binary_str:
                self.decrypt_status_label.config(text="错误: 没有可复制的解密数据", foreground='red')
                return
            # 根据当前算法验证输入数据
            current_algo = self.algorithm.get()
            if "Base2" in current_algo or "二进制" in current_algo:
                if not all(c in '01' for c in binary_str):
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法字符（仅允许0和1）", foreground='red')
                    return
            elif "Base8" in current_algo or "八进制" in current_algo:
                if not all(c in '01234567' for c in binary_str):
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法字符（仅允许0-7）", foreground='red')
                    return
            elif "Base16" in current_algo or "十六进制" in current_algo:
                clean_check = binary_str.lower()
                if not all(c in '0123456789abcdef' for c in clean_check):
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法字符（仅允许0-9, a-f, A-F）", foreground='red')
                    return
            elif "Base32" in current_algo:
                clean_check = binary_str.upper().replace('=', '')
                if not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567' for c in clean_check):
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法的Base32字符", foreground='red')
                    return
            elif "Base64" in current_algo:
                import base64
                try:
                    base64.b64decode(binary_str)
                except Exception:
                    self.decrypt_status_label.config(text="错误: 输入数据包含非法的Base64字符", foreground='red')
                    return
            try:
                # 使用decode模块进行解码
                bytes_data = decode.decode_data(binary_str, current_algo)
            except ValueError as e:
                self.decrypt_status_label.config(text=f"错误: {str(e)}", foreground='red')
                return
            try:
                text_to_copy = bytes_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_to_copy = bytes_data.decode('latin-1')
                except Exception:
                    text_to_copy = bytes_data.hex()
        original_text = self.decrypt_status_label.cget("text")
        if self._copy_to_clipboard(text_to_copy):
            self._show_copy_success_feedback(self.decrypt_status_label, original_text)
        else:
            self.decrypt_status_label.config(text="错误: 复制到剪贴板失败", foreground='red')

    def select_decrypt_file(self):
        """
        打开解密文件选择对话框
        让用户选择包含二进制数据的TXT文件
        """
        file_path = filedialog.askopenfilename(
            title="选择包含二进制数据的文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.decrypt_file_path.set(file_path)
            self.validate_decrypt_input()

    def on_decrypt_text_change(self, event=None):
        """
        解密文本输入框内容变化时的回调函数
        每次键盘按键释放后触发，实时验证输入内容
        """
        self.validate_decrypt_input()

    def validate_decrypt_input(self):
        """
        验证解密模式下的输入是否有效
        根据是否有有效的二进制数据输入来决定"开始解密"按钮的启用/禁用状态
        """
        if self.is_processing:
            self.decrypt_btn.config(state='disabled')
            return

        has_file_input = bool(self.decrypt_file_path.get())
        has_text_input = bool(self.binary_input_text.get("1.0", tk.END).strip())

        self.decrypt_btn.config(state='normal' if (has_file_input or has_text_input) else 'disabled')
        # 新逻辑：复制按钮与导出按钮同步，基于输入有效性启用
        if self.decrypt_copy_btn:
            self.decrypt_copy_btn.config(state='normal' if (has_file_input or has_text_input) else 'disabled')

    def _show_save_dialog_for_decrypt(self):
        """显示解密模式的保存对话框"""
        # 智能生成默认输出文件名（保持原有逻辑不变）
        if self.decrypt_file_path.get():
            input_filename = os.path.basename(self.decrypt_file_path.get())
            # 如果输入文件以 .txt 结尾，去除该后缀作为默认输出名（保留原始扩展名）
            if input_filename.lower().endswith('.txt'):
                default_filename = input_filename[:-4]  # 去掉 .txt 后缀
            else:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = f"decrypted_{timestamp}.bin"
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"decrypted_{timestamp}.bin"

        # 确定初始目录：优先使用配置文件中的解密路径
        initial_dir = self._get_initial_dir_for_decrypt()

        file_path = filedialog.asksaveasfilename(
            title="保存解密后的文件",
            defaultextension="",
            initialfile=default_filename,
            initialdir=initial_dir,
            filetypes=[("所有文件", "*.*")]
        )

        return file_path

    def _get_initial_dir_for_decrypt(self):
        """
        获取解密保存对话框的初始目录
        优先级：配置文件路径 > 安全目录
        
        返回值: 应该使用的初始目录路径
        """
        # 第一优先级：检查配置管理器中的解密保存路径
        config_path = self.config_manager.get_decrypt_last_path()
        if config_path:
            config_path = config_path.strip()
            # 验证路径非空且存在
            if config_path and os.path.exists(config_path) and os.path.isdir(config_path):
                return config_path
        
        # 第二优先级：使用安全目录
        return self._get_safe_save_directory()

    def start_decryption(self):
        """
        开始解密流程的入口方法
        执行以下操作：
        1. 设置处理状态标志
        2. 禁用相关按钮防止重复操作
        3. 重置进度条和状态信息
        4. 启动后台线程执行实际解密工作
        """
        if self.is_processing:
            return

        self.is_processing = True

        # 弹出保存对话框让用户选择输出路径
        output_path = self._show_save_dialog_for_decrypt()
        if not output_path:
            self.is_processing = False
            self.validate_decrypt_input()
            return

        self.decrypt_output_path = output_path

        # 记录本次选择的保存路径到配置管理器
        self.config_manager.update_decrypt_path(output_path)

        self.decrypt_btn.config(state='disabled')

        if self.decrypt_copy_btn:
            self.decrypt_copy_btn.config(state='disabled')

        self.progress_var.set(0)
        self.decrypt_status_label.config(text="解密中...")

        thread = threading.Thread(target=self._decrypt_worker, daemon=True)
        thread.start()

    def _decrypt_worker(self):
        """后台解密工作线程的主函数"""
        try:
            # 创建进度回调函数
            callback = self._make_progress_callback(is_decrypt=True)

            if self.decrypt_file_path.get():
                # ===== 文件输入模式：流式处理 =====
                file_path = self.decrypt_file_path.get()
                
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"文件不存在: {file_path}")
                
                # 执行流式解密并直接写入输出文件（使用decode模块，支持多算法）
                current_algo = self.algorithm.get()
                preview_text, total_bytes = decode.decode_file(
                    file_path,
                    self.decrypt_output_path,
                    current_algo,
                    callback
                )
                
                self.decrypted_text = preview_text
                
                # 更新统计信息
                total_bits = total_bytes * 8
                self.total_bits = total_bits
                self.processed_bits = total_bits
                self.processing_start_time = time.time()
                self.after(0, lambda: self._update_processing_stats(total_bits, total_bits, is_decrypt=True))
                
            else:
                # ===== 文本输入模式：保持原有内存处理 =====
                binary_str = self.binary_input_text.get("1.0", tk.END).strip()
                
                if not binary_str:
                    raise ValueError("二进制数据为空")
                
                binary_str = binary_str.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
                
                if not all(c in '01' for c in binary_str):
                    raise ValueError("输入数据包含非法字符，仅允许0和1")
                
                # 使用decode模块将二进制字符串转换为字节
                self.decrypted_bytes = decode.binary_to_bytes(binary_str)
                
                # 写入输出文件（使用decode模块的工具函数）
                decode.bytes_to_file(self.decrypted_bytes, self.decrypt_output_path)
                
                # 更新统计信息
                total_bits = len(binary_str)
                self.total_bits = total_bits
                self.processed_bits = total_bits
                self.processing_start_time = time.time()
                self.after(0, lambda: self._update_processing_stats(total_bits, total_bits, is_decrypt=True))
                
                try:
                    self.decrypted_text = self.decrypted_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        self.decrypted_text = self.decrypted_bytes.decode('latin-1')
                    except Exception:
                        self.decrypted_text = "[无法解码为文本]"
        
            self.after(0, self._on_decryption_complete)
            
        except Exception as e:
            self.after(0, lambda: self._on_decryption_error(str(e)))

    def _on_decryption_complete(self):
        """解密完成后的UI更新方法"""
        self.is_processing = False
        self.progress_var.set(100)
        
        preview_data = self.decrypted_text if self.decrypted_text else "(二进制数据)"
        
        self.decrypt_preview_text.config(state='normal')
        self.decrypt_preview_text.delete(1.0, tk.END)
        preview_display = preview_data[:200] if len(preview_data) > 200 else preview_data
        self.decrypt_preview_text.insert(tk.END, preview_display)
        self.decrypt_preview_text.config(state='disabled')
        
        # 显示输出文件路径
        if hasattr(self, 'decrypt_output_path') and self.decrypt_output_path:
            self.decrypt_status_label.config(
                text=f"✓ 解密完成 | 文件已保存至: {self.decrypt_output_path}",
                foreground='green'
            )
        else:
            self.decrypt_status_label.config(text=f"解密完成 | 数据大小: {len(self.decrypted_bytes or b''):,} 字节")
        
        # 更新最终统计信息
        final_total = self.total_bits
        self._update_processing_stats(final_total, final_total, is_decrypt=True)

        # 新逻辑：通过 validate_decrypt_input() 恢复复制按钮和导出按钮状态
        self.validate_decrypt_input()

    def _on_decryption_error(self, error_msg):
        """解密出错时的错误处理方法"""
        self.is_processing = False
        self.progress_var.set(0)
        self.decrypt_status_label.config(text=f"错误: {error_msg}", foreground='red')
        messagebox.showerror("解密错误", error_msg)
        
        # 重置统计信息
        self._reset_processing_stats(is_decrypt=True)

        # 新逻辑：通过 validate_decrypt_input() 恢复按钮状态（输入仍然有效时启用）
        self.validate_decrypt_input()


# ===== 程序入口 =====
if __name__ == "__main__":
    """
    程序主入口点
    当直接运行此脚本时（而非作为模块导入）执行以下代码：
    1. 创建应用程序实例
    2. 启动主事件循环（保持窗口显示并响应用户操作）
    """
    # 创建Base2Encryptor应用实例
    app = Base2Encryptor()
    
    # 进入tkinter主事件循环
    # mainloop()是一个无限循环，持续处理用户交互事件
    # 直到窗口关闭才会返回
    app.mainloop()
