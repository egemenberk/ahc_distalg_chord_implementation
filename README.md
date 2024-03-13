# Distributed Algorithms on AHCv2

This is a template project for implementing distributed algorithms on AHCv2. By cloning and using this repository, you agree to GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007. 

## Install AHCv2

```pip3 install adhoccomputing```

or alternatively,

```
git clone https://github.com/cengwins/ahc.git
cd ahc
pip3 install .
```

or alternatively, you can checkout this project and run `make ahc`.

## Before Starting Implementation

There are some issues you have to address before starting implementation, please:


- Rename the keyword `chord` in any foldername (/chord and /docs/disalgname), in any filenames (docs/chord/chord.rst) and in any fields in any file (all instances in index.rst) to a **meaningfull abbreviation** of your distributed algorithm. Note that doc/substitutions.rst defines a keywork |chord| that has to be changed as well.
- Use restructured text for documentation. There is a conf.py and the associated Makefile in the project's root directory. Running``make`` in the project's root directory will provide you a guide on how to build the html, pdf, epub, etc. documentation. For example, run `make html` and open `index.html`  under `_build/html` with a browser.
- Do not edit anything in `_build`, `_static`, `_templates` directories.  
- In `conf.py`  edit `project, copyright, author, release` fields.

## Documenting

- Populate the rst files under the docs/chord: astract, algorithm, conclusion, introduction, results with the extension rst following restructured text syntax. The templates will guide you on what to write in each file. There is also a rubric for self-assessment.
- List your modules in code.rst under docs/chord
- An example implementation of the Snapshot algorithms are provided for your convenience, you can delete it.

## A helper tool for avoiding installation issues

You can use [ahc_dev_container](https://github.com/cengwins/ahc_dev_container.git) and follow the directive thereof.

