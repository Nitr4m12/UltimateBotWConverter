# UltimateBoTWConverter
A script that converts WiiU BotW mods to Switch. It uses every resource I could find that allows for conversion, with some modifications to accomodate for the central script. Thanks to HGStone for testing and creating the bat script. ONLY `converter.py` IS COMPLETELY MADE BY ME, THE ORIGINAL AUTHORS STILL DESERVE ALL THE CREDIT FOR THEIR WORK.

# Requirements
- Python 3.7 or 3.8 (If on Windows, you must check `Add Python to PATH` during installation)
- A legal, unpacked dump of BoTW Switch (1.6.0)
- BCML

For obtaining a BoTW dump, see https://zeldamods.org/wiki/Help:Dumping_games. BCML can be obtained through python's own pip, using `pip install bcml`

# Usage
### Linux:
Open a Terminal window in the script's folder, and run the script with `python converter.py "mod"`, replacing `mod` by your BNP mod/mods, or `path/to/folder/with/bnps/*.bnp` to convert every BNP in a folder.
To use the included bash script, use 
```
chmod +x convert.sh
./convert.sh "mod"
```
### Windows:
Drag and drop your BNP into the included bat file

# Added supported formats
BCML converter is still limited, so using other tools to convert those is our only option for now. With this script, I've automated the process of using thosr other tools and added this formats to the supported list:
- `.bars`
- `.bfstm`
- `.sbfres` (animations are untested, but I'm guessing there would be some problems)
- `.sbitemico`
- `.hkcl`
- `.hkrg`
- `.bflim` (these are inside sblarc files)
- `instSizes` in `ActorInfo.product.sbyml`

# Credits 
- AboodXD - BCFSTM-BCFWAV Converter, BNTX Injector, Bflim Extractor
- NanobotZ - bfstpfixer.py
- SamusAranX - Original bars_extractor.py script
- Aaaboy97 - Bars repacker script
- KillzXGaming - BfresPlatformConverter
- kreny - HKXConvert
- NiceneNerd - BOTW Cross-Platform Mod Loader
- Nitr4m12 - UltimateBoTWConverter

It's worth considering that I'm still new to Python, so any feedback is appreciated!
