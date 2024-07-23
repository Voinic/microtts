import btree
import struct
import array
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
    
    
    def get_diphone(self, diphone):
        key = bytes(diphone, "ascii")
        raw_audio = self.db[key]
        if not self.db_compressed:
            return struct.unpack(f"<{len(raw_audio)//2}h", raw_audio)
        else:
            return self.unpack_adpcm(raw_audio)
    
    
    @micropython.viper
    @staticmethod
    def unpack_adpcm(raw_audio:object) -> object:
        encoded_audio = array.array("b", [])
        raw_audio_len = int(len(raw_audio))
        raw_audio_ptr = ptr8(raw_audio)
        for i in range(raw_audio_len):
            two_samples:int = raw_audio_ptr[i]
            encoded_audio.append(two_samples&0x0f)
            encoded_audio.append((two_samples >> 4)&0x0f)
        decoded_audio = adpcm.decode(encoded_audio)
        return decoded_audio
    
    
    @micropython.viper
    @staticmethod
    def crossfade(array1:object, array2:object, steps:int):
        len1 = int(len(array1))
        len2 = int(len(array2))
        
        if len2 == 0:
            return

        if len1 < steps:
            steps = len1
        if len2 < steps:
            steps = len2
        
        max_ushort = const(1 << 16)
        
        if len1 > 0:
            # Perform the crossfade
            step_increment = int(max_ushort // steps)
            for i in range(steps):
                fade_ratio = i * step_increment
                if fade_ratio > max_ushort:
                    fade_ratio = max_ushort
                inv_fade_ratio = max_ushort - fade_ratio
                array1[len1 - steps + i] = (int(array1[len1 - steps + i]) * inv_fade_ratio + int(array2[i]) * fade_ratio) >> 16
            
        # Copy the non-crossfaded part of array2
        for i in range(steps, len2):
            array1.append(array2[i])

    
    @micropython.native
    def add_silence(self):
        """
        Use the sampling rate, and length required
        to generate a numpy array for silence
        :return:
        """
        length = int(self.silence_length*self.SAMPLE_RATE)
        silence_arr = array.array("h", [0]*length)
        self.output_audios.append(silence_arr)
    
    
    @micropython.native
    def synthesize(self, diphones, crossfade=0):
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
        self.output_audio = array.array("h", [])
        if crossfade > 0:
            window_len = int(crossfade*self.SAMPLE_RATE)
        for audio in self.output_audios:
            if crossfade > 0:
                self.crossfade(self.output_audio, audio, window_len)
            else:
                self.output_audio.extend(audio)
    
    
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
    def get_audio(self, chunk_size=2048):
        """
        Return synthesized output audio data containing
        the concatenated audio for the input diphone sequence.
        """
        output_audio = self.output_audio
        
        if output_audio is None:
            return bytearray()
        
        output_audio_mv = memoryview(output_audio)
        
        packed_audio = bytearray()
        num_chunks = (len(output_audio) + chunk_size - 1) // chunk_size  # Calculate the number of chunks needed

        for i in range(num_chunks):
            chunk = output_audio_mv[i * chunk_size:(i + 1) * chunk_size]
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

