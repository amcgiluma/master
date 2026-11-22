"""Comprueba las salidas del experimento y calcula perfiles léxicos por grupo."""

import argparse
import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score

from clustering_base import ROOT, read_corpus, representations, vectorize

WEIGHTS = ("TF", "TF-IDF", "Binary")


def profile_groups(counts, vocabulary, df, idf, topics, assignments, selected_terms):
    profiles = []
    for group in sorted(set(assignments)):
        mask = assignments == group
        size = int(mask.sum())
        in_group = counts[mask].getnnz(axis=0)
        outside = df - in_group
        difference = in_group / size - outside / (len(topics) - size)
        top = np.argsort(-difference, kind="stable")[:5]

        terms = [
            {
                "term": str(vocabulary[i]),
                "df": int(df[i]),
                "idf": float(idf[i]),
                "in_group": int(in_group[i]),
                "outside": int(outside[i]),
                "difference": float(difference[i]),
            }
            for i in dict.fromkeys([*top, *selected_terms])
        ]
        profiles.append({
            "group": int(group),
            "size": size,
            "topics": dict(sorted(Counter(topics[mask]).items())),
            "terms": terms,
        })
    return profiles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=ROOT / "resultados-base")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--terms", nargs="*", default=[
        "year", "said", "game", "music", "government", "market", "software", "rugby",
    ])
    args = parser.parse_args()

    names, documents, topics = read_corpus(ROOT / "datos" / "bbc-fulltext.zip")
    topics = np.asarray(topics)
    counts, vocabulary = vectorize(documents)
    _, df, idf = representations(counts)
    vocabulary_index = {term: i for i, term in enumerate(vocabulary)}
    selected = [vocabulary_index[term] for term in args.terms]

    with (args.base / "frecuencia-documental.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == len(vocabulary)
    for index, row in enumerate(rows):
        assert row["term"] == vocabulary[index]
        assert int(row["df"]) == df[index]
        assert np.isclose(float(row["idf"]), idf[index], rtol=0, atol=1e-14)

    with (args.base / "grupos.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [row["document"] for row in rows] == names
    assert [row["reference_topic"] for row in rows] == topics.tolist()
    base = json.loads((args.base / "metricas.json").read_text(encoding="utf-8"))

    results = {}
    for weight in WEIGHTS:
        runs = {}
        assignments = {}
        for run in base["runs"]:
            if run["weight"] != weight:
                continue
            seed = run["seed"]
            groups = np.asarray([int(row[f"{weight}_{seed}"]) for row in rows])
            assignments[seed] = groups
            assert adjusted_rand_score(topics, groups) == run["ari"]
            assert adjusted_mutual_info_score(topics, groups) == run["ami"]
            assert np.bincount(groups).tolist() == run["cluster_sizes"]
            runs[seed] = run | {"groups": profile_groups(counts, vocabulary, df, idf, topics, groups, selected)}
        results[weight] = {
            "runs": runs,
            "mean_ari": float(np.mean([run["ari"] for run in runs.values()])),
            "mean_ami": float(np.mean([run["ami"] for run in runs.values()])),
            "partition_ari": {
                f"{a}-{b}": adjusted_rand_score(assignments[a], assignments[b])
                for a, b in combinations(sorted(assignments), 2)
            },
        }

    evidence = {
        "documents": len(documents),
        "vocabulary": len(vocabulary),
        "df_one": int(np.count_nonzero(df == 1)),
        "df_min": int(df.min()),
        "df_max": int(df.max()),
        "df_max_term": str(vocabulary[df.argmax()]),
        "results": results,
    }
    args.output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
