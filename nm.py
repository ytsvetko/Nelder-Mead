#!/usr/bin/env python

# Implements MBR parameter optimization for two kbest lists, objective function
# is bleu.
# Algorithm: Nedler-Mead http://en.wikipedia.org/wiki/Nelder%E2%80%93Mead_method

from __future__ import division
import subprocess
import numpy as np
import argparse
import os
from operator import itemgetter
from concurrent import futures

ALPHA = 1
GAMMA = 2
RO = -0.5
SIGMA = 0.5

parser = argparse.ArgumentParser()
parser.add_argument("--mbr_path", default="/home/ytsvetko/tools/cdec/mteval/mbr_kbest")
parser.add_argument("--bleu_path", default="./bleu.sh")
parser.add_argument("--meteor_path", default="./meteor.sh")
parser.add_argument("--ref", default="data/last500.ref")
parser.add_argument("--kbest1", default="data/sample-kbest.1")
parser.add_argument("--kbest2", default="data/sample-kbest.2")
parser.add_argument("--a1", type=float)
parser.add_argument("--a2", type=float)
parser.add_argument("--b", type=float)
parser.add_argument("--max_iterations", default=10000, type=int)
parser.add_argument("--workdir", default="work")
parser.add_argument("--obj_func", default="bleu")
parser.add_argument("--use_mbr_meteor", action="store_true")
args = parser.parse_args()

def Bleu(hyp_filename):
  command = [args.bleu_path, args.ref, hyp_filename]
  output = subprocess.check_output(command)
  return 100.0 - float(output.split()[2][:-1])

def Meteor(hyp_filename):
  command = [args.meteor_path, args.ref, hyp_filename]
  output = subprocess.check_output(command)
  return 1.0 - float(output.split()[2])

ObjFunc = Bleu if args.obj_func == "bleu" else Meteor

def RealScore(vals):
  a1, a2, b = vals
  mbr_command = [args.mbr_path, "-i", args.kbest1, "-a", str(a1), "-b", "0", "-i", args.kbest2, "-a", str(a2), "-b", str(b)]
  if args.use_mbr_meteor:
    mbr_command.append("-m")
    mbr_command.append("meteor")
    label = "meteor"
  else:
    label = "bleu"
  tmp_file_suffix = "{}_{}_{}_{}".format(label, a1, a2, b)
  mbr_hyp_filename = os.path.join(args.workdir, "hyp_" + tmp_file_suffix)
  mbr_stderr_filename = os.path.join(args.workdir, "mbr_stderr_" + tmp_file_suffix)
  if not os.path.isfile(mbr_hyp_filename):
    with open(mbr_hyp_filename, "w") as tmp_file:
      with open(mbr_stderr_filename, "w") as stderr_file:
        subprocess.check_call(mbr_command, stdout=tmp_file, stderr=stderr_file)
  return ObjFunc(mbr_hyp_filename)

def TestScore(vals):
  a1, a2, b = vals
  # ./nm.py --a1=100 --a2=1000 --b=123343 --max_iterations=10000
  return np.linalg.norm( np.array( (a1, a2, b) ) - np.array( (7.5, 3.4, 9.2) ))

Score = RealScore

class Simplex(object):
  def __init__(self, a1, a2, b):
    x0 = np.array([a1, a2, b])
    vertices = [x0 + np.array((1,1,1)),
                x0 + np.array((1,-1,-1)),
                x0 + np.array((-1,1,-1)),
                x0 + np.array((-1,-1,1))]
    with futures.ThreadPoolExecutor(max_workers=len(vertices)) as executor:
      scores = executor.map(Score, vertices)
      self.vertices = zip(scores, vertices)

  def Order(self):
    self.vertices = sorted(self.vertices, key=itemgetter(0))

  def Centroid(self):
    bestN = self.vertices[:-1]
    centroid = sum( (x for b,x in bestN) ) / len(bestN)
    return centroid

  def Reflection(self, centroid):
    reflection = centroid + ALPHA * (centroid - self.vertices[-1][1])
    bleu = Score(reflection)
    return bleu, reflection

  def Expansion(self, centroid):
    expansion = centroid + GAMMA * (centroid - self.vertices[-1][1])
    bleu = Score(expansion)
    return bleu, expansion

  def Contraction(self, centroid):
    contraction = centroid + RO * (centroid - self.vertices[-1][1])
    bleu = Score(contraction)
    return bleu, contraction

  def Reduction(self):
    x1 = self.vertices[0]
    new_vertices = []
    for _, x_i in self.vertices[1:]:
      new_x_i = x1[1] + SIGMA * (x_i - x1[1])
      new_vertices.append(new_x_i)
    with futures.ThreadPoolExecutor(max_workers=len(new_vertices)) as executor:
      scores = executor.map(Score, new_vertices)
      self.vertices = [x1] + zip(scores, new_vertices)

  def __repr__(self):
    best_score, best_coord = self.vertices[0]
    if args.obj_func == "bleu":
      best_bleu = 100.0 - best_score
      return "Best BLEU: {} at a1={}, a2={}, b={}".format(best_bleu,
                                                          best_coord[0],
                                                          best_coord[1],
                                                          best_coord[2])
    else:
      best_meteor = 1.0 - best_score
      return "Best METEOR: {} at a1={}, a2={}, b={}".format(best_meteor,
                                                            best_coord[0],
                                                            best_coord[1],
                                                            best_coord[2])

def NedlerMead(a1, a2, b):
  simplex = Simplex(a1, a2, b)
  for i in range(args.max_iterations):
    print "Iteration:", i
    simplex.Order()
    print simplex
    x0 = simplex.Centroid()
    r_bleu, reflection = simplex.Reflection(x0)
    if r_bleu < simplex.vertices[0][0]:
      # Expansion
      ex_bleu, expansion = simplex.Expansion(x0)
      if ex_bleu < r_bleu:
        simplex.vertices[-1] = (ex_bleu, expansion)
      else:
        simplex.vertices[-1] = (r_bleu, reflection)
    elif r_bleu < simplex.vertices[-2][0]:
      # Insert reflected (step 3)
      simplex.vertices[-1] = (r_bleu, reflection)
    else:
      # Contraction
      c_blue, contraction = simplex.Contraction(x0)
      if c_blue < simplex.vertices[-1][0]:
        simplex.vertices[-1] = (c_blue, contraction)
      else:
        # Reduction
        simplex.Reduction()

def main():
  NedlerMead(args.a1, args.a2, args.b)

if __name__ == '__main__':
  main()
