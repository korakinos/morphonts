#!/bin/bash

mkdir otb
mkdir bdf

for f in *.bdf
do
  fonttosfnt -o otb/"${f/bdf/otb}" "$f"
  mv $f bdf/
done

