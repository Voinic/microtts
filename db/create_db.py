import btree
import wave
import json
import os
import struct
import adpcm


f = open("lexicon.db", "w+b")
db = btree.open(f)
lexicon_symbols = ["AA", "AA0", "AA1", "AA2", "AE", "AE0", "AE1", "AE2", "AH", "AH0", "AH1", "AH2", "AO", "AO0", "AO1", "AO2", "AW", "AW0", "AW1", "AW2", "AY", "AY0", "AY1", "AY2", "B", "CH", "D", "DH", "EH", "EH0", "EH1", "EH2", "ER", "ER0", "ER1", "ER2", "EY", "EY0", "EY1", "EY2", "F", "G", "HH", "IH", "IH0", "IH1", "IH2", "IY", "IY0", "IY1", "IY2", "JH", "K", "L", "M", "N", "NG", "OW", "OW0", "OW1", "OW2", "OY", "OY0", "OY1", "OY2", "P", "R", "S", "SH", "T", "TH", "UH", "UH0", "UH1", "UH2", "UW", "UW0", "UW1", "UW2", "V", "W", "Y", "Z", "ZH"]
files = os.listdir("cmudict")
for n, filename in enumerate(files):
    print(f"File {n}/{len(files)}: {filename}")
    lexicon = json.load(open("cmudict/"+filename, "r"))
    for i, word in enumerate(lexicon):
        print(f"Word {i}/{len(lexicon)}: {word}")
        res = bytearray()
        for variant in lexicon[word]:
            for symbol in variant:
                code = lexicon_symbols.index(symbol)+1
                res.extend(code.to_bytes(1, "little", False))
            res.extend(b'\x00')
        res = res[:-1]
        db[word] = res
    db.flush()
db.close()
f.close()


compress = False
f = open("diphones.db", "w+b")
#compress = True
#f = open("diphones_lq.db", "w+b")
db = btree.open(f)
block_size = 1024
files = os.listdir("diphones")
for n, filename in enumerate(files):
    print(f"File {n}/{len(files)}: {filename}")
    with wave.open("diphones/"+filename, 'rb') as input_file:
        out_data = bytearray()
        in_data = []
        audio_data = input_file.readframes(block_size)
        while audio_data:
            if compress:
                in_data += struct.unpack(f"<{len(audio_data)//2}h", audio_data)
            else:
                out_data.extend(audio_data)
            audio_data = input_file.readframes(block_size)
        data_encoded = adpcm.encoder(in_data)
        if compress:
            for i in range(0, len(data_encoded)-2, 2):
                samp1, samp2 = data_encoded[i:i+2]
                two_samples = samp1 | (samp2 << 4)
                out_data.append(two_samples)
        db[bytes(filename[:-4], 'utf-8')] = out_data
db.close()
f.close()
