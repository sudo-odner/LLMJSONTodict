import json
from typing import Tuple, List

def custom_json_load(text: str) -> (dict, bool, str):
    result: dict = {}
    # Генерация stack_data
    stack_data, _error_status, _error_text = _gen_stack_data(text)
    if not _error_status:
        return result, False, _error_text

    # Преобразование типов и фильтрация stack_data
    stack_data = _map_stack_data(stack_data)
    # Конвертация stack_data в str
    new_text = _stack_data_to_str(stack_data)

    try:
        # Попытка загрузить JSON
        result = json.loads(new_text)
    except json.JSONDecodeError as e:
        # Ошибка конвертации, добавить логи
        return result, False, f'json load error: {e}'
    return result, True, ""


def _gen_stack_data(text: str) -> (List[Tuple[str, str]], bool, str):
    """
    Функция генерации _stack_data.

    _stack - нужен для вложенности object | array. Нужен для определения вложенности
    _stack_data - это массив из кортежев (тип текста, текст)
    _target - элементы определния типов (тип элемента, символ начала, символ окончания)
    """
    # Находим начало JSON объекта
    idx_start_object = text.find("{")
    if text.find("{") == -1:
        # Мы не нашли объект. Можно сделать более строго
        return [("object", "{"), ("object", "}")], True, ""
    text = text[idx_start_object:]

    _target = [("object", "{", "}"),
               ("array", "[", "]"),
               ("comment", "#", "\n"), ("comment", "//", "\n"), ("comment", "/*", "*/"),
               ("string", "'", "'"), ("string", '"', '"')]

    _stack: List[Tuple[str, str, str]] = []
    _stack_data: List[Tuple[str, str]] = []
    _back_string: int = 0
    _front_string: int = 0
    while _front_string < len(text):
        # some = text[_front_string]
        # Если последний элемент был началом строчки
        if _stack and _stack[-1][0] == "string":
            if text.startswith(_stack[-1][2], _front_string):
                _stack_data.append(("string", text[_back_string:_front_string]))
                _back_string = _front_string + 1
                _front_string += 1
                _stack.pop()
            else:
                _front_string += 1
        # Если последний элемент был началом комментария
        elif _stack and _stack[-1][0] == "comment":
            if text.startswith(_stack[-1][2], _front_string):
                _back_string = _front_string + 1
                _front_string += 1
                _stack.pop()
            else:
                _front_string += 1
        else:
            # Поиск среди начала тригеров
            target_entry = [(type_target, start_target, end_target) for type_target, start_target, end_target in
                            _target if text.startswith(start_target, _front_string)]
            if len(target_entry) > 1:
                # Нашлось 2 совпадения, вероятно у двух объектов одинаковое начало
                # TODO: Write log error
                return [], False, "Проблема определения объекта в _gen_stack_data"
            elif len(target_entry) == 1:
                _stack.append(target_entry[0])
                if target_entry[0][0] == "object" or target_entry[0][0] == "array":
                    _stack_data.append((target_entry[0][0], target_entry[0][1]))
                _back_string = _front_string + len(target_entry[0][1])
                _front_string += len(target_entry[0][1])
            else:
                if _stack:
                    if _stack[-1][0] == 'object':
                        if text[_front_string] == ',':
                            _stack_data.append(("string_f", text[_back_string:_front_string]))
                            _stack_data.append(("mark", ','))
                            _back_string = _front_string + 1
                        elif text[_front_string] == ':':
                            _stack_data.append(("string_f", text[_back_string:_front_string]))
                            _stack_data.append(("mark", ':'))
                            _back_string = _front_string + 1
                    elif _stack[-1][0] == 'array':
                        if text[_front_string] == ',':
                            _stack_data.append(("string_f", text[_back_string:_front_string]))
                            _stack_data.append(("mark", ','))
                            _back_string = _front_string + 1

                    # Если наш _target закрывается, то в _stack_data мы добавляем тип и условие закрытия. И чистим верх _stack
                    if text.startswith(_stack[-1][2], _front_string):
                        _stack_data.append(("string_f", text[_back_string:_front_string]))
                        _stack_data.append((_stack[-1][0], _stack[-1][2]))
                        _back_string = _front_string + 1
                        _stack.pop()

                _front_string += 1


    if _stack:
        # Проблема с вложенностью (она не закрыта)
        return [], False, f"Не закрытая вложенность {_stack}"
    return _stack_data, True, ""

def _is_float(element: any) -> bool:
    """ Проверки на тип float """
    try:
        float(element)
        return True
    except ValueError:
        return False

def _map_stack_data(_stack_data: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """ Функция для чистки и преобразования (в int | float | bool | NoneType) string_f типов """
    _new_stack_data: List[Tuple[str, str]] = []
    for type_data, data in _stack_data:
        if type_data == "string_f":
            data = data.strip()
            if data == '':
                continue
            elif data.isnumeric():
                _new_stack_data.append(("int", data))
            elif _is_float(data):
                _new_stack_data.append(("float", data))
            elif data.lower() == "true":
                _new_stack_data.append(("bool", data))
            elif data.lower() == "false":
                _new_stack_data.append(("bool", data))
            elif data.lower() == "null":
                _new_stack_data.append(("NoneType", data))
            elif data.lower() == "none":
                _new_stack_data.append(("NoneType", data))
            else:
                _new_stack_data.append(("string", data))
        else:
            _new_stack_data.append((type_data, data))
    return _new_stack_data

def _stack_data_to_str(_stack_data: List[Tuple[str, str]]) -> str:
    """ Преобразование _stack_data в str """
    _stack_str = list(map(lambda x: f'"{x[1]}"' if x[0] == "string" else x[1], _stack_data))
    return ''.join(_stack_str)
