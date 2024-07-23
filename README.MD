# MicroTTS

Simple TTS library for MicroPython that works offline

Tis library is a MicroPython port of concatanative diphone-based speach synthesizer. It uses lexicon database to convert words to phonemes, which was converted from [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict) ([License](https://raw.githubusercontent.com/Voinic/microtts/master/db/cmudict_license.txt)). Diphones database was converted from diphone collection by Alan W Black and Kevin Lenzo ([License](https://raw.githubusercontent.com/Voinic/microtts/master/db/diphones_license.txt)).

## Installation

1. Paste folowing code to REPL console to download library

    ```python
    import mip
    mip.install("github:Voinic/microtts")
    ```

2. Copy [lexicon.db](https://raw.githubusercontent.com/Voinic/microtts/master/db/lexicon.db) and any of [diphones.db](https://raw.githubusercontent.com/Voinic/microtts/master/db/diphones.db) and [diphones_lq.db](https://raw.githubusercontent.com/Voinic/microtts/master/db/diphones_lq.db) to SD-card or internal flash (if your have enough space)

Use diphones_lq.db contains recordings with IMA ADPCM compression. You can use it instead of diphones.db if your memory space is limitted. Note that sound quality will decrease.

## Usage

```python
from utts import Utterance, Synth

LEXICON_DB = "/sd/lexicon.db"

DIPHONES_DB = "/sd/diphones.db"
DB_COMPRESSED = False

CROSSFADE = 0.025

TEXT = "This is a test"

utterance = Utterance(LEXICON_DB)
synth = Synth(DIPHONES_DB, DB_COMPRESSED)

utterance.process(TEXT)
diphones = utterance.get_diphones()

synth.synthesize(diphones, CROSSFADE)
audio = synth.get_audio()
```

## Usage examples

- [examples/save_to_wav.py](https://github.com/Voinic/microtts/blob/master/examples/save_to_wav.py) - Converts given text to speach and saves result into WAV file.
- [examples/direct_playback.py](https://github.com/Voinic/microtts/blob/master/examples/direct_playback.py) - Prompts user for input text and sends output audio to I2S DAC.

## Creating databases

`/db` folder contains code and input files that was used for databases creation. Run this code using micropython interpreter, not regular python (I used Unix port of micropython).
