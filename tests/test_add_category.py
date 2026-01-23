import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from db import table_to_df
from components import sidebar

print('Before:')
print(table_to_df('cat_receita'))

data = table_to_df('cat_receita').to_dict()
res = sidebar.add_category(1, 0, 'CategoriaTeste', [], data)
print('Returned message:', res[0])
print('After:')
print(table_to_df('cat_receita'))
