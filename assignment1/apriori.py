import sys
import decimal
from itertools import combinations
from itertools import product


DEBUG = False
context = decimal.getcontext()
context.rounding = decimal.ROUND_HALF_UP

min_support = round(decimal.Decimal(sys.argv[1]), 2)
input_file = sys.argv[2]
output_file = sys.argv[3]

database = []
total_candidate = []
deleted_candidate = []
candidate_support = {}
frequent_item_support = {}

# first database scan
with open(input_file, 'r') as f:   
    for i, line in enumerate(f.readlines()):
        transaction = set()
        for item in line.split():
            candidate_support[tuple([item])] = 0
            transaction.add(item)            
        database.append(transaction)
db_size = len(database)

if DEBUG:
    print('database:')
    for transaction in database:
        print(transaction)

# calculate support of item with length one
for item in candidate_support.keys():
    for transaction in database:
        if transaction & set(item) == set(item):
            candidate_support[item] += 1
for item in candidate_support.keys():
    if round(decimal.Decimal(100 * candidate_support[item] / db_size), 2) < min_support:
        deleted_candidate.append(set(item))
for item in deleted_candidate:
    del candidate_support[tuple(item)]

for candi, sup in candidate_support.items():
    frequent_item_support[candi] = sup

# get frequent items
while len(candidate_support.keys()) > 0:
    # 1. generating candidate
    next_candidate_support = {}
    next_candidate = []
    for i in combinations(candidate_support.keys(), 2):
        c = set(i[0]).union(set(i[1]))
        # do not include candidate which has been generated at previous iterations
        if c not in total_candidate:
            total_candidate.append(c)
            # make candidates independent
            if c not in next_candidate:
                next_candidate.append(c)
    
    # 2. candidate pruning: remove candidate which has a not frequent pattern subset
    candidate_with_infrequent_subset = []
    for c in next_candidate:
        is_subset_frequent = True
        for d in deleted_candidate:
            if c & d == d:
                candidate_with_infrequent_subset.append(c)
                break
    for c in candidate_with_infrequent_subset:
        next_candidate.remove(c)
    for c in next_candidate:
        next_candidate_support[tuple(c)] = 0
    
    # 3. removing candidate under the minimum support
    for c in next_candidate:
        for transaction in database:
            if transaction & c == c:
                next_candidate_support[tuple(c)] += 1
    candidate_under_min_support = []
    for c in next_candidate:
        support = round(decimal.Decimal(100 * next_candidate_support[tuple(c)] / db_size), 2)
        if support < min_support:
            candidate_under_min_support.append(c)
    for c in candidate_under_min_support:
        deleted_candidate.append(c)
        del next_candidate_support[tuple(c)]
    
    for k, v in candidate_support.items():
        frequent_item_support[k] = v
    candidate_support = next_candidate_support

if DEBUG:
    print('\n================frequent items====================')
    for k in frequent_item_support.keys():
        print(k, ':', frequent_item_support[k], '\n')
    print('number of frequent items:', len(frequent_item_support.keys()))
    print('==================================================\n')

# get association rule from frequent items
association_rule = []
for item in frequent_item_support.keys():
    item_length = len(item)
    if item_length == 1:
        continue

    for n in range(item_length):
        if n == item_length - 1:
            break
        p = combinations(item, n + 1)
        q = combinations(item, item_length - (n + 1))
 
        for i, j in product(p, q):
            if len(set(i) & set(j)) == 0:
                association_rule.append((i, j))

if DEBUG:
    print('association rule:')
    print('(item set) -> (associative item set)    support    confidence')

# calcuate support and confidence of association rule
f = open(output_file, 'w')
for p, q in association_rule:
    pq = p + q
    pq_support, p_support = 0, 0

    for item in frequent_item_support.keys():
        if set(pq) == set(item):
            pq_support = frequent_item_support[item]
        if set(p) == set(item):
            p_support = frequent_item_support[item]
        
    association_support = round(decimal.Decimal(100 * pq_support / db_size), 2)
    association_confidence = round(decimal.Decimal(100 * pq_support / p_support), 2)
    
    if association_support >= min_support and association_confidence >= min_support:
        if DEBUG: print(p, '->', q, association_support, association_confidence)

        item_set = ''
        associative_item_set = ''
        for i in list(p):
            item_set += i + ','
        item_set = item_set[:-1]
        for i in list(q):
            associative_item_set += i + ','
        associative_item_set = associative_item_set[:-1]

        f.write(f'{{{item_set}}}\t{{{associative_item_set}}}\t{association_support}\t{association_confidence}\n')
f.close()