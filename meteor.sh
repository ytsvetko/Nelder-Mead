#!/bin/bash

REF=$1
HYP=$2

METEOR=~/tools/meteor/meteor-*.jar

java -Xmx2G -jar ${METEOR} ${HYP} ${REF} -l en -norm > ${HYP}.meteor

tail -n 1 ${HYP}.meteor





