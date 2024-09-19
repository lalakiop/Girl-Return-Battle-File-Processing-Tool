import tkinter as tk
from tkinter import filedialog
import os
import sys
import shutil
import re
import configparser
import subprocess
import ctypes

def find_and_remove_obfuscation(input_file_path, header_signatures):
    """
    查找并去除混淆
    :param input_file_path: 输入文件路径
    :param header_signatures: 特定标识符列表
    """
    log_message(input_file_path)
    with open(input_file_path, 'rb') as input_file:
        input_data = input_file.read()
        
        # 检查文件是否以特定标识符开头
        for header_signature in header_signatures:
            if input_data.startswith(header_signature):
                log_message("无需去混淆")
                return

        # 检查前150个字符是否包含特定标识符
        for header_signature in header_signatures:
            if header_signature in input_data[:150]:
                # 提取文件中 "CAB-" 后面的 33 位字符
                cab_matches = re.findall(b'CAB-(.{33})', input_data)
                log_message(cab_matches)
                
                if cab_matches:
                    cab_char = cab_matches[0].decode('utf-8',errors='ignore')
                    
                    # 检查是否已经记录过该字符
                    existing_chars = set()
                    if os.path.exists("mate.ini"):
                        with open("mate.ini", 'r', encoding='utf-8') as mate_file:
                            for line in mate_file:
                                # 提取已记录的字符部分
                                existing_cab_char = line.strip().split('-')[0]
                                existing_chars.add(existing_cab_char)

                    if cab_char in existing_chars:
                        log_message("数据已存在")
                        # 备份文件到当前目录下，然后删除文件中特定标识符前面的字符，不包括标识符本身
                        #backup_file_path = input_file_path + ".backup"
                        #shutil.copyfile(input_file_path, backup_file_path)
                        with open(input_file_path, 'wb') as original_file:
                            original_file.write(input_data[input_data.find(header_signature):])
                        log_message("已完成去混淆")
                    else:
                        # 提取文件名
                        file_name = os.path.basename(input_file_path)
                        # 提取特定标识符前面的字符（以二进制形式表示）
                        deleted_chars = input_data[:input_data.find(header_signature)].hex().upper()
                        # 存储信息到 mate.ini
                        with open("mate.ini", 'a', encoding='utf-8') as mate_file:
                            mate_file.write(f"{cab_char}-{file_name}-{deleted_chars}-{input_file_path}\n")
                            log_message("数据已记录："f"{cab_char}-{file_name}-{deleted_chars}-{input_file_path}")
                        # 备份文件到当前目录下，然后删除文件中特定标识符前面的字符，不包括标识符本身
                        #backup_file_path = input_file_path + ".backup"
                        #shutil.copyfile(input_file_path, backup_file_path)
                        with open(input_file_path, 'wb') as original_file:
                            original_file.write(input_data[input_data.find(header_signature):])
                        log_message("已完成去混淆")
                    return

        # 如果没有匹配的标识符，输出 "不是标准的 Unity 文件"
        log_message("不是标准的 Unity 文件")

