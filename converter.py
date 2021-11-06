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
from platform import system 
from RepackBars import repack_bars
from bflim_convertor import bntx_dds_injector as bntx
from time import sleep

import shutil
import bars_extractor as barstool
import bcfconverter as sound
import argparse
import bfstpfixer
import oead
import traceback


# Construct an argument parser
parser = argparse.ArgumentParser(description="Converts mods in BNP format using BCML's converter, complemented by some additional tools")
parser.add_argument("mods", nargs='+')
args = parser.parse_args()

# Supported formats
supp_formats = [".sbfres", ".sbitemico", ".hkcl", ".bars", ".bfstm", ".bflim", ".sblarc"]

def confirm_prompt(question: str) -> bool:
    # https://gist.github.com/garrettdreyfus/8153571
    reply = None
    while reply not in ("", "y", "n"):
        reply = input(f"{question} (Y/n): ").lower()
    return (reply in ("", "y"))

def extract_sarc(sarc: oead.Sarc, sarc_path: Path) -> None:
    Path(sarc_path).mkdir(exist_ok=True)
    for file in sarc.get_files():
        if not Path(sarc_path / file.name).parent.exists():
            Path(sarc_path / file.name).parent.mkdir(parents=True)
        Path(sarc_path / file.name).write_bytes(file.data)

def write_sarc(sarc: oead.Sarc, sarc_path: Path, sarc_file: Path) -> None:
    # Write the modified files back to the sarc
    new_sarc = oead.SarcWriter(endian=oead.Endianness.Little)
    for file in sarc_path.rglob("*.*"):
        new_file = f'{file}'.split(f"{sarc_file.name}{sep}")[1]
        new_sarc.files[new_file] = file.read_bytes()
    if sarc_file.suffix == ".pack":
        sarc_file.write_bytes(new_sarc.write()[1])
    else:
        sarc_file.write_bytes(oead.yaz0.compress(new_sarc.write()[1]))

def convert_fres(sbfres: Path) -> None:
    # Convert sbfres files
    if not Path('BfresPlatformConverter').exists():
        # Code adapted from https://gist.github.com/hantoine/c4fc70b32c2d163f604a8dc2a050d5f6
        # Extract BfresPlatformConverter if it's not already in the system
        print("Downloading BfresPlatformConverter...")
        http_response = urlopen('https://gamebanana.com/dl/485626')
        zipfile = ZipFile(BytesIO(http_response.read()))
        zipfile.extractall(path='BfresPlatformConverter')

    if sbfres.suffixes == ['.Tex1', '.sbfres']:
        bfres = util.unyaz_if_needed(sbfres.read_bytes())
        tex2 = Path(f'{sbfres.parent}{sep}{sbfres.name.split(".")[0]}.Tex2.sbfres')
        if Path(f'{sbfres.parent}{sep}{sbfres.name.split(".")[0]}.Tex2.sbfres').exists():
            tex2b = util.unyaz_if_needed(tex2.read_bytes())
            tex2.write_bytes(tex2b)
            sbfres.write_bytes(bfres)

    elif sbfres.suffixes != ['.Tex2', '.sbfres']:
        bfres = util.unyaz_if_needed(sbfres.read_bytes())
        sbfres.write_bytes(bfres)

    if system() == "Windows":
        run(["BfresPlatformConverter\\BfresPlatformConverter.exe", sbfres])
    else:
        run(['mono', "BfresPlatformConverter/BfresPlatformConverter.exe", sbfres])

    if sbfres.suffixes == ['.Tex1', '.sbfres']:
        if tex2.exists():
            c_bfres = oead.yaz0.compress(Path(f'SwitchConverted{sep}{sbfres.stem.rstrip("1")}.sbfres').read_bytes())
            sbfres.write_bytes(c_bfres)
            sbfres.rename(Path(f'{sbfres.parent}{sep}{sbfres.stem.rstrip("1")}.sbfres'))
            tex2.unlink()
    elif sbfres.suffixes != ['.Tex2', '.sbfres']:
        c_bfres = oead.yaz0.compress(Path(f'SwitchConverted{sep}{sbfres.name}').read_bytes())
        sbfres.write_bytes(c_bfres)


