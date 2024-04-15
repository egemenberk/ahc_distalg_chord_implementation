# Chord Protocol Implementation

This repository contains the implementation of the Chord protocol using the AHCv2 platform. The Chord protocol is a distributed lookup protocol, designed to efficiently locate a node within a network of nodes given its key.

## Repository Structure

The repository contains the following Python files under the `./chord/` directory:

- [`./chord/chord_component.py`](./chord/chord_component.py)
- [`./chord/component_registry.py`](./chord/component_registry.py)

## `chord_component.py` Brief

This [file](./chord/chord_component.py) contains the `ChordComponent` class, encompassing definitions and methods specific to the Chord protocol's implementation.

Key functions include `find_successor` and `find_predecessor` and the `join` method, which assists in integrating a node into the pre-existing network or creating a new one if none exist.

## `component_registry.py` Overview

A supportive [Python file](./chord/component_registry.py) in the codebase, component_registry.py contains a singleton class, `ComponentRegistry`, which maintains a registry of components deployed in the environment.

This class provides methods to add components to the registry, find keys corresponding to particular instances, and retrieve components using keys. The `init` function is instrumental in initializing all the components registered, marking the starting point of the system.


## Install AHCv2

```pip3 install adhoccomputing```

or alternatively,

```
git clone https://github.com/cengwins/ahc.git
cd ahc
pip3 install .
```

or alternatively, you can checkout this project and run `make ahc`.


## Documenting

- Populate the rst files under the docs/chord: astract, algorithm, conclusion, introduction, results with the extension rst following restructured text syntax. The templates will guide you on what to write in each file. There is also a rubric for self-assessment.
- List your modules in code.rst under docs/chord
- An example implementation of the Snapshot algorithms are provided for your convenience, you can delete it.

## A helper tool for avoiding installation issues

You can use [ahc_dev_container](https://github.com/cengwins/ahc_dev_container.git) and follow the directive thereof.

