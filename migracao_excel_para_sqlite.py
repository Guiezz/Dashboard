# migracao_excel_para_sqlite.py (VERSÃO MULTI-RESERVATÓRIO CORRIGIDA)

import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
import glob

from database import Base
from models import (
    Reservatorio, BalancoMensal, ComposicaoDemanda, OfertaDemanda,
    PlanoAcao, VolumeMeta, Monitoramento, UsoAgua, Responsavel
)

DATABASE_URL_SYNC = "sqlite:///./dados_patu.db"
engine = create_engine(DATABASE_URL_SYNC)
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def recriar_banco_de_dados():
    print("🗑️  Apagando tabelas antigas e recriando o banco de dados...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados e tabelas recriados com sucesso.")


def carregar_dados():
    db = SessionLocalSync()
    try:
        pastas_reservatorios = [f for f in glob.glob("data/*") if os.path.isdir(f)]

        for pasta in pastas_reservatorios:
            nome_pasta = os.path.basename(pasta)
            print(f"\n🔄 Processando dados para o reservatório: {nome_pasta.upper()}")

            # 1. Carregar Identificação e criar o Reservatório "Pai"
            df_ident = pd.read_excel(os.path.join(pasta, 'identificacao.xlsx'))
            df_ident.columns = [str(col).strip().lower() for col in df_ident.columns]
            info_reservatorio = df_ident.iloc[0].to_dict()

            novo_reservatorio = Reservatorio(
                nome=info_reservatorio.get('nome', nome_pasta.capitalize()),
                municipio=info_reservatorio.get('municipio'),
                descricao=info_reservatorio.get('descricao'),
                lat=info_reservatorio.get('lat'),
                long=info_reservatorio.get('long'),
                nome_imagem=info_reservatorio.get('nome_imagem'),
                nome_imagem_usos=info_reservatorio.get('nome_imagem_usos')
            )
            db.add(novo_reservatorio)
            db.flush()
            reservatorio_id = novo_reservatorio.id
            print(f" -> Reservatório '{novo_reservatorio.nome}' criado com ID: {reservatorio_id}")

            # 2. Carregar todos os outros dados com limpeza, rename e o ID do reservatório

            # Plano de Ação
            df_pa = pd.read_excel(os.path.join(pasta, 'plano_acao.xlsx'))
            df_pa.columns = [str(col).strip().lower() for col in df_pa.columns]
            df_pa.rename(columns={'estado de seca': 'estado_seca', 'problemas': 'problemas',
                                  'tipos de impactos': 'tipos_impactos', 'ações': 'acoes',
                                  'descrição da ação': 'descricao_acao', 'classes de ação': 'classes_acao',
                                  'responsáveis': 'responsaveis', 'situação': 'situacao'}, inplace=True)
            df_pa['reservatorio_id'] = reservatorio_id
            db.bulk_insert_mappings(PlanoAcao, df_pa.to_dict(orient="records"))
            print(" -> Dados de 'Plano de Ação' carregados.")

            # Usos da Água
            df_usos = pd.read_excel(os.path.join(pasta, 'usos_agua.xlsx'))
            df_usos.columns = [str(col).strip().lower() for col in df_usos.columns]
            df_usos.rename(columns={'vazão normal': 'vazao_normal', 'vazão escassez': 'vazao_escassez'}, inplace=True)
            df_usos['reservatorio_id'] = reservatorio_id
            db.bulk_insert_mappings(UsoAgua, df_usos.to_dict(orient="records"))
            print(" -> Dados de 'Usos da Água' carregados.")

            # Monitoramento Histórico
            df_mon = pd.read_excel(os.path.join(pasta, 'monitoramento_historico.xlsx'))
            df_mon.columns = [str(col).strip().lower() for col in df_mon.columns]
            df_mon.rename(columns={'data': 'data', 'volume (hm³)': 'volume_hm3', 'volume (%)': 'volume_percentual'},
                          inplace=True)
            df_mon['reservatorio_id'] = reservatorio_id
            db.bulk_insert_mappings(Monitoramento, df_mon.to_dict(orient="records"))
            print(" -> Dados de 'Monitoramento' carregados.")

            # Volume Meta
            df_vm = pd.read_excel(os.path.join(pasta, 'volume_meta.xlsx'))
            df_vm.columns = [str(col).strip().lower() for col in df_vm.columns]
            meses_map_abrev = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'set': 9,
                               'out': 10, 'nov': 11, 'dez': 12}
            df_vm.rename(columns={'mes_num': 'mes_nome'}, inplace=True)
            df_vm['mes_num'] = df_vm['mes_nome'].str.strip().str.lower().map(meses_map_abrev)
            df_vm['reservatorio_id'] = reservatorio_id
            db.bulk_insert_mappings(VolumeMeta, df_vm.to_dict(orient="records"))
            print(" -> Dados de 'Volume Meta' carregados.")

            # Responsáveis
            print(" -> Carregando dados de 'Responsáveis'...")
            df_resp = pd.read_excel(os.path.join(pasta, 'responsaveis.xlsx'))

            # Padroniza os nomes das colunas (remove espaços, deixa minúsculo)
            df_resp.columns = [str(col).strip().lower() for col in df_resp.columns]

            # Garante que o dataframe tenha todas as colunas necessárias
            colunas_necessarias = ['grupo', 'organizacao', 'cargo', 'nome']
            for col in colunas_necessarias:
                if col not in df_resp.columns:
                    df_resp[col] = None  # Adiciona a coluna vazia se não existir

            # Adiciona o ID do reservatório
            df_resp['reservatorio_id'] = reservatorio_id

            # Remove linhas onde o nome da pessoa está em branco
            df_resp.dropna(subset=['nome'], inplace=True)

            # Converte valores nulos (NaN) para None (compatível com o banco)
            df_resp = df_resp.where(pd.notnull(df_resp), None)

            # Insere os dados no banco de dados
            db.bulk_insert_mappings(Responsavel, df_resp.to_dict(orient="records"))
            print(" -> Dados de 'Responsáveis' carregados com sucesso.")

            # Balanço Hídrico
            with pd.ExcelFile(os.path.join(pasta, 'balanco_hidrico.xlsx')) as xls:
                df_bm = pd.read_excel(xls, 'Balanço Mensal')
                df_bm.columns = [str(col).strip().lower() for col in df_bm.columns]
                df_bm.rename(
                    columns={'mês': 'mes', 'afluência (m³/s)': 'afluencia_m3s', 'demanda (m³/s)': 'demandas_m3s',
                             'evaporação (m³/s)': 'evaporacao_m3s'}, inplace=True)
                df_bm['reservatorio_id'] = reservatorio_id
                db.bulk_insert_mappings(BalancoMensal, df_bm.to_dict(orient="records"))

                df_cd = pd.read_excel(xls, 'Composição Demanda')
                df_cd.columns = [str(col).strip().lower() for col in df_cd.columns]
                df_cd.rename(columns={'uso': 'usos', 'vazão (l/s)': 'demandas_hm3'}, inplace=True)
                df_cd['reservatorio_id'] = reservatorio_id
                db.bulk_insert_mappings(ComposicaoDemanda, df_cd.to_dict(orient="records"))

                df_od = pd.read_excel(xls, 'Oferta Demanda')
                df_od.columns = [str(col).strip().lower() for col in df_od.columns]
                df_od.rename(
                    columns={'cenário': 'cenarios', 'oferta (l/s)': 'oferta_m3s', 'demanda (l/s)': 'demanda_m3s'},
                    inplace=True)
                df_od['reservatorio_id'] = reservatorio_id
                db.bulk_insert_mappings(OfertaDemanda, df_od.to_dict(orient="records"))
            print(" -> Dados de 'Balanço Hídrico' carregados.")

        db.commit()
        print("\n✅ Todos os dados de todos os reservatórios foram carregados com sucesso!")

    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    recriar_banco_de_dados()
    carregar_dados()