def convert_havok(actorpack: Path) -> None:
    # Convert havok files unsupported by BCML
    if not Path('HKXConvert').exists() or Path('HKXConvert.exe').exists():
        # Download HKXConvert if it's not already in the system
        print("Downloading HKXConvert...")
        if system() == "Windows":
            filename, headers = urlretrieve('https://github.com/krenyy/HKXConvert/releases/download/1.0.1/HKXConvert.exe', filename='HKXConvert.exe')
            hkx_c = f".{sep}HKXConvert.exe"
        else:
            filename, headers = urlretrieve('https://github.com/krenyy/HKXConvert/releases/download/1.0.1/HKXConvert', filename='HKXConvert')
            hkx_c = f".{sep}HKXConvert"
        Path(f'{hkx_c}').chmod(0o755)
    actor_path = Path(actorpack.name)
    actor = oead.Sarc(util.unyaz_if_needed(actorpack.read_bytes()))
    extract_sarc(actor, actor_path)
    hkxs = actor_path.rglob('*.hk*')
    for hkx in hkxs:
        run([f'{hkx_c}', 'hkx2json', hkx])
        hkx.unlink()
        run([f'{hkx_c}', 'json2hkx', '--nx', f'{splitext(hkx)[0]}.json'])
        Path(f'{splitext(hkx)[0]}.json').unlink()
    if hkxs:
        print("HKX files converted. Saving...")
        write_sarc(actor, actor_path, actorpack)
    shutil.rmtree(actor_path)

def convert_bars(bars: Path, mod_root: Path) -> None:
    # Convert bars files, and their files inside
    try:
        o_bars = util.get_game_file(f"Voice/USen/{bars.name}").read_bytes()
    except FileNotFoundError:
        try:
            o_bars = util.get_game_file(f"Sound/Resource/{bars.name}").read_bytes()
        except FileNotFoundError:
            bg_path = bars.parent.parent.parent.name
            pack_path = util.get_game_file(f'Pack/{bg_path}')
            pack = oead.Sarc(pack_path.read_bytes())
            if system() == "Windows":
                o_bars = pack.get_file(f'{bars}'.split(f'{pack_path.name}{sep}')[1].replace("\\", "/")).data
            else:
                o_bars = pack.get_file(f'{bars}'.split(f'{pack_path.name}{sep}')[1]).data
                
    barstool.extract_from_bars(bars, '>')
    try:
        bfstps = Path(bg_path).rglob('*.bfstp')
        bfwavs = Path(bg_path).rglob('*.bfwav')
    except:
        bfstps = mod_root.rglob('*.bfstp')
        bfwavs = mod_root.rglob('*.bfwav')
    for bfstp in bfstps:
        sound.convExtFile(bfstp, 'FSTP', '<')
        bfstpfixer.fix(bfstp)
    for bfwav in bfwavs:
        sound.convExtFile(bfwav, 'FWAV', '<')
    bars.write_bytes(o_bars)
    shutil.move(f'{splitext(bars)[0]}_extracted', f'{bars.parent}{sep}new')
    barstool.extract_from_bars(bars, '<')
    repack_bars(bars, f'{splitext(bars)[0]}_extracted', f'{bars.parent}{sep}new')
    shutil.rmtree(f'{splitext(bars)[0]}_extracted')
    shutil.rmtree(f'{bars.parent}{sep}new')

def convert_bflim(sblarc: Path):
    blarc = oead.Sarc(util.unyaz_if_needed(sblarc.read_bytes()))
    blarc_path = Path(sblarc.name)
    if any("bflim" in i.name for i in blarc.get_files()):
        stock_pack = util.get_game_file(f"Pack/{sblarc.parent.parent.name}")
        try:
            stock_sblarc = oead.Sarc(stock_pack.read_bytes()).get_file("Layout/Common.sblarc")
            stock_blarc = oead.Sarc(util.unyaz_if_needed(stock_sblarc.data))
        except (oead.InvalidDataError, AttributeError):
            stock_sblarc = oead.Sarc(stock_pack.read_bytes()).get_file("Layout/Title.sblarc")
            stock_blarc = oead.Sarc(util.unyaz_if_needed(stock_sblarc.data))
        bntx_file = stock_blarc.get_file(f"timg/__Combined.bntx")
        extract_sarc(blarc, blarc_path)
        Path(blarc_path / f'{bntx_file.name}').write_bytes(bntx_file.data)
        for bflim in blarc_path.rglob('*.bflim'):
            bntx.tex_inject(blarc_path / f'{bntx_file.name}', bflim, False)
            Path(bflim).unlink()
        write_sarc(blarc, blarc_path, sblarc)
        shutil.rmtree(blarc_path)

