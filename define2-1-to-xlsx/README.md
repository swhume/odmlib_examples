# define2-1-to-xlsx

## Introduction
The define2-1-to-xlsx program is an odmlib example application that generates an Excel spreadsheet that contains the 
content of a Define-XML v2.1 file. The Exel spreadsheet version of the makes it easier for many to edit or create new 
content to include in a Define-XML v2.1 file. The companion xlsx2define2-1 program takes the updated spreadsheet and 
generates a Define-XML v2.1 file. This example demonstrates some basic odmlib features.

## Getting Started
To run define2-1-to-xlsx.py from the command-line: 

`python define2-1-to-xlsx.py -d ./data/sdtm-xls-define.xml -p ./data/`

The odmlib package must be installed to run define2-1-to-xlsx. See the 
[odmlib repository](https://github.com/swhume/odmlib) to get the source code and the latest version of the odmlib 
package. You may also install odmlib from PyPi with the understanding that it is still in development so might
not have everything available in the odmlib repository. To install from PyPi:

'pip install odmlib'

The odmlib README provides instructions for getting started.

## Limitations
The odmlib examples are basic programs intended to demonstrate some of the basic capabilities of odmlib.
The examples are not complete, production ready applications. However, I'm happy to update these applications to 
accommodate new feature or bug fixes and will also review pull requests.

The odmlib package is still in development.