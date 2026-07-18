from pydantic import BaseModel, Field


class FavoriteCourtsDTO(BaseModel):
    """Resposta das rotas `/users/me/favorites*`.

    Só os ids favoritados — sem integridade referencial com `Court` (T-A2
    não depende do módulo de catálogo), então nenhuma expansão com dados da
    quadra acontece aqui. Ids órfãos (quadra excluída) não são filtrados
    nesta camada; a leitura "verdadeira" ignorando órfãos fica para o
    consumidor que tiver acesso à tabela de courts (front ou fase futura).
    """

    court_ids: list[int] = Field(default_factory=list)
