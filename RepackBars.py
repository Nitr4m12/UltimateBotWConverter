# Aaaboy97 2018
# Modified by Nitr4m12


import os
import shutil

def repack_bars(bars, old, new):
    f_name, f_ext = os.path.splitext(str(bars))
    newBars = open(bars, 'r+b')
    full = newBars.read()

    for file in os.listdir(old):
        sound = open(f'{old}{os.sep}{file}', 'rb')
        orig = sound.read()
        sound.close()

        try:
            sound2 = open(f'{new}{os.sep}{file}', 'rb')
            repl = sound2.read()
            sound2.close()
        except:
            print('No new file for ' + file + ', skipping...')
            continue

        if len(orig) > len(repl):
            repl = repl + b'\x00'*(len(orig) - len(repl))
        elif len(orig) < len(repl):
            print('New file ' + file + ' larger than original, skipping...')
            continue

        offset = full.find(orig)
        if offset != -1:
            newBars.seek(full.find(orig))
            newBars.write(repl)
            print(file + ' was succesfully written')
        else:
            print(file + ' was not found in original bars, skipping...')

    newBars.close()
    print(f'Succesfully written to {bars.name}')
