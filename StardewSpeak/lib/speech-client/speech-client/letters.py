from srabuilder.actions import pydirectinput
import dragonfly as df
import server
import time

letter_map = {
    "(alpha)": "a",
    "(bravo) ": "b",
    "(charlie) ": "c",
    "(danger) ": "d",
    "(eureka) ": "e",
    "(foxtrot) ": "f",
    "(gorilla) ": "g",
    "(hotel) ": "h",
    "(india) ": "i",
    "(juliet) ": "j",
    "(kilo) ": "k",
    "(lima) ": "l",
    "(michael) ": "m",
    "(november) ": "n",
    "(Oscar) ": "o",
    "(papa) ": "p",
    "(quiet) ": "q",
    "(romeo) ": "r",
    "(sierra) ": "s",
    "(tango) ": "t",
    "(uniform) ": "u",
    "(victor) ": "v",
    "(whiskey) ": "w",
    "(x-ray) ": "x",
    "(yankee) ": "y",
    "(zulu) ": "z",
}

letters_rep = df.Repetition(df.Choice(None, letter_map), name="letters", min=1, max=16)
letters = df.Modifier(letters_rep, lambda rep: "".join(map(str, rep)))

def type_letters(letters: str):
    shift_down = False
    for char in letters:
        server.log(char)
        shift_char = char.isupper()
        char = char.lower()
        if shift_char and not shift_down:
            pydirectinput.keyDown('shift')
            shift_down = True
        elif not shift_char and shift_down:
            pydirectinput.keyUp('shift')
            shift_down = False
        pydirectinput.press(char)
    if shift_down:
        pydirectinput.keyUp('shift')