# Akai MPK Mini Flasher

Simple python-based command line tool to configure the Akai MPK Mini 1. Generation. The native configuration tool (32-bit) is not longer supported and does not work anymore on newer MAC's that only allow 64-bit programs. A [web-based interface from gljubojevic](https://github.com/gljubojevic/akai-mpk-mini-editor/tree/master) already reversed engineered the midi protocol, but the tool is not fully implemented yet. Meanwhile this interface should enable people to flash configurations from their command line.

## Install

Installation is described for Mac only, but it could work on other platforms as well with small changes in the installation procedure.

1. Make sure to have **Python >=3.12** with `python -V`.

2. This package uses the mido python library with the rtmidi backend. rtmidi has to be installed first with

```bash
brew install rtmidi
```

3. Create a python virtual environment and install the dependencies by running:

```bash
sudo chmod +x install.bash
./install.bash
```

## Usage

Make sure your midi keyboard is connected to your computer. The virtual environment has to be sourced in every new terminal. For help on the specific arguments run:

```bash
source venv/bin/activate
python miniflasher.py -h
```

### Read example

```bash
source venv/bin/activate
python miniflasher.py r 1 presets/slot1.json
```

### Write Example

```bash
source venv/bin/activate
python miniflasher.py w 1 presets/factory1.json
```

## Notes

The tool primitively checks if a configuration contains valid values. However, it is not guaranteed that wrong values won't "slip through". Just be careful what values you type in and check [gljubojevic](https://github.com/gljubojevic/akai-mpk-mini-editor/tree/master)'s site for a full description on the values that can be set.