def restore_obfuscation(input_file_path, header_signatures):
    """
    还原混淆
    :param input_file_path: 输入文件路径
    :param header_signatures: 特定标识符列表
    """
    with open(input_file_path, 'rb') as input_file:
        input_data = input_file.read()

        # 检查文件是否以特定标识符开头
        for header_signature in header_signatures:
            if input_data.startswith(header_signature):
                # 提取文件中 "CAB-" 后面的 33 位字符
                cab_matches = re.findall(b'CAB-(.{33})', input_data)

                if cab_matches:
                    cab_char = cab_matches[0].decode('utf-8',errors='ignore')

                    # 检查是否已经记录过该字符
                    existing_chars = set()
                    rename_filename = ""
                    # 提取mate.ini中的相同"CAB-"后面字符的文件的被删除的二进制数据
                    deleted_chars_data = ""
                    mate_file_path = "mate.ini"
                    if os.path.exists(mate_file_path):
                        with open(mate_file_path, 'r', encoding='utf-8') as mate_file:
                            for line in mate_file:
                                parts = line.strip().split('-')
                                existing_cab_char = parts[0]
                                existing_chars.add(existing_cab_char)
                                # 如果存在相同的字符
                                if cab_char == existing_cab_char:
                                    # 提取文件名
                                    rename_filename = parts[1]
                                    # 提取被删除的二进制数据
                                    deleted_chars_data = parts[2]

                    if cab_char in existing_chars:
                        if rename_filename:
                            # 检查文件名是否与mate.ini中的一致
                            if os.path.basename(input_file_path) == rename_filename:
                                # 添加被删除的二进制数据到文件的特定标识符之前
                                with open(input_file_path, 'rb+') as renamed_file:
                                    content = renamed_file.read()
                                    renamed_file.seek(0)
                                    renamed_file.write(bytes.fromhex(deleted_chars_data) + content)
                                log_message(f"已完成还原混淆")
                            else:
                                # 复制选中的文件并命名为mate.ini中"CAB-"后面字符的文件名称
                                new_file_path = os.path.join(os.path.dirname(input_file_path), rename_filename)
                                shutil.copyfile(input_file_path, new_file_path)
                                # 添加被删除的二进制数据到文件的特定标识符之前
                                with open(new_file_path, 'rb+') as renamed_file:
                                    content = renamed_file.read()
                                    renamed_file.seek(0)
                                    renamed_file.write(bytes.fromhex(deleted_chars_data) + content)
                                    log_message(f"已完成还原混淆和文件名称")
                                
                                # 删除原文件
                                input_file.close()
                                os.remove(input_file_path)
                        else:
                            log_message("文件名称未找到")
                    else:
                        log_message("数据库无记录")
                else:
                    log_message("文件中未找到 CAB- 后面的 33 位字符")
                return

        # 如果文件不以特定标识符开头，输出 "无需还原混淆"
        log_message("无需还原混淆")

def browse_and_remove_obfuscation():
    """
    浏览并去除混淆
    """
    # 根据复选框状态选择文件对话框模式
    if subfolders_var.get():
        file_paths = filedialog.askopenfilenames(filetypes=[])
    else:
        file_paths = filedialog.askopenfilename(filetypes=[])
    
    if file_paths:
        if isinstance(file_paths, tuple):
            for file_path in file_paths:
                process_remove_obfuscation(file_path)
                open_mate_ini()
        else:
            process_remove_obfuscation(file_paths)
            open_mate_ini()

def process_remove_obfuscation(file_path):
    """
    处理去除混淆
    :param file_path: 文件路径
    """
    if getattr(sys, 'frozen', False):
        folder_path = os.path.dirname(sys.executable)
    else:
        folder_path = os.path.dirname(os.path.abspath(__file__))
        
    ini_file_path = os.path.join(folder_path, 'head.ini')
    
    if not os.path.exists(ini_file_path):
        # 创建并写入内容
        with open(ini_file_path, 'w', encoding='utf-8') as file:
            file.write('55 6E 69 74 79 46 53 00 00 00 00 07 35 2E 78 2E 78 00 32 30 31 39 2E 34 2E 32 35 66 31\n55 6E 69 74 79 46 53 00 00 00 00 07 35 2E 78 2E 78 00 32 30 31 39 2E 34 2E 32 35 11 31\n55 6E 69 74 79 46 53 00 00 00 00 06 35 2E 78 2E 78 00 32 30 31 38 2E 34 2E 33 31 66 31')
    with open("head.ini", 'r', encoding='utf-8') as config_file:
        header_signatures = [bytes.fromhex(line.strip()) for line in config_file if line.strip()]
    find_and_remove_obfuscation(file_path, header_signatures)

