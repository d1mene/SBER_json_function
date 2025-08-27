import numpy as np
import pandas as pd
from .fit_hierarchy import *
from .str_distance_metrics import *
from rapidfuzz import process, fuzz



def update_context_matrix(values_df, hierarchy, branch=set()): 
    if isinstance(hierarchy, dict):
        for key in hierarchy.keys():
            branch_copy = branch.copy()
            branch_copy.add(norm(key))
            update_context_matrix(values_df, hierarchy[key], branch_copy)
    elif isinstance(hierarchy, list):
        for val in hierarchy:
            branch_copy = branch.copy()
            branch_copy.add(norm(val))
            branch_copy = list(branch_copy)
            values_df.loc[branch_copy, branch_copy] = 1
    else:
        raise TypeError('Неправильный формат JSON!')
    
def check_context_compatibility(context_matrix, terms):    
    if not context_matrix.loc[terms, terms].all().all():
        print('Ошибка: Неверный контекст запроса!')
        return False
    return True
    
    
    
def get_query_token(query_terms, window=2):
    doc = []
    for i in range(len(query_terms)-window+1):
        token = query_terms[i]
        for j in range(1, window):
            token = ' '.join([token, query_terms[i+j]])
        doc.append(token)
    return doc

def long_fuzzy_match(query, candidate_long_terms, window=5, limit=5, score_cutoff_wratio=70, score_cutoff_dl=70):
    query = norm(query)
    query_windows = get_query_token(query.split(), window)
    print(query_windows)
    key_words = set()
    
    for i in range(len(query_windows)):
        matches = process.extract(query_windows[i], 
                                  candidate_long_terms, 
                                  scorer=fuzz.partial_token_set_ratio,
                                  score_cutoff=score_cutoff_wratio, 
                                  limit=limit)
        print(matches)
        
        if matches:
            matches_list = [m[0] for m in matches]
            # key_words.update(matches_list)
            
            
            sub_query_windows = get_query_token(query_windows[i].split(), max(len(m[0].split()) for m in matches))
            
            for j in range(len(sub_query_windows)):
                sub_matches = process.extract(sub_query_windows[j], 
                                        matches_list, 
                                        scorer=fuzz.token_set_ratio,
                                        score_cutoff=score_cutoff_dl, 
                                        limit=limit)
                if sub_matches:
                    print('Sub:', sub_matches)
                    key_words.update([m[0] for m in sub_matches])
                    
    return list(key_words)

def short_fuzzy_match(query, candidate_short_terms, limit=5, score_cutoff=70):
    query = norm(query)
    query_windows = query.split()
    print(query_windows)
    key_words = set()
    
    for word in query_windows:
        matches = process.extract(word, 
                                  candidate_short_terms, 
                                  scorer=jaro_winkler_scorer,
                                  score_cutoff=score_cutoff, 
                                  limit=limit)
        print(matches)
        
        if matches:
            matches_list = [m[0] for m in matches]
            key_words.update(matches_list)
                    
    return list(key_words)



def iter_path(query, hierarchy, final_terms, levels, lvl=0):
    if isinstance(hierarchy, dict):
        key_found = False
        
        for key in hierarchy.keys():
            if key in final_terms:
                query[levels[lvl]] = key
                iter_path(query, hierarchy[key], final_terms, levels, lvl+1)
                key_found = True
                break
                
        if not key_found:
            for key in hierarchy.keys():
                iter_path(query, hierarchy[key], final_terms, levels, lvl+1)

    elif isinstance(hierarchy, list):
        for val in hierarchy:
            if val in final_terms:
                query[levels[lvl]] = key
                break
    else:
        raise ValueError('Неправильный формат json!')
            

def build_path(final_terms, hierarchy, norm2keys, levels):
    query = {lvl: 'None' for lvl in levels}
    final_terms = [norm2keys[key] for key in final_terms]
    print(final_terms)
    iter_path(query, hierarchy, final_terms, levels, lvl=0)
    return query



def process_query(query, all_terms, norm2keys, hierarchy, levels):
    long_terms = [term for term in all_terms if len(term.split()) > 1]
    short_terms = [term for term in all_terms if len(term.split()) == 1]

    long_terms = long_fuzzy_match(query, long_terms, score_cutoff_wratio=70, score_cutoff_dl=81)
    print('---', long_terms)

    short_terms = short_fuzzy_match(query, short_terms, score_cutoff=90)
    print('---', short_terms)

    final_terms = long_terms + short_terms
    print('\nFINAL TERMS:', final_terms)
    
    json_values_df = pd.DataFrame(np.zeros((len(all_terms), len(all_terms))), index=all_terms, columns=all_terms)
    update_context_matrix(json_values_df, hierarchy)
    json_values_df
    
    if not check_context_compatibility(json_values_df, final_terms):
        return
    
    final_query = build_path(final_terms, hierarchy, norm2keys, levels)
    
    return final_query
    
    
    
    