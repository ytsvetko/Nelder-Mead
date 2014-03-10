#!/usr/bin/env python

# Uppercase first letter of each sentence

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--in_f", required=True)
parser.add_argument("--out_f", required=True)
args = parser.parse_args()

out_f = open(args.out_f, "w")
for line in open(args.in_f):
  tokens = line.strip().split(" ||| ")
  if len(tokens) == 1:
    sentence_ind = 0
  else:
    sentence_ind = 1
  sentence = tokens[sentence_ind].replace("<s>", "").replace("</s>", "").strip()
  try: 
    tokens[sentence_ind] = "<s> {}{} </s>".format(sentence[0].upper(), sentence[1:])
  except:
    print line
    continue
  out_f.write(" ||| ".join(tokens))
  out_f.write("\n")
  
