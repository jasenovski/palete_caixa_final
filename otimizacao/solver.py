"""
Módulo de otimização do problema Palete-Caixa.

Lógica extraída do notebook palete_caixa.ipynb.
Dado um palete (L x W) e uma caixa (l x w), resolve via PL inteira (PuLP/CBC)
o problema de maximizar o número de caixas encaixadas, sem sobreposição.
Gera duas soluções: a ótima e uma alternativa igualmente válida.
"""

import pulp as plp
from copy import deepcopy
from itertools import product
from random import random, seed as set_seed
from graficos.plotagem import _gerar_figura
from utilidades.utils import _ponto_dentro_caixa, _varname2tuple, _extrair_solucao


# ─── Solver ──────────────────────────────────────────────────────────────

def resolver(
    palete_comp: float,
    palete_larg: float,
    caixa_comp: float,
    caixa_larg: float,
    seed_alt: int = 42,
) -> tuple:
    """
    Resolve o problema de empacotamento via PL inteira (PuLP/CBC).

    Parâmetros
    ----------
    palete_comp, palete_larg : dimensões do palete (cm, arredondadas para int)
    caixa_comp,  caixa_larg  : dimensões da caixa  (cm, arredondadas para int)
    seed_alt                 : semente para geração da solução alternativa

    Retorno
    -------
    (solucoes, qtd_maxima, fig)
      - solucoes   : lista com 2 listas de tuplas (orientação, x, y)
      - qtd_maxima : cota superior teórica (L·W / l·w)
      - fig        : figura matplotlib com as 2 soluções lado a lado
    Retorna (None, 0, None) se inviável.
    """
    # Normaliza: L >= W, l >= w
    L, W = sorted([int(round(palete_comp)), int(round(palete_larg))], reverse=True)
    l_um, w_um = sorted([int(round(caixa_comp)), int(round(caixa_larg))], reverse=True)
    l_dois, w_dois = w_um, l_um  # orientação rotacionada

    ls = [l_um, l_dois]
    ws = [w_um, w_dois]

    # Coordenadas candidatas H (x) e V (y) — somas de múltiplos das dimensões
    f = lambda n1, s1, n2, s2: n1 * s1 + n2 * s2

    H = sorted({
        f(n_um, l_um, n_dois, l_dois)
        for n_um, n_dois in product(range(L), range(L))
        if f(n_um, l_um, n_dois, l_dois) <= L - w_um
    })
    V = sorted({
        f(n_um, w_um, n_dois, w_dois)
        for n_dois, n_um in product(range(W), range(W))
        if f(n_um, w_um, n_dois, w_dois) <= W - w_um
    })

    lista_rs = list(product(H, V))
    lista_variaveis = [
        (i, p, q)
        for i, p, q in product(range(1, 3), H, V)
        if p + ls[i - 1] <= L and q + ws[i - 1] <= W
    ]

    if not lista_variaveis:
        return None, 0, None

    # ── Modelo ────────────────────────────────────────────────────────────────
    prob = plp.LpProblem(name="Palete-Caixa", sense=plp.LpMaximize)
    vars_dict = plp.LpVariable.dicts(name="C", indices=lista_variaveis, 
                                     lowBound=0, upBound=1, cat=plp.LpBinary)
    prob += plp.lpSum(vars_dict.values()), "Objetivo"

    # Restrições de não-sobreposição: ∑ caixas que cobrem (r,s) ≤ 1
    n = 0
    for r, s in lista_rs:
        linha = list({
            vars_dict[(i, p, q)] for i, p, q in lista_variaveis
            if _ponto_dentro_caixa((r, s), (p, q), ls[i - 1], ws[i - 1])
        })
        if linha:
            prob += plp.lpSum(linha) <= 1, f"R1_{n}"
            n += 1

    qtd_maxima = (L * W) // (l_um * w_um)
    prob += plp.lpSum(vars_dict.values()) <= qtd_maxima, "R2"

    # ── Resolução 1 ───────────────────────────────────────────────────────────

    # solver_obj = plp.getSolver("PULP_CBC_CMD", msg=0)
    solver_obj = plp.COIN_CMD(path="/opt/homebrew/bin/cbc")
    prob.solve(solver_obj)

    if plp.LpStatus[prob.status] != "Optimal":
        return None, qtd_maxima, None

    solucao_1 = _extrair_solucao(prob)
    solucoes = [deepcopy(solucao_1)]

    # ── Resolução 2 (alternativa) ─────────────────────────────────────────────
    # Fixa ~20% das variáveis ativas em 0 e resolve novamente
    set_seed(seed_alt)
    idx_r = 0
    for v in prob.variables():
        if v.varValue is not None and v.varValue == 1.0 and random() <= 0.2:
            t = _varname2tuple(v.name)
            prob += vars_dict[t] == 0, f"R3_{idx_r}"
            idx_r += 1

    prob.solve(solver_obj)
    solucoes.append(deepcopy(_extrair_solucao(prob)))

    fig = _gerar_figura(solucoes, L, W, ls, ws, qtd_maxima)
    return solucoes, qtd_maxima, fig
