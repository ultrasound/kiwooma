def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '':
            strip_data = '0'

        format_data = strip_data
        if data.startswith('-'):
            format_data = '-' + format_data
        return format_data

def to_float(data):
    if data.startswith('+'):
        format_data = data[1:]
    elif data == '':
        data = 0
    return float(data)
