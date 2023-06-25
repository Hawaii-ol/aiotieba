import emoji
import jieba
import re
import pathlib
import pprint
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

class BaseLearner:
    basepath = pathlib.Path(__file__).parent / 'dataset'
    def __init__(self) -> None:
        with open(self.basepath / 'stopwords.txt', encoding='utf-8') as fstop,\
            open(self.basepath / 'cyuyan_dict.txt', encoding='utf-8') as fdict:
            self.stopwords = set(line.strip() for line in fstop)
            jieba.load_userdict(fdict)
            self.model = MultinomialNB(alpha=1.0)
            # 文档内容转小写
            # 分词规则：匹配任何长度单词，以空白字符分隔
            self.vec = TfidfVectorizer(
                lowercase=True,
                token_pattern=r'(?u)\S+',
            )
            self.trained = False
    
    def _clean_word(self, word: str) -> bool:
        """清洗文档，过滤无效词汇"""
        # 过滤所有停用词
        if word in self.stopwords:
            return False
        # 过滤空白字符和标点符号
        if re.match(r'^\W*$', word):
            return False
        # 过滤除汉字和qv以外的单个字符:
        if re.match(r'^[^qv\u4e00-\u9fa5]$', word, re.IGNORECASE):
            return False
        # 过滤所有数字字符串
        if word.isdigit():
            return False
        # 过滤单字母+数字，如a1 c99 q123456789
        if re.match(r'^[A-Za-z]\d+$', word):
            return False
        return True

    def train(self, hamfile, spamfile):
        with open(hamfile, encoding='utf-8') as fham,\
            open(spamfile, encoding='utf-8') as fspam:
            cuts = (jieba.cut(line) for line in fham)
            words = (filter(self._clean_word, cut) for cut in cuts)
            text_hams = [' '.join(w) for w in words]
            cuts = (jieba.cut(line) for line in fspam)
            words = (filter(self._clean_word, cut) for cut in cuts)
            text_spams = [' '.join(w) for w in words]
            text_all = text_hams + text_spams
            x_train = self.vec.fit_transform(text_all).toarray()
            y_train = ['ham' if i < len(text_hams) else 'spam' for i in range(len(text_all))]
            self.model.fit(x_train, y_train)
            self.trained = True

    def predict(self, text : str):
        if not self.trained:
            raise RuntimeError('model not trained, use train() to train the model first.')
        # 移除所有的颜文字
        text = emoji.replace_emoji(text)
        cut = jieba.cut(text)
        words = filter(self._clean_word, cut)
        x_test = self.vec.transform([' '.join(words)]).toarray()
        y_text = self.model.predict(x_test)
        return y_text[0]

class AntiSpammer(BaseLearner):
    def __init__(self) -> None:
        return super().__init__()

    def train(self):
        hamfile = self.basepath / 'ham.txt'
        spamfile = self.basepath / 'spam.txt'
        return super().train(hamfile, spamfile)

class AntiFraud(BaseLearner):
    def __init__(self) -> None:
        return super().__init__()
    
    def train(self):
        hamfile = self.basepath / 'fraud_ham.txt'
        spamfile = self.basepath / 'fraud_spam.txt'
        return super().train(hamfile, spamfile)
    
    def predict(self, text : str):
        # 正则检测qq号
        if len(text) < 20 and re.search(r'\d{9,10}', text):
            return 'spam'
        return super().predict(text)

if __name__ == '__main__':
    _aspam = AntiSpammer()
    _aspam.train()
    print('TF-IDF feature names for spam:')
    print(_aspam.vec.get_feature_names_out().tolist())
    _afraud = AntiFraud()
    _afraud.train()
    print('TF-IDF feature names for fraud:')
    print(_afraud.vec.get_feature_names_out().tolist())
