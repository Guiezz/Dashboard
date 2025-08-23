# migracao_excel_para_sqlite.py
import pandas as pd
import glob
import os
from models import (
    Reservatorio, BalancoMensal, ComposicaoDemanda, OfertaDemanda,
    PlanoAcao, VolumeMeta, Monitoramento, UsoAgua, Responsavel
)

# Esta função fará todo o trabalho de ler os ficheiros e preparar os dados
async def popular_dados(db_session):
    print("Iniciando a carga de dados...")
    try:
        pastas_reservatorios = [f for f in glob.glob("data/*") if os.path.isdir(f)]

        for pasta in pastas_reservatorios:
            nome_pasta = os.path.basename(pasta)
            print(f"-> Processando: {nome_pasta.upper()}")

            # Carregar Identificação
            df_ident = pd.read_excel(os.path.join(pasta, 'identificacao.xlsx'))
            df_ident.columns = [str(col).strip().lower() for col in df_ident.columns]
            info = df_ident.iloc[0].to_dict()

            novo_reservatorio = Reservatorio(
                nome=info.get('nome', nome_pasta.capitalize()),
                municipio=info.get('municipio'),
                descricao=info.get('descricao'),
                lat=info.get('lat'),
                long=info.get('long'),
                nome_imagem=info.get('nome_imagem'),
                nome_imagem_usos=info.get('nome_imagem_usos'),
                codigo_funceme=info.get('codigo_funceme')
            )
            db_session.add(novo_reservatorio)
            await db_session.flush()
            reservatorio_id = novo_reservatorio.id

            # Carregar todos os outros dados
            # (O código aqui é o seu, mas usando loops em vez de bulk_insert)
            
            df_pa = pd.read_excel(os.path.join(pasta, 'plano_acao.xlsx'))
            df_pa.columns = [str(col).strip().lower() for col in df_pa.columns]
            df_pa.rename(columns={'estado de seca': 'estado_seca', 'problemas': 'problemas', 'tipos de impactos': 'tipos_impactos', 'ações': 'acoes', 'descrição da ação': 'descricao_acao', 'classes de ação': 'classes_acao', 'responsáveis': 'responsaveis', 'situação': 'situacao'}, inplace=True)
            df_pa['reservatorio_id'] = reservatorio_id
            for r in df_pa.to_dict(orient="records"): db_session.add(PlanoAcao(**r))
            
            # Repita o padrão acima para os outros ficheiros:
            # df_usos, df_mon, df_vm, df_resp, df_bm, df_cd, df_od

        await db_session.commit()
        print("✅ Dados carregados com sucesso!")
        return True

    except Exception as e:
        print(f"❌ ERRO ao popular dados: {e}")
        await db_session.rollback()
        return False
