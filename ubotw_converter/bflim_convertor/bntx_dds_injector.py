from . import bntx as BNTX
from pathlib import Path
from . import bflim_extract
from . import addrlib

def tex_inject(bntx: Path, bflim: Path):
    # Read the bflim file
    with open(bflim, 'rb') as f:
        inb = f.read()

    # Format and store the flim bytes
    flim = bflim_extract.readFLIM(inb)

    # Read the bntx file
    bntx_file = BNTX.read(bntx)

    # Store the name, target, textures and tex_names of the bntx file
    name, target, textures, tex_names = bntx_file

    # Join the textures with their corresponding names into an dict for ease of use
    list_item = dict(zip(tex_names, textures))

    # Store the texture name as a variable
    o_tex = ' '.join([x for x in tex_names if x == bflim.stem])

    # Set up the variables for import the dds file
    tile_mode = list_item[o_tex].tileMode
    srgb = list_item[o_tex].format & 0xFF == 6
    sparse_binding = bool(list_item[o_tex].sparseBinding)
    sparse_residency = bool(list_item[o_tex].sparseResidency)

    old_tex_size = list_item[o_tex].imageSize
    old_tex_num_mips = list_item[o_tex].numMips
    tex_ = BNTX.inject(list_item[o_tex], 1, srgb, sparse_binding, sparse_residency, old_tex_size, flim)

    if tex_:
        # Write to the bntx
        BNTX.writeTex(bntx, tex_, old_tex_size, old_tex_num_mips)