"""UBO resolution on SYNTHETIC multi-layer ownership structures.

Edges point owner -> owned, with pct = direct stake. An individual's effective
ownership of the target = sum over every path of the product of stakes.
Anyone >= 25% is flagged (FATF R.24/25, Wolfsberg).

Outputs: data/processed/ubo_results.csv, docs/ubo_summary.csv,
         docs/ubo_example.png
"""
import random
from pathlib import Path

import networkx as nx
import pandas as pd

random.seed(5)
THRESHOLD = 25.0
MAX_DEPTH = 3


def example_structure():
    """Company A: 60% Company B, 40% Individual X.
    Company B: 40% Individual Y, 60% Individual Z.
    Expected: X 40%, Y 24% (just under), Z 36%."""
    G = nx.DiGraph()
    for n in ("Company A", "Company B"):
        G.add_node(n, kind="company")
    for n in ("Individual X", "Individual Y", "Individual Z"):
        G.add_node(n, kind="person")
    G.add_edge("Company B", "Company A", pct=60)
    G.add_edge("Individual X", "Company A", pct=40)
    G.add_edge("Individual Y", "Company B", pct=40)
    G.add_edge("Individual Z", "Company B", pct=60)
    return G, "Company A"


def random_structure(sid):
    G = nx.DiGraph()
    target = f"CO_{sid}_0"
    G.add_node(target, kind="company")
    n_co, n_p = [0], [0]

    def expand(node, depth):
        k = random.choice([2, 2, 3])
        cuts = sorted(random.sample(range(5, 96), k - 1))
        stakes = [b - a for a, b in zip([0] + cuts, cuts + [100])]
        for pct in stakes:
            if depth < MAX_DEPTH and random.random() < 0.4:
                n_co[0] += 1
                c = f"CO_{sid}_{n_co[0]}"
                G.add_node(c, kind="company")
                G.add_edge(c, node, pct=pct)
                expand(c, depth + 1)
            else:
                n_p[0] += 1
                p = f"P_{sid}_{n_p[0]}"
                G.add_node(p, kind="person")
                G.add_edge(p, node, pct=pct)

    expand(target, 1)
    return G, target


def resolve(G, target):
    """Effective % ownership of target for every individual."""
    out = {}
    for p, d in G.nodes(data=True):
        if d["kind"] != "person":
            continue
        total = 0.0
        for path in nx.all_simple_paths(G, p, target):
            pct = 1.0
            for a, b in zip(path, path[1:]):
                pct *= G[a][b]["pct"] / 100
            total += pct * 100
        if total > 0:
            out[p] = round(total, 2)
    return out


def draw(G, target, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib missing: skipping chart")
        return
    for i, gen in enumerate(nx.topological_generations(G)):
        for n in gen:
            G.nodes[n]["layer"] = i
    pos = nx.multipartite_layout(G, subset_key="layer", align="horizontal")
    pos = {n: (x, -y) for n, (x, y) in pos.items()}
    eff = resolve(G, target)
    colors = ["#e07a5f" if eff.get(n, 0) >= THRESHOLD
              else "#81b29a" if d["kind"] == "person" else "#c9d6df"
              for n, d in G.nodes(data=True)]
    labels = {n: f"{n}\n{eff[n]:.0f}%" if n in eff else n for n in G.nodes}
    plt.figure(figsize=(8, 5))
    nx.draw(G, pos, labels=labels, node_color=colors, node_size=3200,
            font_size=8, arrows=True)
    nx.draw_networkx_edge_labels(
        G, pos, {(a, b): f"{d['pct']}%" for a, b, d in G.edges(data=True)})
    plt.title("Synthetic ownership structure (red = UBO at 25% or more)")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    structures = {"EXAMPLE": example_structure()}
    for i in range(1, 51):
        structures[f"S{i:02d}"] = random_structure(i)

    rows = []
    for sid, (G, target) in structures.items():
        assert nx.is_directed_acyclic_graph(G), f"cycle in {sid}"
        depth = nx.dag_longest_path_length(G)
        for p, eff in resolve(G, target).items():
            direct = G[p][target]["pct"] if G.has_edge(p, target) else 0
            rows.append(dict(structure=sid, layers=depth, person=p,
                             direct_pct=direct, effective_pct=eff,
                             ubo=eff >= THRESHOLD))
    df = pd.DataFrame(rows)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/processed/ubo_results.csv", index=False)

    ubo = df[df.ubo]
    hidden = ubo[ubo.direct_pct == 0]
    summ = pd.Series({
        "structures": df.structure.nunique(),
        "individuals_resolved": len(df),
        "ubos_flagged": len(ubo),
        "ubos_with_no_direct_stake": len(hidden),
        "structures_with_no_ubo": df.structure.nunique()
        - ubo.structure.nunique(),
    })
    summ.to_csv("docs/ubo_summary.csv", header=["value"])
    print("\nExample structure:\n",
          df[df.structure == "EXAMPLE"][["person", "direct_pct",
                                         "effective_pct", "ubo"]]
          .to_string(index=False))
    print("\nSummary:\n", summ.to_string())
    G, target = structures["EXAMPLE"]
    draw(G, target, "docs/ubo_example.png")
    print("\nSaved docs/ubo_example.png")


if __name__ == "__main__":
    main()