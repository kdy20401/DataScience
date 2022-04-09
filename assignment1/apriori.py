import sys
import decimal
from itertools import combinations
from itertools import product


DEBUG_MODE = False

ROUND_AT = 2
context = decimal.getcontext()
context.rounding = decimal.ROUND_HALF_UP

min_support = round(decimal.Decimal(sys.argv[1]), ROUND_AT)
input_file = sys.argv[2]
output_file = sys.argv[3]

database = []
db_size = None
infrequent_item = []
candidate_support = {}
frequent_item_support = {}
item_size = 1

# first database scan
with open(input_file, 'r') as f:   
    for i, line in enumerate(f.readlines()):
        transaction = set()
        for item in line.split():
            candidate_support[tuple([item])] = 0 # note [item]
            transaction.add(item)            
        database.append(transaction)
db_size = len(database)

if DEBUG_MODE:
    print('database:')
    for transaction in database:
        print(transaction)

# calculate support of item with length one
for item in list(candidate_support):
    for transaction in database:
        if transaction & set(item) == set(item):
            candidate_support[item] += 1

# check if item satisfies the minimum support
for item in list(candidate_support):
    support = round(decimal.Decimal(100 * candidate_support[item] / db_size), ROUND_AT)
    if support < min_support:
        infrequent_item.append(set(item))
for item in infrequent_item:
    del candidate_support[tuple(item)]

frequent_item_support = {c:s for c, s in candidate_support.items()}
item_size += 1

# get frequent items
while len(list(candidate_support)) > 0:
    # 1. generating candidate
    unique_key = set([key for item in list(candidate_support) for key in item])
    next_candidate = list(map(set, list(combinations(unique_key, item_size))))

    # 2. candidate pruning: remove candidate which contains an infreqneut item
    candidate_with_infrequent_item = []
    for c in next_candidate:
        is_subset_frequent = True
        for i in infrequent_item:
            if c & i == i:
                candidate_with_infrequent_item.append(c)
                break
    next_candidate = [c for c in next_candidate if c not in candidate_with_infrequent_item]
    next_candidate_support = {tuple(c): 0 for c in next_candidate}
    
    # 3. calculate support and remove candidate under the minimum support
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
        del next_candidate_support[tuple(c)]

    # update frequent item dictionary
    for c, s in next_candidate_support.items():
        frequent_item_support[c] = s
    candidate_support = next_candidate_support
    item_size += 1

if DEBUG_MODE:
    print('\n================frequent items====================')
    for k in list(frequent_item_support):
        print(k, ':', frequent_item_support[k], '\n')
    print('number of frequent items:', len(list(frequent_item_support)))
    print('==================================================\n')

# get association rule from frequent items
association_rule = []
for item in list(frequent_item_support):
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

if DEBUG_MODE:
    print('association rule:')
    print('(item set) -> (associative item set)    support    confidence')

# calcuate support and confidence of association rule
f = open(output_file, 'w')
for p, q in association_rule:
    pq = p + q
    pq_support, p_support = 0, 0

    for item in list(frequent_item_support):
        if set(pq) == set(item):
            pq_support = frequent_item_support[item]
        if set(p) == set(item):
            p_support = frequent_item_support[item]
        
    association_support = round(decimal.Decimal(100 * pq_support / db_size), 2)
    association_confidence = round(decimal.Decimal(100 * pq_support / p_support), 2)
    
    if association_support >= min_support and association_confidence >= min_support:
        if DEBUG_MODE: print(p, '->', q, association_support, association_confidence)

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