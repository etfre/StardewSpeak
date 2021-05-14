import os
import dragonfly as df
from srabuilder import rules
import title_menu, menu_utils, server, df_utils, game, container_menu, server

DIALOGUE_BOX = 'dialogueBox'

map_word_to_phenomes = None

def generate_word_phenomes(word):
    i = 0
    l = len(word)
    phenomes = []
    while i <= l:
        match, match_length = get_phenome_match(word,i)
        match = [match] if isinstance(match, str) else match
        phenomes.extend(match)
        i += match_length
    return phenomes

def get_phenome_match(word, i):
    assert 0
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

def ensure_lexicons_loaded():
    global map_word_to_phenomes
    if map_word_to_phenomes is None:
        map_word_to_phenomes = {}
        for line in load_lexicons():
            spl = line.split()
            map_word_to_phenomes[spl[0]] = tuple(spl[1:])
    

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

async def do_dictation(text):
    ensure_lexicons_loaded()
    menu = await get_dialogue_menu()
    text_phenomes = get_phenomes(text.lower())
    phenomes = [get_phenomes(x['responseText'].lower()) for x in menu['responses']]
    if phenomes:
        scores = [(string_similarity(x, text_phenomes), i) for (i, x) in enumerate(phenomes)]
        scores.sort(key=lambda x: x[0])
        top_score, top_index = scores[-1]
        if top_score:
            if len(scores) == 1 or top_score > scores[-2][0]:
                await menu_utils.click_component(menu['responseCC'][top_index])

async def get_dialogue_menu():
    return await menu_utils.get_active_menu(DIALOGUE_BOX)

async def focus_item(idx):
    menu = await get_dialogue_menu()
    server.log(menu)
    await menu_utils.click_component(menu['responseCC'][idx])

mapping = {
    "(item | response) <positive_index>": df_utils.async_action(focus_item, 'positive_index'),
    "<dictation>": df_utils.async_action(do_dictation, 'dictation')
}

@menu_utils.valid_menu_test
def is_active():
    game.get_context_menu(DIALOGUE_BOX)

def load_grammar():
    grammar = df.Grammar("dialogue_menu")
    main_rule = df.MappingRule(
        name="dialogue_menu_rule",
        mapping=mapping,
        extras=[rules.num, df_utils.positive_index, df_utils.positive_num, df.Dictation("dictation")],
        context=is_active,
        defaults={'positive_num': 1},
    )
    grammar.add_rule(main_rule)
    grammar.load()
    