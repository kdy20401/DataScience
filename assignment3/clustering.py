import sys
import math
from argparse import Namespace


def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def get_density_reachables(start_point, distance_info, is_core):
    cluster = set()
    stack = []
    visited = dict.fromkeys(range(n), False)

    stack.append(start_point)

    while len(stack) > 0:
        p = stack.pop()
        if visited[p] == True:
            continue

        visited[p] = True
        cluster.add(p)

        if not is_core[p]:
            continue

        for next_point, distance in distance_info[p].items():
            if distance <= args.radius:
                if not visited[next_point]:
                    stack.append(next_point)
            else:
                break

    return cluster


def identify_core(distance_info):
    n = len(distance_info)
    is_core = dict.fromkeys(range(n), False)

    # check all points are core or not
    for p in range(n):
        num_neighbor = 0
        for _, dist in distance_info[p].items():
            if num_neighbor >= args.min_points or dist > args.radius:
                break
            num_neighbor += 1

        if num_neighbor >= args.min_points:
            is_core[p] = True

    return is_core


def get_distance_dictionary(data):
    '''
    calcuate distance between all two data points and sort by distance in ascending order.
    
    example for 3 data points:

    distance_info = {0: {0: 0,  1: 1.4,  2: 5.3},
                     1: {1: 0,  0: 1.4,  2: 8.2},
                     2: {2: 0,  0: 5.3,  1: 8.2}}
    
    distance_info.keys()     : point IDs
    distance_info[p]         : point p's distance information(dictionary)
    distance_info[p].items() : distance between point p and the other points
    distance_info[1][2]      : distance between point 1 and 2 
    '''

    distance_info = {}
    n = len(data)
    for p in range(n):
        points = range(n)
        distances = [calculate_distance(data[p], data[q]) for q in points]
        distance_info[p] = dict(sorted(zip(points, distances), key=lambda x: x[1]))

    return distance_info


def load_data(file_name):
    data = {}
    with open(f'./input-data/{file_name}', 'r') as f:
        for i, line in enumerate(f.readlines()):
            x, y = map(float, line.split()[1:])
            data[i] = x, y

    return data

# system arguments
args = Namespace()
input_file_name = sys.argv[1]
args.num_cluster, args.radius, args.min_points = map(int, sys.argv[2:])
    
data = load_data(input_file_name)
n = len(data)

# by priority, get distancess between points and find core points
distance_info = get_distance_dictionary(data)
is_core = identify_core(distance_info)

clusters = {}
cluster_num = {}
cluster_idx = 0
in_cluster = dict.fromkeys(range(n), False)

# main loop for DBSCAN
for p in range(n):
    if not in_cluster[p] and is_core[p]:
        # find all density reachable points from i
        cluster = get_density_reachables(p, distance_info, is_core)
        for c in cluster:
            in_cluster[c] = True
        clusters[cluster_idx] = list(cluster)
        cluster_num[cluster_idx] = len(cluster)
        cluster_idx += 1

# for assignment grading. restrict the number of cluster to args.num_cluster
cluster_num = dict(sorted(cluster_num.items(), key=lambda x: x[1])[cluster_idx - args.num_cluster:])

# write clustering results to file
file_num = input_file_name[-5]
i = 0
for c in cluster_num:
    with open(f'./output-data/input{file_num}_cluster_{i}.txt', 'w') as f:
        for p in clusters[c]:
            f.write(f'{p}\n')
    i += 1