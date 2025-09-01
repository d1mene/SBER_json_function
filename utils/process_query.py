import numpy as np
import pandas as pd
from .fit_hierarchy import *
from .str_distance_metrics import *
from rapidfuzz import process, fuzz



def update_context_matrix(values_df, hierarchy, branch=set()):
    """Функция, наполняющая матрицу контекста в соответствие иерархии

   Аргументы:
        values_df (pd.DataFrame): сопряженная матрица всех ключей иерархии
        hierarchy (dict): иерархия
        branch (set): ветка контекста. 

    Raises:
        TypeError: Неверный формат JSON
    """
    
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

# функция, проверяющая контекст запроса
def check_context_compatibility(context_matrix, terms): 
    if not terms or not context_matrix.loc[terms, terms].all().all():
        return False
    return True


def update_similarity_matrix(values_df, scorer):
    """Функция, наполняющая матрицу схожести слов

   Аргументы:
        values_df (pd.DataFrame): сопряженная матрица всех ключей иерархии
        hierarchy (dict): иерархия
        branch (set): ветка контекста. 

    Raises:
        TypeError: Неверный формат JSON
    """
    terms = list(values_df.columns)
    
    for col in values_df.columns:
        matches=process.extract(col, terms, scorer=scorer, limit=None)
        matches = pd.Series([m[1] for m in matches], index=[m[0] for m in matches])
        values_df[col] = matches
    
    return values_df
    
def check_similarity_compatibility(similarity_matrix, query, terms, threshold):
    """Функция, разрешающая конфликты между полученными запросами.

    Аргументы:
        similarity_matrix (pd.DataFrame): матрица схожести
        query (str): исходный запрос
        terms (list): список терминов для проверки
        threshold (int): порог показателя схожести

    Returns:
        list: список терминов с разрешенным конфликтом
    """
    final_terms = []
    sim_issue = (similarity_matrix >= threshold).sum().sum() > similarity_matrix.shape[0]
    
    if sim_issue:
        sim_df = similarity_matrix.loc[terms, terms]
        sim_df = sim_df[sim_df > threshold]
        print(sim_df)
        sim_list = [list(sim_df[key].dropna().index) for key in sim_df.columns]
        used_list = []
        print(sim_list)
        for keys in sim_list:
            if len(keys) < 2:
                used_list.append(keys)
                final_terms.append(keys[0])
                continue
            
            if keys not in used_list:
                scorer_rank = process.extract(query, keys, scorer=damerau_levenshtein_scorer, score_cutoff=0, limit=None)
                print(scorer_rank)
                if len(scorer_rank) >= 2 and scorer_rank[0][1] - scorer_rank[1][1] < 2:
                    print('Ошибка: Неоднозначный запрос. Пожалуйста, исправьте опечатки или уточните Ваш запрос.')
                    return
                used_list.append(keys)
                final_terms.append(scorer_rank[0][0])

    return list(set(final_terms))


    
    
# функция для возврата токенов размером window слов
def get_query_token(query_terms, window=2):
    doc = []
    for i in range(len(query_terms)-window+1):
        token = query_terms[i]
        for j in range(1, window):
            token = ' '.join([token, query_terms[i+j]])
        doc.append(token)
    return doc

# функция для мэтча длинных ключей
def long_fuzzy_match(query, candidate_long_terms, long_scorer_first=fuzz.partial_token_set_ratio, 
                     long_scorer_second=fuzz.token_set_ratio, window=5, limit=5, 
                     score_cutoff_first=70, score_cutoff_second=70):
    
    query = norm(query)
    query_windows = get_query_token(query.split(), window)
    print(query_windows)
    key_words = set()
    
    for i in range(len(query_windows)):
        matches = process.extract(query_windows[i], 
                                  candidate_long_terms, 
                                  scorer=long_scorer_first,
                                  score_cutoff=score_cutoff_first, 
                                  limit=limit)
        print(matches)
        
        if matches:
            matches_list = [m[0] for m in matches]
            sub_query_windows = get_query_token(query_windows[i].split(), max(len(m[0].split()) for m in matches))
            
            for j in range(len(sub_query_windows)):
                sub_matches = process.extract(sub_query_windows[j], 
                                        matches_list, 
                                        scorer=long_scorer_second,
                                        score_cutoff=score_cutoff_second, 
                                        limit=limit)
                if sub_matches:
                    print('Sub:', sub_matches)
                    key_words.update([m[0] for m in sub_matches])
                    
    return list(key_words)

# функция для мэтча коротких ключей
def short_fuzzy_match(query, candidate_short_terms, short_scorer=jaro_winkler_scorer, limit=5, score_cutoff=70):
    query = norm(query)
    query_windows = query.split()
    print(query_windows)
    key_words = set()
    
    for word in query_windows:
        matches = process.extract(word, 
                                  candidate_short_terms, 
                                  scorer=short_scorer,
                                  score_cutoff=score_cutoff, 
                                  limit=limit)
        print(matches)
        
        if matches:
            matches_list = [m[0] for m in matches]
            key_words.update(matches_list)
                    
    return list(key_words)


