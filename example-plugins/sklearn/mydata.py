'''
Create a dummy dataset.
Messages with a happy emoticon are labelled positive
Messages with a sad emoticon are labelled negative
'''
import random

dataset = []

vocabulary = ['hello', 'world', 'senpy', 'cool', 'goodbye', 'random', 'text']

emojimap = {
    1: [':)', ],
    -1: [':(', ]
}


for tag, values in emojimap.items():
    for i in range(1000):
        msg = ''
        for j in range(3):
            msg += random.choice(vocabulary)
            msg += " "
        msg += random.choice(values)
        dataset.append([msg, tag])


text = []
labels = []

for i in dataset:
    text.append(i[0])
    labels.append(i[1])
