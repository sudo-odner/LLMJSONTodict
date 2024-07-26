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
        _trigger_rune = ("{", "}", "[", "]", ":", ",")
        _context_rune = ("'", '"', "#", "/", "\n")
        _last_rune = ""

        _context_value_dict = False
        _context_form_recurtion = False

        _context_comment = False
        _context_tab = False
        _context_comment_index = 0
        _context_tab_index = 0

        _last_str = ""
        _context_str = False

        parts = list()
        while self._cursor_end < len(self._text):
            rune = self._text[self._cursor_end]
            # Если на символ не является специалным символом, пропускаем его
            if rune not in _trigger_rune and rune not in _context_rune:
                self._cursor_end += 1
                continue

            # Если не определена вложенность, то все символы пропускаем
            if _last_rune == '':
                if rune == '{' or rune == '[':
                    _last_rune = rune
                elif rune == '}':
                    return dict()
                elif rune == ']':
                    return list()
                # Сдвигаем курсор на следуйщей символ
                self._cursor_end += 1
                # Обвновляем курсор начало строки на следующий символ
                self._cursor_start = self._cursor_end
                continue

            # -----------------------------Проверка на то что строчка явялется типом строки-----------------------------
            # Если мы нашли символ отвечающий за начало типа строки
            if rune == "'" or rune == '"':
                # Если контекст типа строки был включен и равен символу открывшего его, то выключаем контекст типа строки
                if _context_str and _last_str == rune:
                    _last_str = ""
                    _context_str = False
                # Если контекст строки не включен, то включаем его
                elif not _context_str:
                    _last_str = rune
                    _context_str = True
                # Сдвигаем курсор на следуйщей символ
                self._cursor_end += 1
                continue

            # Если наш символ находится в срочке, то пропускаем его
            if _context_str:
                self._cursor_end += 1
                continue
            # ------------------------------Проверка на комментарии('/', '#') и табы('\n')------------------------------
            # Если мы встретили комментарий, то учитываем что слудующие символы входят в коментарий
            if rune == '/' or rune == '#':
                _context_comment = True
                self._cursor_end += 1
                continue

            # Если мы встретили '\n', то пропускаем его
            if rune == '\n':
                # Если мы встретили '\n' и коментарий включен, то прекрощяем игнорирование
                if _context_comment:
                    _context_comment = False
                self._cursor_end += 1
                self._cursor_start = self._cursor_end
                continue

            # Если мы находимся в комментарии, то пропускаем специальные символы
            if _context_comment:
                self._cursor_end += 1
                continue
            # ---------------------------------Условия, если вложенность массива('[')-----------------------------------
            if _last_rune == '[':
                # Символы, которые не должны попадаться в открытом массиве
                if rune == ':' or rune == '}':
                    # If rune have ':' or '}' in array - set error
                    self._error(f"Invalid rune - '{rune}' in array.")
                    return list()

                _element_part = self._text[self._cursor_start:self._cursor_end]
                _element_part = _element_part.strip()

                # Если у нас появляется новая вложенность
                if rune == '[' or rune == '{':
                    self._cursor_start = self._cursor_end
                    _element_part = self._next()
                    parts.append(_element_part)

                    # If error inside then go out from recursion
                    if self._error_status:
                        return list()

                # Если все условия до этого были пройдены то скорее всего мы добавим новый элемент
                self._cursor_start = self._cursor_end + 1
                self._cursor_end += 1
                if rune == ',':
                    parts.append(_element_part)
                elif rune == ']':
                    parts.append(_element_part)
                    return self._create_array(parts)
                continue
            # ---------------------------------Условия, если вложенность объекта('{')-----------------------------------
            if _last_rune == '{':
                # Символы которые не должны попадаться в открытом объекте
                if rune == ']':
                    self._error(f"Invalid rune - '{rune}' in object.")
                    return dict()

                _element_part = self._text[self._cursor_start:self._cursor_end]
                _element_part = _element_part.strip()

                # Если у нас появляется новая вложенность
                if rune == '[' or rune == '{':
                    if _context_value_dict:
                        self._cursor_start = self._cursor_end
                        _element_part = self._next()
                        self._cursor_start = self._cursor_end

                        parts.append(_element_part)
                        _context_value_dict = False
                        _context_form_recurtion = True

                        # If error inside then go out from recursion
                        if self._error_status:
                            return list()
                        continue
                    else:
                        self._error("Object hase type - key: value. Object or array can't been key")
                        return list()

                self._cursor_start = self._cursor_end + 1
                self._cursor_end += 1
                # Если у нас спецальные символы разделители
                if rune == ':':
                    if _context_value_dict:
                        self._error("Object hase type - key: value. Not - key:key:value.")
                        return list()

                    parts.append(_element_part)
                    _context_value_dict = True
                elif rune == ',':
                    if _context_form_recurtion:
                        _context_form_recurtion = False
                        _context_value_dict = False
                        continue
                    if not _context_value_dict:
                        self._error("Object hase type - key: value. Not - value:value.")
                        return list()

                    parts.append(_element_part)
                    _context_value_dict = False
                elif rune == '}':
                    if len(parts) == 0:
                        return dict()
                    if _context_form_recurtion:
                        _context_form_recurtion = False
                        _context_value_dict = False
                        return self._create_dict(parts)

                    parts.append(_element_part)
                    _context_value_dict = False
                    return self._create_dict(parts)
                continue

        if _last_rune != '':
            self._error_element_not_closed(_last_rune)
        else:
            self._error("Empty string.")
        return list()

    def custom_load(self, json: str) -> (list | dict, str):
        self._new_text(json)

        result, error = self._next(), self._error_info
        return result, error
