from utts import Utterance, Synth

LEXICON_DB = "/sd/lexicon.db"

DIPHONES_DB = "/sd/diphones.db"
DB_COMPRESSED = False
#DIPHONES_DB = "/sd/diphones_lq.db"
#DB_COMPRESSED = True

POSTPROCESS = True

utterance = Utterance(LEXICON_DB)
synth = Synth(DIPHONES_DB, DB_COMPRESSED)

def tts(text, output):
    print(f"Transcribing text: {text}")
    utterance.process(text)
    diphones = utterance.get_diphones()
    print("Synthesizing speech")
    synth.synthesize(diphones, POSTPROCESS)
    print(f"Writing audio to {output}")
    synth.write_wav(output)
    print("Done.")


input_text = "This is an example of speech synthesis on a micro controller"
output_file = "example.wav"

tts(input_text, output_file)
