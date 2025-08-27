import re
from collections import defaultdict, deque

# нормализуем строку
def norm(s: str) -> str:
    s = re.sub(r'/s+', ' ', s.strip().lower())

    punc_list = ['.', ',', '!', ':', '?', '/']

    for p in punc_list:
        s = s.replace(p, '')
    return s

def add_term(term2nodes, canonical, synonyms, node_id, kp):
        c = norm(canonical)
        term2nodes[c].add(node_id)
        # добавляем синонимы/аббревиатуры в KeywordProcessor
        for s in synonyms:
            kp.add_keyword(norm(s), c)

# функция получения синонимов   
def get_synonyms(key):
        return [p.strip() for p in key.split(';') if p.strip()]
    
def build_index(tree):
    all_terms = set()
    norm2keys = {}
    queue = deque([(k, tree) for k in tree.keys()])
    
    while queue:
        key, sub_tree = queue.popleft()
        
        if isinstance(sub_tree, dict):            
            norm_key = norm(key)
            all_terms.add(norm_key)
            norm2keys[norm_key] = key
            sub_tree = sub_tree[key]
            
            if isinstance(sub_tree, list):
                for val in sub_tree:
                    norm_val = norm(val)
                    all_terms.add(norm_val)
                    norm2keys[norm_val] = val
            else:
                queue += [(k, sub_tree) for k in sub_tree.keys()]           
        else:
            raise ValueError('Неправильный формат JSON!')
        
    return list(all_terms), norm2keys

def fit_hierarchy(hierarchy):
    all_terms, norm2keys = build_index(hierarchy)
    print(all_terms)
    print(norm2keys)
    return all_terms, norm2keys

