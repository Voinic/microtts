# MicroTTS

Simple TTS library for MicroPython that works offline

Tis library is a MicroPython port of concatanative diphone-based speach synthesizer. It uses lexicon database to convert words to phonemes, which was converted from [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict). Diphones database was converted from diphone collection by Alan W Black and Kevin Lenzo ([License](https://raw.githubusercontent.com/Voinic/microtts/master/diphones_license.txt)).

## Installation

1. Paste folowing code to REPL console to download library

    ```python
    import mip
    mip.install("github:Voinic/microtts")
    ```

2. Copy [lexicon.db](https://raw.githubusercontent.com/Voinic/microtts/master/lexicon.db) and [diphones.db](https://raw.githubusercontent.com/Voinic/microtts/master/diphones.db) to SD Card

## Usage

```python
from utts import Utterance, Synth

LEXICON_DB = "/sd/lexicon.db"
DIPHONES_DB = "/sd/diphones.db"

text = "This is a test"

utterance = Utterance(text, LEXICON_DB)
diphones = utterance.get_diphones()

synth = Synth(diphones, DIPHONES_DB)
audio = synth.get_audio()
```

## Usage examples

- [examples/save_to_wav.py](https://github.com/Voinic/microtts/blob/master/examples/save_to_wav.py) - Converts given text to speach and saves result into WAV file.
- [examples/direct_playback.py](https://github.com/Voinic/microtts/blob/master/examples/direct_playback.py) - Prompts user for input text and sends output audio to I2S DAC