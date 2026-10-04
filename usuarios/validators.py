import re

from django.core.exceptions import ValidationError


def limpiar_rut(value):
    """Quita puntos y guion, y deja en mayúsculas: '12.345.678-k' -> '12345678K'."""
    return str(value).replace('.', '').replace('-', '').strip().upper()


def normalizar_rut(value):
    """Formato único para guardar: '12345678-K'. Evita duplicados por formato."""
    rut = limpiar_rut(value)
    return f"{rut[:-1]}-{rut[-1]}"


def validar_rut_chileno(value):
    """
    Valida RUT chileno mediante Módulo 11.
    Acepta formatos con o sin puntos y guion (ej: 12.345.678-K o 12345678K).
    """
    rut_limpio = limpiar_rut(value)

    if not re.match(r'^\d{7,8}[0-9K]$', rut_limpio):
        raise ValidationError('El formato del RUT no es válido.')

    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]

    suma = 0
    multiplicador = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1

    dv_calculado = 11 - (suma % 11)
    if dv_calculado == 11:
        dv_esperado = '0'
    elif dv_calculado == 10:
        dv_esperado = 'K'
    else:
        dv_esperado = str(dv_calculado)

    if dv_ingresado != dv_esperado:
        raise ValidationError('El RUT ingresado no es válido (dígito verificador incorrecto).')