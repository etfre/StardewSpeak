import os
import dragonfly as df

def do_match(text: str, options, threshold=0.1):
    text_phenomes = get_phenomes(text.lower())
    phenomes = [get_phenomes(x.lower()) for x in options]
    if phenomes:
        scores = [(string_similarity(x, text_phenomes), i) for (i, x) in enumerate(phenomes)]
        top_score, top_index = max(scores, key=lambda x: x[0])
        if top_score > threshold:
            return top_index

def generate_word_phenomes(word):
    i = 0
    l = len(word)
    phenomes = []
    while i < l:
        if not word[i].isalpha():
            i += 1
            continue
        match, match_length = get_phenome_match(word,i)
        match = [match] if isinstance(match, str) else match
        phenomes.extend(match)
        i += match_length
    return phenomes

def get_phenome_match(word, i):
    import server
    server.log(word)
    char = word[i]
    char2 = word[i:i+2]
    if char == 'a':
        return "'{", 1
    elif char2 in ('bb', 'dd', 'pp'):
        return char, 2
    elif char2 == 'th':
        return 'T', 2
    else:
        return char, 1

def load_lexicons():
    import main
    paths = [
        os.path.join(main.MODELS_DIR, 'kaldi_model', 'lexicon.txt'),
        os.path.join(main.MODELS_DIR, 'kaldi_model', 'user_lexicon.txt'),
    ]
    for path in paths:
        with open(path, encoding='utf-8') as f:
            for line in f:
                if line:
                    yield line

def get_phenomes(s: str):
    words = s.split()
    phenomes = []
    for word in words:
        if word in map_word_to_phenomes:
            word_phenomes = map_word_to_phenomes[word]
        else:
            word_phenomes = generate_word_phenomes(word)
            map_word_to_phenomes[word] = word_phenomes
        phenomes.extend(word_phenomes)
    return phenomes

def get_bigrams(s: str):
    '''
    Takes a string and returns a list of bigrams
    '''
    return {tuple(s[i:i+2]) for i in range(len(s) - 1)}

def string_similarity(str1, str2):
    '''
    Perform bigram comparison between two strings
    and return a percentage match in decimal form
    '''
    pairs1 = get_bigrams(str1)
    pairs2 = get_bigrams(str2)
    return (2.0 * len(pairs1 & pairs2)) / (len(pairs1) + len(pairs2))

map_word_to_phenomes = {}
for line in load_lexicons():
    spl = line.split()
    map_word_to_phenomes[spl[0]] = tuple(spl[1:])