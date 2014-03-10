#!/bin/bash

#### DE-EN

REF_FILE=data/last500.ref
KBEST1=data/kbest.1
KBEST2=data/kbest.2

CMD="./nm.py --a1=4 --a2=4 --b=3 --kbest1=$KBEST1 --kbest2=$KBEST2 --ref=$REF_FILE --max_iterations=10000"

# BLEU MBR + BLEU ObjFunc
rm -rf workBB
mkdir workBB
$CMD --workdir=workBB &

# BLEU MBR + METEOR ObjFunc
rm -rf workBM
mkdir workBM
$CMD --obj_func=meteor --workdir=workBM &

##### SLOW

# METEOR MBR + BLEU ObjFunc
rm -rf workMB
mkdir workMB
$CMD --use_mbr_meteor --workdir=workMB &

# METEOR MBR + METEOR ObjFunc
rm -rf workMM
mkdir workMM
$CMD --obj_func=meteor --use_mbr_meteor --workdir=workMM &

#### HI-EN
