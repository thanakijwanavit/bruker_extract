# Bruker OPUS Reader

## Introduction
The brukeropusreader Python package enables reading the binary OPUS files generated by Bruker spectrometers.

## Usage
from bruker_load import Wave
root="./sample_data"
wave_object=Wave(root)

# list names of files
wave_object.list_names()

## save file as csv
wave_object.to_csv('csv_test')

#load csv file
wave_object.load_csv('./csv_test')

# list names of files
wave_object.list_names()

# plot chart of file (matplotlibb)
wave_object.plot('Fish Meal - RM_M359_12062019_MIX3_20190612_170936')

For full code see [example](Example_usage.ipynb).

## Structure of OPUS files
OPUS files consist of several series of spectra. 
Each series is described by a few parameters: 

- NPT (number of points)
- FXV (value of first wavelength)
- LXV (value of last wavelength)
- END (address of spectra series)

These parameters are found by searching for ASCII strings in the binary files.
After finding a match with one of these parameters, we move the pointer a few bytes further to read the values.
Unfortunately, there is no published open standard describing how much further the pointer should be moved.
We empirically checked that this shift factor is 8 bytes for NPT, FXV, and LXV, and 12 bytes for END.
In addition, each file contains some metadata about the hardware used for measurement.

## Known issues
As Bruker's OPUS file format is not described openly, we do not know its exact structure.  One problem is, given only a few series, how to decide which are absorption spectra? Our solution, empirically developed, is as follows:

1. Remove broken series (such as ones where FXV > LXV, missing NPT information, etc.)
2. Remove interferograms. (See [simplerspec](https://github.com/philipp-baumann/simplerspec).) Interferograms have a starting value of 0.
3. If after these two steps we still have more than one series left, choose the one with highest average value. We empirically verified that other series are usually random noise with values near 0.

## Contact
For developer issues, please start a ticket in Github. 
You can also write to the dev team directly at brukeropusreader-dev@qed.ai. 
For other issues, please write to: brukeropusreader@qed.ai

## License
Copyright (c) 2018 [Quantitative Engineering Design](https://qed.ai). All rights reserved.
This project is released under the terms of the AGPL license, which is included in LICENSE.txt.

--
QED | https://qed.ai
