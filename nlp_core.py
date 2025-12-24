import os
import sys
import json
import jieba
import jieba.posseg as pseg
import jieba.analyse
from collections import Counter
import joblib
from sklearn.exceptions import NotFittedError
import tkinter.messagebox


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(path): return path

    exe_dir = os.path.dirname(sys.executable)
    path = os.path.join(exe_dir, relative_path)
    if os.path.exists(path): return path

    return os.path.join(os.path.abspath("."), relative_path)


MODEL_PATH = get_resource_path("model/text_classifier_5cat.pkl")
STOPWORDS_PATH = get_resource_path("stopwords.txt")

classifier = None


def load_stopwords():
    stopwords = set()
    if os.path.exists(STOPWORDS_PATH):
        with open(STOPWORDS_PATH, "r", encoding="utf-8") as f:
            stopwords = {line.strip() for line in f if line.strip()}
    return stopwords


def load_trained_classifier():
    global classifier
    if classifier is None:
        if os.path.exists(MODEL_PATH):
            try:
                classifier = joblib.load(MODEL_PATH)
            except Exception as e:
                tkinter.messagebox.showerror("错误", f"模型加载失败: {str(e)}")
                classifier = None
        else:
            tkinter.messagebox.showerror("错误", f"找不到模型文件: {MODEL_PATH}")
            classifier = None
    return classifier


def analyze_content(json_line):
    try:
        data = json.loads(json_line)
        title = data.get("title", "无标题")
        document = data.get("content", "")
        full_text = title + " " + document
        stopwords = load_stopwords()
        valid_words = [w for w in jieba.lcut(full_text) if w not in stopwords and len(w) > 1 and w.strip()]

        keywords = []
        if valid_words:
            clf = load_trained_classifier()
            if clf:
                try:
                    tfidf_vectorizer = clf.named_steps["tfidf"]
                    tfidf_matrix = tfidf_vectorizer.transform([" ".join(valid_words)])
                    feature_names = tfidf_vectorizer.get_feature_names_out()
                    word_weights = sorted(zip(feature_names, tfidf_matrix.toarray()[0]), key=lambda x: x[1],
                                          reverse=True)
                    keywords = [word for word, _ in word_weights[:5]]
                except NotFittedError:
                    keywords = jieba.analyse.extract_tags(full_text, topK=5)
            else:
                keywords = jieba.analyse.extract_tags(full_text, topK=5)

        hf_words = [word for word, count in Counter(valid_words).most_common(5)] if valid_words else []
        key_hf_combined = f"{','.join(keywords)}|{','.join(hf_words)}"

        entities = []
        for word, pos in pseg.cut(full_text):
            if pos in ["nr", "ns", "nt"] and len(word) > 1 and word not in stopwords:
                entities.append(word)
        entities = list(set(entities))[:5]
        entity_str = ",".join(entities) if entities else "无"

        class_label = "生活"
        clf = load_trained_classifier()
        if clf and valid_words:
            try:
                class_label = clf.predict([" ".join(valid_words)])[0]
            except Exception:
                class_label = "生活"

        abstract = document[:200] + ("..." if len(document) > 200 else "")

        return {
            "Title": title,
            "ClassLabel": class_label,
            "KeyWord_HFWord": key_hf_combined,
            "NamedEntity": entity_str,
            "Abstract": abstract,
            "Document": document
        }
    except Exception:
        return None