import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from components import dashboards
from myindex import df_receitas_aux, df_despesas_aux
from globals import cat_receita, cat_despesa
import traceback

try:
    fig = dashboards.update_output(df_despesas_aux, df_receitas_aux, cat_despesa, cat_receita, 'QUARTZ')
    print('OK - figure type:', type(fig))
except Exception as e:
    print('ERROR:', type(e).__name__, e)
    traceback.print_exc()