def browse_and_restore_obfuscation():
    """
    浏览并还原混淆
    """
    # 根据复选框状态选择文件对话框模式
    if subfolders_var.get():
        file_paths = filedialog.askopenfilenames(filetypes=[])
    else:
        file_paths = filedialog.askopenfilename(filetypes=[])
    
    if file_paths:
        if isinstance(file_paths, tuple):
            for file_path in file_paths:
                process_restore_obfuscation(file_path)
        else:
            process_restore_obfuscation(file_paths)

def process_restore_obfuscation(file_path):
    """
    处理还原混淆
    :param file_path: 文件路径
    """
    if getattr(sys, 'frozen', False):
        folder_path = os.path.dirname(sys.executable)
    else:
        folder_path = os.path.dirname(os.path.abspath(__file__))
        
    ini_file_path = os.path.join(folder_path, 'head.ini')
    
    if not os.path.exists(ini_file_path):
        # 创建并写入内容
        with open(ini_file_path, 'w', encoding='utf-8') as file:
            file.write('55 6E 69 74 79 46 53 00 00 00 00 07 35 2E 78 2E 78 00 32 30 31 39 2E 34 2E 32 35 66 31\n55 6E 69 74 79 46 53 00 00 00 00 07 35 2E 78 2E 78 00 32 30 31 39 2E 34 2E 32 35 11 31\n55 6E 69 74 79 46 53 00 00 00 00 06 35 2E 78 2E 78 00 32 30 31 38 2E 34 2E 33 31 66 31')
    
    with open("head.ini", 'r', encoding='utf-8') as config_file:
        header_signatures = [bytes.fromhex(line.strip()) for line in config_file if line.strip()]
    restore_obfuscation(file_path, header_signatures)

def search_files(event):
    """
    搜索文件
    :param event: 事件对象
    """
    query = search_var.get().strip().lower()
    file_listbox.delete(0, tk.END)
    with open("mate.ini", "r", encoding="utf-8") as file:
        for line in file:
            match = re.search(r'-(.*?)-', line)
            if match:
                content_between_hyphens = match.group(1)
                if query in content_between_hyphens.lower():
                    file_listbox.insert(tk.END, content_between_hyphens)

def open_file_location():
    """
    打开文件所在位置
    """
    selected_index = file_listbox.curselection()
    if selected_index:
        selected_file = file_listbox.get(selected_index)
        with open("mate.ini", "r", encoding="utf-8") as file:
            for line in file:
                if selected_file in line:
                    file_path = line.strip().split('-')[-1]
                    folder_path = replace_slashes(file_path)
                    # 打开文件所在位置
                    subprocess.Popen(['explorer', '/select,', folder_path])

def replace_slashes(text):
    """
    替换路径中的斜杠
    :param text: 路径文本
    :return: 替换斜杠后的文本
    """
    return text.replace('/', '\\')

