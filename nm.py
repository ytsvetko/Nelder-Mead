#!/usr/bin/env python

# Implements MBR parameter optimization for two kbest lists, objective function
# is bleu.
# Algorithm: Nedler-Mead http://en.wikipedia.org/wiki/Nelder%E2%80%93Mead_method

from __future__ import division
import subprocess
import numpy as np
import argparse
import os

ALPHA = 1
GAMMA = 2
RO = -0.5
SIGMA = 0.5

parser = argparse.ArgumentParser()
parser.add_argument("--mbr_path", default="/home/ytsvetko/tools/cdec/mteval/mbr_kbest")
parser.add_argument("--bleu_path", default="/home/ytsvetko/tools/mosesdecoder/scripts/generic/multi-bleu.perl")
parser.add_argument("--ref", default="last500.ref")
parser.add_argument("--kbest1", default="sample-kbest.1")
parser.add_argument("--kbest2", default="sample-kbest.2")
parser.add_argument("--a1", type=float)
parser.add_argument("--a2", type=float)
parser.add_argument("--b", type=float)
parser.add_argument("--max_iterations", default=20, type=int)
parser.add_argument("--workdir", default="work")
args = parser.parse_args()

def RealBleu(a1, a2, b):
  mbr_command = [args.mbr_path, "-i", args.kbest1, "-a", str(a1), "-b", "0", "-i", args.kbest2, "-a", str(a2), "-b", str(b)]
  bleu_command = [args.bleu_path, args.ref]
  tmp_file_suffix = "{}_{}_{}".format(a1,a2,b)
  mbr_hyp_filename = os.path.join(args.workdir, "hyp_" + tmp_file_suffix)
  bleu_filename = os.path.join(args.workdir, "bleu_" + tmp_file_suffix)
  if not os.path.isfile(mbr_hyp_filename):
    with open(mbr_hyp_filename, "w") as tmp_file:
      subprocess.check_call(mbr_command, stdout=tmp_file)
  with open(bleu_filename, "w") as bleu_file:
    with open(mbr_hyp_filename) as tmp_file:
      subprocess.check_call(bleu_command, stdin=tmp_file, stdout=bleu_file)
  line = open(bleu_filename).readlines()
  bleu = float(line[0].split()[2][:-1])
  return 100.0 - bleu

def TestBleu(a1, a2, b):
  # ./nm.py --a1=100 --a2=1000 --b=123343 --max_iterations=10000
  return np.linalg.norm( np.array( (a1, a2, b) ) - np.array( (7.5, 3.4, 9.2) ))

Bleu = RealBleu

class Simplex(object):
  def __init__(self, a1, a2, b):
    x0 = np.array([a1, a2, b])
    vertices = [x0 + np.array((1,1,1)),
                x0 + np.array((1,-1,-1)),
                x0 + np.array((-1,1,-1)),
                x0 + np.array((-1,-1,1))]
    self.vertices = [(Bleu(*x), x) for x in vertices]

  def Order(self):
    self.vertices = sorted(self.vertices)

  def Centroid(self):
    bestN = self.vertices[:-1]
    centroid = sum( (x for b,x in bestN) ) / len(bestN)
    return centroid

  def Reflection(self, centroid):
    reflection = centroid + ALPHA * (centroid - self.vertices[-1][1])
    bleu = Bleu(*reflection)
    return bleu, reflection

  def Expansion(self, centroid):
    expansion = centroid + GAMMA * (centroid - self.vertices[-1][1])
    bleu = Bleu(*expansion)
    return bleu, expansion

  def Contraction(self, centroid):
    contraction = centroid + RO * (centroid - self.vertices[-1][1])
    bleu = Bleu(*contraction)
    return bleu, contraction

  def Reduction(self):
    x1 = self.vertices[0]
    new_vertices = [x1]
    for _, x_i in self.vertices[1:]:
      new_x_i = x1 + SIGMA * (x_i - x1)
      new_vertices.append( (Bleu(*new_x_i), new_x_i) )
    self.vertices = new_vertices

  def __repr__(self):
    best_bleu, best_coord = self.vertices[0]
    best_bleu = 100.0 - best_bleu
    return "Best BLEU: {} at a1={}, a2={}, b={}".format(best_bleu,
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
