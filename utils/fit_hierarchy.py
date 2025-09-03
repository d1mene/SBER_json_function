import re
from collections import defaultdict, deque

# нормализуем строку
def norm(s: str) -> str:
    s = re.sub(r'/s+', ' ', s.strip().lower())

    punc_list = ['.', ',', '!', ':', '?', '/']

    for p in punc_list:
        s = s.replace(p, '')
    return s

# функция получения синонимов   
def get_synonyms(key):
        return [p.strip() for p in key.split(';') if p.strip()]

# функция нахождения списка всех терминов и словаря "нормализованный ключ - исходный ключ" 
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
    """Обход дерева для получения информации о нем

    Аргументы:
        hierarchy (dict): иерархия

    Возвращает:
        list: список всех нормализованных ключей иерархии
        dict: словарь "нормализованный ключ - исходный ключ"
    """
    all_terms, norm2keys = build_index(hierarchy)
    return all_terms, norm2keys

