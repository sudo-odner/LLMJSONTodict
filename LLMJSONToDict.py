class LLMJSONToDict:
    def __init__(self):
        self._cursor_start = 0
        self._cursor_end = 0
        self._text = ""
        self._error_status = False
        self._error_info = ""

    def _new_text(self, new_text):
        self._cursor_start = 0
        self._cursor_end = 0
        self._text = new_text
        self._error_status = False
        self._error_info = ""

    # Error if in recursion find error
    def _error(self, info: str):
        self._error_status = True
        self._error_info = info

    # Custom error
    def _error_invalid_char(self, info: str):
        self._error("""Invalid characters. Use single or dabble quotes for siting.""" + "Data: " + f"({info})")

    def _error_invalid_dict(self):
        self._error("""Length of data key is not equal to length of data value""")

    def _error_element_not_closed(self, info: str):
        self._error("""Element is not closed""" + "Data: " + f"({info})")

    # Filter key in JSON object.
    # Key in JSON always is string, some time one word without single or dabble quotes.
    # If _text is string with single or dabble quotes -> add all body inside like key
    # Else _text without single or dabble quotes -> check space in name -> if True add key, else set Error
    def _filter_key(self, text: str) -> str:
        text = text.strip()
        if (text[0] and text[-1] == "'") or (text[0] and text[-1] == '"'):
            return text[1:-1]
        else:
            if text.find(" ") != -1:
                self._error_invalid_char(text)
            else:
                return text
        return text

    # For check float value
    def _is_float(self, element: any) -> bool:
        try:
            float(element)
            return True
        except ValueError:
            return False

    # Filter value
    # In JSON have some type: array(list), object(dict), string, number (integer | float), boolean, null(None)
    # This code convert string, number (integer | float), boolean, null(None)
    # If we have str with zero rune -> return None
    def _filter_value(self, text: str | list | dict) -> list | dict | str | int | float | bool | None :
        # If _text is array or dict, return array or dict
        if (type(text) == list) or (type(text) == dict):
            return text
        # Else data is not array and dict, set type
        text = text.replace("\n", ' ')
        text = text.strip()
        # If _text is Zero return None
        if len(text) == 0:
            return None
        elif (text[0] and text[-1] == "'") or (text[0] and text[-1] == '"'):
            return text[1:-1]
        elif text.isnumeric():
            return int(text)
        elif self._is_float(text):
            return float(text)
        elif text.lower().find("true") != -1:
            return True
        elif text.lower().find("false") != -1:
            return False
        elif text.lower().find("null") != -1:
            return None
        elif text.lower().find("none") != -1:
            return None

        # If not found correct type -> set Error and return None.
        self._error_invalid_char(text)
        return None

    # Creating and filtering dict from array.
    # Array created with pattern: first value -> key, second value -> value.
    # Example: ["some", 1, "this is key", "this value"] -> {"some": 1, "this is key": "this value"}
    # If we have different quantity key and value in array -> set Error.
    def _create_dict(self, data: list) -> dict:
        # Set key array and value array
        data_key, data_value = data[::2], data[1::2]
        # If array key and value have different quantity -> set Error.
        if len(data_key) != len(data_value):
            self._error_invalid_dict()
            return dict()

        new_dict = dict()
        for idx in range(len(data_key)):
            # Create a key and a value with a filtered type.
            name_key, name_val = self._filter_key(data_key[idx]), self._filter_value(data_value[idx])
            # Check state Error, if we get an error -> exit the loop, else continue.
            if self._error_status:
                return dict()
            else:
                new_dict[name_key] = name_val

        return new_dict

    # Creating and filtering the received array
    # If we have different quantity key and value in array -> set Error.
    def _create_array(self, data: list) -> list:
        new_array = list()
        for i in range(len(data)):
            # Create a value with a filtered type.
            new_element = self._filter_value(data[i])
            # Check state Error, if we get an error -> exit the loop, else continue.
            if self._error_status:
                return list()
            else:
                new_array.append(new_element)

        return new_array

    # Main function with recursion
    # We have three types of trigger:
    # 1. Deepening -> '{', '}', '[', ']'. They are necessary for deep recursion of the search for a certain type element.
    # 2. Separation -> ',', ':', '}', ']'. They are necessary to perform the separation of elementsю
    # 3. Contextual -> '/', '#', '\n', '"', "'". They needed for understand reading rune. In data string? This is comment?
    def _next(self) -> list | dict:
        _last_rune = ""

        _context_value_dict = False

        _context_comment = False
        _context_tab = False
        _context_comment_index = 0
        _context_tab_index = 0

        _last_str = ""
        _context_str = False

        parts = list()
        while self._cursor_end < len(self._text):
            rune = self._text[self._cursor_end]
            # If last rune is not set
            if _last_rune == '' and (rune == '{' or rune == '['):
                _last_rune = rune
                self._cursor_start = self._cursor_end + 1
            # If last rune is '['
            elif _last_rune == '[' and not _context_str:
                if rune == ':':
                    # If rune have ':' in array, and it not in str context -> set Error
                    self._error_invalid_char("Array can't have ':'")
                    return list()
                if rune == ',':
                    # If rune have ',' in array - we create new part from self.context + 1 to self.context + _local_idx
                    # After set _local_idx
                    # if part is '', not append in parts
                    _element_part = self._text[self._cursor_start:self._cursor_end]
                    self._cursor_start = self._cursor_end + 1
                    if _element_part.strip() != '':
                        parts.append(_element_part)
                elif rune == ']':
                    # If rune have ']' in array - we create last part from self.context + 1 to self.context + _local_idx
                    # After set _local_idx
                    # if part is '', not append in parts
                    # After return from recursion
                    _element_part = self._text[self._cursor_start:self._cursor_end]
                    self._cursor_start = self._cursor_end + 1
                    if _element_part.replace("\n", " ").strip() != "":
                        parts.append(_element_part)

                    return self._create_array(parts)
                elif rune == '}':
                    # If rune have '}' in array - set error
                    self._error("Unexpected end of array")
                elif rune == '{' or rune == '[':
                    # If find new object or array
                    # Set new self._cursor_start += _local_idx, and set _local_idx
                    # After recursion add new part
                    self._cursor_start = self._cursor_end
                    _element_part = self._next()
                    self._cursor_start = self._cursor_end + 1
                    parts.append(_element_part)
                    # If error inside then go out from recursion
                    if self._error_status:
                        return list()
            # If last rune is '{'
            elif _last_rune == '{' and not _context_str:
                if rune == ':':
                    # If find ':' check comment.
                    #   If we haven't comment -> add key and open context_dict to add value
                    #   Else wait when find \n, then add key and open context_dict to add value
                    if _context_comment:
                        if _context_tab:
                            _element_part = self._text[_context_tab_index:self._cursor_end]
                            self._cursor_start = self._cursor_end + 1
                            if _element_part.strip() != '':
                                parts.append(_element_part)
                                _context_comment = False
                                _context_tab = False
                                _context_value_dict = True
                            pass
                        pass
                    else:
                        _element_part = self._text[self._cursor_start:self._cursor_end]
                        self._cursor_start = self._cursor_end + 1
                        if _element_part.strip() != '':
                            parts.append(_element_part)
                            _context_value_dict = True
                            _context_comment = False
                            _context_tab = False
                elif rune == ',':
                    # If find ',' check comment.
                    #   If we have open context_dict -> add value
                    #   Else next rune
                    if _context_value_dict:
                        _element_part = self._text[self._cursor_start:self._cursor_end]
                        self._cursor_start = self._cursor_end + 1
                        if _element_part.strip() != '':
                            parts.append(_element_part)
                            _context_value_dict = False
                    else:
                        self._cursor_start = self._cursor_end + 1
                elif rune == '}':
                    # If find '}' check comment.
                    #   If we have open context_dict -> add value
                    #   Else return dict
                    if _context_value_dict:
                        _element_part = self._text[self._cursor_start:self._cursor_end]
                        self._cursor_start = self._cursor_end + 1
                        if _element_part.replace("\n", " ").strip() != "":
                            parts.append(_element_part)

                    return self._create_dict(parts)
                elif rune == ']':
                    # If rune have ']' in array - set error
                    if not _context_comment:
                        self._error("Unexpected end of object")
                        return list()
                # If find new object or array
                elif rune == '[' or rune == '{' :
                    # If find new object or array
                    # Set new self._cursor_start += _local_idx, and set _local_idx
                    # After recursion add new part
                    if _context_value_dict:
                        self._cursor_start = self._cursor_end
                        _element_part = self._next()
                        self._cursor_start = self._cursor_end + 1
                        parts.append(_element_part)
                        _context_value_dict = False
                        # If error inside then go out from recursion
                        if self._error_status:
                            return list()
                    else:
                        self._error("Unexpected end of object")
                        return list()


            # For understand start and end index comment LLM
            if (not _context_comment) and (not _context_str) and (rune == '/' or rune == '#') and _last_rune != '':
                _context_comment = True
                _context_comment_index = self._cursor_end + 1
            if _context_comment and (not _context_str) and rune == '\n' and _last_rune != '':
                _context_tab = True
                _context_tab_index = self._cursor_end + 1

            # For understand context is string or not
            if (not _context_str) and (rune == "'" or rune == '"') and _last_rune != '':
                _last_str = rune
                _context_str = True
            elif _context_str and (_last_str == rune):
                _last_str = ""
                _context_str = False

            self._cursor_end += 1
        self._error_element_not_closed(_last_rune)
        return list()

    def custom_load(self, json: str) -> (list | dict, str):
        self._new_text(json)

        result, error = self._next(), self._error_info
        return result, error
