from morphonts import *
import bdflib
from PIL import Image, ImageDraw, ImageFont


def write_test_sequence(glyph):
    img = img_from_glyph(glyph)
    img.save("0.png")
    img_list = [img.copy()]
    for i, op in enumerate(img_ops):
        img = op(img)
        img_list.append(img)
        img.save(str(i+1) + ".png")
    return img_list
