class SearchTree:  #inverted tree rooted at Start, grown by the search through add_child
    def __init__(self, root):  
        self.root = root  
        self.parent = {root: None}  
        self.children = {root: []}  
        self.depth = {root: 0}  

    def add_child(self, parent, child):  
        self.parent[child] = parent  
        self.children[parent].append(child)  
        self.children[child] = []  
        self.depth[child] = self.depth[parent] + 1  

    def contains(self, node):  
        return node in self.parent  

    def nodes(self):  
        return list(self.parent.keys())  

    def edges(self):  
        pairs = []  
        for parent, kids in self.children.items():  
            for child in kids:  
                pairs.append((parent, child))  
        return pairs  

    def path_to(self, node):   #follows parent links back to the root, returned root first
        path = []
        while node is not None:
            path.append(node)
            node = self.parent[node]
        path.reverse()
        return path
