# ToBeGreen

### Description

ToBeGreen is a python3 library used for (de)serialization between python data objects and blobs, and verification that the python objects conform to a particular type structure. It is intended as a quick-implementation and prototyping tool for anyone who just needs to push data across a network between 2 python processes, while avoiding the following issues:
- Arbitrary code execution upon deserialization as in the default 'pickle' library and the extension 'dill' library
- Not being able to package blobs or arbitrary objects easily as in 'json' libraries
- Being extremely slow as in 'yaml' libraries

### Naming Notes

This library used to be named 'Thwomp'. It is now named 'ToBeGreen' based upon a terrible pun in Spanish: the primary functions that this library provides are 'Ser', 'Ver', and 'Des' (for serialize, verify, and deserialize, respectively). Together, this would form the Spanish phrase 'Ser Verdes' (to be green).

### Installation

After cloning this repository, run './install-hooks.sh' from the project root directory in order to install some git hooks that are useful for project development.

### Copyright Information

See the file 'LICENSE.txt' for details.