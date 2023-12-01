import sys
import logging
import os.path
import pathlib

import args

logging_dir = os.path.join(os.path.expanduser("~"), ".StardewSpeak", "logs")
pathlib.Path(logging_dir).mkdir(parents=True, exist_ok=True)

if args.args.named_pipe:
    sys.stderr = open(os.path.join(logging_dir, "err.txt"), "w")
    
logger = logging.getLogger('speech-client')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(os.path.join(logging_dir,'stardewspeak.log'), "w")
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


