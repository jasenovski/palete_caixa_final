import re
from pulp import LpProblem

def _slug(texto: str) -> str:
    """Converte string para nome seguro de chave S3."""
    return re.sub(r"[^\w\-]", "_", texto.strip().lower())

def _ponto_dentro_caixa(ponto: tuple, bl: tuple, l: int, w: int) -> bool:
    """Verifica se o ponto (x, y) está dentro da caixa com canto inferior esquerdo bl."""
    x, y = ponto
    p, q = bl
    return p <= x < p + l and q <= y < q + w


def _varname2tuple(varname: str) -> tuple:
    """Converte o nome de variável PuLP (ex: 'C_(1,_2,_3)') para tupla (1, 2, 3)."""
    return tuple(
        int(x) for x in str(varname)
        .replace("C_", "").replace("(", "").replace(")", "").split(",_")
    )


def _extrair_solucao(prob: LpProblem) -> list:
    """Retorna lista ordenada de (orientação, x, y) para variáveis ativas."""
    return sorted(
        [_varname2tuple(v.name) for v in prob.variables()
         if v.varValue is not None and v.varValue == 1.0],
        key=lambda x: (x[1], x[2]),
    )