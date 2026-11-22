"""Compara tres ponderaciones sobre los artículos del corpus BBC News."""

import argparse
import csv
import sys
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from urllib.request import urlopen
from zipfile import ZipFile

import numpy as np
import scipy
import sklearn
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score
from sklearn.preprocessing import normalize
from threadpoolctl import threadpool_limits


ROOT = Path(__file__).resolve().parent
CORPUS_URL = (
    "https://raw.githubusercontent.com/derekgreene/bbc-datasets/"
    "d81c6d9543cb90683b6927f35f6d06ccb4f59b55/raw/bbc-fulltext.zip"
)
CORPUS_SHA256 = "a351031a62325b3d7ff13146eeb035c22feca8290913b5183d1ff3be35109495"
TOPICS = {"business", "entertainment", "politics", "sport", "tech"}
TOKEN_PATTERN = r"(?u)\b[a-z]{2,}\b"
SEEDS = (0, 1, 2, 3, 4)
KMEANS = dict(n_clusters=5, n_init=1, max_iter=300, tol=0.0, algorithm="lloyd")


def read_corpus(archive):
    if not archive.exists():
        with urlopen(CORPUS_URL, timeout=30) as response:
            data = response.read()
        if sha256(data).hexdigest() != CORPUS_SHA256:
            raise ValueError("La descarga no coincide con el corpus fijado.")
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(data)

    if sha256(archive.read_bytes()).hexdigest() != CORPUS_SHA256:
        raise ValueError("El ZIP local no coincide con el corpus fijado.")

    with ZipFile(archive) as corpus:
        names = sorted(
            name for name in corpus.namelist()
            if name.endswith(".txt") and PurePosixPath(name).parent.name in TOPICS
        )
        documents = [corpus.read(name).decode("utf-8") for name in names]

    if len(names) != 2225 or len(set(names)) != len(names):
        raise ValueError("El corpus debe contener 2.225 artículos distintos por identificador.")
    topics = [PurePosixPath(name).parent.name for name in names]
    return names, documents, topics


def vectorize(documents):
    tokenizer = CountVectorizer(
        lowercase=True, token_pattern=TOKEN_PATTERN, stop_words="english",
        ngram_range=(1, 1), min_df=1, dtype=np.float64,
    )
    counts = tokenizer.fit_transform(documents)
    if not np.all(counts.getnnz(axis=1)):
        raise ValueError("El preprocesado dejó algún documento sin términos.")
    return counts, tokenizer.get_feature_names_out()


def representations(counts):
    binary = counts.copy()
    binary.data.fill(1.0)
    df = counts.getnnz(axis=0)
    idf = np.log((1 + counts.shape[0]) / (1 + df)) + 1
    weights = {
        "TF": counts,
        "TF-IDF": counts.multiply(idf).tocsr(),
        "Binary": binary,
    }
    return {name: normalize(matrix, norm="l2") for name, matrix in weights.items()}, df, idf


def cluster(matrices, names, topics):
    # Cada semilla elige los mismos cinco documentos de partida para los tres pesados.
    starts = {
        seed: np.random.default_rng(seed).choice(len(names), KMEANS["n_clusters"], replace=False)
        for seed in SEEDS
    }
    runs = []
    assignments = {}
    with threadpool_limits(limits=1):
        for seed, indices in starts.items():
            for weight, matrix in matrices.items():
                model = KMeans(**KMEANS, init=matrix[indices].toarray(), random_state=seed)
                groups = model.fit_predict(matrix)
                sizes = np.bincount(groups, minlength=KMEANS["n_clusters"])
                if not sizes.all() or model.n_iter_ == KMEANS["max_iter"]:
                    raise RuntimeError(f"Agrupamiento incompleto con {weight} y semilla {seed}.")
                # Las categorías de referencia solo se usan al evaluar los grupos.
                runs.append({
                    "weight": weight,
                    "seed": seed,
                    "ari": adjusted_rand_score(topics, groups),
                    "ami": adjusted_mutual_info_score(topics, groups),
                    "iterations": model.n_iter_,
                    "cluster_sizes": sizes.tolist(),
                })
                assignments[weight, seed] = groups
    return runs, assignments, {seed: [names[i] for i in ids] for seed, ids in starts.items()}


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=ROOT / "datos" / "bbc-fulltext.zip")
    parser.add_argument("--output", type=Path, default=ROOT / "resultados-base")
    args = parser.parse_args()

    names, documents, topics = read_corpus(args.corpus)
    counts, terms = vectorize(documents)
    matrices, df, idf = representations(counts)
    runs, assignments, starts = cluster(matrices, names, topics)
    summary = {
        "corpus": {"url": CORPUS_URL, "sha256": CORPUS_SHA256, "classes": dict(sorted(Counter(topics).items()))},
        "preprocessing": {
            "encoding": "utf-8", "document_order": "sorted archive paths",
            "lowercase": True, "token_pattern": TOKEN_PATTERN, "stop_words": "sklearn:english",
            "min_df": 1, "normalization": "l2",
        },
        "shape": list(counts.shape),
        "idf_formula": "ln((1 + N) / (1 + df)) + 1",
        "kmeans": KMEANS,
        "initial_documents": starts,
        "versions": {
            "python": sys.version.split()[0], "numpy": np.__version__,
            "scipy": scipy.__version__, "scikit-learn": sklearn.__version__,
        },
        "runs": runs,
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metricas.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8",
    )
    write_csv(args.output / "frecuencia-documental.csv", ("term", "df", "idf"), zip(terms, df, idf))
    write_csv(
        args.output / "grupos.csv",
        ["document", "reference_topic", *(f"{weight}_{seed}" for weight, seed in assignments)],
        ((name, topic, *(groups[i] for groups in assignments.values()))
         for i, (name, topic) in enumerate(zip(names, topics))),
    )


if __name__ == "__main__":
    main()
