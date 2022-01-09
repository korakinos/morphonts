# morphonts. Upscaling bitmap fonts with morphological operations

morphonts tries to address a common problem of using bitmap fonts on high-resolution monitors: They appear much smaller than on the low-resolution displays for which they are usually designed, so that even a typeface's largest available size can be to small to be comfortably usable.

The best solution to this would be to design beautiful larger fonts manually, but this takes work and expertise. The easiest automatic solution is to scale fonts up by integer factors, but the results look unnecessarily pixelated and overly bold, and there is no obvious method for fractional scaling. 

This script uses a custom set of operations from [Mathematical Morphology](https://en.wikipedia.org/wiki/Mathematical_Morphology) to upscale fonts of size `n` to size `2n-1` without bolding (for the most part). **Mor**e **fonts** through **morph**ology, hence the name: morphonts.


## Dependencies

Python 3 modules:
 - bdflib
 - pillow


## Usage

morphonts works on bitmap fonts in BDF format. It expects an input and an output filename/path as command line arguments.

```
$ morphonts.py <input-file>.bdf <output-file>.bdf
```

The filenames of BDF fonts often contain size information, like in "t0-12-uni.bdf" (size 12). These are **not** handled by morphonts, you will have to rename the files yourself afterwards (in the example to "t0-23-uni.bdf", as `12*2-1=23`). 

If you happen to use the [ranger](https://ranger.github.io/) file manager and vim, you may find this vim command in combination with ranger's `:bulkrename` useful: `:%s/\%V\(.*\)\%V/\=submatch(1)*2-1/g`. (Works on visual selection.)


## How does it work?

The basic algorithm is:

 1. Scale each glyph's bitmap up by 4.
 2. Morphologically reinforce diagonal strokes.
 3. Morphologically shrink everything horizontally and vertically.
 4. Downscale everything by factor 2. This can produce grey pixels.
 5. Convert grey pixels to black/white using a threshold.

Step 5 allows for some variability: If the threshold is set to almost-white, so that all grey pixels are accepted as black, the algorithm produces knobby artifacts in corners and intersections of strokes. A threshold of 75% brightness, on the other hand, avoids these artifacts, but produces step-like structures in fonts with two or more pixels wide strokes, especially in bold fonts, which may not be to everyone's preference. At the moment, morphonts uses the second method exclusively.

Except for some necessary adding and removing of border pixels from the images, that's it! As an example, here is how morphonts transforms the "%" and "R" glyph from [UW ttyp0](https://people.mpi-inf.mpg.de/~uwe/misc/uw-ttyp0/) from sizes 15 and 22 to 29 and 43. (The images were magnified by factor 10 for better visibility.)

| "&", 15 to 29                                                                                 | "&", 22 to 43                                                                                 | "R", 15 to 29                                                                         | "R", 22 to 43                                                                         |
|-----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| ![Original](/pictures/sequences/t0-15-uni/ampersand/scale-10/0.png)                           | ![Original](/pictures/sequences/t0-22-uni/ampersand/scale-10/0.png)                           | ![Original](/pictures/sequences/t0-15-uni/R/scale-10/0.png)                           | ![Original](/pictures/sequences/t0-22-uni/R/scale-10/0.png)                           |
| ![upscale by 4](/pictures/sequences/t0-15-uni/ampersand/scale-10/1.png)                       | ![upscale by 4](/pictures/sequences/t0-22-uni/ampersand/scale-10/1.png)                       | ![upscale by 4](/pictures/sequences/t0-15-uni/R/scale-10/1.png)                       | ![upscale by 4](/pictures/sequences/t0-22-uni/R/scale-10/1.png)                       |
| ![reinforce diagonal strokes](/pictures/sequences/t0-15-uni/ampersand/scale-10/4.png)         | ![reinforce diagonal strokes](/pictures/sequences/t0-22-uni/ampersand/scale-10/4.png)         | ![reinforce diagonal strokes](/pictures/sequences/t0-15-uni/R/scale-10/4.png)         | ![reinforce diagonal strokes](/pictures/sequences/t0-22-uni/R/scale-10/4.png)         |
| ![shrink vertically and horizontally](/pictures/sequences/t0-15-uni/ampersand/scale-10/6.png) | ![shrink vertically and horizontally](/pictures/sequences/t0-22-uni/ampersand/scale-10/6.png) | ![shrink vertically and horizontally](/pictures/sequences/t0-15-uni/R/scale-10/6.png) | ![shrink vertically and horizontally](/pictures/sequences/t0-22-uni/R/scale-10/6.png) |
| ![downscale by 0.5](/pictures/sequences/t0-15-uni/ampersand/scale-10/7.png)                   | ![downscale by 0.5](/pictures/sequences/t0-22-uni/ampersand/scale-10/7.png)                   | ![downscale by 0.5](/pictures/sequences/t0-15-uni/R/scale-10/7.png)                   | ![downscale by 0.5](/pictures/sequences/t0-22-uni/R/scale-10/7.png)                   |
| ![convert to binary](/pictures/sequences/t0-15-uni/ampersand/scale-10/8.png)                  | ![convert to binary](/pictures/sequences/t0-22-uni/ampersand/scale-10/8.png)                  | ![convert to binary](/pictures/sequences/t0-15-uni/R/scale-10/8.png)                  | ![convert to binary](/pictures/sequences/t0-22-uni/R/scale-10/8.png)                  |


## Showcase

A few examples of morphonts. Pictures generated with `pilfont.py` from [pillow-scripts](https://github.com/python-pillow/pillow-scripts).

### [UW ttyp0](https://people.mpi-inf.mpg.de/~uwe/misc/uw-ttyp0/), size 31 (from 16)

![ttyp0-morphont regular, size 31](/pictures/samples/t0-31-uni.png)
![ttyp0-morphont italic, size 31](/pictures/samples/t0-31i-uni.png)
![ttyp0-morphont bold, size 31](/pictures/samples/t0-31b-uni.png)

### [Dina](https://www.dcmembers.com/jibsen/download/61/), size 19 (from 10)

![dina-morphont regular, size 19](/pictures/samples/Dina_r400-19.png)
![dina-morphont italic, size 19](/pictures/samples/Dina_i400-19.png)
![dina-morphont bold, size 19](/pictures/samples/Dina_r700-19.png)
![dina-morphont bold italic, size 19](/pictures/samples/Dina_i700-19.png)

### others

Another beautiful font to scale up with morphont is the proportional/non-monospace (!) **hlv** from the [**M+** bitmap font family](https://tracker.debian.org/pkg/xfonts-mplus). Unfortunately the spacing comes out far too narrow in `pilfont.py`'s rendering. If anyone manages to generate a good sample image, I would be happy to include it here.


## Notes on installing fonts

Installing bitmap fonts on contemporary Linux desktop systems can be a bit of a mess, depending in what programs you want to use them. Search the web for "pango bitmap fonts" if you want to research the full story.

For know, the recommended method appears to be to convert bitmap fonts to the OTB format before installing them, although there can be rendering issues. There are a [number](https://ndim.fedorapeople.org/stuff/bitmapfonts2otb/bitmapfonts2otb.py) of [command](https://github.com/ctrlcctrlv/bitmapfont2otb) line [tools](https://gist.github.com/Earnestly/6bc5bad7666f7bf8816d054b7b76112e) to [do this](https://gitlab.freedesktop.org/xorg/app/fonttosfnt), some of which combine related BDF fonts into one OTB file, and it can apparently also be done with FontForge (see [this comment](https://gitlab.gnome.org/GNOME/pango/-/issues/386#note_570411) in a bug tracker thread). For me, using the latest development version of [fonttosfnt](https://gitlab.freedesktop.org/xorg/app/fonttosfnt) on each BDF file *separately* seems to work best. (Note that for building fonttosfnt on Debian-based distros you need to install `xutils-dev`, otherwise `./autogen.sh` will fail.)

If your intended application can use fonts in BDF format (like many terminal emulators), you may be better off not converting to OTB. Or you could try installing BDF and OTB fonts with different names side-by-side to have both available for different applications.


## Links

### Morphology stuff

morphonts uses the morphology module from [pillow](https://pillow.readthedocs.io/en/latest/reference/ImageMorph.html).

Another morphology module for python is in [scikit-image](https://scikit-image.org/docs/stable/api/skimage.morphology.html), but it doesn't appear to support custom kernels.

ImageMagick has a [very comprehensive](https://legacy.imagemagick.org/Usage/morphology/) morphology operator.

### BDF stuff

morphonts uses [bdflib](https://bdflib.readthedocs.io/en/latest/about.html). The author has a short and very informative [blog post](https://thristian.livejournal.com/90017.html) about working with BDF fonts on Linux.

[Monobit](https://github.com/robhagemans/monobit) is another python package for reading and writing bitmap fonts.

Some other libraries (including [pillow](https://pillow.readthedocs.io/en/latest/reference/ImageFont.html)) support reading and rendering, but not editing and writing bitmap fonts.

`pilfont.py` from [pillow-scripts](https://github.com/python-pillow/pillow-scripts), while intended for converting bdf fonts to pillow's font format, also prints handy preview images of fonts. It's what I used for the samples above.
