import winsound
import shutil
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
import shlex
import argparse

from dragonfly import RecognitionObserver, get_engine, AppContext
from dragonfly.log import setup_log
from srabuilder import sleep, environment
import srabuilder

import any_context, new_game_menu, shop_menu, container_menu, title_menu, load_game_menu, dialogue_menu, no_menu, any_menu, shipping_bin_menu, carpenter_menu, billboard_menu, geode_menu, museum_menu
import letter_viewer_menu, quest_log_menu, animal_query_menu, coop_menu, title_text_input_menu, cutscene, level_up_menu, shipped_items_menu, fishing_menu
import locations
from game_menu import game_menu, crafting_page, inventory_page, exit_page

IS_FROZEN = getattr(sys, 'frozen', False)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--main', default=__file__,help='Path of main file, needed when script is invoked by Stardew Valley')
parser.add_argument('--model_dir', default=None, help='Model directory')
args = parser.parse_args()

def find_model_dir():
    current_dir = os.path.join(os.path.dirname(__file__))
    return os.path.join(current_dir, '..', 'models')
    

MODELS_DIR = args.model_dir or find_model_dir()

user_lexicon = (
    ('joja', "dZ 'o U dZ 'V"),
)


class Observer(RecognitionObserver):
    def on_begin(self):
        pass

    def on_recognition(self, words):
        import server
        server.log("Recognized:", " ".join(words), level=1)

    def on_failure(self):
        pass

def add_base_user_lexicon(model_dir: str):
    import df_utils
    dst = os.path.join(model_dir, "user_lexicon.txt")
    shutil.copyfile(df_utils.lexicon_source_path(), dst)

def download_model(write_dir):
    import game
    model_url = 'https://github.com/daanzu/kaldi-active-grammar/releases/download/v1.8.0/kaldi_model_daanzu_20200905_1ep-biglm.zip'
    game.show_hud_message(f'Downloading speech recognition model. This may take a few minutes...', 2)
    url_open = urllib.request.urlopen(model_url)
    with ZipFile(BytesIO(url_open.read())) as my_zip_file:
        my_zip_file.extractall(write_dir)
    shutil.rmtree(os.path.join(write_dir, "kaldi_model.tmp"), ignore_errors=True)


def setup_engine(silence_timeout, model_dir):
    if not os.path.isdir(model_dir):
        if IS_FROZEN:
            raise RuntimeError(f"Cannot find kaldi model at {os.path.abspath(model_dir)} using executable path {__file__}")
        download_model(MODELS_DIR)
        add_base_user_lexicon(model_dir)
    # Set any configuration options here as keyword arguments.
    engine = get_engine(
        "kaldi",
        model_dir=model_dir,
        expected_error_rate_threshold=0,
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
    model_dir = os.path.join(MODELS_DIR, "kaldi_model")
    engine = setup_engine(300, model_dir)

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
    locations.load_grammar()
    cutscene.load_grammar()
    level_up_menu.load_grammar()
    shipped_items_menu.load_grammar()
    fishing_menu.load_grammar()
    if not IS_FROZEN:
        src = os.path.join(model_dir, "user_lexicon.txt")
        dst = os.path.join(os.path.abspath(__file__), "..", "..", "user_lexicon.txt")
        shutil.copyfile(src, dst)
    run_engine()


if __name__ == "__main__":
    main(sys.argv[1:])
