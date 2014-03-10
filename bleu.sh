#!/bin/bash

REF=$1
HYP=$2

BLEU=~/tools/mosesdecoder/scripts/generic/multi-bleu.perl

$BLEU ${REF} < ${HYP} > ${HYP}.blue

tail ${HYP}.blue
