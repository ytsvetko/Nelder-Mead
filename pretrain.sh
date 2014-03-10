#!/bin/bash

REF=data/deen/ref
#KBEST=data/deen/kbest.1
#TUNE_DIR=data/deen/austin-pretrain
KBEST=data/deen/kbest.3
TUNE_DIR=data/deen/greg-pretrain-1

MBR=~/tools/cdec/mteval/mbr_kbest
BLEU=~/tools/mosesdecoder/scripts/generic/multi-bleu.perl


DO_MBR=0
DO_EVAL=1

function mbr {
  kbest_list=$1
  tune_dir=$2
  range=$3
  mkdir -p ${tune_dir}
  for a in ${range};
  do
    ${MBR} -i ${kbest_list} -a $a -b 0 > ${tune_dir}/`basename ${kbest_list}`-a${a} &
  done
}

function bleu {
  kbest_list=$1
  tune_dir=$2
  range=$3
  for a in ${range};
  do
    hyp=${tune_dir}/`basename ${kbest_list}`-a${a}
    out=${tune_dir}/`basename ${kbest_list}`-a${a}.bleu  
    $BLEU ${REF} < ${hyp} > ${out}
  done 
}

if (( ${DO_MBR} )); then
  mbr ${KBEST} ${TUNE_DIR} "$(seq 0 1 10)"
fi

if (( ${DO_EVAL} )); then
  echo "Eval kbest"
  bleu ${KBEST} ${TUNE_DIR} "$(seq 0 1 10)"
fi


todo='
tail -n +1 -- data/deen/austin-pretrain/kbest.1-a*.bleu > data/deen/austin-pretrain/kbest.1-all.blue
tail -n +1 -- data/deen/greg-pretrain/kbest.2-a*.bleu > data/deen/greg-pretrain/kbest.2-all.blue
tail -n +1 -- data/deen/greg-pretrain-1/kbest.3-a*.bleu > data/deen/greg-pretrain-1/kbest.3-all.blue

python

max_bleu = 0
max_a = 0
for line in open("greg-kbest_tune_a/kbest.2-a.blue"):
  print line
  # ==> kbest_tune_a/kbest.2-a0.bleu <==
  if line.startswith("==>"):
    a = line.split("-")[1].split(".")[0][1:]
  if line.startswith("BLEU"):
    bleu = float(line.split()[2][:-1])
    if max_bleu < bleu:
      max_bleu = bleu
      max_a = a


print max_bleu
print max_a

'


