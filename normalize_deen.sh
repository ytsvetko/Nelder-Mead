#!/bin/bash

set -x 

# Normalize inputs of two systems:
# for Greg's files:
# split by ||| to retain only sentence num and sentence
# tokenize-anything.sh
# insert <s> and </s> around the sentences.
# for Chris's system:
# Uppercase first letter of each sentence

REF_ORIG=data/deen/ref-orig
REF_OUT=data/deen/ref
FROM_CHRIS_ORIG=data/deen/austin-test.nbest
FROM_CHRIS_OUT=data/deen/test-kbest.1
FROM_GREG=data/deen/greg-test.nbest
FROM_GREG_OUT=data/deen/test-kbest.3

TOOLS=~/tools/cdec/corpus

util/uppercase.py --in_f=${REF_ORIG} --out_f=${REF_OUT}
util/uppercase.py --in_f=${FROM_CHRIS_ORIG} --out_f=${FROM_CHRIS_OUT}

${TOOLS}/cut-corpus.pl 1 ${FROM_GREG} > tmp/from_greg.sentnum
${TOOLS}/cut-corpus.pl 2 ${FROM_GREG} | ${TOOLS}/tokenize-anything.sh > tmp/from_greg.sent
${TOOLS}/cut-corpus.pl 3 ${FROM_GREG} > tmp/from_greg.feat
${TOOLS}/cut-corpus.pl 4 ${FROM_GREG} > tmp/from_greg.score

util/insert_sent_boundaries.py --in_f=tmp/from_greg.sent \
                                --out_f=tmp/from_greg.sentbound

${TOOLS}/paste-files.pl tmp/from_greg.sentnum \
                        tmp/from_greg.sentbound \
                        tmp/from_greg.feat \
                        tmp/from_greg.score > ${FROM_GREG_OUT}

