# schemas.py (VERSÃO FINAL COM ALIASES CORRETOS PARA O FRONTEND)
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


# --- Schemas Base (sem alterações) ---
class Identificacao(BaseModel):
    descricao: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    nome: Optional[str] = None
    municipio: Optional[str] = None
    url_imagem: Optional[str] = None # <- Adicione esta linha
    url_imagem_usos: Optional[str] = None
    class Config: from_attributes = True

class UsoAgua(BaseModel):
    uso: Optional[str] = None
    vazao_normal: Optional[float] = None
    vazao_escassez: Optional[float] = None
    class Config: from_attributes = True



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
    problemas: Optional[str] = None
    tipos_impactos: Optional[str] = None
    acoes: Optional[str] = None
    descricao_acao: Optional[str] = None
    classes_acao: Optional[str] = None
    responsaveis: Optional[str] = None
    prazo: Optional[str] = None
    situacao: Optional[str] = None
    indicadores: Optional[str] = None
    orgaos_envolvidos: Optional[str] = None
    custo_estimado_rs: Optional[float] = None

    class Config: from_attributes = True


class Monitoramento(BaseModel):
    data: date
    volume_hm3: Optional[float] = None
    volume_percentual: Optional[float] = None

    class Config: from_attributes = True


class VolumeMeta(BaseModel):
    mes_num: int
    mes_nome: Optional[str] = None
    meta1v: Optional[float] = None
    meta2v: Optional[float] = None
    meta3v: Optional[float] = None

    class Config: from_attributes = True


class ActionPlanFilterOptions(BaseModel):
    estados_de_seca: List[str]
    tipos_de_impacto: List[str]
    problemas: List[str]
    acoes: List[str]


# --- CORREÇÃO APLICADA NOS SCHEMAS DE SAÍDA ABAIXO ---

class PlanoAcaoMedidas(BaseModel):
    # O frontend espera: "Ação", "Descrição"
    Ação: Optional[str] = Field(None, alias='acoes')
    Descrição: Optional[str] = Field(None, alias='descricao_acao')

    class Config:
        from_attributes = True
        populate_by_name = True


class PlanoAcaoSituacao(BaseModel):
    # O frontend espera: "AÇÕES", "RESPONSÁVEIS", "SITUAÇÃO"
    AÇÕES: Optional[str] = Field(None, alias='acoes')
    RESPONSÁVEIS: Optional[str] = Field(None, alias='responsaveis')
    SITUAÇÃO: Optional[str] = Field(None, alias='situacao')

    class Config:
        from_attributes = True
        populate_by_name = True


class DashboardSummary(BaseModel):
    volumeAtualHm3: float
    volumePercentual: float
    estadoAtualSeca: str
    dataUltimaMedicao: date
    diasDesdeUltimaMudanca: int
    # Usa o schema correto para Medidas
    medidasRecomendadas: List[PlanoAcaoMedidas]