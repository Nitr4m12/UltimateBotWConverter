# UltimateBoTWConverter
A script that convert WiiU BotW mods to Switch. It uses every resource I could find under the sun that allows for conversion, with some modifications to accomodate for the central script. ONLY `converter.py` IS COMPLETELY MADE BY ME, THE ORIGINAL AUTHORS STILL DESERVE ALL THE CREDIT FOR THEIR WORK.

# Requirements
- Python 3.7 or 3.8 (If on Windows, you must check `Add Python to PATH` during installation)
- A legal, unpacked dump of BoTW Switch (1.6.0)
- BCML
- leoetlino's sarc tool

The last two can be obtained through Python's pip, using `pip install bcml` for BCML, and `pip install sarc` for leoetlino's tool. 
**Important**: BCML must be set up and put in Switch mode, or the script won't work. Also, this script doesn't modify files inside `TitleBG.pack`, so those you'll still have to manually modify yourself.

# Usage
Open CMD on Windows or a Terminal window on Linux, and run the script with `python converter.py [mod]`, replacing `mod` by your BNP mod/mods, or `path/to/folder/with/bnps/*.bnp` to convert every BNP in a folder.

# Added supported formats
BCML converter is still limited, so using other tools to convert those is our only option for now. With this script, I've added this formats to the supported list:
- `.bars`
- `.bfstm`
- `.sbfres` (animations are untested, but I'm guessing there would be some problems)
- `.sbitemico`
- `.hkcl`
- `instSizes` in `ActorInfo.product.sbyml`
