"""Genera medias de vectores GloVe con el mismo orden de filas que TF y TF-IDF."""

import argparse
from collections import Counter
from hashlib import file_digest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np
from scipy.sparse import load_npz

from generar_tf import construir_tf, decodificar_cuerpo, guardar_json, leer_cuerpos, palabras_normalizadas


MODELO = "glove.2024.wikigiga.50d"
DIMENSION = 50
ARCHIVO_VECTORES = "wiki_giga_2024_50_MFT20_vectors_seed_123_alpha_0.75_eta_0.075_combined.txt"


def sha256_archivo(ruta):
    with ruta.open("rb") as archivo:
        return file_digest(archivo, "sha256").hexdigest()


def comprobar_entrada(corpus, anterior):
    """Comprueba el corpus y los índices y matrices del bloque anterior."""
    estadisticas = json.loads((anterior / "estadisticas.json").read_text(encoding="utf-8"))
    indice = anterior / "documentos.json"
    vocabulario = anterior / "vocabulario.json"
    for ruta, clave in (
        (corpus, "corpus_sha256"),
        (indice, "orden_sha256"),
        (vocabulario, "vocabulario_sha256"),
    ):
        if sha256_archivo(ruta) != estadisticas[clave]:
            raise ValueError(f"El archivo {ruta.name} no coincide con el del bloque anterior.")

    documentos = json.loads(indice.read_text(encoding="utf-8"))
    terminos = json.loads(vocabulario.read_text(encoding="utf-8"))
    orden_corpus = leer_cuerpos(corpus)
    if documentos != [identificador for identificador, _ in orden_corpus]:
        raise ValueError("El orden de documentos no coincide con el corpus.")
    matrices = {}
    for nombre, clave in (("tf", "tf"), ("tf-idf", "tf_idf")):
        ruta = anterior / f"{nombre}.npz"
        if sha256_archivo(ruta) != estadisticas[clave]["sha256"]:
            raise ValueError(f"El archivo {ruta.name} no coincide con el del bloque anterior.")
        matriz = load_npz(ruta)
        if matriz.format != "csr" or matriz.shape != (len(documentos), len(terminos)):
            raise ValueError(f"Formato o dimensiones incorrectas en {ruta.name}.")
        if not np.isfinite(matriz.data).all():
            raise ValueError(f"Valores no finitos en {ruta.name}.")
        matrices[nombre] = {
            "dimensiones": list(matriz.shape),
            "sha256": estadisticas[clave]["sha256"],
        }
    return documentos, orden_corpus, matrices, estadisticas


def cargar_vectores(modelo, vocabulario):
    """Lee el ZIP de Stanford una vez y guarda solo los vectores del corpus."""
    vectores = {}
    with ZipFile(modelo) as archivo, archivo.open(ARCHIVO_VECTORES) as entrada:
        for linea in entrada:
            palabra, _, valores = linea.partition(b" ")
            palabra = palabra.decode("utf-8")
            if palabra not in vocabulario:
                continue
            vector = np.fromstring(valores.decode("ascii"), sep=" ", dtype=np.float64)
            if vector.shape != (DIMENSION,) or not np.isfinite(vector).all():
                raise ValueError("El modelo contiene un vector con dimensión o valores incorrectos.")
            if palabra in vectores:
                raise ValueError("El modelo contiene un término del corpus repetido.")
            vectores[palabra] = vector
    if not vectores:
        raise ValueError("El vocabulario del modelo no cubre ningún término del corpus.")
    return vectores


def media(frecuencias, vectores):
    """Divide cada suma vectorial por la suma de los pesos representables."""
    pesos = np.asarray(frecuencias.sum(axis=1)).ravel()
    valores = frecuencias @ vectores
    resultado = np.zeros_like(valores)
    np.divide(valores, pesos[:, None], out=resultado, where=pesos[:, None] > 0)
    return resultado.astype(np.float32)


def guardar_matriz(ruta, vectores, documentos):
    np.savez_compressed(ruta, vectores=vectores, documentos=documentos)
    with np.load(ruta, allow_pickle=False) as datos:
        if datos["vectores"].dtype != np.float32 or not np.array_equal(datos["vectores"], vectores):
            raise ValueError(f"Los vectores cambiaron al recargar {ruta.name}.")
        if not np.array_equal(datos["documentos"], documentos):
            raise ValueError(f"El orden de documentos cambió al recargar {ruta.name}.")
    return {"dimensiones": list(vectores.shape), "dtype": str(vectores.dtype), "sha256": sha256_archivo(ruta)}


