import datetime

def converter_datas_para_string(obj):
    """
    Função recursiva para percorrer um dicionário ou lista e converter
    todos os objetos datetime.date para strings no formato ISO.
    """
    if isinstance(obj, dict):
        return {k: converter_datas_para_string(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [converter_datas_para_string(i) for i in obj]
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    return obj