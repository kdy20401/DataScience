import sys
import numpy as np
import pandas as pd


class Node:
    '''
    Tree node for decision tree.
    
    Instance Variables:
        isLeaf(bool): indicate whether a node is internal or leaf
        label(str): the label value in leaf node. internal node doesn't have label.
        splitting_attribute(str): the attribute which split the current node (ex, 'age')
        splitting_criteria(numpy.ndarray): attribute's values. (ex, ['<=30', '30...40'])
        each criterion indicates the path to the child nodes. acts like a pointer to the child nodes
        children(dict): key is criterion and value is Node.
    
    Instance Method:
        set_splitting_criteria: make branch(pointer) to child nodes using criteria
        check: decide which branch to follow and return corresponding child node.
        when reached to leaf node, return label.
    '''

    def __init__(self, isLeaf=False, label=None):
        self.isLeaf = isLeaf
        self.label = label

    def is_leaf(self):
        return self.isLeaf

    def attach_sibling(self, criterion, node):
        self.children[criterion] = node
    
    def set_splitting_attribute(self, attribute, criteria):
        self.splitting_attribute = attribute
        self.splitting_criteria = criteria
        self.children = {c: None for c in criteria}

    def set_label(self, label):
        self.isLeaf = True
        self.label = label

    def get_label(self):
        return self.label
    
    def check(self, data):
        if self.isLeaf:
            return self.label

        criterion = data[self.splitting_attribute]
        return self.children[criterion]


def ID3(data, attribute, label_column):
    '''
    Calculate sum of the entropy of nodes splitted by the attribute.
    
    Parameters:
        data(pandas.Dataframe): tablular data
        label_column(str): label attribute
        attribute(str): target attribute to split data
    '''

    delta = 1e-7 # to avoid Nan
    table = data.groupby([attribute, label_column])[attribute].count().unstack().fillna(0).to_numpy()
    coeff = np.sum(table, axis=1) / np.sum(table)
    p = table / np.sum(table, axis=1).reshape(-1, 1)
    log_p = np.log2(p + delta)
    entropy = -np.sum(p * log_p, axis=1)
    return np.sum(coeff * entropy)


def find_the_best_splitting_attribute(data, attribute_list, label_column, attribute_selection_method):
    '''
    Find the optimal splitting attribute and return the attribute criteria.
    
    Parameters:
        data(pandas.Dataframe): tablular data
        attribute_list(dict): key is attribute, value is list of unique values. this parameter
        saves the kinds of value the specific attribute contains.
        label_column(str): label attribute
        attribute_selection_method(function): function used to calculate impurity. (in this code, ID3)
    '''

    entropy = {}  # key: attribute, value: sum of data's entropy splitted by that attribute

    for attribute in attribute_list:
        entropy[attribute] = attribute_selection_method(data, attribute, label_column)

    # find the minimum entropy
    entropy = sorted(entropy.items(), key=lambda x: x[1])
    splitting_attribute = entropy[0][0]
    return splitting_attribute


def generate_decision_tree(data, attribute_list, label_column, attribute_selection_method):
    '''
    Generate a decision tree based on the data using an attribute selection method.
    
    Parameters:
        data(pandas.Dataframe): tablular data
        attribute_list(dict): key is attribute, value is list of unique values.
        this parameter is saving the kinds of value the specific attribute contains.
        label_column(str): label attribute
        attribute_selection_method(function): function used to calculate impurity. (in this code, ID3)
    '''
    
    node = Node()

    # samples in the data consists of only one class
    unique_label_value = data[label_column].unique()
    if len(unique_label_value) == 1:
        label = unique_label_value[0]
        node.set_label(label)
        return node
        
    # there is no splitting attribute
    if len(attribute_list) == 0:
        label = data[label_column].value_counts().index[0] # majority voting
        node.set_label(label)
        return node

    # find the best attribute to split node
    splitting_attribute = find_the_best_splitting_attribute(data, attribute_list, label_column, attribute_selection_method)
    node.set_splitting_attribute(splitting_attribute, attribute_list[splitting_attribute])

    # remove the selected splitting attribute from attribute list
    splitting_criteria = attribute_list.pop(splitting_attribute)

    # split the current node by the splitting criterion
    for criterion in splitting_criteria:
        row_idx = data[splitting_attribute] == criterion
        sub_data = data[row_idx].reset_index(drop=True)

        # splitted node is empty
        if sub_data.shape[0] == 0:
            label = data[label_column].value_counts().index[0] # majority voting 
            child_node = Node(isLeaf=True, label=label)
            node.attach_sibling(criterion, child_node)
        else:
            # recursive call starts
            # note: pass a copy of dictionary to the argument 
            node.attach_sibling(criterion, generate_decision_tree(sub_data, attribute_list.copy(), label_column, attribute_selection_method))

    return node


def predict_label(decision_tree, data):
    '''
    Predict data's label using decision tree.
    
    Parameters:
        decision_tree(Node): root node of decision tree
        data(dict): e,g, {'age': '<=30', 'income': 'high',,, 'Class:buys_computer': 'no'}
    '''

    node = decision_tree.check(data)

    while not node.is_leaf():
        node = node.check(data)

    return node.get_label()


def main():
    train_data_file = sys.argv[1]
    test_data_file = sys.argv[2]
    output_file = sys.argv[3]

    train_data = pd.read_csv(f'./data/{train_data_file}', sep='\t')
    test_data = pd.read_csv(f'./data/{test_data_file}', sep='\t')

    columns_without_label = train_data.columns[:-1].to_numpy()
    label_column = train_data.columns[-1]
    unique_values = []
    for col in columns_without_label:
        unique_values.append(train_data[col].unique())
    attribute_list = {col: vals for col, vals in zip(columns_without_label, unique_values)}

    # generate decision tree using train data
    dt = generate_decision_tree(train_data, attribute_list, label_column, ID3)

    # predict labels 
    predictions = []
    for i in range(test_data.shape[0]):
        row = test_data.iloc[i].to_dict()
        label = predict_label(dt, row)
        predictions.append(label)
    test_data[label_column] = predictions
    test_data.to_csv(output_file, index=False, sep='\t')


if __name__ == '__main__':
    main()