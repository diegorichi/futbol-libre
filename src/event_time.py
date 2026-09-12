from datetime import datetime, timedelta


def hora_mas_cercana(hora_str, ahora=None):
    ahora = ahora or datetime.now()
    hora_obj = datetime.strptime(hora_str, "%H:%M").replace(
        year=ahora.year, month=ahora.month, day=ahora.day
    )
    diferencia = hora_obj - ahora
    if diferencia > timedelta(hours=12):
        hora_obj -= timedelta(days=1)
    elif diferencia < timedelta(hours=-12):
        hora_obj += timedelta(days=1)
    return hora_obj
