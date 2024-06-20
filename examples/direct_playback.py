from machine import I2S
from machine import Pin
from utts import Utterance, Synth

LEXICON_DB = "/sd/lexicon.db"

DIPHONES_DB = "/sd/diphones.db"
DB_COMPRESSED = False
#DIPHONES_DB = "/sd/diphones_lq.db"
#DB_COMPRESSED = True

SCK_PIN = 37
WS_PIN = 38
SD_PIN = 36

audio_out = I2S(0,
    sck=Pin(SCK_PIN),
    ws=Pin(WS_PIN),
    sd=Pin(SD_PIN),
    mode=I2S.TX,
    bits=Synth.BITS_PER_SAMPLE,
    format=I2S.MONO,
    rate=Synth.SAMPLE_RATE,
    ibuf=1024,
)

def tts(text):
    print(f"Converting text to speech: {text}")
    utterance = Utterance(text, LEXICON_DB)
    diphones = utterance.get_diphones()
    synth = Synth(diphones, DIPHONES_DB, DB_COMPRESSED)
    audio = synth.get_audio()
    print("Playing...")
    audio_out.write(audio)
    print("Done.")


try:
    while True:
        input_text = input("Input text to speak (Ctrl-C to exit): ")
        tts(input_text)
except KeyboardInterrupt:
    print("Exiting.")

audio_out.deinit()