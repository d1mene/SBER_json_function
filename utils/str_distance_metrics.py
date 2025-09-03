def damerau_levenshtein_distance(s1, s2):
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in range(-1,lenstr1+1):
        d[(i,-1)] = i+1
    for j in range(-1,lenstr2+1):
        d[(-1,j)] = j+1
 
    for i in range(lenstr1):
        for j in range(lenstr2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1
            d[(i,j)] = min(
                           d[(i-1,j)] + 1, 
                           d[(i,j-1)] + 1,
                           d[(i-1,j-1)] + cost,
                          )
            if i and j and s1[i] == s2[j-1] and s1[i-1] == s2[j]:
                d[(i,j)] = min(d[(i,j)], d[i-2,j-2] + 1)
 
    return d[lenstr1-1,lenstr2-1]

def damerau_levenshtein_scorer(s1, s2, score_cutoff = 0):
    d = damerau_levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    
    if max_len == 0:
        score = 100
    else:
        score = (1-d/max_len)*100
    
    if score_cutoff and score < score_cutoff:
        score = 0
    
    return score

def jaro_winkler_scorer(s1, s2, p=0.1, score_cutoff = 0):
    s1_len, s2_len = len(s1), len(s2)
    
    if s1_len == 0 and s2_len == 0:
        return 1.0
    if s1_len == 0 or s2_len == 0:
        return 0.0

    match_distance = max(s1_len, s2_len) // 2 - 1

    s1_matches = [False] * s1_len
    s2_matches = [False] * s2_len

    matches = 0
    transpositions = 0

    # Находим совпадения
    for i in range(s1_len):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, s2_len)
        
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    s1_match_chars = [s1[i] for i in range(s1_len) if s1_matches[i]]
    s2_match_chars = [s2[j] for j in range(s2_len) if s2_matches[j]]
    
    for c1, c2 in zip(s1_match_chars, s2_match_chars):
        if c1 != c2:
            transpositions += 1
    transpositions /= 2

    # расстояние Джаро
    jaro = (
        (matches / s1_len +
         matches / s2_len +
         (matches - transpositions) / matches) / 3
    )

    # префикс (макс 4 символа)
    prefix = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            prefix += 1
        else:
            break
        if prefix == 4:
            break
    # расстояние Джаро-Винклера
    d_w = (jaro + prefix * p * (1 - jaro))*100
    
    if score_cutoff and d_w < score_cutoff:
        return 0.0
    
    return d_w