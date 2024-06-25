import btree
import struct
import re

try:
    import adpcm
except ImportError:
    print("Warning: adpcm module missing. Some features will be unavailable.")


class Synth:
    SAMPLE_RATE = 16000
    BITS_PER_SAMPLE = 16
    NUM_CHANNELS = 1
    
    def __init__(self, diphones_db, compressed=False):
        """
        Initialize synthesizer.
        """
        self.dbfile = open(diphones_db, "rb")
        self.db = btree.open(self.dbfile, cachesize=1024)
        self.db_compressed = compressed
    
    
    def __del__(self):
        self.db.close()
        self.dbfile.close()
    
    
    @micropython.native
    def get_diphone(self, diphone):
        key = bytes(diphone, "ascii")
        raw_audio = self.db[key]
        if not self.db_compressed:
            return struct.unpack(f"<{len(raw_audio)//2}h", raw_audio)
        else:
            audio = []
            for two_samples in raw_audio:
                audio.append(two_samples&0x0f)
                audio.append((two_samples >> 4)&0x0f)
            decoded_audio = adpcm.decoder(audio)
            return decoded_audio
    
    
    @micropython.native
    def naively_concatenate(self):
        self.output_audio = []
        for audio in self.output_audios:
            self.output_audio += audio


    # Main function to process the array
    @micropython.native
    def crossfade(self, seconds=0.02):
        """
        This function concatenates the waveforms by using window
        length cross-fading.
        :param seconds:
        :return:
        """
        self.output_audio = None

        # initialise the windowlength
        window_len = int(seconds*self.SAMPLE_RATE)

        # Begin by going through arrays in the saved list
        for array in self.output_audios:
            # Initialize the windowed array
            windowed_array = []

            # Calculate the windowed array in loop
            for i, sample in enumerate(array):
                if i < window_len:
                    window_coeff = i / (window_len - 1)
                elif i < len(array) - window_len:
                    window_coeff = 1
                else:
                    window_coeff = (len(array) - i - 1) / (window_len - 1)
                
                windowed_array.append(int(window_coeff * sample))
            
            # If diphones_array is None, initialize it
            if self.output_audio is None:
                self.output_audio = windowed_array
                continue

            # Calculate length of silence
            len_silence = len(self.output_audio) - window_len
            
            # Update diphones_array in loop
            for i in range(len(self.output_audio) + len(windowed_array) - window_len):
                if i < len(self.output_audio):
                    if i >= len_silence:
                        self.output_audio[i] += windowed_array[i - len_silence]
                else:
                    self.output_audio.append(windowed_array[i - len_silence])

    
    @micropython.native
    def add_silence(self):
        """
        Use the sampling rate, and length required
        to generate a numpy array for silence
        :return:
        """
        length = int(self.silence_length*self.SAMPLE_RATE)
        self.output_audios.append([0]*length)
    
    
    @micropython.native
    def synthesize(self, diphones, crossfade=False):
        # Create audio sequence from diphones
        self.output_audios = []
        
        for diphone in diphones:
            self.silence_length = 0
            
            try:
                # Delete silence specification in string form (for now...)
                key_no_sil = re.sub('[24]', '', diphone)

                # Find the diphone in db
                audio = self.get_diphone(key_no_sil)
                
                # put audio data into the bytearray
                self.output_audios.append(audio)
            except KeyError:
                print(f"{diphone} don't exist in database")

                # Attempt an emergency key search
                backupkey = self.emergency_diphone(diphone)
                
                if backupkey is None:
                    continue

                # Find the diphone in db
                audio = self.get_diphone(backupkey)
                
                # put audio data into the bytearray
                self.output_audios.append(audio)

            # investigate if a pau item had
            if diphone[-1] == '2':
                # 200ms of silence
                self.silence_length = 0.2

            if diphone[-1] == '4':
                # 400ms of silence
                self.silence_length = 0.4

            # append silence to the list if a value was added to variable self.silence_length during loop
            if self.silence_length != 0:
                self.add_silence()

        # join audio data chunks into one waveform
        self.crossfade() if crossfade else self.naively_concatenate()
    
    
    @micropython.native
    def emergency_diphone(self, lostkey):
        """
        Select an emergency diphone by using regex, this
        function will look through the dictionary's keys
        to find a key that is a near orthographic match
        to the lost key
        :param lostkey a key not in the dictionary
        :return: a new key to search
        """
        # Find the midpoint of the current diphone key
        midpoint = lostkey.find('-')

        # If '-' is not found, midpoint will be -1. Handle this case.
        if midpoint == -1:
            print("Invalid key format. No '-' found in the key.")
            return None

        # Key fragment is the latter phone of the lost key (anything past '-')
        fragmentlatter = lostkey[midpoint+1:]
        fragmentformer = lostkey[:midpoint+1]

        # Go backwards from the end of the key fragment
        for charindex in range(len(fragmentlatter.split())):
            # Two cases of latter key length:
            # 1: latter phone len == 2
            if len(fragmentlatter) == 2:
                ideal_key = re.compile('{}{}{}'.format(fragmentformer, fragmentlatter[charindex], '*'))
            # 2: latter phone len == 1
            elif len(fragmentlatter) == 1:
                ideal_key = re.compile('{}{}'.format(fragmentformer, '*'))
            else:
                print(f"invalid latter {fragmentlatter}")
                break

            # Search for the ideal key in the diphones dictionary
            for k in self.db.keys():
                k = str(k, "ascii")
                if re.match(ideal_key, k):
                    print(f"using '{k}' instead")
                    return k

        print("no emergency diphones were found")
        return None


    @micropython.native
    def get_audio(self, chunk_size=1024):
        """
        Return synthesized output audio data containing
        the concatenated audio for the input diphone sequence.
        """
        if self.output_audio is None:
            return bytearray()
        
        packed_audio = bytearray()
        num_chunks = (len(self.output_audio) + chunk_size - 1) // chunk_size  # Calculate the number of chunks needed

        for i in range(num_chunks):
            chunk = self.output_audio[i * chunk_size:(i + 1) * chunk_size]
            packed_audio.extend(struct.pack(f"<{len(chunk)}h", *chunk))
        
        return packed_audio
    
    
    @staticmethod
    def create_wav_header(sample_rate, bits_per_sample, num_channels, num_samples, data_format=1):
        datasize = num_samples * num_channels * bits_per_sample // 8
        header = bytes("RIFF", "ascii")  # (4byte) Marks file as RIFF
        header += (datasize + 36).to_bytes(4, "little")  # (4byte) File size in bytes excluding this and RIFF marker
        header += bytes("WAVE", "ascii")  # (4byte) File type
        header += bytes("fmt ", "ascii")  # (4byte) Format Chunk Marker
        header += (16).to_bytes(4, "little")  # (4byte) Length of above format data
        header += (data_format).to_bytes(2, "little")  # (2byte) Format type (1 - PCM)
        header += (num_channels).to_bytes(2, "little")  # (2byte)
        header += (sample_rate).to_bytes(4, "little")  # (4byte)
        header += (sample_rate * num_channels * bits_per_sample // 8).to_bytes(4, "little")  # (4byte)
        header += (num_channels * bits_per_sample // 8).to_bytes(2, "little")  # (2byte)
        header += (bits_per_sample).to_bytes(2, "little")  # (2byte)
        header += bytes("data", "ascii")  # (4byte) Data Chunk Marker
        header += (datasize).to_bytes(4, "little")  # (4byte) Data size in bytes
        return header
    
    
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

