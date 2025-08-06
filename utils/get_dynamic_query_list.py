def get_dynamic_query_list(hierarchy, query):
    """ Функция, возвращающая список словарей всевозможных комбинаций 
    из соответсвующих значений переданного объекта

    Аргументы:
        hierarchy (dict): структура, по которой ведется поиск
        query (dict): запрос
    """
    # функция, итерирующаяся по уровням и собирающая комбинации
    def iter_levels(hierarchy, target_level, branch=[], level_num=0):
        # критерий остановки - достижение уровня n
        if level_num == target_level:
            driver = branch[-1]
            # на всякий случай - если показания счетчика нечисловые
            if isinstance(hierarchy, dict):
                return [dict(zip(query_keys, branch))]
            return []
        
        answer = []
        # значение на данном уровне
        val = query_values[level_num]
        
        if isinstance(hierarchy, dict) and val in hierarchy:
            # сначала добавляем ветку самого значения
            answer += iter_levels(hierarchy[val], target_level, branch+[val], level_num+1) + answer
            # если оно вдруг None, пробегаемся по "вершинам" на том же уровне
            # и добавляем их значения в начало списка
            if val == 'None':
                for key in hierarchy.keys():
                    if key != val:
                        answer = iter_levels(hierarchy[key], target_level, branch+[key], level_num+1)\
                                + answer

        
        return answer
    # создаем отсортированные списки ключей и значений
    query_keys = sorted(query.keys(), key=lambda x: int(x.split('_')[1]))
    query_values = [query[key] for key in query_keys]
    # находим длину
    n = len(query_keys)
    # вызываем функцию и возвращаем ее вывод
    return iter_levels(hierarchy, n)