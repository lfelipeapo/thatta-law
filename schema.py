from pydantic import BaseModel
from typing import List

class DocumentSchema(BaseModel):
    Localidade: str
    Autoridade: str
    Título: str
    Data: str
    Ementa: str
    URN: str
    Link: str
    MaisDetalhes: str

class DocumentListagemSchema(BaseModel):
    documentos: List[DocumentSchema]
    
class MensagemResposta(BaseModel):
    """Representação de uma mensagem de retorno seja de erro ou sucesso"""
    mensagem: str
