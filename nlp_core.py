import os
import sys
import re
import jieba
import jieba.posseg as pseg
import jieba.analyse
from collections import Counter
import joblib


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


MODEL_PATH = get_resource_path("model/text_classifier_5cat.pkl")
STOPWORDS_PATH = get_resource_path("stopwords.txt")

classifier = None
stopwords_cache = None


def load_stopwords():
    global stopwords_cache
    if stopwords_cache is not None:
        return stopwords_cache
    if os.path.exists(STOPWORDS_PATH):
        with open(STOPWORDS_PATH, "r", encoding="utf-8") as f:
            stopwords_cache = {line.strip() for line in f if line.strip()}
            return stopwords_cache
    stopwords_cache = set()
    return stopwords_cache


def get_best_abstract(title, document, max_len=200):
    if not document: return ""

    clean_title = re.sub(r'[？?？\s]', '', title)
    clean_doc = re.sub(r'[\r\n\t]+', ' ', document)
    clean_doc = re.sub(r'\s+', ' ', clean_doc).strip()

    sentences = re.split(r'([。！？?！])', clean_doc)
    parts = []
    for i in range(0, len(sentences) - 1, 2):
        s = sentences[i].strip() + sentences[i + 1]
        if len(s) > 8: parts.append(s)

    if not parts: return clean_doc[:max_len]

    title_keywords = [w for w in jieba.lcut(clean_title) if len(w) > 1]
    answer_indicators = {'是', '因为', '由于', '建议', '方法', '做法', '原因', '通过', '可以', '导致'}
    noise_words = {'来源', '点击', '下载', '作者', '卖家', '转载'}

    scored_parts = []
    for idx, s in enumerate(parts[:15]):
        score = 0
        match_count = sum(1 for kw in title_keywords if kw in s)
        score += match_count * 3.5
        if any(ind in s for ind in answer_indicators): score += 4
        score += max(0, 5 - idx * 0.5)
        if any(noise in s for noise in noise_words): score -= 10
        scored_parts.append((s, score, idx))

    top_candidates = sorted(scored_parts, key=lambda x: x[1], reverse=True)[:3]
    top_candidates = sorted(top_candidates, key=lambda x: x[2])

    abstract = "".join([c[0] for c in top_candidates])

    if len(abstract) < 40 and parts:
        abstract = parts[0] + abstract

    if len(abstract) > max_len:
        last_punct = -1
        for punct in ['。', '！', '？', '!']:
            pos = abstract.rfind(punct, 0, max_len)
            if pos > last_punct: last_punct = pos
        if last_punct != -1:
            abstract = abstract[:last_punct + 1]
        else:
            abstract = abstract[:max_len]

    abstract = abstract.strip().rstrip('，,：:;；')
    if abstract and not abstract.endswith(('。', '！', '？')):
        abstract += "。"

    return abstract


def extract_keywords(text, stopwords):
    tfidf_tags = jieba.analyse.extract_tags(
        text,
        topK=10,
        withWeight=False,
        allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'vn', 'v')
    )
    return tfidf_tags


def extract_entities(text, stopwords):
    entities = []
    seen = set()
    for w, p in pseg.cut(text):
        if p in ('nr', 'ns', 'nt') and len(w) > 1 and w not in stopwords:
            if w not in seen:
                entities.append(w)
                seen.add(w)
        if len(entities) >= 5: break
    return entities


def analyze_content(title, document):
    stopwords = load_stopwords()
    full_text = title + " " + document

    keywords = extract_keywords(full_text, stopwords)[:5]

    words = [w for w in jieba.lcut(document) if len(w) > 1 and w not in stopwords]
    freq = Counter(words)
    hf_words = []
    for w, _ in freq.most_common(20):
        if w not in keywords:
            hf_words.append(w)
        if len(hf_words) >= 5: break

    key_hf = f"{','.join(keywords)}|{','.join(hf_words)}"
    entity_str = ",".join(extract_entities(document, stopwords)) or "无"

    abstract = get_best_abstract(title, document, 200)

    global classifier
    label = "生活"
    if classifier is None and os.path.exists(MODEL_PATH):
        try:
            classifier = joblib.load(MODEL_PATH)
        except:
            pass

    if classifier and words:
        label = classifier.predict([" ".join(words[:200])])[0]

    return {
        "Title": title,
        "ClassLabel": label,
        "KeyWord_HFWord": key_hf,
        "NamedEntity": entity_str,
        "Abstract": abstract,
        "Document": document
    }