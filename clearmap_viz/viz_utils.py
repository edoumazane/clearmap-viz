from napari.utils import DirectLabelColormap
from .params import ONTOLOGY_PATH
import pandas as pd


def get_allen_cm(additional_colors: dict|None =None):
    hex_to_rgb = lambda x: tuple(int(x[i:i+2], 16)/255 for i in (0, 2, 4))
    allen_dict =pd.read_json(ONTOLOGY_PATH, lines=True).set_index("id")["color_hex_triplet"].map(hex_to_rgb).to_dict()
    allen_dict |= {None: 'black'}
    if additional_colors:
        allen_dict |= additional_colors

    return DirectLabelColormap(color_dict=allen_dict)