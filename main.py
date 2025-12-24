import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import json
import time
import threading
import re
from nlp_core import analyze_content


class DocumentAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文本分析工具ver1.0 - 作者:202312033001-陈一翀")
        self.root.geometry("1100x850")
        self.current_dir = ""
        self.file_list = []
        self.current_file_idx = -1
        self.setup_ui()

    def setup_ui(self):
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill=tk.X, padx=10)
        tk.Button(top_frame, text="选择目录", command=self.select_dir).pack(side=tk.LEFT)
        self.path_label = tk.Label(top_frame, text="未选择目录...", fg="grey", padx=10)
        self.path_label.pack(side=tk.LEFT)

        main_body = tk.Frame(self.root)
        main_body.pack(fill=tk.BOTH, expand=True, padx=10)

        left_panel = tk.Frame(main_body, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH)
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="待分析文件列表", font=("微软雅黑", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        list_frame = tk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.file_listbox = tk.Listbox(list_frame, font=("微软雅黑", 9))
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        scrollbar = tk.Scrollbar(list_frame, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        bottom_left_frame = tk.Frame(left_panel)
        bottom_left_frame.pack(fill=tk.X, pady=(10, 0))
        self.batch_btn = tk.Button(bottom_left_frame, text="开始批量分析",
                                   command=self.batch_analyze, bg="#bbdefb", height=2, font=("微软雅黑", 10))
        self.batch_btn.pack(fill=tk.X, padx=2)

        right_panel = tk.Frame(main_body)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self.fields = {}

        field_configs = [
            ("题目:", "Title", 1),
            ("类标:", "ClassLabel", 1),
            ("关键词|高频词:", "KeyWord_HFWord", 1),
            ("实体:", "NamedEntity", 1),
            ("摘要:", "Abstract", 6)
        ]

        for label_text, key, height in field_configs:
            row = tk.Frame(right_panel, pady=3)
            row.pack(fill=tk.X)
            tk.Label(row, text=label_text, width=12, anchor="e").pack(side=tk.LEFT)
            if height == 1:
                widget = tk.Entry(row)
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            else:
                widget = tk.Text(row, height=height, font=("微软雅黑", 10))
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            self.fields[key] = widget

        btn_frame = tk.Frame(right_panel, pady=15)
        btn_frame.pack(fill=tk.X)
        btn_container = tk.Frame(btn_frame)
        btn_container.pack(expand=True)
        tk.Button(btn_container, text="上一篇", width=12, command=self.prev_file).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_container, text="下一篇", width=12, command=self.next_file).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_container, text="保存修改", width=12, bg="#e1f5fe", command=self.save_modify).pack(side=tk.LEFT,
                                                                                                         padx=10)
        tk.Button(btn_container, text="退出", width=12, bg="#ffebee", command=self.root.quit).pack(side=tk.LEFT,
                                                                                                   padx=10)

        tk.Label(right_panel, text="原文（Document）:", anchor="w").pack(fill=tk.X)
        self.raw_text = scrolledtext.ScrolledText(right_panel, height=12, bg="#f5f5f5", font=("微软雅黑", 9))
        self.raw_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def result_append(self, file, D_Mark, FileName, Title, KeyWord_HFWord, ClassLabel, NamedEntity, Abstract, Document):
        one_result = {}
        timestamp = time.time()
        one_result["TimeStamp"] = [str(timestamp)]
        one_result["D_Mark"] = [D_Mark]
        one_result["FileName"] = [FileName]
        one_result["Title"] = [Title]
        one_result["KeyWord_HFWord"] = [KeyWord_HFWord]
        one_result["ClassLabel"] = [ClassLabel]
        one_result["NamedEntity"] = [NamedEntity]
        one_result["Abstract"] = [Abstract]
        one_result["Document"] = [Document]
        result_string = json.dumps(one_result, ensure_ascii=False) + "\n"
        file.writelines(result_string)

    def select_dir(self):
        path = filedialog.askdirectory()
        if path:
            if os.path.basename(path) != "examples":
                messagebox.showerror("错误", "请选择名为'examples'的目录！")
                return
            self.current_dir = path
            self.path_label.config(text=path)
            self.file_list = [f for f in os.listdir(path) if f.endswith(".jsonl")]
            self.file_list.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', x)])
            self.file_listbox.delete(0, tk.END)
            for f in self.file_list:
                self.file_listbox.insert(tk.END, f)

    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        self.current_file_idx = selection[0]
        filename = self.file_list[self.current_file_idx]
        try:
            with open(os.path.join(self.current_dir, filename), "r", encoding="utf-8") as f:
                json_line = f.readline().strip()
                data = json.loads(json_line)
                title = data.get("title") or data.get("Title") or ""
                document = data.get("content") or data.get("Content") or data.get("Document") or ""
                if document:
                    res = analyze_content(title, document)
                    if res:
                        self.fill_fields(res, document)
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败：{str(e)}")

    def fill_fields(self, data, original_doc):
        for key, widget in self.fields.items():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, data.get(key, ""))
            else:
                widget.delete("1.0", tk.END)
                widget.insert("1.0", data.get(key, ""))
        self.raw_text.delete("1.0", tk.END)
        self.raw_text.insert("1.0", original_doc)

    def save_modify(self):
        if self.current_file_idx == -1:
            messagebox.showwarning("提示", "请先选择要保存的文件！")
            return
        save_path = os.path.join(self.current_dir, "result", "result_log.jsonl")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        filename = self.file_list[self.current_file_idx]
        title = self.fields["Title"].get().strip()
        key_hf = self.fields["KeyWord_HFWord"].get().strip()
        class_label = self.fields["ClassLabel"].get().strip()
        entity = self.fields["NamedEntity"].get().strip()
        abstract = self.fields["Abstract"].get("1.0", tk.END).strip()
        document = self.raw_text.get("1.0", tk.END).strip()
        with open(save_path, "a", encoding="utf-8") as f:
            self.result_append(f, "M", filename, title, key_hf, class_label, entity, abstract, document)
        messagebox.showinfo("成功", "人工修改结果已保存")

    def batch_analyze(self):
        if not self.file_list:
            messagebox.showwarning("提示", "请先选择包含JSONL文件的examples目录！")
            return
        save_path = os.path.join(self.current_dir, "result", "result_log.jsonl")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        self.batch_btn.config(state=tk.DISABLED, text="分析中...")

        def task():
            success_count = 0
            for fname in self.file_list:
                try:
                    with open(os.path.join(self.current_dir, fname), "r", encoding="utf-8") as f_in:
                        json_line = f_in.readline().strip()
                        data = json.loads(json_line)
                        title = data.get("title") or data.get("Title") or ""
                        document = data.get("content") or data.get("Content") or data.get("Document") or ""
                        if document:
                            res = analyze_content(title, document)
                            if res:
                                with open(save_path, "a", encoding="utf-8") as f_out:
                                    self.result_append(f_out, "A", fname, res["Title"], res["KeyWord_HFWord"],
                                                       res["ClassLabel"], res["NamedEntity"], res["Abstract"], document)
                                success_count += 1
                except Exception as e:
                    continue
            self.root.after(0, lambda: [
                messagebox.showinfo("批量分析完成", f"处理结束！\n成功分析：{success_count}/{len(self.file_list)}个文件"),
                self.batch_btn.config(state=tk.NORMAL, text="开始批量分析")
            ])

        threading.Thread(target=task).start()

    def prev_file(self):
        if self.current_file_idx > 0:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.current_file_idx - 1)
            self.file_listbox.see(self.current_file_idx - 1)
            self.on_file_select(None)

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