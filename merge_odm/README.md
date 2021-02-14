# merge_odm

## Introduction
The merge_odm program is an odmlib example application that generates a target ODM file with a CRF 
moved from a source ODM file. The merge_odm application merges a form in a source ODM file, such as might be
used as a CRF library, and moved into another, target, ODM file. This example demonstrates some basic odmlib
features.

## Getting Started
To run merge_odm.py from the command-line: `python merge_odm.py`

The application expects a source and target xml file in a data directory that exists in the same path as the
merge_odm.py application.

The odmlib package must be installed to run merge_odm. See the [odmlib repository](https://github.com/swhume/odmlib) 
to get the odmlib package. Eventually, it may make its way into PyPi, but for now you'll need to install from the 
source. The odmlib README provides instructions for getting started.

## Limitations
The odmlib examples are basic programs intended to demonstrate some of the basic capabilities of odmlib.
The examples are not complete, production ready applications.

The odmlib package is still in development. Although odmlib supports all of ODM more work remains 
to complete all features for processing ClinicalData. The initial focus has been on getting 
the metadata sections complete. 