# вспомогательная функция для создания запроса
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
                query[levels[lvl]] = val
                break
    else:
        raise ValueError('Неправильный формат json!')
            
# функция, составляющая конечный запрос
def build_path(final_terms, hierarchy, norm2keys, levels):
    query = {lvl: 'None' for lvl in levels}
    final_terms = [norm2keys[key] for key in final_terms]
    print(final_terms)
    iter_path(query, hierarchy, final_terms, levels, lvl=0)
    return query



def process_query(query, all_terms, norm2keys, hierarchy, levels,
                  long_score_cutoff_first=70, long_score_cutoff_second=81, short_score_cutoff=90, window=5,
                  long_scorer_first=fuzz.partial_token_set_ratio, long_scorer_second=fuzz.token_set_ratio,
                  short_scorer=jaro_winkler_scorer, sim_threshold=70, sim_scorer=damerau_levenshtein_scorer):
    
    """Функция, обрабатывающая входящий query. 
    Для корректной работы нужно сначала получить all_terms и norm2keys,
    используя метод fit_hierarchy на нужной иерархии.

    Аргументы:
        query (str): входящий запрос для обработки.
        all_terms (list): список всех значений (нормализованных).
        norm2keys (dict): словарь "нормализованный ключ - значение".
        hierarchy (dict): структура, по которой ведется поиск.
        levels (list): названия уровней.
        long_score_cutoff_first (int, optional): Порог для первой функции обработки длинных ключей (по умолчанию 70).
        long_score_cutoff_second (int, optional): Порог для второй функции обработки длинных ключей (по умолчанию 81).
        short_score_cutoff (int, optional): Порог для функции обработки коротких ключей (по умочланию 90).
        window (int, optional): Размер окна для обработки длинных ключей (по умолчанию 5).
        long_scorer_first (func(s1: str, s2: str, score_cutoff=int), optional): 
            Скорер для первого обхода запроса в поиске длинных ключей (по умолчанию fuzz.partial_token_set_ratio).
        long_scorer_second (func(s1: str, s2: str, score_cutoff=int), optional): 
            Скорер для второго обхода запроса в поиске длинных ключей (по умолчанию fuzz.token_set_ratio).
        short_scorer (func(s1: str, s2: str, score_cutoff=int), optional): 
            Скорер для обхода запроса в поиске коротких ключей (по умолчанию jaro_winkler_scorer).
        sim_threshold (int, optional): Порог для меры схожести двух ключей (по умолчанию 70)
        sim_scorer (func(s1: str, s2: str, score_cutoff=int), optional): 
            Скорер для функции схожести ключей (по умолчанию damerau_levenshtein_scorer)

    Возвращает:
        dict: словарь с заполненными уровнями, если поступил правильный запрос
        None: пустое значение, если поступил неверный запрос
    """
    
    long_terms = [term for term in all_terms if len(term.split()) > 1]
    short_terms = [term for term in all_terms if len(term.split()) == 1]

    long_terms = long_fuzzy_match(query, 
                                  long_terms, 
                                  window=window, 
                                  long_scorer_first=long_scorer_first, 
                                  long_scorer_second=long_scorer_second,
                                  score_cutoff_first=long_score_cutoff_first,
                                  score_cutoff_second=long_score_cutoff_second)
    print('---', long_terms)

    short_terms = short_fuzzy_match(query, short_terms, short_scorer=short_scorer, score_cutoff=short_score_cutoff)
    print('---', short_terms)

    chosen_terms = long_terms + short_terms
    print('\nCHOSEN TERMS:', chosen_terms)
    if not chosen_terms:
        print('Не найдены ключевые слова. Пожалуйста, уточните Ваш запрос.')
        return
    
    json_values_df = pd.DataFrame(np.zeros((len(all_terms), len(all_terms))), index=all_terms, columns=all_terms)
    update_context_matrix(json_values_df, hierarchy)
    
    if not check_context_compatibility(json_values_df, chosen_terms):
        similarity_matrix = json_values_df.copy()
        update_similarity_matrix(similarity_matrix, sim_scorer)
        
        chosen_terms = check_similarity_compatibility(similarity_matrix, query, chosen_terms, threshold=sim_threshold)
        
        if not check_context_compatibility(json_values_df, chosen_terms):
            print('Ошибка: Неверный контекст запроса!')
            return
    print('\nFINAL TERMS:', chosen_terms)
    
    final_query = build_path(chosen_terms, hierarchy, norm2keys, levels)
    
    return final_query
    
    
    
    