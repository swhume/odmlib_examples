# xlsx2define2-1

## Introduction
The xlsx2define2-1 program is an odmlib example application that generates a Define-XML v2.1 file from 
an Excel spreadsheet that contains the study metadata needed to create the Define-XML file. The Exel 
spreadsheet version of the makes it easier for many to edit or create new content to include in a 
Define-XML v2.1 file. The companion define2-1-to-xlsx program takes the generated Define-XML file and creates
a spreadsheet using the metadata. This example demonstrates some basic odmlib features.

## Getting Started
To run xls2define.py from the command-line: 

`python xls2define.py -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml`

Or, to run it with both XML schema validation (-v) and some basic conformance checking (-c):

`-v -c -e ./data/odmlib-define-metadata.xlsx -d ./data/odmlib-roundtrip-define.xml 
-s "/home/sam/standards/DefineV211/schema/cdisc-define-2.1/define2-1-0.xsd`

The odmlib package must be installed to run xlsx2define2-1. See the 
[odmlib repository](https://github.com/swhume/odmlib) to install the odmlib source code and latest features. 
The odmlib package can also be installed from PyPi with the understanding that it is still in development 
so might not have everything available in the odmlib repository. It can be installed from PyPi using:

'pip install odmlib'

The odmlib README provides instructions for getting started.

## Limitations
The odmlib examples are basic programs intended to demonstrate some of the basic capabilities of odmlib.
The examples are not complete, production ready applications. However, I'm happy to update these applications 
to accommodate new feature or bug fixes and will also review pull requests.

The odmlib package is still in development. 