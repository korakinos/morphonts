#!/usr/bin/python3

from PIL import Image
from PIL.ImageMorph import MorphOp
from PIL.ImageOps import expand, crop, scale
import bdflib.reader
import bdflib.writer
import sys


def glyph_bytes(glyph):
    byte_data = bytearray()
    for row in glyph.iter_pixels():
        for pixel in row:
            byte_data.append(0 if pixel else 255)
    return byte_data


def img_from_glyph(glyph):
    # construct Image from glyph bytes
    # Fails with some glyphs (ValueError: tile cannot extend outside image)
    # -> presumably empty glyphs (thus empty list returned by
    # glyph_bytes()) can I skip those by not using "for glyph in
    # font.glyphs"? For now I catch the exception.

    # construct image in greyscale mode "L", not "1" (b/w), because ImageMorph
    # operations only works on "L" images
    img = Image.new("L", (glyph.bbW, glyph.bbH))
    try:
        img.frombytes(bytes(glyph_bytes(glyph)))
    except ValueError:  # empty glyph
        pass
    return img


# I am not just converting an image to a new glyph, because I also need all
# the metadata from the old one.
def update_glyph_with_img(glyph, img):
    width = img.width
    height = img.height

    # rescale measures of glyph
    glyph.bbW = width  # should be equal to morph_rescale(glyph.bbW)
    glyph.bbH = height  # should be equal to morph_rescale(glyph.bbH)
    glyph.bbX = morph_rescale(glyph.bbX)
    glyph.bbY = morph_rescale(glyph.bbY)
    glyph.advance = morph_rescale(glyph.advance)

    # make compatible ints from pixels
    # (see docs for Glyph.data (not .get_data()!))

    int_rows = []

    # allocate a new int representing each row in the glyph, pre-filled with 0
    # bits, then switch the bits corresponding to black/true pixels to 1
    for y in range(height):
        int_rows.insert(0, 0)  # prepend a zero
        for x in range(width):
            if img.getpixel((x, y)) == 0:
                int_rows[0] = int_rows[0] | (1 << width - 1 - x)

    glyph.data = int_rows


def morph(image, number):
    morph_ops = [
        # The initial "4" means to rotate the pattern four times and apply it
        # in each orientation. For glyphs "1" means background, "0"
        # foreground.
        # fmt: off
        # reinforce points of diagonal contact
        MorphOp(patterns=['4:(.01    ' \
                          '   .10    ' \
                          '   ...)->0']),
        # shrink vertically and horizontally (not diagonally)
        MorphOp(patterns=['4:(.1.    ' \
                          '   .0.    ' \
                          '   ...)->1'])
        # fmt: on
    ]
    return morph_ops[number].apply(image)[1]


# list of image operations in order in the format of function(Image) -> Image
img_ops = [
    lambda img: scale(img, 4, Image.NEAREST),
    lambda img: expand(img, 2, 255),
    lambda img: morph(img, 0),
    lambda img: crop(img, 1),
    lambda img: morph(img, 1),
    lambda img: crop(img, 2),
    lambda img: scale(img, 0.5, Image.BOX),
    lambda img: img.point((lambda v: 255 if (v == 255) else 0), "L"),
]

# The numeric operations of this rescale function depend on the morphological
# operations above, of course. Change it when you change them!
def morph_rescale(measure):
    if measure:  # don't try to rescale zero
        return measure * 2 - 1
    else:
        return measure


