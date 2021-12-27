#!/usr/bin/env python

from subprocess import run
from os.path import sep, splitext
from glob import glob
from urllib.request import urlopen, urlretrieve
from io import BytesIO
from zipfile import ZipFile
from platform import system 
from json import loads
from pathlib import Path
from itertools import islice
from multiprocessing import Pool
from functools import partial
import shutil
import argparse
import traceback
import logging

from bcml.install import open_mod, find_modded_files
from bcml.dev import convert_mod
from bcml import util
from bars_py import bars, bcf_converter
from bflim_convertor import bntx_dds_injector as bntx
import oead

# Construct an argument parser
parser = argparse.ArgumentParser(description="Converts mods in BNP format using BCML's converter, complemented by some additional tools")
parser.add_argument("bnp", nargs='+')
parser.add_argument("-o", "--output", help="Specify an output file")
parser.add_argument("-log", "--log-level", default="warning", help="Set the logging level. Example --log-level debug. Default is warning")
args = parser.parse_args()

# Error logging
logging.basicConfig(filename="error.log", filemode="w", level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

# Supported formats
supp_formats = [".sbfres", ".sbitemico", ".hkcl", ".hkrg", ".shknm2", ".bars", ".bfstm", ".bflim", ".bcamanim", ".sblarc"]

BFRES_EXT = [".sbfres", ".sbitemico", ".bcamanim"]
HAVOK_EXT = [".hkcl", ".hkrg", ".shknm2"]
LAYOUT_EXT = [".bflan", ".bgsh", ".bnsh", ".bushvt", ".bflyt", ".bflim", ".bntx"]
SOUND_EXT = [".bfstm", ".bfstp", ".bfwav", ".bars"]

def confirm_prompt(question: str) -> bool:
    # https://gist.github.com/garrettdreyfus/8153571
    reply = None
    while reply not in ("", "y", "n"):
        reply = input(f"{question} (Y/n): ").lower()
    return reply in ("", "y")

def extract_sarc(sarc: oead.Sarc, sarc_path: Path) -> None:
    # Extract the data from a SARC file
    Path(sarc_path).mkdir(exist_ok=True)
    for file in sarc.get_files():
        if not Path(sarc_path / file.name).parent.exists():
            Path(sarc_path / file.name).parent.mkdir(parents=True)
        Path(sarc_path / file.name).write_bytes(file.data)

def write_sarc(sarc: oead.Sarc, sarc_path: Path, sarc_file: Path) -> None:
    # Overwrite the SARC file with the modified files
    new_sarc = oead.SarcWriter(endian=oead.Endianness.Little)
    for file in sarc_path.rglob("*.*"):
        new_file = f'{file}'.split(f"{sarc_file.name}{sep}")[1].replace("\\", "/")
        new_sarc.files[new_file] = file.read_bytes()
    if sarc_file.suffix == ".pack":
        sarc_file.write_bytes(new_sarc.write()[1])
    else:
        sarc_file.write_bytes(oead.yaz0.compress(new_sarc.write()[1]))

def convert_bfres(sbfres: Path) -> None:
    # Convert sbfres files

    # If our BFRES file is a texture, use the Tex2 file which should be in the same folder...
    if '.Tex1' in sbfres.suffixes:
        bfres = util.unyaz_if_needed(sbfres.read_bytes())
        tex2 = Path(f'{sbfres.parent}{sep}{sbfres.name.replace("Tex1", "Tex2")}')
        if tex2.exists():
            tex2b = util.unyaz_if_needed(tex2.read_bytes())
            tex2.write_bytes(tex2b)
            sbfres.write_bytes(bfres)
        else:
            raise FileNotFoundError("Could not find Tex2 file for mipmap data.")
    # ...else, work with our BFRES file only
    else:
        bfres = util.unyaz_if_needed(sbfres.read_bytes())
        sbfres.write_bytes(bfres)

    # Convert the BFRES file, formatting the path to the converter according to the OS
    if system() == "Windows":
        run(["BfresPlatformConverter\\BfresPlatformConverter.exe", str(sbfres)])
    else:
        run(['mono', "BfresPlatformConverter/BfresPlatformConverter.exe", str(sbfres)])

    # Save our new file
    if sbfres.suffixes == ['.Tex1', '.sbfres']:
        c_bfres = oead.yaz0.compress(Path(f'SwitchConverted{sep}{sbfres.name.replace("Tex1", "Tex")}').read_bytes())
        sbfres.write_bytes(c_bfres)
        sbfres.rename(Path(f'{sbfres.parent}{sep}{sbfres.name.replace("Tex1", "Tex")}'))
        tex2.unlink()
    elif sbfres.suffix.startswith(".s"):
        c_bfres = oead.yaz0.compress(Path(f'SwitchConverted{sep}{sbfres.name}').read_bytes())
        sbfres.write_bytes(c_bfres)
    else:
        sbfres.write_bytes(Path(f'SwitchConverted{sep}{sbfres.name}').read_bytes())

def convert_havok(hkx: Path) -> None:
    # Convert havok files unsupported by BCML
    hkx_c = ".\HKXConvert.exe" if system() == "Windows" else "./HKXConvert"
    # Make sure we can run the program by setting the correct permissions
    Path(f'{hkx_c}').chmod(0o755)

    # Convert every hkx found into json, and then to switch
    print(f"Converting {hkx.name}")
    if hkx.suffix.startswith(".s"):
        unyazed_hkx = util.unyaz_if_needed(hkx.read_bytes())
        hkx.write_bytes(unyazed_hkx)

    run([hkx_c, 'hkx2json', str(hkx)])
    hkx.unlink()
    run([hkx_c, 'json2hkx', '--nx', f'{splitext(hkx)[0]}.json', str(hkx)])
    Path(f'{splitext(hkx)[0]}.json').unlink()

    if hkx.suffix.startswith(".s"):
        yaz0_hkx = oead.yaz0.compress(hkx.read_bytes())
        hkx.write_bytes(yaz0_hkx)

def get_stock_bfstp(bfstp_name: str, bars_file: Path):
    # Look for the bars file containing the bfstp
    try:
        stock_bars = util.get_game_file(f"Sound/Resource/{bars_file.name}")
        stock_tracks,_ = bars.get_bars_tracks(stock_bars.read_bytes())
    except FileNotFoundError:
        # If there's no loose bars file, find one inside packs
        try:
            # Look in regular packs
            stock_pack = util.get_game_file(f'Pack/{bars_file.parent.parent.parent.name}')
            stock_bars = oead.Sarc(stock_pack.read_bytes()).get_file(f"Sound/Resource/{bars_file.name}")
            # Get the stock tracks
            stock_tracks, stock_offsets = bars.get_bars_tracks(bytearray(stock_bars.data))
        except FileNotFoundError:
            # Look in event packs
            stock_pack = util.get_game_file(f'Event/{bars_file.parent.parent.parent.name}')
            stock_bars = oead.Sarc(util.unyaz_if_needed(stock_pack.read_bytes())).get_file(f"Sound/Resource/{bars_file.name}")
            if not isinstance(stock_bars, oead.File):
                raise FileNotFoundError(f"File Sound/Resource/{bars_file.name} was not found in game dump.")
            # Get the stock tracks
            stock_tracks, stock_offsets = bars.get_bars_tracks(bytearray(stock_bars.data))
    return stock_tracks[bfstp_name]

def convert_bflim(sblarc: Path) -> None:
    # Convert bflim files inside a WiiU sblarc
    blarc = oead.Sarc(util.unyaz_if_needed(sblarc.read_bytes()))
    blarc_path = Path(sblarc.name)

    if any("bflim" in i.name for i in blarc.get_files()):
        # Get the pack file where the sblarc comes from
        stock_pack = util.get_game_file(f"Pack/{sblarc.parent.parent.name}")

        if sblarc.parent.parent.name == "Bootup.pack":
            # If the sblarc is in Bootup.pack, get a stock Common.sblarc
            stock_sblarc = oead.Sarc(stock_pack.read_bytes()).get_file("Layout/Common.sblarc")
            stock_blarc = oead.Sarc(util.unyaz_if_needed(stock_sblarc.data))

        elif sblarc.parent.parent.name == "Title.pack":
            # If the sblarc is in Title.pack, get a stock Title.sblarc
            stock_sblarc = oead.Sarc(stock_pack.read_bytes()).get_file("Layout/Title.sblarc")
            stock_blarc = oead.Sarc(util.unyaz_if_needed(stock_sblarc.data))

        # Get a stock bntx file
        bntx_file = stock_blarc.get_file("timg/__Combined.bntx")
        extract_sarc(blarc, blarc_path)
        Path(blarc_path / bntx_file.name).write_bytes(bntx_file.data)

        for bflim in blarc_path.rglob('*.bflim'):
            try:
                # Inject every bflim found into the bntx file
                bntx.tex_inject(blarc_path / bntx_file.name, bflim, False)
                Path(bflim).unlink()
            except Exception as err:
                if Path(f'{bflim.stem}.dds').exists():
                    Path(f'{bflim.stem}.dds').unlink()
                logging.warning(f"{bflim.relative_to(blarc_path)} could not be converted")
                logging.debug(err, exc_info=True)
        # Write the new blarc file
        write_sarc(blarc, blarc_path, sblarc)

        # Remove the temporary folder
        shutil.rmtree(blarc_path)

def convert_files(file: Path, mod_path: Path) -> None:
    try:
        # Convert supported files
        if file.exists() and file.stat().st_size != 0:
            if file.suffix in BFRES_EXT:
                # Convert FRES files
                if ".Tex2" not in file.suffixes:
                    convert_bfres(file)

            elif file.suffix == ".bars":
                # Convert bars files
                bars_bytes = bytearray(file.read_bytes())
                tracks, offsets = bars.get_bars_tracks(bars_bytes)
                for name, data in tracks.items():
                    # Read the track header and convert appropiately
                    magic: str = data[:0x4].decode("utf-8")
                    try:
                        bfstm_exists = next(mod_path.rglob(name + ".bfstm"))
                    except StopIteration:
                        bfstm_exists = None

                    if magic == 'FWAV':
                        tracks[name] = bcf_converter.conv_file(data, magic, '<')

                    elif magic == 'FSTP' and bfstm_exists:
                        tracks[name] = bcf_converter.conv_file(data, magic, '<')

                    elif magic == 'FSTP' and not bfstm_exists:
                        tracks[name] = get_stock_bfstp(name, file)

                    bars_bytes[offsets[name]:offsets[name] + len(tracks[name])] = tracks[name]

                new_bars = bars.convert_bars(bars_bytes, '<')
                file.write_bytes(bytes(new_bars))
                print("Successfully converted " + file.name + "!")

            elif file.suffix == ".bfstm":
                # Convert BFSTM files
                new_bfstm = bcf_converter.conv_file(file.read_bytes(), "FSTM", '<')
                file.write_bytes(bytes(new_bfstm))
                print("Successfully converted " + file.name + "!")

            elif "pack" in file.suffix and file.suffix != ".sbquestpack":
                # Convert files inside of pack files
                pack = oead.Sarc(util.unyaz_if_needed(file.read_bytes()))
                pack_path = Path(file.name)
                if any(splitext(i.name)[1] in supp_formats for i in pack.get_files()):
                    extract_sarc(pack, pack_path)
                    new_files = pack_path.rglob('*.*')
                    for new in new_files:
                        try:
                            convert_files(new, pack_path)
                        except Exception as err:
                            logging.warning(f"{new.relative_to(pack_path)} could not be converted")
                            logging.debug(err, exc_info=True)
                    write_sarc(pack, pack_path, file)
                    shutil.rmtree(pack_path)

            elif file.suffix == ".sblarc":
                if file.name == "BootUp.sblarc":
                    logging.warning("A BootUp.sblarc was found! These files are not used on Switch, so it was skipped")
                    file.unlink()
                else:
                    # Convert bflim files inside of sblarc files
                    convert_bflim(file)

            elif file.suffix in HAVOK_EXT:
                # If there's an hkx file not in an actorpack, convert it as well
                convert_havok(file)
    except Exception as err:
        logging.warning(f"{file.relative_to(mod_path)} could not be converted")
        logging.debug(err, exc_info=True)

def clean_up() -> None:
    if Path('HKXConvert').exists():
        Path('HKXConvert').unlink()
    shutil.rmtree('BfresPlatformConverter', ignore_errors=True)
    shutil.rmtree('SwitchConverted', ignore_errors=True)
    shutil.rmtree('WiiUConverted', ignore_errors=True)

def download_converters(files) -> None:
    if any(hk.suffix in HAVOK_EXT for hk in files):
        if system() == "Windows" and not Path('HKXConvert.exe').exists():
            # Download HKXConvert if it's not already in the system
            print("Downloading HKXConvert...")
            filename, headers = urlretrieve('https://github.com/krenyy/HKXConvert/releases/download/1.0.1/HKXConvert.exe', filename='HKXConvert.exe')
        elif system() == "Linux" and not Path('HKXConvert').exists():
            print("Downloading HKXConvert...")
            # Download HKXConvert if it's not already in the system
            filename, headers = urlretrieve('https://github.com/krenyy/HKXConvert/releases/download/1.0.1/HKXConvert', filename='HKXConvert')

    if any(bfres.suffix in BFRES_EXT for bfres in files):
        if not Path('BfresPlatformConverter').exists():
            # Code adapted from https://gist.github.com/hantoine/c4fc70b32c2d163f604a8dc2a050d5f6
            # Extract BfresPlatformConverter if it's not already in the system
            print("Downloading BfresPlatformConverter...")
            http_response = urlopen('https://gamebanana.com/dl/485626')
            zipfile = ZipFile(BytesIO(http_response.read()))
            zipfile.extractall(path='BfresPlatformConverter')

def convert(mod: Path) -> None:
    # Open the mod
    mod_path = open_mod(mod)
    if (mod_path / "info.json").exists():
        meta = loads((mod_path / "info.json").read_text("utf-8"))
    if meta["platform"] == "switch":
        raise RuntimeError("Ultimate BoTW Converter does not support Switch to Wii U conversion yet!")
    files = mod_path.rglob('*.*')
    # download_converters(find_modded_files(mod_path))
    try:

        with util.TempSettingsContext({"wiiu": False}):
            with Pool(maxtasksperchild=500) as pool:
                # Convert supported files
                pool.map(partial(convert_files, mod_path=mod_path), files)
                pool.close()
                pool.join()
        
        # Run the mod through BCML's automatic converter first 
        warnings = convert_mod(mod_path, False, True)

        # Pack the converted mod into a new bnp
        out = Path(f'{args.output}.bnp') if args.output else mod.with_name(f"{mod.stem}_switch.bnp")
        if Path(out).exists():
            Path(out).unlink()
        x_args = [
            util.get_7z_path(),
            "a",
            str(out),
            f'{str(mod_path / "*")}',
        ]
        run(x_args)

        # Write BCML's warning to a file
        if warnings:
            with open("error.log", "a", encoding="utf-8") as file:
                for warning in warnings:
                    # Write BCML's warning to a file    
                    if all(i not in warning for i in supp_formats):
                        logger.warning(warning)

    except Exception as err:
        # logging.exception(err)
        print(traceback.format_exc())
        # clean_up()

    finally:
        # Remove the temporary mod_path
        shutil.rmtree(mod_path, ignore_errors=True)

def main() -> None:
    if len(args.bnp) == 1: # one argument
        mods = glob(args.bnp[0])
    else: # more than one argument
    	mods = args.bnp

    downloaded = False
    if Path('BfresPlatformConverter').exists() and (Path('HKXConvert').exists() or Path('HKXConvert.exe').exists()):
        downloaded = True
    
    for mod in mods:
        convert(Path(mod))

    if Path("error.log").stat().st_size != 0:
        print("It seems some files could not be converted. Please check error.log for more info.")

    if (Path('BfresPlatformConverter').exists() or Path('HKXConvert').exists() or Path('HKXConvert.exe').exists()) and not downloaded:
        keep = confirm_prompt("Would you like to keep the downloaded files?")
        if not keep:
            clean_up()


if __name__ == "__main__":
    main()      