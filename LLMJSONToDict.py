class LLMJSONToDict:
    def __init__(self, text):
        # Настройки работы с текстом
        self._cursor_start = 0
        self._cursor_end = 0
        self._text = text
        # Настройки для отладки и ошибок
        self._error_status = False
        self._error_info = ""
        # Запуск основного алгоритма
        self._answer = self._next()

    # Получить ответ
    def get(self) -> (dict | list, str):
        return self._answer, self._error_info

    # Для изменения статуса ошибки
    def _error(self, info: str):
        self._error_status = True
        self._error_info = info


    # Фильтр ключа JSON object(dict в Python).
    # Ключ в JSON всегда имеет тип строки, но иногда указывают их без одинарной или двойной кавычки.
    # Если text - это строка с двойными или одинарными кавычками, то добавляю все тело ключа (даже если слова разделены пробелом).
    # Если text - это строка без двойных или одинарных кавычек, то проверяю что это слово(не словосочетание) и добавляю ключ.
    def _filter_key(self, text: str) -> str:
        text = text.strip()
        if (text[0] and text[-1] == "'") or (text[0] and text[-1] == '"'):
            return text[1:-1]
        else:
            if text.find(" ") != -1:
                self._error("""Invalid characters. Use single or dabble quotes for siting.""" + "Data: " + f"({info})")
            else:
                return text
        return text

    # Для проверки что строка это float
    def _is_float(self, element: any) -> bool:
        try:
            float(element)
            return True
        except ValueError:
            return False

    # Фильтр значения
    # В JSON есть несколько типов: array(list), объект(dict), string, number(integer | float), boolean, null(None)
    # Этот код преобразует в тип string, number (integer | float), boolean, null(None)
    # Если строка равна нулевой длинне, то вернем None
    def _filter_value(self, text: str | list | dict) -> list | dict | str | int | float | bool | None :
        # Проверяем если мы получили массив или список то его возвращяем
        if (type(text) == list) or (type(text) == dict):
            return text
        # Фильтруем строку, убираем пробелы справо и слево
        text = text.strip()
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

        self._error("""Invalid characters. Use single or dabble quotes for siting.""" + "Data: " + f"({info})")
        return None

    # Создание и фильтрация dict из получаемого массива.
    # Массив создан с патерном: [ключ, значение, ключ, значение]
    # Если у нас есть разница в размерах массива ключ, значение, то вернем ошибку.
    def _create_dict(self, data: list) -> dict:
        # Разделяем массив на ключ и значение
        data_key, data_value = data[::2], data[1::2]
        if len(data_key) != len(data_value):
            self._error("""Length of data key is not equal to length of data value""")
            return dict()

        new_dict = dict()
        for idx in range(len(data_key)):
            # Фильтруем ключ и значение
            name_key, name_val = self._filter_key(data_key[idx]), self._filter_value(data_value[idx])
            if self._error_status:
                return dict()
            else:
                new_dict[name_key] = name_val

        return new_dict

    # Создание и фильтрация получаемого массива.
    def _create_array(self, data: list) -> list:
        new_array = list()
        for i in range(len(data)):
            # Фильтруем значение
            new_element = self._filter_value(data[i])
            if self._error_status:
                return list()
            else:
                new_array.append(new_element)

        return new_array


    # Основная функция с рекурсией
    # У нас есть три типа триггеров:
    # 1. Углубляющий -> '{', '}', '[', ']'. Они необходимы для глубокой рекурсии поиска элемента определенного типа.
    # 2. Разделение -> ',', ':', '}', ']'. Они необходимы для выполнения разделения элементов.
    # 3. Контекстное -> '/', '#', '\n', '"', "'". Они нужны для понимания контекста типа строки и комментария.
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
            self._error("""Element is not closed""" + "Data: " + f"({_last_rune})")
        else:
            self._error("Empty string.")
        return list()
