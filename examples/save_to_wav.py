from utts import Utterance, Synth

LEXICON_DB = "/sd/lexicon.db"
DIPHONES_DB = "/sd/diphones.db"

def tts(text, output):
    print(f"Converting text to speech: {text}")
    utterance = Utterance(text, LEXICON_DB)
    diphones = utterance.get_diphones()
    synth = Synth(diphones, DIPHONES_DB)
    synth.write_wav(output)
    print(f"Done. Output saved to: {output}")


input_text = "This is an example of speech synthesis"
output_file = "example.wav"

tts(input_text, output_file)
