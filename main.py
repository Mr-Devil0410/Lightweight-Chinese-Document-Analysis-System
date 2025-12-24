import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import json
import time
import threading
import re
from nlp_core import analyze_content  # 导入NLP核心分析函数

class DocumentAnalyzerApp:
    def __init__(self, root):
        self.root = root
        # 窗口标题：按要求填入学号+姓名
        self.root.title("文本分析工具ver1.0 - 作者:202312033001-陈一翀")
        self.root.geometry("1100x850")  # 固定窗口大小，符合样板
        self.current_dir = ""  # 当前选中的examples目录
        self.file_list = []  # examples下的JSONL文件列表
        self.current_file_idx = -1  # 当前选中文件索引
        self.current_doc = ""  # 当前文件的原文（Document字段）
        self.setup_ui()  # 初始化界面

    def setup_ui(self):
        # 顶部工具栏：选择目录+路径显示
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill=tk.X, padx=10)
        tk.Button(top_frame, text="选择目录", command=self.select_dir).pack(side=tk.LEFT)
        self.path_label = tk.Label(top_frame, text="未选择目录...", fg="grey", padx=10)
        self.path_label.pack(side=tk.LEFT)

        # 中间主体：文件列表+分析结果
        main_body = tk.Frame(self.root)
        main_body.pack(fill=tk.BOTH, expand=True, padx=10)

        # 左侧文件列表（带滚动条）
        left_frame = tk.Frame(main_body)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        tk.Label(left_frame, text="文件列表").pack(anchor="w")
        self.file_listbox = tk.Listbox(left_frame, width=25)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        # 滚动条
        scrollbar = tk.Scrollbar(left_frame, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # 右侧分析结果展示（按样板布局）
        right_frame = tk.Frame(main_body)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.fields = {}  # 存储分析结果控件

        # 分析结果字段配置（标签文本、字段名、控件高度）
        field_configs = [
            ("题目:", "Title", 1),
            ("类标:", "ClassLabel", 1),
            ("关键词|高频词:", "KeyWord_HFWord", 1),
            ("实体:", "NamedEntity", 1),
            ("摘要:", "Abstract", 6)
        ]

        # 生成每个字段的UI控件
        for label_text, key, height in field_configs:
            row = tk.Frame(right_frame, pady=3)
            row.pack(fill=tk.X)
            tk.Label(row, text=label_text, width=12, anchor="e").pack(side=tk.LEFT)
            if height == 1:
                widget = tk.Entry(row)
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            else:
                widget = tk.Text(row, height=height, font=("微软雅黑", 10))
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            self.fields[key] = widget

        # 中间控制按钮（上一篇/下一篇/保存/退出）
        btn_frame = tk.Frame(right_frame, pady=15)
        btn_frame.pack(fill=tk.X)
        btn_container = tk.Frame(btn_frame)
        btn_container.pack(expand=True)
        tk.Button(btn_container, text="上一篇", width=12, command=self.prev_file).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_container, text="下一篇", width=12, command=self.next_file).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_container, text="保存修改", width=12, bg="#e1f5fe", command=self.save_modify).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_container, text="退出", width=12, bg="#ffebee", command=self.root.quit).pack(side=tk.LEFT, padx=10)

        # 底部原文展示区（标注Document字段）
        tk.Label(right_frame, text="原文（Document）:", anchor="w").pack(fill=tk.X)
        self.raw_text = scrolledtext.ScrolledText(right_frame, height=12, bg="#f5f5f5", font=("微软雅黑", 9))
        self.raw_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # 最底部批量分析按钮
        bottom_bar = tk.Frame(self.root, pady=10, bg="#f0f0f0")
        bottom_bar.pack(fill=tk.X)
        tk.Button(bottom_bar, text="开始分析 (全目录自动处理并保存)",
                  command=self.batch_analyze, bg="#bbdefb", height=2).pack(padx=20)

    # 核心：结果保存函数（严格遵循附录1格式）
    def result_append(self, file, d_mark, filename, title, key_hf, class_label, entity, abstract, document):
        """
        按附录1规范写入结果：
        - 所有字段值为数组类型
        - 追加保存JSONL格式
        - 字段：TimeStamp、D_Mark、FileName、Title、KeyWord_HFWord、ClassLabel、NamedEntity、Abstract、Document
        """
        result = {}
        timestamp = time.time()
        result["TimeStamp"] = [str(timestamp)]
        result["D_Mark"] = [d_mark]  # A=自动分析，M=人工修改
        result["FileName"] = [filename]
        result["Title"] = [title]
        result["KeyWord_HFWord"] = [key_hf]
        result["ClassLabel"] = [class_label]
        result["NamedEntity"] = [entity]
        result["Abstract"] = [abstract]
        result["Document"] = [document]  # 替换原Content字段
        # 转换为JSON字符串（不转义中文），追加换行
        file.write(json.dumps(result, ensure_ascii=False) + "\n")

    # 选择目录（强制要求examples目录）
    def select_dir(self):
        path = filedialog.askdirectory()
        if path:
            if os.path.basename(path) != "examples":
                messagebox.showerror("错误", "请选择名为'examples'的目录！\n作业要求分析该目录下的252个JSONL文件。")
                return
            self.current_dir = path
            self.path_label.config(text=path)
            # 读取JSONL文件，自然排序（解决数字文件名乱序）
            self.file_list = [f for f in os.listdir(path) if f.endswith(".jsonl")]
            self.file_list.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', x)])
            # 更新文件列表框
            self.file_listbox.delete(0, tk.END)
            for f in self.file_list:
                self.file_listbox.insert(tk.END, f)

    # 选择文件并显示分析结果
    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        self.current_file_idx = selection[0]
        filename = self.file_list[self.current_file_idx]
        try:
            # 读取JSONL文件第一行（按作业示例逻辑）
            with open(os.path.join(self.current_dir, filename), "r", encoding="utf-8") as f:
                json_line = f.readline().strip()
                res = analyze_content(json_line)
                if res:
                    self.current_doc = res.get("Document", "")
                    self.fill_fields(res)
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败：{str(e)}")

    # 填充分析结果到界面控件
    def fill_fields(self, data):
        for key, widget in self.fields.items():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, data.get(key, ""))
            else:
                widget.delete("1.0", tk.END)
                widget.insert("1.0", data.get(key, ""))
        # 填充原文
        self.raw_text.delete("1.0", tk.END)
        self.raw_text.insert("1.0", self.current_doc)

    # 保存人工修改结果（D_Mark=M）
    def save_modify(self):
        if self.current_file_idx == -1:
            messagebox.showwarning("提示", "请先选择要保存的文件！")
            return
        # 创建result目录（若不存在）
        res_dir = os.path.join(self.current_dir, "result")
        if not os.path.exists(res_dir):
            os.makedirs(res_dir)
        save_path = os.path.join(res_dir, "result_log.jsonl")
        # 读取界面修改后的内容
        filename = self.file_list[self.current_file_idx]
        title = self.fields["Title"].get().strip()
        key_hf = self.fields["KeyWord_HFWord"].get().strip()
        class_label = self.fields["ClassLabel"].get().strip()
        entity = self.fields["NamedEntity"].get().strip()
        abstract = self.fields["Abstract"].get("1.0", tk.END).strip()
        document = self.current_doc  # 原文不允许修改
        # 追加保存（D_Mark=M）
        with open(save_path, "a", encoding="utf-8") as f:
            self.result_append(f, "M", filename, title, key_hf, class_label, entity, abstract, document)
        messagebox.showinfo("成功", "人工修改结果已保存（D_Mark=M）\n文件路径：" + save_path)

    # 批量自动分析所有文件（D_Mark=A）
    def batch_analyze(self):
        if not self.file_list:
            messagebox.showwarning("提示", "请先选择包含JSONL文件的examples目录！")
            return
        res_dir = os.path.join(self.current_dir, "result")
        if not os.path.exists(res_dir):
            os.makedirs(res_dir)
        save_path = os.path.join(res_dir, "result_log.jsonl")

        # 多线程执行，避免界面卡死
        def task():
            success_count = 0
            for fname in self.file_list:
                fpath = os.path.join(self.current_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f_in:
                        json_line = f_in.readline().strip()
                        if json_line:
                            res = analyze_content(json_line)
                            if res:
                                with open(save_path, "a", encoding="utf-8") as f_out:
                                    self.result_append(
                                        f_out, "A", fname,
                                        res["Title"], res["KeyWord_HFWord"],
                                        res["ClassLabel"], res["NamedEntity"],
                                        res["Abstract"], res["Document"]
                                    )
                                success_count += 1
                except Exception as e:
                    print(f"处理文件{fname}失败：{str(e)}")
                    continue
            # 分析完成提示
            messagebox.showinfo("批量分析完成",
                                f"处理结束！\n成功分析：{success_count}/{len(self.file_list)}个文件\n结果路径：{save_path}")

        threading.Thread(target=task).start()

    # 上一篇文件导航
    def prev_file(self):
        if self.current_file_idx > 0:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.current_file_idx - 1)
            self.file_listbox.see(self.current_file_idx - 1)
            self.on_file_select(None)

    # 下一篇文件导航
    def next_file(self):
        if self.current_file_idx < len(self.file_list) - 1:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.current_file_idx + 1)
            self.file_listbox.see(self.current_file_idx + 1)
            self.on_file_select(None)


if __name__ == "__main__":
    root = tk.Tk()
    app = DocumentAnalyzerApp(root)
    root.mainloop()