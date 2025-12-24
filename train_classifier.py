import os
import random
import jieba
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import warnings

warnings.filterwarnings('ignore')

jieba.initialize()

TARGET_5CATS = ["教育", "健康", "生活", "娱乐", "游戏"]
DATASET_ROOT = "THUCNews"
HEALTH_CORPUS_PATH = "health_corpus.txt"
MODEL_SAVE_PATH = "model/text_classifier_5cat.pkl"

# 增加样本量，提高模型泛化能力
SAMPLE_PER_CAT = 600
MAX_TFIDF_FEATURES = 4000
STOPWORDS_PATH = "stopwords.txt"

CATEGORY_MAPPING = {
    "教育": "教育",
    "游戏": "游戏",
    "娱乐": "娱乐",
    "家居": "生活",
    "社会": "生活",
    "时尚": "生活",
    "星座": "生活",
    "财经": "生活",
    "彩票": "生活",
    "房产": "生活",
    "股票": "生活",
    "时政": "生活",
    "科技": "生活"
}


def load_stopwords():
    if os.path.exists(STOPWORDS_PATH):
        with open(STOPWORDS_PATH, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []


def load_health_corpus():
    if not os.path.exists(HEALTH_CORPUS_PATH):
        raise FileNotFoundError(f"健康类语料文件 {HEALTH_CORPUS_PATH} 不存在")

    health_texts = []
    with open(HEALTH_CORPUS_PATH, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < SAMPLE_PER_CAT:
        print(f"健康类语料不足{SAMPLE_PER_CAT}条，使用全部{len(lines)}条")
        selected_lines = lines
    else:
        selected_lines = random.sample(lines, SAMPLE_PER_CAT)

    stopwords = load_stopwords()

    for line in selected_lines:
        words = jieba.lcut(line)
        valid_words = [w for w in words if w not in stopwords and len(w) > 1 and w.strip()]
        if valid_words:
            health_texts.append(" ".join(valid_words))

    return health_texts


def load_train_data():
    texts = []
    labels = []
    stopwords = load_stopwords()
    cat_count = {cat: 0 for cat in TARGET_5CATS}

    # 加载健康类语料
    health_samples = load_health_corpus()
    texts.extend(health_samples)
    labels.extend(["健康"] * len(health_samples))
    cat_count["健康"] = len(health_samples)

    # 加载THUCNews数据
    for original_cat in os.listdir(DATASET_ROOT):
        cat_path = os.path.join(DATASET_ROOT, original_cat)
        if not os.path.isdir(cat_path):
            continue
        if original_cat not in CATEGORY_MAPPING:
            continue

        target_cat = CATEGORY_MAPPING[original_cat]
        if target_cat == "健康":  # 健康类已单独处理
            continue

        if cat_count[target_cat] >= SAMPLE_PER_CAT:
            continue

        txt_files = [f for f in os.listdir(cat_path) if f.endswith(".txt")]
        random.shuffle(txt_files)

        for filename in txt_files:
            if cat_count[target_cat] >= SAMPLE_PER_CAT:
                break

            file_path = os.path.join(cat_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if len(content) < 80:  # 增加最小长度要求
                        continue

                    words = jieba.lcut(content)
                    valid_words = [w for w in words if w not in stopwords and len(w) > 1 and w.strip()]
                    if len(valid_words) < 15:  # 增加最小词汇量要求
                        continue

                    texts.append(" ".join(valid_words))
                    labels.append(target_cat)
                    cat_count[target_cat] += 1

            except Exception as e:
                continue

    print(f"训练数据分布: {cat_count}")
    return texts, labels


def train_model():
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    texts, labels = load_train_data()

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    # 使用逻辑回归
    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=MAX_TFIDF_FEATURES,
            ngram_range=(1, 2),
            stop_words=load_stopwords(),
            min_df=2,
            max_df=0.8
        )),
        ("clf", LogisticRegression(
            C=1.0,
            max_iter=1000,
            random_state=42,
            class_weight='balanced'  # 处理类别不平衡
        ))
    ])

    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    print("模型评估报告：")
    print(classification_report(y_test, y_pred, target_names=TARGET_5CATS))

    joblib.dump(model, MODEL_SAVE_PATH)
    model_size = os.path.getsize(MODEL_SAVE_PATH) / 1024 / 1024
    print(f"模型保存路径：{MODEL_SAVE_PATH}")
    print(f"模型体积：{model_size:.2f} MB")


if __name__ == "__main__":
    try:
        train_model()
    except Exception as e:
        print(f"训练异常：{str(e)}")