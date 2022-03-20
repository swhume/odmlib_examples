# define2xls

## Introduction
Use the define2-1-to-xlsx example instead of this one. The Define-XML v2.1 examples are getting more use and testing 
creating study Define-XML files, so they're getting updated more frequently. 

The define2xls program is an odmlib example application that generates an Excel spreadsheet that contains the content
of a Define-XML v2.0 file. The Exel spreadsheet version of the makes it easier for many to edit or create new content
to include in a Define-XML v2.0 file. The companion xls2define program takes the updated spreadsheet and generates a
Define-XML file. This example demonstrates some basic odmlib
features.

## Getting Started
To run define2xls.py from the command-line: 

`python define2xls.py -d ./data/sdtm-xls-define.xml -p ./data/`

The odmlib package must be installed to run define2xls. See the [odmlib repository](https://github.com/swhume/odmlib) 
to get the odmlib package. Eventually, it may make its way into PyPi, but for now you'll need to install from the 
source. The odmlib README provides instructions for getting started.

## Limitations
The odmlib examples are basic programs intended to demonstrate some of the basic capabilities of odmlib.
The examples are not complete, production ready applications.

The odmlib package is still in development. Although odmlib supports all of ODM more work remains 
to complete all features for processing ClinicalData. The initial focus has been on getting 
the metadata sections complete. 