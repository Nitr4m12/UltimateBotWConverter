# Ultimate BotW Converter
A script combining various sources to convert BotW WiiU mods for the Switch version of the game

## Requirements
- Python 3.7 or 3.8 (If on Windows, you must check `Add Python to PATH` during installation)
- A legal, unpacked dump of BoTW Switch (1.6.0)
- [BotW Cross-Platform Mod Loader](https://github.com/NiceneNerd/BCML)

For obtaining a BoTW dump, see https://zeldamods.org/wiki/Help:Dumping_games. BCML can be obtained through python's PyPI, using `pip install bcml`

## Installation
Run `pip install ubotw-converter` from a Command-Line Interface(CLI).  

If wanting to install from source, run `pip install -e .` inside the folder where the source code is located 

## Usage
In a CLI, run `convert_to_switch path/to/your/bnp`, and the conversion process will start. If you encounter problems caused by multi-processing, you can use `convert_to_switch -s path/to/your/bnp` to enable single core. 

## Supported formats
BCML's converter is still limited, so using other tools to convert those files that it can't is our only option for now. With this script, I've automated the process of using those other tools and added these formats to the supported list:
- `.bars`
- `.bfstm`
- `.sbfres`
- `.sbitemico`
- `.hkcl`
- `.hkrg`
- `.shknm2`
- `.bflim`*
- `.bcamanim`**

\*For bflim files, only files that replace the original ones can be converted, not completely new ones.  

\*\*`.bcamanim` files are a bit tricky, since none of the tools currently available can convert them properly. Instead, the converter looks in your game files for an equivalent one, and replaces the WiiU one with that one. This means that `.bcamanim` files that are not packed in vanilla-named files will mean you would have to replace them manually

## Credits 
- [AboodXD](https://github.com/aboood40091) - BCFSTM-BCFWAV Converter, BNTX Injector, Bflim Extractor
- [NanobotZ](https://github.com/NanobotZ) - bfstpfixer.py
- [SamusAranX](https://github.com/SamusAranX) - Original bars_extractor.py script
- [Aaaboy97](https://github.com/Aaaboy97) - Bars repacker script
- [KillzXGaming](https://github.com/KillzXGaming) - BfresPlatformConverter, BfresLibrary
- [krenyy](https://gitlab.com/krenyy) - HKXConvert
- [NiceneNerd](https://github.com/NiceneNerd) - BOTW Cross-Platform Mod Loader
- [Leoetlino](https://github.com/leoetlino) - All his tools for working with BotW files
- [HGStone](https://github.com/HGStone) - Bat script and testing
