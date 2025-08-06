def get_query_list(hierarchy, query):
    """ Функция, возвращающая список словарей всевозможных комбинаций 
    из соответсвующих значений переданного объекта

    Аргументы:
        hierarchy (dict): структура, по которой ведется поиск
        query (dict): запрос
    """
    # список отсортированых по ключам значений
    values = [query[item] for item in sorted(query.keys())]
    
    if values[-1] == 'None':
        raise ValueError('driver не может быть None!')
    # ответ
    answer = []
    
    # функция, возвращающая последний не None списка, уровень рекурсии 
    # и флажок, показывающий наличие None в запросе
    def iter_levels(hierarchy, values, last_not_nan = None, level_num = 0, has_none = False):
        # критерий остановки рекурсии
        if level_num == len(values)-1 or not isinstance(hierarchy, dict) or len(hierarchy) == 0:
            return hierarchy, last_not_nan, level_num, has_none
        
        val = values[level_num]
        if val not in hierarchy:
            # ЗДЕСЬ ДОЛЖНО БЫТЬ ВОССТАНОВЛЕНИЕ ПУТИ ПРИ ПРОПУСКЕ УРОВНЯ 
            raise ValueError(f'Нет значения {val} на уровне {level_num} в json!')
        
        if val != 'None':
            last_not_nan = val
        else:
            has_none = True
        
        return iter_levels(hierarchy[val], values, last_not_nan, level_num+1, has_none)
    
    # находим последнее не None и уровень, на котором остановилась рекурсия
    new_hierarchy, last_not_nan, level_num, has_none = iter_levels(hierarchy, values)
    
    # если не блоы None - просто возвращаем запрошенное значение
    if not has_none:
        return new_hierarchy[values[-1]]
    
    
    # создаем копию переданной структуры
    new_hierarchy = hierarchy.copy()
    # сохраняем значения двух первых уровней
    level_not_nan = 1
    curr_val = values[level_not_nan]
    prev_val = values[level_not_nan-1]
    
    # циклом доходим до нужной иерархии (сверху последнего не None)
    while curr_val != last_not_nan:
        new_hierarchy = new_hierarchy[prev_val]
        level_not_nan = level_not_nan + 1
        
        prev_val = curr_val
        curr_val = values[level_not_nan]
        
    # создаем список значений данного уровня
    if isinstance(new_hierarchy, dict):
        item_list = new_hierarchy.keys()
    else:
        item_list = new_hierarchy
    # проходимся по значениям и добавляем их в ответ 
    for item in item_list:
        # дублируем словарь, чтобы не изменять исходный
        query_copy = query.copy()
        query_copy[f'lvl_{level_not_nan-1}'] = item
        answer.append(query_copy)
        
    return answer