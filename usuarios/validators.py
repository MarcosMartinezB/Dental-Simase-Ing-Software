import re
from django.core.exceptions import ValidationError

def validar_rut_chileno(value):
    """
    Valida RUT chileno mediante Módulo 11.
    Acepta formatos con o sin puntos y guion (ej: 12.345.678-K o 12345678K).
    """
    rut_limpio = str(value).replace('.', '').replace('-', '').strip().upper()
    
    if not re.match(r'^\d{7,8}[0-9K]$', rut_limpio):
        raise ValidationError('El formato del RUT no es válido.')

    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]

    suma = 0
    multiplicador = 2

    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1

    resto = suma % 11
    dv_calculado = 11 - resto

    if dv_calculado == 11:
        dv_esperado = '0'
    elif dv_calculado == 10:
        dv_esperado = 'K'
    else:
        dv_esperado = str(dv_calculado)

    if dv_ingresado != dv_esperado:
        raise ValidationError('El RUT ingresado no es válido (dígito verificador incorrecto).')