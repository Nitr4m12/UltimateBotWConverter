# UltimateBotWConverter
A script that converts WiiU BotW mods to Switch. It uses every resource I could find that allows for conversion, with some modifications to accomodate for the central script. 

DISCLAIMER: While I made modifications of my own to various of the tools included here, the original authors still deserve all the credit for all their work.

# Requirements
- Python 3.7 or 3.8 (If on Windows, you must check `Add Python to PATH` during installation)
- A legal, unpacked dump of BoTW Switch (1.6.0)
- [BotW Cross-Platform Mod Loader](https://github.com/NiceneNerd/BCML)

For obtaining a BoTW dump, see https://zeldamods.org/wiki/Help:Dumping_games. BCML can be obtained through python's PyPI, using `pip install bcml`

# Usage
### Linux:
Open a Terminal window in the script's folder, and run the script with `python converter.py "mod"`, replacing `mod` by your BNP mod/mods, or `path/to/folder/with/bnps/*.bnp` to convert every BNP in a folder.
### Windows:
Open a CMD window in the script's folder, and run the script with `python converter.py "mod"`, replacing `mod` by your BNP mod/mods, or `path\to\folder\with\bnps\*.bnp` to convert every BNP in a folder. You can also drag and drop your BNP(s) into the included bat file.

# Supported formats
BCML's converter is still limited, so using other tools to convert those files that it can't is our only option for now. With this script, I've automated the process of using those other tools and added these formats to the supported list:
- `.bars`
- `.bfstm`
- `.sbfres`*
- `.sbitemico`
- `.hkcl`
- `.hkrg`
- `.bflim`**

### Limitations:
- \*If trying to convert a `.sbres` file that replaces animations, it might or might not work due to limitations with BfresPlatformConverter.
- \*\*For bflim files, only files that replace the original ones can be converted, not completely new ones.


# Credits 
- AboodXD - BCFSTM-BCFWAV Converter, BNTX Injector, Bflim Extractor
- NanobotZ - bfstpfixer.py
- SamusAranX - Original bars_extractor.py script
- Aaaboy97 - Bars repacker script
- KillzXGaming - BfresPlatformConverter, BfresLibrary
- kreny - HKXConvert
- NiceneNerd - BOTW Cross-Platform Mod Loader
- HGStone - Bat script and testing

It's worth considering that I'm still new to Python, so any feedback is appreciated!
