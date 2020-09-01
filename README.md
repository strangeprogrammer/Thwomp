# Thwomp

### Description

Thwomp is a python3 library used for (de)serialization between python data objects and bytes strings. It is intended as a quick-implementation and prototyping tool for anyone who just needs to push data across a network between 2 python processes, while avoiding the following issues:
- Arbitrary code execution upon deserialization as in the default 'pickle' library and the extension 'dill' library
- Not being able to package binary objects or arbitrary objects as in the defualt 'json' library

### Copyright Information

See the file 'LICENSE.txt' for details.