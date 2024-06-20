import btree
import struct

import adpcm

class Utterance:
    def __init__(self, utterance, lexicon):
        """
        Initialize utterance.
        """
    
        # Initialize token filter and pronunciation lexicon
        self.lexicon_symbols = ["AA", "AA0", "AA1", "AA2", "AE", "AE0", "AE1", "AE2", "AH", "AH0", "AH1", "AH2", "AO", "AO0", "AO1", "AO2", "AW", "AW0", "AW1", "AW2", "AY", "AY0", "AY1", "AY2", "B", "CH", "D", "DH", "EH", "EH0", "EH1", "EH2", "ER", "ER0", "ER1", "ER2", "EY", "EY0", "EY1", "EY2", "F", "G", "HH", "IH", "IH0", "IH1", "IH2", "IY", "IY0", "IY1", "IY2", "JH", "K", "L", "M", "N", "NG", "OW", "OW0", "OW1", "OW2", "OY", "OY0", "OY1", "OY2", "P", "R", "S", "SH", "T", "TH", "UH", "UH0", "UH1", "UH2", "UW", "UW0", "UW1", "UW2", "V", "W", "Y", "Z", "ZH"]
        self.filter = [" ", "\n", "\r", "'", '\\', '`', '(', '_', '#', ']', '{', '+', '/', '=', '|', ';', '?', '$', '^', '*', '%', '&', '~', '!', '<', '"', ')', '[', '-', ',', '.', ':', '>', '@', '}']
        self.utterance = utterance
        self.dbfile = open(lexicon, "rb")
        self.db = btree.open(self.dbfile)

        # Tokenize and extract phones from input utterance
        self.phones = []
        for word in self.get_words(utterance):
            for phone in self.get_phones(word):
                self.phones.append(phone)
    
    def __del__(self):
        self.db.close()
        self.dbfile.close()
    
    def pron_variants(self, word):
        variants = []
        current_variant = []
        for byte in self.db[word]:
            if byte == 0:
                variants.append(current_variant)
                current_variant = []
            else:
                symbol = self.lexicon_symbols[byte-1]
                current_variant.append(symbol)
        # Append the last variant if not empty
        if current_variant:
            variants.append(current_variant)
    
        return variants

    def get_words(self, utterance):
        """
        Return tokenized utterance without punctuation.
        """
        words = []
        
        for word in utterance.split():
            # Exclude words in filter
            for sign in self.filter:
                word = word.replace(sign, "")

            # Exit if word contains non-alphabetic characters
            if not word.isalpha():
                raise NotImplementedError(f"{word}: Text must only contain alphabetic characters")
            
            words.append(word.lower())

        return words

    def get_phones(self, word, variant=0):
        """
        Given a word, return a normalized phonemic transcription
        if available in pronunciation lexicon. Otherwise, exit
        program.
        """
        # Select variant pronunciation if it exists
        word = bytes(word, "utf-8")
        
        if word not in self.db:
            raise NotImplementedError(f"Couldn't transcribe '{word}'")
        
        lex_entry = self.pron_variants(word)
        if variant <= len(lex_entry) - 1:
            pronunciation = lex_entry[variant]
        else:
            pronunciation = lex_entry[0]

        return map(lambda phone: phone.lower().rstrip("012"), pronunciation)

    def get_diphones(self):
        """
        Expand phone sequence into a diphone sequence.
        """

        # Initialize diphone sequence
        diphones = [[None, self.phones[0]]]

        # Expand phones into diphones
        for i in range(len(self.phones) - 1):
            ph1 = self.phones[i]
            ph2 = self.phones[i + 1]
            diphones.append([ph1, ph2])

        # Add last diphone to sequence
        diphones.append([self.phones[len(self.phones) - 1], None])
        return diphones


class Synth:
    SAMPLE_RATE = 16000
    BITS_PER_SAMPLE = 16
    NUM_CHANNELS = 1
    
    def __init__(self, diphones, diphones_db, compressed=False):
        """
        Initialize synthesizer.
        """
        self.diphones = diphones
        self.dbfile = open(diphones_db, "rb")
        self.db = btree.open(self.dbfile)
        self.db_compressed = compressed
    
    def __del__(self):
        self.db.close()
        self.dbfile.close()

    def get_audio(self):
        """
        Return synthesized output audio data containing
        the concatenated audio for the input diphone sequence.
        """

        # Create audio sequence from diphones
        output_audio = bytearray()
        for diphone in self.diphones:
            ph1 = diphone[0] if diphone[0] is not None else "pau"
            ph2 = diphone[1] if diphone[1] is not None else "pau"
            key = bytes(f"{ph1}-{ph2}", "utf-8")
            try:
                raw_audio = self.db[key]
            except KeyError:
                print(f"{key} don't exist in database")
            if self.db_compressed:
                audio = []
                for two_samples in raw_audio:
                    audio.append(two_samples&0x0f)
                    audio.append((two_samples >> 4)&0x0f)
                decoded_audio = adpcm.decoder(audio)
                packed_audio = struct.pack(f"<{len(audio)}h", *decoded_audio)
                output_audio.extend(packed_audio)
            else:
                output_audio.extend(raw_audio)

        return output_audio
    
    @staticmethod
    def create_wav_header(sampleRate, bitsPerSample, num_channels, num_samples):
        datasize = num_samples * num_channels * bitsPerSample // 8
        o = bytes("RIFF", "ascii")  # (4byte) Marks file as RIFF
        o += (datasize + 36).to_bytes(
            4, "little"
        )  # (4byte) File size in bytes excluding this and RIFF marker
        o += bytes("WAVE", "ascii")  # (4byte) File type
        o += bytes("fmt ", "ascii")  # (4byte) Format Chunk Marker
        o += (16).to_bytes(4, "little")  # (4byte) Length of above format data
        o += (1).to_bytes(2, "little")  # (2byte) Format type (1 - PCM)
        o += (num_channels).to_bytes(2, "little")  # (2byte)
        o += (sampleRate).to_bytes(4, "little")  # (4byte)
        o += (sampleRate * num_channels * bitsPerSample // 8).to_bytes(4, "little")  # (4byte)
        o += (num_channels * bitsPerSample // 8).to_bytes(2, "little")  # (2byte)
        o += (bitsPerSample).to_bytes(2, "little")  # (2byte)
        o += bytes("data", "ascii")  # (4byte) Data Chunk Marker
        o += (datasize).to_bytes(4, "little")  # (4byte) Data size in bytes
        return o
    
    def write_wav(self, filename):
        audio = self.get_audio()

        # create header for WAV file and write to SD card
        wav_header = Synth.create_wav_header(
            Synth.SAMPLE_RATE,
            Synth.BITS_PER_SAMPLE,
            Synth.NUM_CHANNELS,
            int(len(audio)*8/Synth.BITS_PER_SAMPLE),
        )
        
        with open(filename, "wb") as wav:
            wav.write(wav_header)
            wav.write(audio)

