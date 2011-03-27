#!/usr/bin/python
# For comparing the speed of the two vision algorithms
# usage: vision_compare.py [block_size] [ant_spacing]
#   block_size, is the number of rows and columns of ants to use
#       (default is a 10x10 block of ants)
#   spacing is the amount of space between each row and column
#       (it defaults to 1 space in between if not supplied)


import sys
import timeit
from collections import deque, defaultdict
from math import sqrt

# possible directions an ant can move
AIM = {'n': (-1, 0),
       'e': (0, 1),
       's': (1, 0),
       'w': (0, -1)}

class Ant:
    def __init__(self, loc):
        self.loc = loc

class CheckVision:
    def __init__(self, ant_locs, size, vr2=96):
        self.ants = [Ant(l) for l in ant_locs]
        self.height = size[0]
        self.width = size[1]
        self.viewradius2 = vr2

    def player_ants(self, player):
        return self.ants

    def destination(self, loc, d):
        """ Returns the location produced by offsetting loc by d """
        return ((loc[0] + d[0]) % self.height, (loc[1] + d[1]) % self.width)

    def distance(self, x, y):
        """ Returns distance between x and y squared """
        d_row = abs(x[0] - y[0])
        d_row = min(d_row, self.height - d_row)
        d_col = abs(x[1] - y[1])
        d_col = min(d_col, self.width - d_col)
        return d_row**2 + d_col**2

    def vision_by_ant(self, player=0):
        """ Determine which squares are visible to the given player """

        if not hasattr(self, 'vision_offsets'):
            # precalculate squares to test
            self.vision_offsets = []
            mx = int(sqrt(self.viewradius2))
            for d_row in range(-mx,mx+1):
                for d_col in range(-mx,mx+1):
                    d = d_row**2 + d_col**2
                    if d <= self.viewradius2:
                        self.vision_offsets.append((d_row,d_col))

        vision = [[False]*self.width for row in range(self.height)]
        for ant in self.player_ants(player):
            loc = ant.loc
            for v_loc in self.vision_offsets:
                row, col = self.destination(ant.loc, v_loc)
                vision[row][col] = True
        return vision

    def vision_distance(self, loc1, loc2):
        # this returns the square of the euclidean distance
        # so it can be compared with the viewradius2, which is squared
        row1, col1 = loc1
        row2, col2 = loc2
        d_col = min(abs(col1 - col2), self.width - abs(col1 - col2))
        d_row = min(abs(row1 - row2), self.height - abs(row1 - row2))
        return d_row**2 + d_col**2

    def vision_by_square(self, player=0):
        'determine which squares are visible to the given player'

        vision = [[False for col in range(self.width)]
                       for row in range(self.height)]
        # squares_to_check is a list of painted squares that may still
        # have unpainted squares near it
        # a deque is like a list, but faster when poping items from the left
        squares_to_check = deque()
        # for each ant, slowly paint all the squares around it
        # keep rotating ants so that they all paint at the same rate
        # if 2 ants paint the same square, it is merged and we save time
        for ant in self.player_ants(player):
            squares_to_check.append((ant.loc, ant.loc))
        while squares_to_check:
            a_loc, v_loc = squares_to_check.popleft()
            # paint all 4 squares around the square to check at once
            for d in AIM.values():
                n_loc = self.destination(v_loc, d)
                n_row, n_col = n_loc
                if (not vision[n_row][n_col] and
                        self.vision_distance(a_loc, n_loc) <= self.viewradius2):
                    # we can see this square
                    vision[n_row][n_col] = True
                    # add to list to see if other square near it are also
                    # visible
                    squares_to_check.append((a_loc, n_loc))
        return vision

    def vision_by_distance(self, player=0):
        vision = [[False]*self.width for row in range(self.height)]
        min_dist = 0
        squares_to_check = [[] for i in range(self.viewradius2 + 1)]
        squares_to_check.append([None]) # sentinal
        for ant in self.player_ants(player):
            squares_to_check[0].append((ant.loc, ant.loc))
            vision[ant.loc[0]][ant.loc[1]] = True
        while min_dist <= self.viewradius2:
            a_loc, v_loc = squares_to_check[min_dist].pop()
            while not squares_to_check[min_dist]:
                min_dist += 1
            for d in AIM.values():
                n_loc = self.destination(v_loc, d)
                n_row, n_col = n_loc
                if not vision[n_row][n_col]:
                    dist = self.vision_distance(a_loc, n_loc)
                    if dist <= self.viewradius2:
                        vision[n_row][n_col] = True
                        squares_to_check[dist].append((a_loc, n_loc))
        return vision

def make_block(size, offset=0, spacing=1):
    locs = []
    for row in xrange(size[0]):
        for col in xrange(size[1]):
            locs.append(((row * spacing) + offset, (col * spacing) + offset))
    return locs

def time_to_str(seconds):
    units = ["secs", "msecs", "usecs", "nsecs"]
    for unit in units:
        if seconds > 0.1:
            break
        seconds *= 1000.
    return "%.2f %s" % (seconds, unit)

def vision_to_str(vision):
    return '\n'.join(''.join('x' if v else '.' for v in row) for row in vision)

def check_algos():
    size = (50, 50)
    cloc = (25, 25)
    result = True
    for row in xrange(size[0]):
        for col in xrange(size[1]):
            cv = CheckVision([cloc, (row, col)], size)
            by_ant = cv.vision_by_ant()
            by_distance = cv.vision_by_distance()
            if by_ant != by_distance:
                print "Vision didn't match"
                print "first ant at", cloc
                print "second ant at", (row, col)
                print
                return False
    return result

if __name__ == "__main__":
    block_size = 5
    if len(sys.argv) > 1:
        block_size = int(sys.argv[1])
    spacing = 2
    if len(sys.argv) > 2:
        spacing = int(sys.argv[2]) + 1
    size = max(120, ((block_size-1) * spacing) + 30)
    size = (size, size)
    print "Checking vision_by_distance against vision_by_ant"
    if not check_algos():
        sys.exit()
    global cv
    cv = CheckVision(make_block((block_size, block_size), 15, spacing), size)
    repetitions = 1000
    print "Timing vision_by_ant"
    by_ant = timeit.timeit("cv.vision_by_ant()",
            setup="from __main__ import cv", number=repetitions)
    print "It took %s per call to vision_by_ant" % (
            time_to_str(by_ant / repetitions))
    print "Timing vision_by_distance"
    by_distance = timeit.timeit("cv.vision_by_distance()",
            setup="from __main__ import cv", number=repetitions)
    print "It took %s per call to vision_by_distance" % (
            time_to_str(by_distance / repetitions))
    print "Timing vision_by_squares (broken)"
    by_square = timeit.timeit("cv.vision_by_square()",
            setup="from __main__ import cv", number=repetitions)
    print "It took %s per call to vision_by_square" % (
            time_to_str(by_square / repetitions))