def process_font(font_path):
    # bdflib.reader doesn't read the FACE_NAME property, only reading FONT as
    # what is indexed as "FACE_NAME" in bdflib.model.Font.properties, and
    # bdflib.writer incorrectly overwrites it with that value on writing. So we
    # parse FACE_NAME separately here (if the font has one) and write it back
    # to the generated font in the very end.

    face_name = ""

    # load font into model and also try to parse FACE_NAME separately
    with open(font_path, "rb") as infile:
        font = bdflib.reader.read_bdf(infile)
    with open(font_path, "rb") as infile:
        for line in infile:
            if line.startswith(b"FACE_NAME "):
                # extract name without quotes, linebreak and, for good measure,
                # whitespace from a line like:
                # FACE_NAME "Liberation Mono"
                face_name = line.split(maxsplit=1)[1].strip(b'"\n\r ')
                break

    # try to parse the FONT read by bdflib.reader (which is confusingly indexed
    # as "FACE_NAME" in Font.properties) as an X Logical Font Description
    # (XLFD) string. If successful, rescale certain measures in it.
    xlfd = font[b"FACE_NAME"].split(b"-")
    if len(xlfd) != 15:
        # FONT is not in XLFD format (xlfd doubles as bool below)
        xlfd = False
    else:
        # convert measures in xlfd to int, rescale, convert back to ascii bytes
        #  - ignoring possible matrix format of PIXEL_SIZE and POINT_SIZE
        #  - taking decipoint unit of POINT_SIZE and "tenth of pixels" of
        #    AVERAGE_WIDTH into account
        # https://www.x.org/releases/X11R7.6/doc/xorg-docs/specs/XLFD/xlfd.html#fontname_field_definitions
        # 7: PIXEL_SIZE, 8: POINT_SIZE, 12: AVERAGE_WIDTH
        xlfd[7] = str(morph_rescale(int(xlfd[7]))).encode("ascii")
        xlfd[8] = str(round(morph_rescale(int(xlfd[8]) / 10) * 10)).encode("ascii")
        xlfd[12] = str(round(morph_rescale(int(xlfd[12]) / 10) * 10)).encode("ascii")

    # prepare a new font object
    # I am not cloning the font object using font.copy() because
    # IGNORABLE_PROPERTIES cannot be set after creating the font object (see
    # bdflib/model.py), including POINT_SIZE and PIXEL_SIZE, and I don't want
    # wrong size info to be stuck in there.
    morphed_font = bdflib.model.Font(
        # use rescaled xlfd for name if it exists
        name=b"-".join(xlfd) if xlfd else font[b"FACE_NAME"],
        ptSize=morph_rescale(font[b"POINT_SIZE"]),
        xdpi=font[b"RESOLUTION_X"],
        ydpi=font[b"RESOLUTION_Y"],
    )

    # hack: save face_name in custom BDF property (for by write_font() below)
    if face_name:
        morphed_font[b"_MORPHONTS_FACE_NAME"] = face_name

    # copy all properties, rescaling all measures
    #  - notable exception: UNDERLINE_THICKNESS (as thickness of font doesn't
    #    change either)
    #  - also excepted: all RAW_* properties (because I don't understand them)
    #  - Rescaling is only precise for measures referring to the full width or
    #    height of one glyph, not for word measures like MIN_SPACE and not for
    #    sub-glyph measures like UNDERLINE_POSITION.
    # See https://www.x.org/releases/X11R7.6/doc/xorg-docs/specs/XLFD/xlfd.html
    # for reference.
    for p in font.property_names():
        if p in [
            b"AVERAGE_WIDTH",
            b"MIN_SPACE",
            b"NORM_SPACE",
            b"MAX_SPACE",
            b"END_SPACE",
            b"AVG_CAPITAL_WIDTH",
            b"AVG_LOWERCASE_WIDTH",
            b"QUAD_WIDTH",
            b"FIGURE_WIDTH",
            b"SUPERSCRIPT_X",
            b"SUPERSCRIPT_X",
            b"SUBSCRIPT_X",
            b"SUBSCRIPT_Y",
            b"SUPERSCRIPT_SIZE",
            b"SUBSCRIPT_SIZE",
            b"SMALL_CAP_SIZE",
            b"UNDERLINE_POSITION",
            b"SRIKEOUT_ASCENT",
            b"STRIKEOUT_DESCENT",
            b"CAP_HEIGHT",
            b"X_HEIGHT",
            b"FONT_ASCENT",
            b"FONT_DESCENT",
        ]:
            morphed_font[p] = morph_rescale(font[p])
        else:
            morphed_font[p] = font[p]

    # signature analogous to how Xmbdfed does it
    morphed_font[b"_MORPHONTS_INFO"] = b"Upscaling by morphonts."

    # for every glyph present in font:
    for glyph in font.glyphs:
        img = img_from_glyph(glyph)

        # run morph operations
        for op in img_ops:
            img = op(img)

        # image to new glyph in new font (by updating old glyph in-place
        # first)
        # Note that as a side effect, this changes the glyph in the original
        # font object. This is the result of using the
        # bdflib.Model.new_glyph_from_data() method, which I have to do
        # because writing directly to bdflib.model.glyphs or
        # .glyphs_by_codepoint results in inconsistent font objects (e.g.
        # empty codepoint list, when adding to .glyphs).

        update_glyph_with_img(glyph, img)
        morphed_font.new_glyph_from_data(
            name=glyph.name,
            data=glyph.get_data(),
            bbX=glyph.bbX,
            bbY=glyph.bbY,
            bbW=glyph.bbW,
            bbH=glyph.bbH,
            advance=glyph.advance,
            codepoint=glyph.codepoint,
        )

    return morphed_font


def write_font(font_model, output_filename):
    # try to find the preserved FACE_NAME hidden in a custom property
    face_name = b""
    try:
        face_name = font_model[b"_MORPHONTS_FACE_NAME"]
    except KeyError:
        pass

    # write BDF from model to disk
    with open(output_filename, "wb") as outfile:
        bdflib.writer.write_bdf(font_model, outfile)

    # if necessary, read the file back in and correct FACE_NAME, then write it
    # back out
    if face_name:
        lines = []
        with open(output_filename, "rb") as infile:
            for line in infile:
                if line.startswith(b"FACE_NAME "):
                    line = b'FACE_NAME "' + face_name + b'"\n'
                lines.append(line)
        with open(output_filename, "wb") as outfile:
            for line in lines:
                if not line.startswith(b"_MORPHONTS_FACE_NAME"):
                    outfile.write(line)


if __name__ == "__main__":
    try:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
    except IndexError:
        print(f"Usage: {sys.argv[0]} <infile> <outfile>")
        sys.exit(1)

    try:
        write_font(process_font(input_path), output_path)
    except FileNotFoundError as e:
        print("Error " + e.errno + ", file not found: " + e.filename)
        print(e.strerror)
        sys.exit(-1)
    except PermissionError:
        print("Error " + e.errno + ", not permitted.")
        print(e.strerror)
        sys.exit(-2)

    sys.exit(0)
