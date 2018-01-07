from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split

from mydata import text, labels

X_train, X_test, y_train, y_test = train_test_split(text, labels, test_size=0.12, random_state=42)

from sklearn.naive_bayes import MultinomialNB


count_vec = CountVectorizer(tokenizer=lambda x: x.split())
clf3 = MultinomialNB()
pipeline = Pipeline([('cv', count_vec),
                    ('clf', clf3)])

pipeline.fit(X_train, y_train)
print('Feature names: {}'.format(count_vec.get_feature_names()))
print('Class count: {}'.format(clf3.class_count_))


if __name__ == '__main__':
    print('--Results--')
    tests = [
        (['The sentiment for senpy should be positive :)', ], 1),
        (['The sentiment for anything else should be negative :()', ], -1)
    ]
    for features, expected in tests:
        result = pipeline.predict(features)
        print('Input: {}\nExpected: {}\nGot: {}'.format(features[0], expected, result))