def convert_files(files, mod_path: Path) -> None:
    for file in files:
        if file.exists() and file.stat().st_size != 0:
            if file.suffix == ".sbfres" or file.suffix == ".sbitemico":
                # Convert FRES files
                convert_fres(file)

            elif file.suffix == ".sbactorpack":
                # Convert havok files inside actor packs
                actor = oead.Sarc(util.unyaz_if_needed(file.read_bytes()))
                actor_path = Path(f'{file.name}')
                if any("hkcl" in i.name for i in actor.get_files()) or any("hkrg" in i.name for i in actor.get_files()):
                    convert_havok(file)

            elif file.suffix == ".bars":
                # Convert bars files
                convert_bars(file, mod_path)

            elif file.suffix == ".bfstm":
                # Convert BFSTM files
                sound.convExtFile(file, "FSTM", '<')

            elif file.suffix == ".pack" or file.suffix == ".sbeventpack":
                # Convert files inside of pack files
                pack = oead.Sarc(util.unyaz_if_needed(file.read_bytes()))
                pack_path = Path(f'{file.name}')
                if any(splitext(i.name)[1] in supp_formats for i in pack.get_files()):
                    extract_sarc(pack, pack_path)
                    convert_files(pack_path.rglob('*.*'), mod_path)
                    write_sarc(pack, pack_path, file)
                    shutil.rmtree(pack_path)

            elif file.suffix == ".sblarc":
                # Convert bflim files inside of sblarc files
                convert_bflim(file)

            elif file.suffix == ".hkcl":
                convert_havok(file)

def clean_up():
    if Path('HKXConvert').exists():
        Path('HKXConvert').unlink()
    shutil.rmtree('BfresPlatformConverter', ignore_errors=True)
    shutil.rmtree('SwitchConverted', ignore_errors=True)
    shutil.rmtree('WiiUConverted', ignore_errors=True)

def convert(mod) -> None:
    # Open the mod
    bnp = Path(mod)
    mod_path = open_mod(bnp)
    files = mod_path.rglob('*.*')
    try: 

        # Run the mod through BCML's automatic converter first 
        warnings = convert_mod(mod_path, False, True)

        # Convert supported files
        convert_files(files, mod_path)
            
        out = bnp.with_name(f"{bnp.stem}_switch.bnp")
        if Path(out).exists():
            Path(out).unlink()
        x_args = [
            util.get_7z_path(),
            "a",
            out,
            f'{mod_path / "*"}',
        ]
        run(x_args)

        # Write BCML's warning to a file
        if warnings:
            with open("error.log", "a") as file:
                for warning in warnings:
                    # Write BCML's warning to a file
                    if type(warning) == list:
                        for error in warning:
                            if all(i not in error for i in supp_formats):
                                file.write(error + "\n")
                        continue
                    if all(i not in warning for i in supp_formats):
                        file.write(warning + "\n")

    except Exception:
        print(traceback.format_exc())
        clean_up()

    finally:
        shutil.rmtree(mod_path, ignore_errors=True)

def main() -> None:
    if len(args.mods) == 1: # one argument
        mods = glob(args.mods[0])
    else: # more than one argument
    	mods = args.mods

    downloaded = False
    if Path('BfresPlatformConverter').exists() and (Path('HKXConvert').exists() or Path('HKXConvert.exe').exists()):
        downloaded = True

    # Set BCML to Switch mode
    settings = util.get_settings()
    settings["wiiu"] = False
    util.save_settings()
    
    for mod in mods:
        convert(mod)

    if (Path('BfresPlatformConverter').exists() or Path('HKXConvert').exists() or Path('HKXConvert.exe').exists()) and not downloaded:
        reply = confirm_prompt("Would you like to keep the downloaded files?")
        if not reply:
            clean_up()


if __name__ == "__main__":
    main()      
