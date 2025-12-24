# 轻量级中文文档分析工具

---

## 项目简介

一个基于 Python 的离线中文文档分析工具，能够自动提取文本的关键词、高频词、命名实体、摘要和分类标签，并支持人工修改与批量处理。系统完全离线运行，程序体积小于 100MB，符合轻量级要求。

---

## 运行环境

- **Python 版本**：Python 3.12 或更高版本  
- **操作系统**：Windows 10/11, macOS, Linux  
- **内存**：至少 2GB RAM  
- **存储**：100MB 可用空间  

---

## 安装步骤

### 1. 克隆/下载项目  
将项目文件下载到本地目录。  

### 2. 安装 Python 依赖包  
在终端中运行以下命令：
pip install -r requirements.txt

### 3. 数据与模型准备
本工具默认已包含运行所需的全部资源，**直接运行 `main.py` 即可使用**。请确保根目录下包含以下文件：
- `stopwords.txt` - 中文停用词表
- `health_corpus.txt` - 健康类补充语料
- `model/text_classifier_5cat.pkl` - **预训练分类模型（核心文件）**

> **注意**：
> 只有当你拥有 `THUCNews` 完整数据集目录并希望自行改进模型时，才需要运行 `python train_classifier.py`。
> **若本地没有该数据集，请勿运行训练脚本，直接使用自带的预训练模型即可。**

---

## 项目文件结构
项目根目录/
├── main.py              # 主程序入口（图形界面）
├── nlp_core.py          # NLP核心分析模块（分词、提取、分类调用）
├── train_classifier.py  # 分类器训练脚本（需 THUCNews 数据集）
├── requirements.txt     # 依赖包列表
├── stopwords.txt        # 停用词表
├── health_corpus.txt    # 健康类语料（用于弥补通用数据集不足）
├── DocumentAnalyzer.spec # PyInstaller 打包配置文件
├── model/
│   └── text_classifier_5cat.pkl  # 训练好的轻量化模型文件
└── examples/            # 待分析的示例数据目录
    └── result/          # 分析结果存放目录（自动生成）

---

## 操作流程
1. **选择目录**：点击"选择目录"按钮，选择包含 JSONL 文件的 `examples` 目录。
2. **浏览文件**：在左侧文件列表中选择任意文件。
3. **查看分析**：系统自动在右侧显示分析结果，包括：
   - 题目、类标（教育/健康/生活/娱乐/游戏）
   - 关键词|高频词（各取前5个）
   - 实体（人名/地名/机构名）
   - 摘要（前200字精简）
4. **人工修改**：可在右侧文本框中手动修正分析内容。
5. **保存修改**：点击"保存修改"按钮，结果将以 `D_Mark="M"` 标志追加保存。
6. **批量分析**：点击底部"开始分析"按钮，一键处理目录下所有 252 个文件。
7. **导航功能**：使用"上一篇"/"下一篇"按钮快速切换。

---

## 输出结果

- **保存路径**：`examples/result/result_log.jsonl`
- **格式**：JSONL 格式，每行一条记录，支持追加保存。
- **关键字段说明**：
  - `TimeStamp`：操作时间戳
  - `D_Mark`：**"A"** 为全自动分析，**"M"** 为人工修改确认
  - `ClassLabel`：严格限定在五大类别
  - `KeyWord_HFWord`：格式为 “关键词1,2...|高频词1,2...”



## 打包命令
# 彻底清理
Remove-Item -Recurse -Force build, dist, DocumentAnalyzer.spec -ErrorAction SilentlyContinue

#使用隐藏导入命令
pyinstaller -F -w --name DocumentAnalyzer `
--hidden-import "sklearn.pipeline" `
--hidden-import "sklearn.preprocessing._label" `
--hidden-import "sklearn.utils._cython_blas" `
--hidden-import "sklearn.utils._typedefs" `
--hidden-import "sklearn.neighbors._partition_nodes" `
--hidden-import "sklearn.neighbors._quad_tree" `
--hidden-import "sklearn.tree._utils" `
--hidden-import "sklearn.feature_extraction.text" `
--hidden-import "sklearn.naive_bayes" `
main.py