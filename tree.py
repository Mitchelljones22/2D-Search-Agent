from collections import deque


class SearchTree:  
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


# TEMPORARY: previews the tree before the real search exists.
# The search algorithm will replace this by calling add_child as it expands nodes.
def build_preview_tree(graph, root):  
    tree = SearchTree(root)  
    queue = deque([root])  
    while queue:  
        current = queue.popleft()  
        for neighbor in graph.neighbors(current):  
            if not tree.contains(neighbor):  
                tree.add_child(current, neighbor)  
                queue.append(neighbor)  
    return tree  