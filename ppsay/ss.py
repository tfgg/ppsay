# -*- coding: utf-8 -*-

from collections import Counter
import sys


quotes = [u'"', u'”', u"'", u'“']
titles = [u'Dr', u'Mr', u'Mrs', u'Ms', u'h.D']
end_marks = [u'.', u'?', u'!']
whitespace = [u' ', u'\n', u'\r', u'\t']

def is_end_of_sentence(s):
  if s[4] in end_marks and (s[2:4] in titles or s[1:4] in titles):
    return False
  elif s[4] in end_marks and s[5] in quotes:
    return True
  elif s[4] in end_marks and s[5] in whitespace:
    return True
  else:
    return False

def is_start_of_word(s):
  if (s[3] in whitespace and s[4] not in quotes) or s[3] in quotes:
    return True
  else:
    return False

def is_end_of_word(s):
  eos = is_end_of_sentence(s)
  eos1 = is_end_of_sentence(" " + s)

  if (((s[4] in whitespace and s[3] != ',') or s[4] == ',') and not eos1) or eos:
    return True
  else:
    return False

def is_start_bracket(s):
  if s[3] == '(':
    return True
  else:
    return False

def is_end_bracket(s):
  if s[4] == ')':
    return True
  else:
    return False

#sample = "Hello my name is Dr. Tim. 'Why am I a doctor?' Well, I completed my Ph.D. recently."

def samples(ss, l, r):
  for i in range(len(ss) + 1):
    extra_prefix = max(l-i, 0)
    extra_suffix = max(i + r - len(ss), 0)
    s = " " * extra_prefix + ss[max(i-(l),0):min(i+(r),len(ss))] + " " * extra_suffix
    yield (i, s)

class Text(object):
  def __init__(self, sample=None):
    self.end_of_sentences = []
    self.start_of_words = []
    self.end_of_words = []
    self.start_of_brackets = []
    self.end_of_brackets = []

    if sample is not None:
        self.parse(sample)

  def parse(self, sample):
    self.sample = sample

    for i, s in samples(sample, 4, 4):
      end_of_sentence = is_end_of_sentence(s)
      start_of_word = is_start_of_word(s)
      end_of_word = is_end_of_word(s)
      start_of_bracket = is_start_bracket(s)
      end_of_bracket = is_end_bracket(s)

      if end_of_sentence:
        self.end_of_sentences.append(i)

      if start_of_word:
        self.start_of_words.append(i)

      if end_of_word:
        self.end_of_words.append(i)

      if start_of_bracket:
        self.start_of_brackets.append(i)
      
      if end_of_bracket:
        self.end_of_brackets.append(i)

  def print_debug(self):
    for i, s in samples(sample, 4, 4):
      print i, s,
      if i in self.end_of_sentences:
        print '*',
      if i in self.start_of_words:
        print '+',
      if i in self.end_of_words:
        print '-',
      if i in self.start_of_brackets:
        print '<',
      if i in self.end_of_brackets:
        print '>',
      print

  def markup(self):
    out = []
    for i, c in enumerate(self.sample):
      if i in self.start_of_words:
        out.append('<w>')
      
      if i in self.end_of_words:
        out.append('</w>')
      
      if i in self.end_of_sentences:
        out.append('</s>')

      if i in self.start_of_brackets:
        out.append('<b>')
 
      if i in self.end_of_brackets:
        out.append('</b>')

      out.append(c)
    return "".join(out)

  def get_words(self):
    words = [sample[a:b] for a, b in zip(self.start_of_words, self.end_of_words)]
    return words

if __name__ == "__main__":
  sample = open(sys.argv[1]).read().decode('utf-8')

  t = Text()
  t.parse(sample)

  words = t.get_words()

  print t.markup().encode('utf-8')

  #for word in words:
  #  print word