def generar(corpus, anterior, modelo, destino):
    if destino.exists():
        raise FileExistsError(f"El directorio de salida ya existe: {destino}")
    documentos, cuerpos, matrices, anterior_stats = comprobar_entrada(corpus, anterior)
    conteos = []
    vocabulario = Counter()
    for _, cuerpo in cuerpos:
        texto, _ = decodificar_cuerpo(cuerpo)
        conteo = Counter(palabras_normalizadas(texto.split()))
        conteos.append(conteo)
        vocabulario.update(conteo)
    vectores = cargar_vectores(modelo, vocabulario)
    terminos = sorted(vectores)
    columnas = {termino: columna for columna, termino in enumerate(terminos)}
    frecuencias = construir_tf(conteos, columnas)
    embeddings = np.stack([vectores[termino] for termino in terminos])

    # La frecuencia documental de cada término cubierto se mide sobre las 805 filas.
    # Excluir columnas OOV no cambia la frecuencia documental de las demás.
    df = np.bincount(frecuencias.indices, minlength=len(terminos))
    idf = 1 + np.log((1 + len(documentos)) / (1 + df))
    simple = media(frecuencias, embeddings)
    ponderada = media(frecuencias.multiply(idf).tocsr(), embeddings)
    sin_representacion = np.flatnonzero(np.diff(frecuencias.indptr) == 0)
    for resultado in (simple, ponderada):
        if resultado.shape != (len(documentos), DIMENSION) or not np.isfinite(resultado).all():
            raise ValueError("Dimensiones o valores incorrectos en los embeddings de documentos.")
        if not np.array_equal(np.flatnonzero(~resultado.any(axis=1)), sin_representacion):
            raise ValueError("Las filas nulas no coinciden con los documentos sin representación.")

    total = vocabulario.total()
    cubiertas = int(frecuencias.sum())
    estadisticas = {
        "modelo": MODELO,
        "fuente_modelo": "https://downloads.cs.stanford.edu/nlp/data/wordvecs/glove.2024.wikigiga.50d.zip",
        "modelo_sha256": sha256_archivo(modelo),
        "licencia_modelo": "PDDL-1.0",
        "dimension": DIMENSION,
        "documentos": len(documentos),
        "corpus_sha256": anterior_stats["corpus_sha256"],
        "orden_sha256": anterior_stats["orden_sha256"],
        "vocabulario_seleccionado_tf": anterior_stats["vocabulario_seleccionado"],
        "tipos": {
            "total": len(vocabulario),
            "cubiertos": len(terminos),
            "oov": len(vocabulario) - len(terminos),
            "proporcion_oov": 1 - len(terminos) / len(vocabulario),
        },
        "ocurrencias": {
            "total": total,
            "cubiertas": cubiertas,
            "oov": total - cubiertas,
            "proporcion_oov": 1 - cubiertas / total,
        },
        "filas_sin_representacion": [
            {"indice": int(fila), "documento": documentos[fila]} for fila in sin_representacion
        ],
        "matrices": matrices,
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destino.parent, prefix=".embeddings-") as temporal:
        salida = Path(temporal) / "salida"
        salida.mkdir()
        for nombre, resultado in (("embeddings-media", simple), ("embeddings-tf-idf", ponderada)):
            matrices[nombre] = guardar_matriz(salida / f"{nombre}.npz", resultado, np.asarray(documentos))
        guardar_json(salida / "estadisticas.json", estadisticas)
        salida.rename(destino)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path, help="ZIP de cuerpos sin cabeceras")
    parser.add_argument("vectorial", type=Path, help="directorio de las matrices TF y TF-IDF y sus índices")
    parser.add_argument("modelo", type=Path, help=f"ZIP preentrenado de Stanford {MODELO}.zip")
    parser.add_argument("destino", type=Path, help="directorio nuevo para matrices y estadísticas")
    args = parser.parse_args()
    generar(args.corpus, args.vectorial, args.modelo, args.destino)


if __name__ == "__main__":
    main()
