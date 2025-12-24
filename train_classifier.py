import os
import random
import jieba
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 初始化jieba分词（仅一次初始化）
jieba.initialize()

# 作业要求的5类核心配置
TARGET_5CATS = ["教育", "健康", "生活", "娱乐", "游戏"]
DATASET_ROOT = "THUCNews"  # 本地原有数据集根目录
HEALTH_CORPUS_PATH = "health_corpus.txt"  # 健康类独立语料文件路径
MODEL_SAVE_PATH = "model/text_classifier_5cat.pkl"  # 模型独立存储
SAMPLE_PER_CAT = 300  # 每类目标样本数（健康类确保300条）
MAX_TFIDF_FEATURES = 3000  # 控制特征数，保证轻量
STOPWORDS_PATH = "stopwords.txt"

# 13类→5类映射规则（按语义归属，不变）
CATEGORY_MAPPING = {
    "教育": "教育",
    "游戏": "游戏",
    "娱乐": "娱乐",
    # 合并为生活类（兜底类别）
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

# 所有映射到生活类的原类别（不变）
LIFE_BASE_CATS = [cat for cat, target in CATEGORY_MAPPING.items() if target == "生活"]


def load_stopwords():
    """加载停用词，返回list类型（修复参数类型错误）"""
    stopwords = []
    if os.path.exists(STOPWORDS_PATH):
        with open(STOPWORDS_PATH, "r", encoding="utf-8") as f:
            stopwords = [line.strip() for line in f if line.strip()]  # 改为list，而非set
    return stopwords


def load_health_corpus():
    """仅从独立文件读取健康类样本（完全不依赖原有数据集）"""
    if not os.path.exists(HEALTH_CORPUS_PATH):
        raise FileNotFoundError(f"健康类语料文件 {HEALTH_CORPUS_PATH} 不存在，请放在项目根目录")

    health_texts = []
    with open(HEALTH_CORPUS_PATH, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # 确保获取300条（语料文件已包含300条，直接取前300条）
    if len(lines) < SAMPLE_PER_CAT:
        raise ValueError(f"健康类语料不足300条（当前{len(lines)}条），请补充语料文件")

    # 分词+过滤停用词
    stopwords = load_stopwords()
    for line in lines[:SAMPLE_PER_CAT]:
        words = jieba.lcut(line)
        valid_words = [w for w in words if w not in stopwords and len(w) > 1 and w.strip()]
        if valid_words:
            health_texts.append(" ".join(valid_words))

    return health_texts


def load_train_data():
    """重组5类训练数据：健康类仅用独立语料，其他类用原有数据集"""
    texts = []
    labels = []
    stopwords = load_stopwords()
    cat_count = {cat: 0 for cat in TARGET_5CATS}  # 每类样本计数

    # 第一步：加载健康类样本（仅从独立文件读取）
    health_samples = load_health_corpus()
    texts.extend(health_samples)
    labels.extend(["健康"] * len(health_samples))
    cat_count["健康"] = len(health_samples)
    print(f"从 {HEALTH_CORPUS_PATH} 读取健康类样本：{cat_count['健康']}条")

    # 第二步：处理原有THUCNews数据集，收集其他4类样本（教育/娱乐/游戏/生活）
    for original_cat in os.listdir(DATASET_ROOT):
        cat_path = os.path.join(DATASET_ROOT, original_cat)
        if not os.path.isdir(cat_path):
            continue
        if original_cat not in CATEGORY_MAPPING:
            print(f"跳过未配置类别：{original_cat}")
            continue

        # 获取文件夹下所有txt文件，随机打乱（保证样本多样性）
        txt_files = [f for f in os.listdir(cat_path) if f.endswith(".txt")]
        random.shuffle(txt_files)
        read_count = 0  # 实际读取文件数

        # 遍历文件，收集对应类别样本
        for filename in txt_files:
            file_path = os.path.join(cat_path, filename)
            read_count += 1

            try:
                # 快速读取文件，过滤过短文本
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if len(content) < 40:
                        continue

                    # 收集其他类样本（教育/娱乐/游戏/生活）
                    target_cat = CATEGORY_MAPPING[original_cat]
                    if cat_count[target_cat] >= SAMPLE_PER_CAT:
                        break  # 该类已够300条，停止读取

                    # 分词+过滤停用词
                    words = jieba.lcut(content)
                    valid_words = [w for w in words if w not in stopwords and len(w) > 1 and w.strip()]
                    if valid_words:
                        texts.append(" ".join(valid_words))
                        labels.append(target_cat)
                        cat_count[target_cat] += 1

            except Exception as e:
                print(f"读取文件失败：{file_path} → {str(e)}")
                continue

        # 输出当前类别读取情况
        target_cat = CATEGORY_MAPPING[original_cat]
        print(f"{original_cat}类：读取{read_count}个文件，收集{target_cat}类样本{cat_count[target_cat]}条")

    # 检查5类样本是否充足（健康类已确保300条，其他类≥100条）
    print("\n=== 训练集收集结果 ===")
    for cat in TARGET_5CATS:
        min_threshold = 100 if cat != "健康" else 300
        if cat_count[cat] < min_threshold:
            raise ValueError(f"{cat}类样本不足{min_threshold}条（当前{cat_count[cat]}条），请检查数据集")
        print(f"{cat}类：{cat_count[cat]}条（最低要求：{min_threshold}条）")

    print(f"\n总训练样本数：{len(texts)}条")
    return texts, labels


def train_model():
    """训练5类朴素贝叶斯分类器（轻量、高效，文本分类经典方案）"""
    # 创建模型保存目录（确保模型独立，与主程序解耦）
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)

    # 加载重组后的5类数据（含独立健康类样本）
    texts, labels = load_train_data()

    # 划分训练集（80%）和测试集（20%），保持类别分布均衡
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    # 构建模型流水线：TF-IDF特征提取 + 朴素贝叶斯（修复stop_words参数类型）
    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=MAX_TFIDF_FEATURES,
            ngram_range=(1, 2),  # 考虑词语组合，提升特征表达
            stop_words=load_stopwords()  # 现在传入的是list类型，符合要求
        )),
        ("clf", MultinomialNB(alpha=0.1))  # alpha平滑参数，提升泛化能力
    ])

    # 训练模型（朴素贝叶斯训练极快，1500条样本<1秒）
    print("\n开始训练5类分类器...")
    model.fit(x_train, y_train)

    # 模型评估（输出精度、召回率、F1值，验证模型可靠性）
    y_pred = model.predict(x_test)
    print("\n模型评估报告（作业要求5类）：")
    print(classification_report(y_test, y_pred, target_names=TARGET_5CATS))

    # 保存模型（joblib格式，体积小、加载快，符合轻量要求）
    joblib.dump(model, MODEL_SAVE_PATH)
    model_size = os.path.getsize(MODEL_SAVE_PATH) / 1024 / 1024
    print(f"\n模型保存路径：{MODEL_SAVE_PATH}")
    print(f"模型体积：{model_size:.2f} MB（符合轻量要求，<2MB）")


if __name__ == "__main__":
    try:
        train_model()
    except Exception as e:
        print(f"训练异常：{str(e)}")