def show_context_menu(event):
    """
    显示右键菜单
    :param event: 事件对象
    """
    try:
        file_listbox.selection_clear(0, tk.END)
        file_listbox.selection_set(file_listbox.nearest(event.y))
        context_menu.post(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()

def open_mate_ini():

    """
    打开 "mate.ini" 文件并更新列表框内容
    """
    file_listbox.delete(0, tk.END)
    if getattr(sys, 'frozen', False):
        folder_path = os.path.dirname(sys.executable)
    else:
        folder_path = os.path.dirname(os.path.abspath(__file__))
        
    ini_file_path = os.path.join(folder_path, 'mate.ini')
    
    if not os.path.exists(ini_file_path):
        # 创建并写入内容
        with open(ini_file_path, 'w', encoding='utf-8') as file:
            file.write('[MergedFiles]')
    
    with open("mate.ini", "r", encoding="utf-8") as file:
        for line in file:
            match = re.search(r'-(.*?)-', line)
            if match:
                content_between_hyphens = match.group(1)
                file_listbox.insert(0, content_between_hyphens)


def log_message(message):
    if isinstance(message, list):
        message = [m.decode('utf-8') if isinstance(m, bytes) else str(m) for m in message]
        log_text.insert(tk.END, ''.join(message) + '\n')
    else:
        log_text.insert(tk.END, message + '\n')
    log_text.see(tk.END)




# 设置DPI感知
ctypes.windll.shcore.SetProcessDpiAwareness(2)
# 创建主窗口
window = tk.Tk()
#window.tk.call('tk', 'scaling',1.2)  # 设置缩放因子为2.0，您可以根据实际需要调整


window.title("Unity文件去混淆工具")
window.geometry("5000x300")
window.minsize(500, 300)  # 设置最小尺寸

# 设置窗口居中
window_width = 1080
window_height = 400
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x_position = (screen_width - window_width) // 2
y_position = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

# 创建标签
label = tk.Label(window, text="请选择要执行的操作：")
label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

# 创建去混淆按钮
button1 = tk.Button(window, text="选择文件去混淆", command=browse_and_remove_obfuscation)
button1.grid(row=1, column=0, padx=10, pady=10)

# 创建还原混淆按钮
button2 = tk.Button(window, text="选择文件还原混淆", command=browse_and_restore_obfuscation)
button2.grid(row=2, column=0, padx=10, pady=10)

# 创建搜索框
search_var = tk.StringVar()
search_entry = tk.Entry(window, textvariable=search_var)
search_entry.grid(row=0, column=2, padx=10, pady=10, sticky='ew')
# 绑定键释放事件
search_entry.bind("<KeyRelease>", search_files)  

# 创建已处理的文件标签
label = tk.Label(window, text="已处理的文件：")
label.grid(row=1, column=2, padx=10, pady=10)

# 创建滚动条
scrollbar = tk.Scrollbar(window)
scrollbar.grid(row=2, column=3, rowspan=6, sticky='ns')

# 创建列表框
file_listbox = tk.Listbox(window, width=40, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
file_listbox.grid(row=2, column=2, rowspan=6, padx=10, pady=10, sticky='nsew')
scrollbar.config(command=file_listbox.yview)


# 创建日志显示控件
log_label = tk.Label(window, text="日志：")
log_label.grid(row=0, column=4, padx=10, pady=10, sticky='w')

log_text = tk.Text(window, wrap=tk.WORD, state=tk.NORMAL, height=30, width=50)
log_text.grid(row=1, column=4, rowspan=5, padx=10, pady=10, sticky='nsew')

log_scrollbar = tk.Scrollbar(window, orient=tk.VERTICAL, command=log_text.yview)
log_scrollbar.grid(row=1, column=5, rowspan=5, sticky='ns')
log_text.config(yscrollcommand=log_scrollbar.set)

# 读取文件内容
open_mate_ini()

# 配置行列权重
window.grid_rowconfigure(0, weight=0)
window.grid_rowconfigure(1, weight=1)
window.grid_rowconfigure(2, weight=1)
window.grid_rowconfigure(3, weight=1)
window.grid_rowconfigure(4, weight=1)
window.grid_rowconfigure(5, weight=1)
window.grid_columnconfigure(0, weight=0)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)
window.grid_columnconfigure(4, weight=1)
window.grid_columnconfigure(5, weight=1)

# 创建并放置框架
frame = tk.Frame(window)
frame.grid(row=3, column=0, padx=10, pady=10)

# 创建并放置复选框
subfolders_var = tk.BooleanVar(value=True)
subfolders_check = tk.Checkbutton(frame, text="多选", variable=subfolders_var)
subfolders_check.grid(row=0, column=0, padx=10, pady=10)

# 创建右键菜单
context_menu = tk.Menu(window, tearoff=0)
context_menu.add_command(label="打开文件所在位置", command=open_file_location)

# 绑定右键事件到列表框
file_listbox.bind("<Button-3>", show_context_menu)

# 启动主事件循环
window.mainloop()