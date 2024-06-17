# Claudia
Claudia is a helper utility that simplifies setting up and managing a development environment for the XRP Ledger. 
It helps the user to run a local network using a built/installed instance of rippled. 
This network can be used to perform local testing and debugging.

Claudia was developed by the XRPL Automation Team as an internal tool to help with XRPL local development, debugging and
testing. As the tool matured, the team quickly realized its potential and decided to expose it outside of Ripple, so
that everyone can benefit from its capabilities.

Following are some of the important tasks that can be performed using Claudia:

- Build rippled from local code.
- Install rippled from pre-built binaries released by Ripple.
- Manage a local-mainnet network using local rippled instance.

---

## General Prerequisites

Claudia can be installed on both macOS and Ubuntu. Currently, there is no support for Windows. Following prerequisites
must be installed before installing Claudia:

- [Python3](https://www.python.org/)
    - Run ```python3 --version``` to check if Python3 is already installed.
    - If Python3 is not installed, please install it using the
      official [Python installer](https://www.python.org/downloads/).
    - Verify installation by running: ```python3 --version```
- [pip3](https://pip.pypa.io/en/stable/)
    - Run ```pip3 --version``` to check if Python3 is already installed.
    - If pip3 is not installed, follow the next steps:
        - macOS:
            - ```python3 -m ensurepip --upgrade```
        - Linux:
            - ```sudo apt update```
            - ```sudo apt install python3-pip```
        - Verify installation by running: ```pip3 --version```
- [docker](https://www.docker.com/)
    - Run ```docker --version``` to check if docker is already installed.
    - If docker is not installed, follow the next steps:
        - macOS:
            - Download and then run
              the [Docker Desktop installer for macOS](https://docs.docker.com/desktop/install/mac-install/).
        - Linux:
            - Download and then run
              the [Docker Desktop installer for Linux](https://docs.docker.com/desktop/install/linux-install/).

---

## Installation

Once the general prerequisites have been installed, Claudia can be installed
from [PyPi](https://pypi.org/project/claudia/). From your terminal please run:

    pip3 install claudia

### If you want to build Claudia from the local code, you can run:

      rm -fr build/ dist/ claudia.egg-info
      pip uninstall -y claudia
      python3 setup.py sdist bdist_wheel
      pip install dist/*.tar.gz
      rm -fr build/ dist/ claudia.egg-info

---

## Usage

Claudia has a bunch of self-explanatory features. Claudia CLI offers two CLI experiences:

1. Demo mode. This is an interactive mode that can help reduce typing efforts significantly. You would mostly navigate a
   pre-built menu using ↑ ↓ and ↵ keys. Minimal typing will be required.
2. (Standard) CLI mode.

### How to run Claudia CLI commands?

After installing claudia, go to your terminal and run claudia. Each command supports --help flag that displays the usage
and arguments. e.g. `claudia --help`, `claudia run --help` etc.

### How to run Claudia in demo mode?

From your terminal and type `claudia demo`.

---

## Features

Claudia offers a bunch of features which allows you to manage local rippled instance, manage networks, run tests and
even learn a few XRPL tricks. This section walks you through some major features.

### How to build rippled?

Claudia offers a way to build rippled from local code. You will need to
clone [rippled](https://github.com/XRPLF/rippled) repository first before starting with this step.

Once the repository has been cloned, you can build rippled as follows. Each option would require you to provide the ***absolute path*** to the cloned repository.

- CLI Mode
    - Run `claudia rippled build --repo <repo_path>`
- Demo Mode
    - Select `Custom XRPL Networks` -> `Build rippled from local code`

### How to install rippled?

Claudia offers a way to install rippled using the pre-built binaries distributed by Ripple.
By default, Claudia will choose binaries generated from the master branch.
You also have an option to from `master`, `develop` and `release` branches.
You can install rippled as follows:

- CLI Mode
  - Run `claudia rippled install` to install rippled binaries built from master branch.
  - Run `claudia rippled install --rippled_branch <branch_name>` and choose the rippled branch.
- Demo Mode
    - Select `Custom XRPL Networks` -> `Install rippled`

### How to switch between build and install rippled modes?

Once you build or install rippled, Claudia will remember that context. If you have already built and installed
rippled in both modes, and would like to switch between the two modes, run the following:

- CLI Mode
    - Run `claudia set-install-mode build` to set build mode.
    - Run `claudia set-install-mode install` to set install mode.
- Demo Mode
    - Select `Settings` -> `Set install mode as build` to set build mode.
    - Select `Settings` -> `Set install mode as install` to set install mode.

*Please note that all previously running networks will have to be stopped and started again after switching rippled
modes.*

### How to enable a feature in rippled?

Please note that there is no validation for feature name. Please make sure the feature name is correct (case-sensitive).
You can follow these instructions to enable a rippled feature:

- CLI Mode
    - Run `claudia enable-feature --feature <feature_name>`
- Demo Mode
    - Select `Settings` -> `Enable a rippled feature`

### How to disable a feature in rippled?

Please note that there is no validation for feature name. Please make sure the feature name is correct (case-sensitive).
You can follow these instructions to disable a rippled feature:

- CLI Mode
    - Run `claudia disable-feature --feature <feature_name>`
- Demo Mode
    - Select `Settings` -> `Disable a rippled feature`

### How to start a local-mainnet network?

Before you can start a local mainnet network, rippled has to be built or installed locally. Afterwards, you can follow
these instructions to start a local mainnet network:

- CLI Mode
    - Run `claudia local-mainnet start`
- Demo Mode
    - Select `Custom XRPL Networks` -> `Start local-mainnet`

This can take up to a minute. Once the network has been launched, you can access the network as follows:
- WebSocket (ws): 127.0.0.1:6001
- JSON-RPC (http): 127.0.0.1:5001

### How to stop a local-mainnet network?

You can follow these instructions to stop a local mainnet network:

- CLI Mode
    - Run `claudia local-mainnet stop`
- Demo Mode
    - Select `Custom XRPL Networks` -> `Stop local-mainnet`

### How to clean up your computer and free resources after running Claudia?

While using claudia, there are a few files created permanently. Also, there are a few system resources which are
reserved for future use. Running this command will delete these files and free up resources. As a result, any progress
made by using Claudia will be lost. This action cannot be undone. Resources can be freed and your machine can be freed
as follows:

- CLI Mode
    - Run `claudia clean`
- Demo Mode
    - Select `Settings` -> `Clean up the host and free resources`

### How to uninstall Claudia?

*We recommend that you clean up your machine before uninstalling Claudia.* Afterwards, please run:

    pip3 uninstall claudia

## Contributions

Claudia is developed by Ripple Automation Team. The following people contributed to this release:

- Manoj Doshi <mdoshi@ripple.com>
- Ramkumar SG <rsg@ripple.com>
- Kaustubh Saxena <ksaxena@ripple.com>
- Michael Legleux <mlegleux@ripple.com>
- Anagha Agashe <aagashe@ripple.com>
- Mani Mounika Kunasani <mkunasani@ripple.com>
