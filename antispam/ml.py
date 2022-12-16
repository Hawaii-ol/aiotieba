import emoji
import jieba
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

dataset_dir = os.path.join(os.path.dirname(__file__), 'dataset')

class AntiSpammer:
    def __init__(self) -> None:
        with open(os.path.join(dataset_dir, 'stopwords.txt'), encoding='utf-8') as fstop,\
            open(os.path.join(dataset_dir, 'cyuyan_dict.txt'), encoding='utf-8') as fdict:
            self.stopwords = set(line.strip() for line in fstop)
            jieba.load_userdict(fdict)
            self.model = MultinomialNB(alpha=1.0)
            self.vec = TfidfVectorizer()
            self.trained = False

    def train(self):
        with open(os.path.join(dataset_dir, 'ham.txt'), encoding='utf-8') as fham,\
            open(os.path.join(dataset_dir, 'spam.txt'), encoding='utf-8') as fspam:
            cuts = (jieba.cut(line.lower().strip()) for line in fham)
            words = (filter(lambda x: x not in self.stopwords, cut) for cut in cuts)
            text_hams = [','.join(w) for w in words]
            cuts = (jieba.cut(line.lower().strip()) for line in fspam)
            words = (filter(lambda x: x not in self.stopwords, cut) for cut in cuts)
            text_spams = [','.join(w) for w in words]
            text_all = text_hams + text_spams
            x_train = self.vec.fit_transform(text_all).toarray()
            y_train = ['ham' if i < len(text_hams) else 'spam' for i in range(len(text_all))]
            self.model.fit(x_train, y_train)
            self.trained = True

    def predict(self, text : str):
        if not self.trained:
            raise RuntimeError('model not trained, use train() to train the model first.')
        # 转小写
        text = text.lower()
        # 替换所有的换行符
        text = text.replace('\n', '_')
        # 移除所有的颜文字
        text = emoji.replace_emoji(text)
        cut = jieba.cut(text)
        words = list(filter(lambda x: x not in self.stopwords, cut))
        x_test = self.vec.transform([','.join(words)]).toarray()
        y_text = self.model.predict(x_test)
        return y_text[0]

if __name__ == '__main__':
    _aspam = AntiSpammer()
    _aspam.train()