# migracao_excel_para_sqlite.py (VERSÃO FINAL COM CONVERSÃO NUMÉRICA FORÇADA)

import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

from database import Base
from models import (
    Identificacao, BalancoMensal, ComposicaoDemanda, OfertaDemanda,
    PlanoAcao, VolumeMeta, Monitoramento, UsoAgua
)

DATABASE_URL_SYNC = "sqlite:///./dados_patu.db"
engine = create_engine(DATABASE_URL_SYNC)
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def recriar_banco_de_dados():
    """FORÇA a recriação do banco de dados."""
    print("🗑️  Apagando tabelas antigas e recriando o banco de dados...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados e tabelas recriados com sucesso.")


def carregar_dados_do_excel():
    db = SessionLocalSync()
    try:
        print("\n🔄 Iniciando carregamento de dados a partir dos arquivos Excel...")

        # --- ARQUIVO 2: balanco_hidrico_patu.xlsx ---
        caminho_balanco = 'data/balanco_hidrico_patu.xlsx'
        if os.path.exists(caminho_balanco):
            # Aba: Balanço Mensal
            df_bm = pd.read_excel(caminho_balanco, sheet_name='Balanço Mensal')
            df_bm.columns = [str(col).strip().lower() for col in df_bm.columns]
            # --- CORREÇÃO: Força a conversão para tipo numérico ---
            for col in ['afluência (m³/s)', 'demanda (m³/s)', 'evaporação (m³/s)']:
                if col in df_bm.columns:
                    df_bm[col] = pd.to_numeric(df_bm[col], errors='coerce').fillna(0)
            df_bm.rename(columns={'mês': 'mes', 'afluência (m³/s)': 'afluencia_m3s', 'demanda (m³/s)': 'demandas_m3s',
                                  'evaporação (m³/s)': 'evaporacao_m3s'}, inplace=True)
            if 'balanco_m3s' not in df_bm.columns: df_bm['balanco_m3s'] = df_bm['afluencia_m3s'] - df_bm['demandas_m3s']
            db.query(BalancoMensal).delete()
            db.bulk_insert_mappings(BalancoMensal, df_bm.to_dict(orient="records"))
            print(" -> Dados de 'Balanço Mensal' carregados.")

            # Aba: Composição Demanda
            df_cd = pd.read_excel(caminho_balanco, sheet_name='Composição Demanda')
            df_cd.columns = [str(col).strip().lower() for col in df_cd.columns]
            # --- CORREÇÃO: Força a conversão para tipo numérico ---
            if 'vazão (l/s)' in df_cd.columns:
                df_cd['vazão (l/s)'] = pd.to_numeric(df_cd['vazão (l/s)'], errors='coerce').fillna(0)
            df_cd.rename(columns={'uso': 'usos', 'vazão (l/s)': 'demandas_hm3'}, inplace=True)
            db.query(ComposicaoDemanda).delete()
            db.bulk_insert_mappings(ComposicaoDemanda, df_cd.to_dict(orient="records"))
            print(" -> Dados de 'Composição Demanda' carregados.")

            # Aba: Oferta Demanda
            df_od = pd.read_excel(caminho_balanco, sheet_name='Oferta Demanda')
            df_od.columns = [str(col).strip().lower() for col in df_od.columns]
            # --- CORREÇÃO: Força a conversão para tipo numérico ---
            for col in ['oferta (l/s)', 'demanda (l/s)']:
                if col in df_od.columns:
                    df_od[col] = pd.to_numeric(df_od[col], errors='coerce').fillna(0)
            df_od.rename(columns={'cenário': 'cenarios', 'oferta (l/s)': 'oferta_m3s', 'demanda (l/s)': 'demanda_m3s'},
                         inplace=True)
            if 'balanco_m3s' not in df_od.columns: df_od['balanco_m3s'] = df_od['oferta_m3s'] - df_od['demanda_m3s']
            db.query(OfertaDemanda).delete()
            db.bulk_insert_mappings(OfertaDemanda, df_od.to_dict(orient="records"))
            print(" -> Dados de 'Oferta Demanda' carregados.")

        # (O resto do código para outros arquivos permanece igual)
        caminho_identificacao = 'data/identificacao_patu.xlsx'
        if os.path.exists(caminho_identificacao):
            df = pd.read_excel(caminho_identificacao, sheet_name='identificacao')
            df.columns = [str(col).strip().lower() for col in df.columns]
            # Adicionado 'nome_imagem' ao rename
            df.rename(columns={'identificacao': 'descricao', 'lat': 'lat', 'long': 'long', 'nome': 'nome',
                               'municipio': 'municipio', 'nome_imagem': 'nome_imagem', 'nome_imagem_usos': 'nome_imagem_usos'}, inplace=True)
            db.query(Identificacao).delete()
            db.bulk_insert_mappings(Identificacao, df.to_dict(orient="records"))
            print(" -> Dados de 'identificacao' carregados.")

        # --- ADICIONE ESTA NOVA SEÇÃO PARA OS USOS ---
        caminho_usos = 'data/usos_patu.xlsx'
        if os.path.exists(caminho_usos):
            df_usos = pd.read_excel(caminho_usos)
            df_usos.columns = [str(col).strip().lower() for col in df_usos.columns]
            df_usos.rename(columns={'vazão normal': 'vazao_normal', 'vazão escassez': 'vazao_escassez'}, inplace=True)
            for col in ['vazao_normal', 'vazao_escassez']:
                if col in df_usos.columns:
                    df_usos[col] = pd.to_numeric(df_usos[col], errors='coerce').fillna(0)
            db.query(UsoAgua).delete()
            db.bulk_insert_mappings(UsoAgua, df_usos.to_dict(orient="records"))
            print(" -> Dados de 'Usos da Água' carregados.")

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

        caminho_monitoramento = 'data/monitoramento_historico_patu.xlsx'
        if os.path.exists(caminho_monitoramento):
            df_mon = pd.read_excel(caminho_monitoramento)
            df_mon.columns = [str(col).strip().lower() for col in df_mon.columns]
            df_mon.rename(columns={'data': 'data', 'volume (hm³)': 'volume_hm3', 'volume (%)': 'volume_percentual'},
                          inplace=True)
            df_mon['data'] = pd.to_datetime(df_mon['data']).dt.date
            db.query(Monitoramento).delete()
            db.bulk_insert_mappings(Monitoramento, df_mon.to_dict(orient="records"))
            print(" -> Dados de 'Monitoramento Histórico' carregados do arquivo local.")

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
