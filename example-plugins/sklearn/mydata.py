#
#    Copyright 2014 Grupo de Sistemas Inteligentes (GSI) DIT, UPM
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

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
