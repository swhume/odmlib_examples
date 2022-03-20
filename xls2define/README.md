# xls2define

## Introduction
Use the xlsx2define2-1 example instead of this one. The Define-XML v2.1 examples are getting more use and testing 
creating study Define-XML files, so they're getting updated more frequently. 

The xls2define program is an odmlib example application that generates a Define-XML v2.0 file from 
an Excel spreadsheet that contains the study metadata needed to create the Define-XML file. The Exel 
spreadsheet version of the makes it easier for many to edit or create new content to include in a 
Define-XML v2.0 file. The companion define2xls program takes the generated Define-XML file and creates
a spreadsheet using the metadata. This example demonstrates some basic odmlib features.

## Getting Started
To run xls2define.py from the command-line: 

`python xls2define.py -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml`

The odmlib package must be installed to run xls2define. See the 
[odmlib repository](https://github.com/swhume/odmlib) to get the odmlib package. Eventually, it 
may make its way into PyPi, but for now you'll need to install from the source. The odmlib 
README provides instructions for getting started.

## Limitations
The odmlib examples are basic programs intended to demonstrate some of the basic capabilities of odmlib.
The examples are not complete, production ready applications.

The odmlib package is still in development. Although odmlib supports all of ODM more work remains 
to complete all features for processing ClinicalData. The initial focus has been on getting 
the metadata sections complete. 