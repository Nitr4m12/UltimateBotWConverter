from pathlib import Path
from bcml.install import open_mod
from bcml.dev import convert_mod
from bcml import util
from subprocess import run
from os.path import sep, splitext
from glob import glob
from urllib.request import urlopen, urlretrieve
from io import BytesIO
from zipfile import ZipFile
from oead import byml, S32
from platform import system 
from RepackBars import repack_bars

import shutil
import bars_extractor as barstool
import bcfconverter as sound
import argparse
import bfstpfixer

# Construct an argument parser
parser = argparse.ArgumentParser(description="Converts mods in BNP format using BCML's converter, complemented by some additional tools")
parser.add_argument("mods", nargs='+')
args = parser.parse_args()

# supp_formats = ['sbfres', 'sbitemico', 'hkcl', 'hkrg', 'bars', 'bfstm', 'instSize']

def convertFres(file):
    # Convert sbfres files
    if not Path('BfresPlatformConverter').exists():
        # Code adapted from https://gist.github.com/hantoine/c4fc70b32c2d163f604a8dc2a050d5f6
        # Extract BfresPlatformConverter if it's not already in the system
        print("Downloading BfresPlatformConverter...")
        http_response = urlopen('https://gamebanana.com/dl/485626')
        zipfile = ZipFile(BytesIO(http_response.read()))
        zipfile.extractall(path='BfresPlatformConverter')
    if system() == "Windows":
        run(["BfresPlatformConverter\BfresPlatformConverter.exe", file])
    else:
        run(['mono', "BfresPlatformConverter/BfresPlatformConverter.exe", file])
    if file.suffixes == ['.Tex1', '.sbfres']:
        file.unlink()
        shutil.move(f"SwitchConverted{sep}{file.stem.split('.')[0]}.Tex.sbfres", f"{file.parent}{sep}")
        Path(f"{file.parent}{sep}{file.stem.split('.')[0]}.Tex2.sbfres").unlink()
    elif file.suffixes == ['.sbfres'] or file.suffix == ".sbitemico":
        file.unlink()
        shutil.move(f"SwitchConverted{sep}{file.name}", f"{file}")

def convertHavok(file, mod_root):
    # Convert havok files unsupported by BCML
    if not Path('HKXConvert').exists():
        # Download HKXConvert if it's not already in the system
        print("Downloading HKXConvert...")
        filename, headers = urlretrieve('https://github.com/krenyy/HKXConvert/releases/download/1.0.1/HKXConvert', filename='HKXConvert')
        Path('HKXConvert').chmod(0o755)
    run(['sarc', 'extract', file])
    hkxs = mod_root.glob(f'**{sep}*.hk*')
    for hkx in hkxs:
        run([f'.{sep}HKXConvert', 'hkx2json', hkx])
        hkx.unlink()
        run([f'.{sep}HKXConvert', 'json2hkx', '--nx', f'{splitext(hkx)[0]}.json'])
        Path(f'{splitext(hkx)[0]}.json').unlink()
    if hkxs:
        print("HKX files converted. Saving...")
        run(['sarc', 'create', f'{splitext(file)[0]}', file])
    shutil.rmtree(f'{splitext(file)[0]}')

def convertInstS(ainfo):
    # Convert any instSize entries, if any are modified
    actorinfo = byml.from_text(open(ainfo, "r", encoding="utf-8").read()) 
    for _, actor in actorinfo.items():
        if "instSize" in actor:
            actor["instSize"] = S32(int(actor["instSize"].v * 1.6)) 
    open(ainfo, "w", encoding="utf-8").write(byml.to_text(actorinfo))

def convertBars(file, mod_root):
    # Convert bars files, and their files inside
    oBars = util.get_game_file(f"Voice{sep}USen{sep}{file.name}")
    barstool.extract_from_bars(file, '>')
    bfstps = mod_root.glob(f'**{sep}*.bfstp')
    bfwavs = mod_root.glob(f'**{sep}*.bfwav')
    for bfstp in bfstps:
        sound.convExtFile(bfstp, 'FSTP', '<')
        bfstpfixer.fix(bfstp)
    for bfwav in bfwavs:
        sound.convExtFile(bfwav, 'FWAV', '<')
    shutil.copy2(f'{oBars}', file)
    shutil.move(f'{splitext(file)[0]}_extracted', f'{file.parent}{sep}new')
    barstool.extract_from_bars(file, '<')
    repack_bars(file, f'{splitext(file)[0]}_extracted', f'{file.parent}{sep}new')
    shutil.rmtree(f'{splitext(file)[0]}_extracted')
    shutil.rmtree(f'{file.parent}{sep}new')

def converter(mod):
    try:
        bnp = Path(mod)
        mod_path = open_mod(bnp)
        files = mod_path.glob(f'**{sep}*.*')
        game_path = util.get_game_dir()
        # Run the mod through BCML's automatic converter first 
        warnings = convert_mod(mod_path, False, True)
        for file in files:
            if file.suffix == ".sbfres" or file.suffix == ".sbitemico":
                convertFres(file)
            elif file.suffix == ".sbactorpack":
                actorfiles = run(['sarc', 'list', file], capture_output=True, text=True)
                if 'hkcl' in actorfiles.stdout:
                    convertHavok(file, mod_path)
            elif file.suffix == ".bars":
                convertBars(file, mod_path)
            elif file.suffix == ".bfstm":
                # Convert BFSTM files
                sound.convExtFile(file, "FSTM", '<')
            elif file.name == "actorinfo.yml":
                convertInstS(file)
        out = bnp.with_name(f"{bnp.stem}_switch.bnp")
        x_args = [
            util.get_7z_path(),
            "a",
            out,
            f'{str(mod_path / "*")}',
        ]
        run(x_args)
    except RuntimeError as e:
        shutil.rmtree(mod_path, ignore_errors=True)
        if Path('HKXConvert').exists():
            Path('HKXConvert').unlink()
        shutil.rmtree('SwitchConverted', ignore_errors=True)
        shutil.rmtree('WiiUConverted', ignore_errors=True)
        shutil.rmtree('BfresPlatformConverter', ignore_errors=True)
        print(e)

    shutil.rmtree(mod_path, ignore_errors=True)
    if Path('HKXConvert').exists():
        Path('HKXConvert').unlink()
    shutil.rmtree('SwitchConverted', ignore_errors=True)
    shutil.rmtree('WiiUConverted', ignore_errors=True)
    shutil.rmtree('BfresPlatformConverter', ignore_errors=True)
    # if warnings:
    #     with open("error.log", "w") as file:
    #         for warning in warnings:
    #             # Write BCML's warning to a file
    #             if type(warning) == list:
    #                 for error in warning:
    #                     if any(i not in error for i in supp_formats):
    #                         file.write(error + "\n")
    #                 continue
    #             if any(i not in warning for i in supp_formats):
    #                 file.write(warning + "\n")

def main():
    if len(args.mods) == 1: # one argument
        mods = glob(args.mods[0])
    else: # more than one argument
    	mods = args.mods
    
    for mod in mods:
        try:
            converter(mod)
        except RuntimeError as e:
            print(e)


if __name__ == "__main__":
    main()
            
