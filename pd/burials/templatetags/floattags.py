from django.template.defaultfilters import floatformat
from django.template import Library

register = Library()

def formatted_float(value):
    """
    Фильтр шаблона, где в десятичном числе, независимо от локализации, будет десятичная точка
    
    Значение аргумента по умолчанию, 10, принято, т.к. шаблон будет применяться
    в основном для географических координат
    """
    value = floatformat(value, arg=10)
    return str(value).replace(',','.')


register.filter('formatted_float', formatted_float)
