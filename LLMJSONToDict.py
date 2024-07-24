class LLMJSONToDict:
    def __init__(self):
        self._cursor = 0
        self.text = ""
        self._status_error = False
        self._status_info = ""

    def _error(self, info: str):
        self._status_error = True
        self._status_info = info

    # Get str and change cursor
    def _add_parts(self, _local_idx: int):
        _element_part = self.text[self._cursor+1:(self._cursor+_local_idx)]
        self._cursor += _local_idx
        _local_idx = 0
        return _element_part

    def _filter_key(self, text: str) -> str:
        text = text.strip()
        if (text[0] == "'" and text[-1] == "'") or (text[0] == '"' and text[-1] == '"'):
            return text[1:-1]
        else:
            if text.find(" ") != -1:
                self._error("Invalid characters in key -> ' ' in line. Use single quotes.")
            else:
                return text
        return text

    def _filter_value(self, text: str | list) -> list | dict | str | int | bool | None :
        # If data in list is array, return array
        if type(text) == list:
            return text
        # If data in list is dict, return dict
        elif type(text) == dict:
            return text
        # Else data in list is not array, select another type
        text = text.strip()
        if len(text) == 0:
            return None
        elif (text[0] == "'" and text[-1] == "'") or (text[0] == '"' and text[-1] == '"'):
            return text[1:-1]
        elif text.isnumeric():
            return int(text)
        elif text.lower().find("true") != -1:
            return True
        elif text.lower().find("false") != -1:
            return False
        elif text.lower().find("null") != -1:
            return None
        elif text.lower().find("none") != -1:
            return None

        self._error("Invalid characters in value -> ' ' in line. Use single quotes for string. Value: '{}'".format(text))
        return None

    def _create_dict(self, data: list) -> dict:
        data_key = data[::2]
        data_value = data[1::2]
        if len(data_key) != len(data_value):
            self._error("Length of data key is not equal to length of data value")
            return dict()

        new_dict = dict()
        for idx in range(len(data_key)):
            name_key, name_val = self._filter_key(data_key[idx]), self._filter_value(data_value[idx])
            if self._status_error:
                return dict()
            else:
                new_dict[name_key] = name_val

        return new_dict


    def _create_array(self, data: list) -> list:
        new_array = list()
        for i in range(len(data)):
            new_element = self._filter_value(data[i])
            if self._status_error:
                return list()
            else:
                new_array.append(new_element)

        return new_array

    def next(self) -> list | dict:
        _last_rune = ""

        _context_value_dict = False

        _context_comment = False
        _context_tab = False
        _context_comment_index = 0
        _context_tab_index = 0

        _last_str = ""
        _context_str = False

        parts = list()
        _local_idx = 0
        while self._cursor < len(self.text):
            rune = self.text[self._cursor + _local_idx]
            # If last rune is not set
            if _last_rune == '' and (rune == '{' or rune == '['):
                _last_rune = rune
            # If last rune is '['
            elif _last_rune == '[':
                if rune == ':':
                    if not _context_str:
                        self._error("Invalid characters in array -> array can't have ':'. Use single quotes.")
                if rune == ',':
                    _element_part = self.text[self._cursor+1:(self._cursor+_local_idx)]
                    if _element_part.strip() != '':
                        parts.append(_element_part)
                    self._cursor += _local_idx
                    _local_idx = 0
                elif rune == ']':
                    _element_part = self.text[self._cursor+1:(self._cursor+_local_idx)]
                    parts.append(_element_part)
                    self._cursor += _local_idx
                    _local_idx = 0
                    return self._create_array(parts)
                elif rune == '}':
                    self._error("Unexpected end of array")
                # If find new object or array
                elif rune == '{' or rune == '[':
                    self._cursor += _local_idx
                    _local_idx = 0
                    _element_part = self.next()
                    parts.append(_element_part)
                    # If error inside then go out from recursion
                    if self._status_error:
                        return list()
            # If last rune is '{'
            elif _last_rune == '{':
                if rune == ':':
                    if _context_comment:
                        if _context_tab:
                            _element_part = self.text[_context_tab_index+1:(self._cursor+_local_idx)]
                            if _element_part.strip() != '':
                                parts.append(_element_part)
                                _context_comment = False
                                _context_tab = False
                                _context_value_dict = True
                            self._cursor += _local_idx
                            _local_idx = 0
                            pass
                        pass
                    else:
                        _element_part = self.text[self._cursor+1:(self._cursor+_local_idx)]
                        if _element_part.strip() != '':
                            parts.append(_element_part)
                            _context_value_dict = True
                        self._cursor += _local_idx
                        _local_idx = 0
                elif rune == ',':
                    if _context_value_dict:
                        _element_part = self.text[self._cursor+1:(self._cursor+_local_idx)]
                        if _element_part.strip() != '':
                            parts.append(_element_part)
                            _context_value_dict = False
                        self._cursor += _local_idx
                        _local_idx = 0
                elif rune == '}':
                    if _context_value_dict:
                        _element_part = self.text[self._cursor+1:(self._cursor+_local_idx)]
                        parts.append(_element_part)
                        self._cursor += _local_idx
                        _local_idx = 0

                    return self._create_dict(parts)
                elif rune == ']':
                    if not _context_comment:
                        self._error("Unexpected end of object")
                        return list()
                # If find new object or array
                elif rune == '[':
                    if _context_value_dict:
                        self._cursor += _local_idx
                        _local_idx = 0
                        _element_part = self.next()
                        parts.append(_element_part)
                        _context_value_dict = False
                        # If error inside then go out from recursion
                        if self._status_error:
                            return list()
                    else:
                        if not _context_comment:
                            self._error("Unexpected end of object")
                            return list()


            # For understand start and end index comment LLM
            if (not _context_comment) and (not _context_str) and (rune == '/' or rune == '#'):
                _context_comment = True
                _context_comment_index = self._cursor + _local_idx
            if (not _context_str) and rune == '\n':
                _context_tab = True
                _context_tab_index = self._cursor + _local_idx

            # For understand context is string or not
            if (not _context_str) and (rune == "'" or rune == '"'):
                _last_str = rune
                _context_str = True
            elif _context_str and (_last_str == rune):
                _last_str = ""
                _context_str = False

            _local_idx += 1
        return parts

    def custom_load(self, json: str) -> (list, str):
        self._cursor = 0
        self.text = json
        self._status_error = False
        self._status_info = ""

        return self.next(), self._status_info

test_data = "[{'some': [[1,,,,,,],2,3,4,5], // [this] this works [, is comment: yep, yep \n other: 'text'}, {k: 1}]"
worker = LLMJSONToDict()
print(worker.custom_load(test_data))