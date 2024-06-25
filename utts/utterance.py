import btree
import re

LEXICON_ALPHABET = ["AA", "AA0", "AA1", "AA2", "AE", "AE0", "AE1", "AE2", "AH", "AH0", "AH1", "AH2", "AO",
                    "AO0", "AO1", "AO2", "AW", "AW0", "AW1", "AW2", "AY", "AY0", "AY1", "AY2", "B", "CH",
                    "D", "DH", "EH", "EH0", "EH1", "EH2", "ER", "ER0", "ER1", "ER2", "EY", "EY0", "EY1",
                    "EY2", "F", "G", "HH", "IH", "IH0", "IH1", "IH2", "IY", "IY0", "IY1", "IY2", "JH",
                    "K", "L", "M", "N", "NG", "OW", "OW0", "OW1", "OW2", "OY", "OY0", "OY1", "OY2", "P",
                    "R", "S", "SH", "T", "TH", "UH", "UH0", "UH1", "UH2", "UW", "UW0", "UW1", "UW2", "V",
                    "W", "Y", "Z", "ZH"]

NUMBERS = {  'teens':{ '19':"nineteen", '18':"eighteen", '17':"seventeen", '16':"sixteen", '15':"fifteen",
                      '14':"fourteen", '13':"thirteen", '12': "twelve", '11': "eleven"},

            'digits':{  '9':"nine", '8':"eight", '7':"seven", '6':"six", '5':"five", '4':"four", '3':"three",
                        '2':"two", '1':"one"},

            'ordinals':{'1':"first", '2':"second", '3':"third", '4':"fourth", '5':"fifth", '6':"sixth",
                        '7':"seventh", '8':"eighth", '9':"ninth", '10':"tenth", '11':"eleventh",
                        '12':"twelfth", '13':"thirteenth", '14':"fourteenth", '15':"fifteenth", '16':"sixteenth",
                        '17':"seventeenth", '18':"eighteenth", '19':"nineteenth", '20':"twentieth",
                        '30':"thirtieth"},

            'decimals':{'1':"ten",'2':"twenty",'3':"thirty",'4':"forty",'5':"fifty",'6':"sixty",
                        '7':"seventy",'8':"eighty",'9':"ninety",'0':"o"},

            'hundreds':{'0':"hundred"},

            'mil':{'00':'thousand'}
        }

MONTHS = ["",
          "january",
          "february",
          "march",
          "april",
          "may",
          "june",
          "july",
          "august",
          "september",
          "october",
          "november",
          "december"]


