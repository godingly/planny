""" utility for sqlite db"""

def query_all_tables_names():
        return '''
        SELECT name 
        FROM sqlite_master 
        WHERE 
            type ='table' AND name NOT LIKE 'sqlite_%';
        '''

def values_to_sql(values: list) -> str:
    """ receives [1, 'Paul', 20.00], 
    returns a string 1,'Paul',20.00
    """
    str_values = []
    for val in values:
        if type(val) == str:
            val = f"'{val}'"
        str_values.append(str(val))
    res = ','.join(str_values)
    print(res)
    return res

def dict_to_col_types(col_names_types_dict: dict) -> str:
    """ get {'ID':'INT PRIMARY KEY', 'NAME:'TEXT'},
    returns the string ID INT PRIMARY KEY, NAME TEXT
    """
    l = [f'{col_name} {col_type}' for col_name, col_type in col_names_types_dict.items()]
    return ','.join(l)