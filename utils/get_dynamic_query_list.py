# функция, итерирующаяся по уровням и собирающая комбинации    
def iter_levels(hierarchy, keys_order, target_level, missed_levels, query_values, branch={}, level_num=0):
    if hierarchy is None:
        return []
    elif isinstance(hierarchy, list):
        if query_values[level_num] == 'None':
            branch[keys_order[level_num]] = hierarchy
        else:
            for val in hierarchy:
                if val == query_values[level_num]:
                    branch[keys_order[level_num]] = val
        return [branch]
                
    # критерий остановки - достижение уровня n
    if level_num == target_level:
            return [branch]
    
    answer = []
    # если уровень не определен - проводим поиск пути на данном уровне
    if level_num in missed_levels:
        for key in hierarchy.keys():
            # добавляем новую ветку в словарь-ответ
            new_branch = branch.copy()
            new_branch[keys_order[level_num]] = key
            
            answer += iter_levels(hierarchy[key], keys_order, target_level, missed_levels, query_values,
                                  new_branch, level_num+1)
    else:
        # значение на данном уровне
        val_list = query_values[level_num]
        
        if not isinstance(val_list, list):
            val_list = [val_list]
        
        if isinstance(hierarchy, dict):
            for val in val_list:
                # добавляем новую ветку в словарь-ответ
                new_branch = branch.copy()
                new_branch[keys_order[level_num]] = val
                
                # сначала добавляем ветку самого значения
                answer += iter_levels(hierarchy.get(val), keys_order, target_level, missed_levels, query_values,
                                        new_branch, level_num+1)
                # если оно вдруг None, пробегаемся по "вершинам" на том же уровне
                # и добавляем их значения в начало списка
                if val == 'None':
                    for key in hierarchy.keys():
                        if key != val:
                            # добавляем новую ветку в словарь-ответ
                            new_branch = branch.copy()
                            new_branch[keys_order[level_num]] = key
                            
                            answer = iter_levels(hierarchy[key], keys_order, target_level, 
                                                    missed_levels, query_values,
                                                    new_branch, level_num+1) + answer        
    return answer



def get_dynamic_query_list(hierarchy, query, keys_order):
    
    """ Функция, возвращающая список словарей всевозможных комбинаций 
    из соответсвующих значений переданного объекта

    Аргументы:
        hierarchy (dict): структура, по которой ведется поиск
        query (dict): запрос
        keys_order (list): порядок ключей в иерархии
    """    
    if not query:
        print('Был получен пустой запрос: None')
        return
    
    # создаем отсортированные списки значений по уровням
    query_values = [
        query[key] if key in query.keys() 
        else None
        for key in keys_order
    ]

    # создаем список номеров пропущенных уровней
    missed_levels = [
        level for level in range(len(keys_order))
        if keys_order[level] not in query.keys()
    ]

    # находим длину запроса
    n = len(query_values)
    # вызываем функцию прохождение дерева и возвращаем ее вывод
    return iter_levels(hierarchy, keys_order, n, missed_levels, query_values)