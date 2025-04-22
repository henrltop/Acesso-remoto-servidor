from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """
    Divide uma string pelo separador especificado.
    
    Uso: {{ valor|split:"separador" }}
    
    Exemplo: {{ "arquivo.txt"|split:"." }} retorna ['arquivo', 'txt']
    """
    return value.split(arg)

@register.filter
def get_item(lst, index):
    """
    Obtém um item de uma lista pelo índice.
    
    Uso: {{ lista|get_item:indice }}
    
    Exemplo: {{ "arquivo.txt"|split:"."|get_item:1 }} retorna 'txt'
    """
    try:
        return lst[int(index)]
    except (IndexError, ValueError):
        return ''

@register.filter
def last(lst):
    """
    Retorna o último item de uma lista.
    
    Uso: {{ lista|last }}
    
    Exemplo: {{ "arquivo.txt"|split:"."|last }} retorna 'txt'
    """
    try:
        if isinstance(lst, list):
            return lst[-1]
        return lst.split('.')[-1]
    except (IndexError, AttributeError):
        return ''

@register.filter
def get_file_extension(filename):
    """
    Obtém a extensão de um arquivo.
    
    Uso: {{ nome_do_arquivo|get_file_extension }}
    
    Exemplo: {{ "arquivo.txt"|get_file_extension }} retorna 'txt'
    """
    try:
        return filename.split('.')[-1]
    except (IndexError, AttributeError):
        return ''

@register.filter
def get_file_icon(extension):
    """
    Retorna o ícone correspondente à extensão do arquivo.
    
    Uso: {{ extensao|get_file_icon }}
    """
    extension = extension.lower()
    
    if extension == 'py':
        return 'fab fa-python text-primary'
    elif extension in ['js', 'json']:
        return 'fab fa-js-square text-warning'
    elif extension in ['html', 'htm']:
        return 'fab fa-html5 text-danger'
    elif extension == 'css':
        return 'fab fa-css3-alt text-info'
    elif extension == 'php':
        return 'fab fa-php text-primary'
    elif extension == 'md':
        return 'fab fa-markdown text-secondary'
    else:
        return 'fas fa-file-code text-secondary'
