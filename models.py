# models.py (VERSÃO FINAL MULTI-RESERVATÓRIO)

from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Reservatorio(Base):
    __tablename__ = "reservatorios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    municipio = Column(String, nullable=True)
    descricao = Column(Text, nullable=True)
    lat = Column(Float, nullable=True)
    long = Column(Float, nullable=True)
    nome_imagem = Column(String, nullable=True)
    nome_imagem_usos = Column(String, nullable=True)
    codigo_funceme = Column(String, nullable=True) # Adicionado para corresponder ao script de migração


class BalancoMensal(Base):
    __tablename__ = "balanco_mensal"
    id = Column(Integer, primary_key=True, index=True)
    mes = Column(String)
    afluencia_m3s = Column(Float)
    demandas_m3s = Column(Float)
    evaporacao_m3s = Column(Float, nullable=True)
    reservatorio_id = Column(Integer, ForeignKey("reservatorios.id"))


class ComposicaoDemanda(Base):
    __tablename__ = "composicao_demanda"
    id = Column(Integer, primary_key=True, index=True)
    usos = Column(String)
    demandas_hm3 = Column(Float)
    reservatorio_id = Column(Integer, ForeignKey("reservatorios.id"))


class OfertaDemanda(Base):
    __tablename__ = "oferta_demanda"
    id = Column(Integer, primary_key=True, index=True)
    cenarios = Column(String)
    oferta_m3s = Column(Float)
    demanda_m3s = Column(Float)
    reservatorio_id = Column(Integer, ForeignKey("reservatorios.id"))


class PlanoAcao(Base):
    __tablename__ = "plano_acao"
    id = Column(Integer, primary_key=True, index=True)
    estado_seca = Column(String, index=True)
    problemas = Column(String, nullable=True)
    tipos_impactos = Column(String, nullable=True)
    acoes = Column(String, index=True)
    descricao_acao = Column(Text, nullable=True)
    classes_acao = Column(String, nullable=True)
    responsaveis = Column(String, nullable=True)
    situacao = Column(String, index=True, nullable=True)
    indicadores = Column(String, nullable=True)
    orgaos_envolvidos = Column(String, nullable=True)
    reservatorio_id = Column(Integer, ForeignKey("reservatorios.id"))


class VolumeMeta(Base):
    __tablename__ = "volume_meta"
    id = Column(Integer, primary_key=True, index=True)
    mes_num = Column(Integer)
    mes_nome = Column(String)
    meta1v = Column(Float, nullable=True)
    meta2v = Column(Float, nullable=True)
    meta3v = Column(Float, nullable=True)
    reservatorio_id = Column(Integer, ForeignKey("reservatorios.id"))


class Monitoramento(Base):
    __tablename__ = "monitoramento"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, index=True)
    volume_hm3 = Column(Float)
    volume_percentual = Column(Float)
    reservatorio_id = Column(Integer, ForeignKey("reservatorios.id"))


class UsoAgua(Base):
    __tablename__ = "uso_agua"
    id = Column(Integer, primary_key=True, index=True)
    uso = Column(String, nullable=True)
    vazao_normal = Column(Float, nullable=True)
    vazao_escassez = Column(Float, nullable=True)
    reservatorio_id = Column(Integer, ForeignKey("reservatorios.id"))


class Responsavel(Base):
    __tablename__ = "responsaveis"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    grupo = Column(String, index=True, nullable=True)
    organizacao = Column(String, nullable=True)
    cargo = Column(String, nullable=True)
    reservatorio_id = Column(Integer, ForeignKey("reservatorios.id"))
    reservatorio = relationship("Reservatorio")
