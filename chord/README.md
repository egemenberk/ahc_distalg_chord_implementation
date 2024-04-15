# Chord Protocol Implementation

This repository contains the implementation of the Chord protocol using the AHCv2 platform. The Chord protocol is a distributed lookup protocol, intended to efficiently locate a node within a network of nodes when supplied with its key.

## Repository Structure

The repository contains the following Python files:

- [`chord_component.py`](./chord_component.py)
- [`component_registry.py`](./component_registry.py)

## `chord_component.py` Brief

This [chord_component.py](./chord_component.py) file contains the `ChordComponent` class, encompassing definitions and methods specific to the Chord protocol's implementation.

Key functions include `find_successor` and `find_predecessor` and the `join` method, which assists in integrating a node into the pre-existing network or creating a new one if none exist.

## `component_registry.py` Overview

A supportive [Python file](./component_registry.py) in the codebase, component_registry.py contains a singleton class, `ComponentRegistry`, which maintains a registry of components deployed in the environment.

This class provides methods to add components to the registry, find keys corresponding to particular instances, and retrieve components using keys. The `init` function is instrumental in initializing all the components registered, marking the starting point of the system.
