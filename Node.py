
class Node:
    '''
    
    '''
    def __init__(self, node_obj):
        self.node_obj = node_obj # node object
        self.variables = [] # node variable (data)
        self.surs_ptr = [] # pointer to specific row in surrogate pool
        self.score = [] # score(category) the surrogate data belongs

        # *using list as there might be more than one value being read from one node(sensor)
    
    def add_var(self, var):
        #TODO: change to assignment instead
        self.variables.append(var)
    
    def add_surs_ptr(self, ptr):
        self.surs_ptr.append(ptr)
    
    def add_score(self, score):
        self.score.append(score)
    
    def update_surs_ptr(self, index, ptr):
        self.surs_ptr[index] = ptr

