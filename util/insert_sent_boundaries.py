#!/usr/bin/env python

# insert <s> and </s> around the sentences.

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--in_f", required=True)
parser.add_argument("--out_f", required=True)
args = parser.parse_args()

out_f = open(args.out_f, "w")
for line in open(args.in_f):
  out_f.write("<s> {} </s>\n".format(line.strip()))
  