class Utterance:
    def __init__(self, lexicon_db):
        """
        Initialize utterance.
        """
        self.phrase = None
        self.diphonelist = []
        
        self.dbfile = open(lexicon_db, "rb")
        self.db = btree.open(self.dbfile)
    
    
    def __del__(self):
        self.db.close()
        self.dbfile.close()
        
    
    def pron_variants(self, word):
        variants = []
        current_variant = []
        key = bytes(word, "ascii")
        for byte in self.db[key]:
            if byte == 0:
                variants.append(current_variant)
                current_variant = []
            else:
                symbol = LEXICON_ALPHABET[byte-1]
                current_variant.append(symbol)
        # Append the last variant if not empty
        if current_variant:
            variants.append(current_variant)
        return variants

    
    def spell(self):
        """
        This splits the phrase into letters and separates
        using full-stops.
        """
        spelllist = []
        tempphrase = ' '.join(self.phrase)
        for char in tempphrase:
            if not char in '.,?!:; ':
                spelllist.append(str('{}.'.format(char)))

        self.phrase = spelllist


    def unknownword(self, pron_attempt=None, unkword=None, i=0, flag=0):
        """
        Attempt to pronounce an unk (unknown word)
        by searching for words recursively!

        :param unkword: a unkword to pronounce
        :param flag: a flag that is used to indicate whether 3 recusion passes have been performed
        :return: cmu, letter for letter to pronounce the unkword
        """
        # begin indexing from the end of the word
        # (attempting to get the largest word possible)
        for index in range(len(unkword), 0, -1):
            # create a variable that is the number of characters until the index
            chars = unkword[:index]
            try:
                # If a pronunciation exists in the dictionary...
                # Add to flag, append pron_attempt and return to the function
                # with variables updates.
                flag += 1
                variant = self.pron_variants(chars)[i]
                pron_attempt.append(variant)
                return self.unknownword(pron_attempt, unkword[index:], i, flag)
            except KeyError:
                # Naturally, there will be keyerrors attempting
                # to index the cmudict with nonsense
                pass
            
            # If the function has been called more that three times from inside the method
            # then break, returning with basic isolated letter pronunciation rules for the remainder
            # of the word.
            """if flag > 2:
                print("Transcribing by letters")
                attempt = []
                for j in unkword[index-1:]:
                    attempt += self.db[j][i]
                print(attempt)
                pron_attempt.append(attempt)
                return self.unknownword(pron_attempt, unkword[index:], i, flag)"""

        if len(unkword) == 0:
            resultantpronunciation = [phone for wordfound in pron_attempt for phone in wordfound]
            print("Transcribing it as", resultantpronunciation)
            return resultantpronunciation


    def clean(self):
        """
        Cleans the self.phrase string using regex
        and turns it into a list.

        :return: a lowercase list cleaned of punctuation
        """
        self.phrase=re.sub('[\^%$@)(><=+&\[\]`-]', '', self.phrase).lower().split()

    
    def preprocess_dates_numbers(self):
        """
        This function normalizes dates, numbers
        
        :return: None
        """

        results = []
        for index in range(len(self.phrase)):
            self.paus_or_phone = self.phrase[index]
            self.paus_or_phone = re.sub('[.,;:?!]', '', self.paus_or_phone)

            # Check if the paus_or_phone is in date format
            if re.match('\\d+[.\-/]\\d+([\\.\\-/]\\d+|)', self.paus_or_phone):
                print(f"Found date: {self.paus_or_phone}")
                try:
                    pronounce = self.process_date()
                    print(f"Pronounce as {pronounce}")
                    results.extend(pronounce)
                except Exception as e:
                    print("Error processing date")
                    print(e)
                    continue
            
            # Check if the paus_or_phone is in emphasis format (emphasis addition still in development)
            elif re.match('([1-9]\\d?\\d?[-.\\s]?)?\\d\\d\\d[-.\\s]?\\d\\d\\d[-.\\s]?\\d\\d\\d\\d', self.paus_or_phone):
                print(f"Found phone number: {self.paus_or_phone}")
                try:
                    phone = re.sub('[-.\\s]', '', self.paus_or_phone)
                    pronounce = []
                    if len(phone) > 10:
                        pronounce.append("plus")
                        self.paus_or_phone = phone[:-10]
                        pronounce.extend(self.process_number())
                    for d in phone[-10:]:
                        if d == "0":
                            pronounce.append("o")
                        else:
                            self.paus_or_phone = d
                            pronounce.extend(self.process_number())
                    print(f"Pronounce as {pronounce}")
                    results.extend(pronounce)
                except Exception as e:
                    print("Error processing phone number")
                    print(e)
                    continue

            # Check if paus_or_phone is in number format (only whole integers can be read out)
            elif re.match('\\d+', self.paus_or_phone):
                print(f"Found number: {self.paus_or_phone}")
                try:
                    pronounce = self.process_number()
                    print(f"Pronounce as {pronounce}")
                    results.extend(pronounce)
                except Exception as e:
                    print("Error processing number")
                    print(e)
                    continue
                    
            else:
                results.append(self.paus_or_phone)

        self.phrase=results


    def process_date(self):
        """
        process_date takes a paus_or_phone that has the format of a
        date and normalizes the digits using British conventions
        params:
        :return:
        """
        
        results = []
        
        tokens = self.paus_or_phone.replace(".", " ").replace("-", " ").replace("/", " ").split()
           
        day_raw = tokens[0]
        day = self.get_day_str(day_raw)
        
        month_raw = int(tokens[1])
        if month_raw > 12:
            day = self.get_day_str(day_raw)
            month_raw = day_raw
        month = MONTHS[month_raw]
        
        results.append(month)
        results.append(day)
        
        if len(tokens) > 2:
            year_raw = tokens[2]
            if len(year_raw) == 2:
                year_raw = "19"+year_raw
            year = self.get_year_str(year_raw)
            results.extend(year)
        
        return results


    def get_day_str(self, d):
        """
        This function processes a day numeric string
        and returns a linguistic string that represents the day.

        :param d: a two-char string of a numeric day (e.g. d='06')
        :return: a phrase denoting the input param d (e.g. dstr='sixth')
        """

        day_ten_to_teen = NUMBERS['ordinals'][d] if d in NUMBERS['ordinals'] else None

        flag = (day_ten_to_teen or d[-2]!=0)

        day_zero_to_nine = NUMBERS['ordinals'][d[-1]] if d[-1] in NUMBERS['ordinals'] and not flag else None

        # If the date is not in the teens/ exception list of odd spelling then construct a string using indexing rules
        day_other=str()

        if not (day_zero_to_nine or day_ten_to_teen):
            decimal = NUMBERS['decimals'][d[0]]
            ordinal = NUMBERS['ordinals'][d[1]]
            day_other = ('{} {}').format(decimal, ordinal)

        day_to_word_list = [day_zero_to_nine, day_ten_to_teen, day_other]

        daystr = ' '.join(filter(None, day_to_word_list))

        return daystr


    def get_year_str(self, y):
        """
        This function takes a year (in string-numeric form from process_date
        and returns a linguistic string that represents the year.
        :param y: a four-char string of a numeric date (e.g. y='1999')
        :return: a phrase denoting the input param year (e.g. ystr='nineteen ninety nine'
        """
        # 1. Mid Digits:
        millenialexception1 = None
        millenialexception2 = None

        # Case a: generate 'thousand' for \d00\d. First check if date is millenial.
        mil_y = NUMBERS['mil'][y[-3:-1]] if y[-3:-1] in NUMBERS['mil'] else None

        # 2. Last Digits

        # Case a: generate '-teen' at end of date. e.g. 12,13,14.
        # Check last two digits & assign iff they are teen.
        teen_y = NUMBERS['teens'][y[-2:]] if y[-2:] in NUMBERS['teens'] else None

        # Case b: generate 'ten/-ty' at end of date. e.g. 20,40,60.
        # Check last two digits & assign str for these digits.
        decimal_zero_year = NUMBERS['decimals'][y[-2]] if y[-1] == '0' and not y[-2:] == '00' else None

        # Case c: generate 'digit' at end of date iff end digit
        # is not equal to 0 (in the case of decimal_zero_year).
        last_digit = NUMBERS['digits'][y[-1]] if y[-1] in NUMBERS['digits'] and not teen_y else None

        # Case d: Check the second to last digit in the date
        # and assign a str iff a digit has already been assigned.
        decimal_year = NUMBERS['decimals'][y[-2]] if last_digit and not mil_y and y[-2] in NUMBERS['decimals'] else None

        # Case e: generate 'hundred'. Check last two digits.
        hundreds_year = NUMBERS['hundreds'][y[-2]] if not mil_y and y[-2:] == '00' else None

        # 3. First Digits:

        # Case a: generate '-teen' at beg. of date. Check first two
        # digits & assign a str iff they are a teen.
        first_two_teens = NUMBERS['teens'][y[:2]] if y[:2] in NUMBERS['teens'] else None

        # Case b: generate 'ten/ -ty' at beg. of date iff first
        # two digits are of the form decimal-0.
        first_two_dec = NUMBERS['decimals'][y[0]] if y[0] in NUMBERS['decimals'] and not (first_two_teens or mil_y) else None

        # Case c: generate 'digit' at beg. of date iff mil_y=True and if
        # the first two digits are neither teens (19\d\d) nor decimals (20)
        first_digit = NUMBERS['digits'][y[0]] if not (first_two_teens or first_two_dec) and mil_y else None

        # The following if statement adds the word 'and' between a millenial year and a digit
        # and sets the variables to none thereafter. e.g. (two thousand and six)
        if mil_y and last_digit:
            millenialexception1 = mil_y
            millenialexception2 = last_digit
            mil_y = None
            last_digit = None

        # Print these to create the linguistic date structure
        year_to_word_list = [first_digit, mil_y, first_two_teens, first_two_dec,
                             millenialexception1, millenialexception2, hundreds_year, decimal_zero_year, decimal_year, teen_y, last_digit]
        
        # The following line filters out any of the above values that are None type, creating the final string ystr.
        return [value for value in year_to_word_list if not value is None]


    def process_number(self):
        """
        This function processes numbers
        from 1-9,999 in string format.

        :return: a normalized number string
        """

        number=self.paus_or_phone
        normalized_number=[]
        
        if len(number[-4:])==4:
            normalized_number.append(NUMBERS['digits'][number[-4]])
            normalized_number.append('thousand')

        if len(number[-3:])==3 and number[-3] in NUMBERS['digits']:
            normalized_number.append(NUMBERS['digits'][number[-3]])
            normalized_number.append('hundred')

        if len(number)>2 and not number[-2:]=='00':
            normalized_number.append('and')

        if not number[-2:]=='00' and (number[-1] in NUMBERS['digits'] or number[-2] in NUMBERS['decimals']):
            if len(number) > 1 and number[-2]=='0':
                if number[-1] in NUMBERS['digits']:
                    normalized_number.append(NUMBERS['digits'][number[-1]])
                    return normalized_number

            elif len(number)>1 and number[-2]=='1'and number[-1]!='0':
                normalized_number.append(NUMBERS['teens'][number[-2:]])
                return normalized_number

            else:
                if len(number)>1 and number[-2] in NUMBERS['decimals']:
                    normalized_number.append(NUMBERS['decimals'][number[-2]])

                if number[-1] in NUMBERS['digits']:
                    normalized_number.append(NUMBERS['digits'][number[-1]])
                    return normalized_number
        
        return normalized_number


    def get_diphones(self): # Initialise CMU sequence, add pauses, and turn into a diphone sequence
        """
        Initialise CMU sequence, add pauses, and
        turn into a diphone sequence
        :param pronunciation: the raw pronunciation from cmudict
        :return: a tuple of diphones
        """
        phonelist = [] # first, make a phonelist

        for cmupro in range(len(self.pronunciation)):
            for token in range(len(self.pronunciation[cmupro])):
                if self.pronunciation[cmupro][token] in '.:?!': # Some punctuation requires longer pauses
                    phonelist.append('pau4') # 400ms
                elif self.pronunciation[cmupro][token] == ',': # Other punctuation requires shorter pauses
                    phonelist.append('pau2') # 200ms
                else: # Most cases just require CMU substitution.
                    phonelist.append(re.sub('[0-9]', '', self.pronunciation[cmupro][token].lower()))

            if cmupro==len(self.pronunciation)-1 and phonelist[-1][-3:]!='pau': # Append pause
                phonelist.append('pau4')  # 400ms

        diphonelist = []

        for phone in range(len(phonelist)-1): # This for loop creates the diphones using phonelist indicies
            diphonelist.append(str(phonelist[phone]+'-'+phonelist[phone+1]))

        return diphonelist


    def punctuation(self):
        """
        Takes the list self.phrase and checks each end index and as to
        whether the end char is a punctuation character.
        number which is used later in the pipeline to create a pause.
        :return: a tuple containing a punctuation marker and word index for pauses
        """
        self.punctmarker = []
        for i in range(len(self.phrase)):
            if self.phrase[i][-1] in '.,;:?!':
                self.punctmarker.append((i,self.phrase[i][-1]))


    def delpunct(self):
        """
        deletes punctuation in the self.phrase list
        as one of the preprocessing steps in
        get_phone_seq()
        :return: None
        """
        q = []
        for i in self.phrase:
            #if args.spell:
            #    q.append(re.sub('[,;:?!]', '', i))
            #else:
            q.append(re.sub('[.,;:?!]', '', i))

        self.phrase=q

    
    def process(self, phrase, spell=False):
        """
        Postcondition: Diphone sequence is generated

        How: Turns a phrase into a listed sequence of diphones
        ready to be read by the synthesizer by A. Preprocessing
        the utterance, B. I) Searching for tokens in the CMU lexicon
        B. II) reintroducing punctuation and C. Changing the
        phonelist into a diphone list.

        :return: self.diphonelist
        """
        
        self.phrase = phrase
        self.pronunciation = []

        # Preprocess step 1a.: remove special chars, convert line to lower case, split line.
        self.clean()
        # Preprocess step 1b: preprocess i. dates and ii. numbers, iii. emphasis markers & update self.phrase
        self.preprocess_dates_numbers()
        # Preprocess step 2: spell
        if spell: self.spell()
        # Preprocess step 3a: store punctuation
        self.punctuation()
        # Preprocess step 3b: delete the remaining punctuation & update self.phrase
        self.delpunct()

        # Create a diphone word-marking list to keep track of words that become phones
        punctcount = 0
        for wordindex, word in enumerate(self.phrase):
            # Decide on a method later to choose an index depending on the word POS
            index_to_choose = 0

            # Load a word:
            try:
                self.pronunciation.append(self.pron_variants(word)[0])
            except KeyError:
                print(f"No transcription for word {word}")
                unk = self.unknownword([], word, index_to_choose, 0)
                self.pronunciation.append(unk)

            # Punctuation pause placement:
            if punctcount < len(self.punctmarker):
                # Reintroduce the punctuation markers into the utterance
                if wordindex == self.punctmarker[punctcount][0]:
                    # put the punctuation back into the list
                    self.pronunciation.append([self.punctmarker[punctcount][1]])
                    # add to the punctuation counter index
                    punctcount += 1

        # Return only the diphones list by joining the phones using '<phone>-<phone>'
