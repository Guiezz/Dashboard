# migracao_excel_para_sqlite.py (VERSÃO FINAL QUE INCLUI MONITORAMENTO LOCAL)

import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

from database import Base
from models import (
    Identificacao, BalancoMensal, ComposicaoDemanda, OfertaDemanda,
    PlanoAcao, VolumeMeta, Monitoramento  # Adicionado Monitoramento aqui
)

DATABASE_URL_SYNC = "sqlite:///./dados_patu.db"
engine = create_engine(DATABASE_URL_SYNC)
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def recriar_banco_de_dados():
    """Cria as tabelas no banco de dados se elas não existirem."""
    print("Verificando e criando tabelas se necessário...")
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados e tabelas prontos.")


def carregar_dados_do_excel():
    """Lê os dados dos arquivos Excel e os insere no banco de dados."""
    db = SessionLocalSync()
    try:
        print("\n🔄 Iniciando carregamento de dados a partir dos arquivos Excel...")

        # (As seções 1, 2, 3 e 4 permanecem as mesmas)
        # --- ARQUIVO 1: identificacao_patu.xlsx ---
        caminho_identificacao = 'data/identificacao_patu.xlsx'
        if os.path.exists(caminho_identificacao):
            df = pd.read_excel(caminho_identificacao, sheet_name='identificacao')
            df.columns = [str(col).strip().lower() for col in df.columns]
            df.rename(columns={'identificacao': 'descricao', 'lat': 'lat', 'long': 'long'}, inplace=True)
            db.query(Identificacao).delete()
            db.bulk_insert_mappings(Identificacao, df.to_dict(orient="records"))
            print(" -> Dados de 'identificacao' carregados.")

        # --- ARQUIVO 2: balanco_hidrico_patu.xlsx ---
        caminho_balanco = 'data/balanco_hidrico_patu.xlsx'
        if os.path.exists(caminho_balanco):
            df_bm = pd.read_excel(caminho_balanco, sheet_name='Balanço Mensal')
            df_bm.columns = [str(col).strip().lower() for col in df_bm.columns]
            df_bm.rename(columns={'mês': 'mes', 'afluência (m³/s)': 'afluencia_m3s', 'demanda (m³/s)': 'demandas_m3s'},
                         inplace=True)
            if 'balanco_m3s' not in df_bm.columns: df_bm['balanco_m3s'] = df_bm['afluencia_m3s'] - df_bm['demandas_m3s']
            db.query(BalancoMensal).delete()
            db.bulk_insert_mappings(BalancoMensal, df_bm.to_dict(orient="records"))
            print(" -> Dados de 'Balanço Mensal' carregados.")
            df_cd = pd.read_excel(caminho_balanco, sheet_name='Composição Demanda')
            df_cd.columns = [str(col).strip().lower() for col in df_cd.columns]
            df_cd.rename(columns={'uso': 'usos', 'vazão (l/s)': 'demandas_hm3'}, inplace=True)
            db.query(ComposicaoDemanda).delete()
            db.bulk_insert_mappings(ComposicaoDemanda, df_cd.to_dict(orient="records"))
            print(" -> Dados de 'Composição Demanda' carregados.")
            df_od = pd.read_excel(caminho_balanco, sheet_name='Oferta Demanda')
            df_od.columns = [str(col).strip().lower() for col in df_od.columns]
            df_od.rename(columns={'cenário': 'cenarios', 'oferta (l/s)': 'oferta_m3s', 'demanda (l/s)': 'demanda_m3s'},
                         inplace=True)
            if 'balanco_m3s' not in df_od.columns: df_od['balanco_m3s'] = df_od['oferta_m3s'] - df_od['demanda_m3s']
            db.query(OfertaDemanda).delete()
            db.bulk_insert_mappings(OfertaDemanda, df_od.to_dict(orient="records"))
            print(" -> Dados de 'Oferta Demanda' carregados.")

        # --- ARQUIVO 3: plano_acao_patu_junto.xlsx ---
        caminho_plano = 'data/plano_acao_patu_junto.xlsx'
        if os.path.exists(caminho_plano):
            df_pa = pd.read_excel(caminho_plano, sheet_name='Junto')
            df_pa.columns = [str(col).strip().lower() for col in df_pa.columns]
            df_pa.rename(columns={'estado de seca': 'estado_seca', 'problemas': 'problemas',
                                  'tipos de impactos': 'tipos_impactos', 'ações': 'acoes',
                                  'descrição da ação': 'descricao_acao', 'classes de ação': 'classes_acao',
                                  'responsáveis': 'responsaveis', 'situação': 'situacao'}, inplace=True)
            db.query(PlanoAcao).delete()
            colunas_do_modelo = [c.name for c in PlanoAcao.__table__.columns if c.name != 'id']
            colunas_para_inserir = [col for col in colunas_do_modelo if col in df_pa.columns]
            db.bulk_insert_mappings(PlanoAcao, df_pa[colunas_para_inserir].to_dict(orient="records"))
            print(" -> Dados de 'Plano de Ação' carregados.")

        # --- ARQUIVO 4: volume_meta_patu.xlsx ---
        caminho_volume_meta = 'data/volume_meta_patu.xlsx'
        if os.path.exists(caminho_volume_meta):
            df_vm = pd.read_excel(caminho_volume_meta, sheet_name='Plan1')
            df_vm.columns = [str(col).strip().lower() for col in df_vm.columns]
            meses_map_abrev = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'set': 9,
                               'out': 10, 'nov': 11, 'dez': 12}
            if 'mes_num' in df_vm.columns:
                df_vm.rename(columns={'mes_num': 'mes_nome'}, inplace=True)
                df_vm['mes_num'] = df_vm['mes_nome'].str.strip().str.lower().map(meses_map_abrev)
                if df_vm['mes_num'].isnull().any(): raise ValueError(
                    f"Abreviações de meses não reconhecidas: {df_vm[df_vm['mes_num'].isnull()]['mes_nome'].tolist()}.")
                db.query(VolumeMeta).delete()
                colunas_do_modelo_vm = [c.name for c in VolumeMeta.__table__.columns if c.name != 'id']
                colunas_para_inserir_vm = [col for col in colunas_do_modelo_vm if col in df_vm.columns]
                db.bulk_insert_mappings(VolumeMeta, df_vm[colunas_para_inserir_vm].to_dict(orient="records"))
                print(" -> Dados de 'Volume Meta' carregados.")

        # --- NOVO: ARQUIVO 5: monitoramento_historico_patu.xlsx ---
        caminho_monitoramento = 'data/monitoramento_historico_patu.xlsx'
        if os.path.exists(caminho_monitoramento):
            df_mon = pd.read_excel(caminho_monitoramento)
            df_mon.columns = [str(col).strip().lower() for col in df_mon.columns]

            # Renomeia as colunas do Excel para as colunas do banco de dados
            df_mon.rename(columns={
                'data': 'data',
                'volume (hm³)': 'volume_hm3',
                'volume (%)': 'volume_percentual'
            }, inplace=True)

            # Garante que a coluna 'data' está no formato correto
            df_mon['data'] = pd.to_datetime(df_mon['data']).dt.date

            db.query(Monitoramento).delete()
            db.bulk_insert_mappings(Monitoramento, df_mon.to_dict(orient="records"))
            print(" -> Dados de 'Monitoramento Histórico' carregados do arquivo local.")
        else:
            print(
                " -> AVISO: Nenhum arquivo de monitoramento histórico local encontrado em 'data/monitoramento_historico_patu.xlsx'.")

        db.commit()
        print("\n✅ Todos os dados foram carregados e salvos no banco de dados com sucesso!")

    except Exception as e:
        print(f"\n❌ ERRO INESPERADO DURANTE O CARREGAMENTO: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    recriar_banco_de_dados()
    carregar_dados_do_excel()