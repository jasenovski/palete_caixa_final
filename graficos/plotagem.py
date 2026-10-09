import matplotlib.pyplot as plt

def _gerar_figura(solucoes: list, L: int, W: int, ls: list, ws: list, qtd_maxima: int):
    """Gera figura matplotlib com as duas soluções lado a lado."""
    fig, axes = plt.subplots(ncols=2, figsize=(20, 10))
    fig.set_facecolor("#f4f4f4")

    for idx, (ax, solucao) in enumerate(zip(axes, solucoes), start=1):
        ax.set_facecolor("#f4f4f4")
        ax.set_xlim(-1, L + 1)
        ax.set_ylim(-1, W + 1)
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)

        # Borda da palete
        for x0, y0, x1, y1 in [(0, 0, L, 0), (0, 0, 0, W), (0, W, L, W), (L, 0, L, W)]:
            ax.plot([x0, x1], [y0, y1], "k-", lw=2)

        for n_caixa, (i, p, q) in enumerate(solucao, start=1):
            ax.add_patch(plt.Rectangle(
                xy=(p, q),
                width=ls[i - 1],
                height=ws[i - 1],
                facecolor="#4e4af1" if i == 1 else "#d16262",
                edgecolor="white",
                lw=1,
            ))
            ax.text(
                p + ls[i - 1] / 2,
                q + ws[i - 1] / 2,
                str(n_caixa),
                ha="center", va="center",
                fontsize=14, color="#f4f4f4",
            )

        ax.set_title(
            f"Solução {idx} — {len(solucao)} caixas  (máx. teórico: {qtd_maxima})"
            f"\n(L={L}cm, W={W}cm, l={ls[0]}cm, w={ws[0]}cm)",
            fontsize=16,
        )
        ax.tick_params(labelsize=12)

    plt.tight_layout()
    return fig