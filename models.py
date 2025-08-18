# models.py
from sqlalchemy import Column, Integer, String, Float, Date, Text
# CORREÇÃO: Removido o ponto da importação
from database import Base


class Identificacao(Base):
    __tablename__ = "identificacao"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(Text, nullable=True)
    nome = Column(String, nullable=True)
    municipio = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    long = Column(Float, nullable=True)
    nome_imagem = Column(String, nullable=True)
    nome_imagem_usos = Column(String, nullable=True)

class UsoAgua(Base):
    __tablename__ = "uso_agua"
    id = Column(Integer, primary_key=True, index=True)
    uso = Column(String, nullable=True)
    vazao_normal = Column(Float, nullable=True)
    vazao_escassez = Column(Float, nullable=True)


class BalancoMensal(Base):
    __tablename__ = "balanco_mensal"
    id = Column(Integer, primary_key=True, index=True)
    mes = Column(String, unique=True)
    afluencia_m3s = Column(Float)
    demandas_m3s = Column(Float)
    balanco_m3s = Column(Float)
    evaporacao_m3s = Column(Float, nullable=True)


class ComposicaoDemanda(Base):
    __tablename__ = "composicao_demanda"
    id = Column(Integer, primary_key=True, index=True)
    usos = Column(String)
    demandas_hm3 = Column(Float)


class OfertaDemanda(Base):
    __tablename__ = "oferta_demanda"
    id = Column(Integer, primary_key=True, index=True)
    cenarios = Column(String)
    oferta_m3s = Column(Float)
    demanda_m3s = Column(Float)
    balanco_m3s = Column(Float)


class PlanoAcao(Base):
    __tablename__ = "plano_acao"
    id = Column(Integer, primary_key=True, index=True)
    estado_seca = Column(String, index=True)
    problemas = Column(String)
    tipos_impactos = Column(String)
    acoes = Column(String, index=True)
    descricao_acao = Column(Text)
    classes_acao = Column(String)
    responsaveis = Column(String)
    prazo = Column(String)
    situacao = Column(String, index=True)
    indicadores = Column(String)
    orgaos_envolvidos = Column(String)
    custo_estimado_rs = Column(Float)


class VolumeMeta(Base):
    __tablename__ = "volume_meta"
    id = Column(Integer, primary_key=True, index=True)
    mes_num = Column(Integer, unique=True)
    mes_nome = Column(String)
    meta1v = Column(Float)
    meta2v = Column(Float)
    meta3v = Column(Float)


class Monitoramento(Base):
    __tablename__ = "monitoramento"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, unique=True, index=True)
    volume_hm3 = Column(Float)
    volume_percentual = Column(Float)

class Responsavel(Base):
    __tablename__ = "responsaveis"
    id = Column(Integer, primary_key=True, index=True)
    equipa = Column(String, index=True)
    nome = Column(String)