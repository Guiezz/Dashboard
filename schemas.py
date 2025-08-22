# schemas.py (VERSÃO MULTI-RESERVATÓRIO)

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# --- Schema para a lista de seleção no frontend ---
class ReservatorioSelecao(BaseModel):
    id: int
    nome: str
    class Config: from_attributes = True

# --- Schema principal do Reservatório (antiga Identificacao) ---
class Reservatorio(BaseModel):
    id: int
    nome: str
    municipio: Optional[str] = None
    descricao: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    url_imagem: Optional[str] = None
    url_imagem_usos: Optional[str] = None
    class Config: from_attributes = True

# --- Outros schemas que já tínhamos ---
class BalancoMensal(BaseModel):
    mes: Optional[str] = None
    afluencia_m3s: Optional[float] = None
    demandas_m3s: Optional[float] = None
    balanco_m3s: Optional[float] = None
    class Config: from_attributes = True

class ComposicaoDemanda(BaseModel):
    usos: Optional[str] = None
    demandas_hm3: Optional[float] = None
    class Config: from_attributes = True

class OfertaDemanda(BaseModel):
    cenarios: Optional[str] = None
    oferta_m3s: Optional[float] = None
    demanda_m3s: Optional[float] = None
    balanco_m3s: Optional[float] = None
    class Config: from_attributes = True

class PlanoAcao(BaseModel):
    estado_seca: Optional[str] = None
    acoes: Optional[str] = None
    descricao_acao: Optional[str] = None
    responsaveis: Optional[str] = None
    situacao: Optional[str] = None
    class Config: from_attributes = True

class UsoAgua(BaseModel):
    uso: Optional[str] = None
    vazao_normal: Optional[float] = None
    vazao_escassez: Optional[float] = None
    class Config: from_attributes = True

class Responsavel(BaseModel):
    # --- CAMPOS ATUALIZADOS ---
    grupo: Optional[str] = None
    organizacao: Optional[str] = None
    cargo: Optional[str] = None
    nome: str
    # -------------------------

    class Config:
        from_attributes = True

# --- SCHEMA ADICIONADO AQUI ---
class ActionPlanFilterOptions(BaseModel):
    # --- CORREÇÃO AQUI ---
    # Altere os nomes dos campos para o novo padrão
    estados: List[str]
    impactos: List[str]
    # ---------------------

    problemas: List[str]
    acoes: List[str]

    class Config:
        from_attributes = True