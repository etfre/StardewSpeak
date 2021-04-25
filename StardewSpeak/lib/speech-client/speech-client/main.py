import winsound
import subprocess
import os.path
import os
import threading
import time
import logging
import sys
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import urllib.request

from dragonfly import RecognitionObserver, get_engine, AppContext
from dragonfly.log import setup_log
from srabuilder import sleep, environment
import srabuilder

import any_context, new_game_menu, shop_menu, container_menu, title_menu, load_game_menu, dialogue_menu, no_menu, any_menu, shipping_bin_menu, carpenter_menu, billboard_menu, geode_menu, museum_menu
import letter_viewer_menu, quest_log_menu, animal_query_menu, coop_menu, title_text_input_menu
from game_menu import game_menu, crafting_page, inventory_page, exit_page

MODELS_DIR = os.path.join(str(Path.home()), '.stardewspeak', 'models')

user_lexicon = (
    ("backspace", "b { k s p e I s"),
    ("crystalarium", "k r I s t V l { r i V m"),
    ("geode", "dZ i o U d"),
    ("glowstone", "g l o U s t o U n"),
    ("jack-o-lantern", "dZ { k o U l { n t 3 n"),
    ('joja', "dZ 'o U dZ 'V"),
    ("krobus", "k r o U b V s"),
    ("kwee", "k w i"),
    ("lamp-post", "l { m p p o U s t"),
    ("riverland", "r I v 3 l { n d"),
    ("stardrop", "s t A r d r A p"),
    ("x-ray", "E k s r e I"),
    ("yoba", "j o U b V"),
)


class Observer(RecognitionObserver):
    def on_begin(self):
        pass

    def on_recognition(self, words):
        import server
        server.log("Recognized:", " ".join(words), level=1)

    def on_failure(self):
        pass

def add_user_lexicon(model_dir: str):
    with open (os.path.join(model_dir, "user_lexicon.txt"), 'w') as f:
        for word, phonetics in user_lexicon:
            line = f'{word} {phonetics}\n'
            f.write(line)

def download_model(write_dir):
    import game
    model_url = 'https://github.com/daanzu/kaldi-active-grammar/releases/download/v1.8.0/kaldi_model_daanzu_20200905_1ep-biglm.zip'
    game.show_hud_message(f'Downloading speech recognition model. This may take a few minutes...', 2)
    url_open = urllib.request.urlopen(model_url)
    with ZipFile(BytesIO(url_open.read())) as my_zip_file:
        my_zip_file.extractall(write_dir)

def setup_engine(silence_timeout=500, models_dir=MODELS_DIR):
    # use abspath for model dir, this may change with app freezing
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(models_dir, "kaldi_model")
    if not os.path.isdir(model_dir):
        download_model(models_dir)
        add_user_lexicon(model_dir)
    # Set any configuration options here as keyword arguments.
    engine = get_engine(
        "kaldi",
        model_dir=model_dir,
        expected_error_rate_threshold=0.05,
        # tmp_dir='kaldi_tmp',  # default for temporary directory
        # vad_aggressiveness=3,  # default aggressiveness of VAD
        vad_padding_start_ms=0,  # default ms of required silence surrounding VAD
        vad_padding_end_ms=silence_timeout,  # default ms of required silence surrounding VAD
    )
    # Call connect() now that the engine configuration is set.
    engine.connect()
    return engine   

def run_engine():
    import game
    engine = get_engine()
    engine.prepare_for_recognition()
    game.show_hud_message('Speech recognition is ready', 4)
    try:
        engine.do_recognition()
    except KeyboardInterrupt:
        pass

def main(args):
    import server
    logging.basicConfig(level=logging.INFO)
    engine = setup_engine(silence_timeout=300)

    # Register a recognition observer
    observer = Observer()
    observer.register()

    sleep.load_sleep_wake_grammar(True)
    startdew_context = AppContext(title="stardew")
    server.setup_async_loop()
    map_contexts_to_builder = {
        (startdew_context,): any_context.rule_builder(),
    }
    srabuilder.load_environment_grammars(map_contexts_to_builder)
    new_game_menu.load_grammar()
    shop_menu.load_grammar()
    container_menu.load_grammar()
    game_menu.load_grammar()
    crafting_page.load_grammar()
    inventory_page.load_grammar()
    exit_page.load_grammar()
    title_menu.load_grammar()   
    load_game_menu.load_grammar()   
    dialogue_menu.load_grammar()   
    no_menu.load_grammar()   
    any_menu.load_grammar()
    shipping_bin_menu.load_grammar()
    carpenter_menu.load_grammar()
    billboard_menu.load_grammar()
    geode_menu.load_grammar()
    museum_menu.load_grammar()
    letter_viewer_menu.load_grammar()
    quest_log_menu.load_grammar()
    animal_query_menu.load_grammar()
    coop_menu.load_grammar()
    title_text_input_menu.load_grammar()
    run_engine()


if __name__ == "__main__":
    main(sys.argv[1:])
