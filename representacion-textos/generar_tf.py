"""Genera dos matrices CSR y conserva el orden de sus filas y columnas."""

import argparse
from collections import Counter
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from unicodedata import normalize
from zipfile import ZipFile

import numpy as np
from nltk.stem import PorterStemmer
from scipy.sparse import csr_matrix, load_npz, save_npz
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfTransformer


DOCUMENTOS_ESPERADOS = 805
DF_MINIMA = 2
BORDES = re.compile(r"^[\W_]+|[\W_]+$")
BYTES_INVALIDOS = re.compile(r"[\udc80-\udcff]")


def leer_cuerpos(origen):
    """Devuelve pares (identificador, bytes) en orden numérico de identificador."""
    with ZipFile(origen) as archivo:
        entradas = [entrada for entrada in archivo.infolist() if not entrada.is_dir()]
        nombres = [entrada.filename for entrada in entradas]
        if any(re.fullmatch(r"[0-9]+", nombre) is None for nombre in nombres):
            raise ValueError("Se necesita un ZIP de cuerpos con nombres numéricos, sin rutas.")
        if len({int(nombre) for nombre in nombres}) != len(nombres):
            raise ValueError("Hay identificadores numéricos repetidos.")
        if len(nombres) != DOCUMENTOS_ESPERADOS:
            raise ValueError(f"Se esperaban {DOCUMENTOS_ESPERADOS} cuerpos, hay {len(nombres)}.")
        return [(nombre, archivo.read(nombre)) for nombre in sorted(nombres, key=int)]


def decodificar_cuerpo(cuerpo):
    """Mantiene el UTF-8 válido y sustituye cada byte inválido por un espacio."""
    texto = cuerpo.decode("utf-8", errors="surrogateescape")
    return BYTES_INVALIDOS.subn(" ", texto)


def palabras_normalizadas(tokens):
    """Limpia tokens ya separados por espacios y aplica las stop-words inglesas."""
    for token in tokens:
        token = normalize("NFC", token.lower()).replace("’", "'")
        palabra = BORDES.sub("", token)
        partes = palabra.replace("'", "-").split("-")
        if all(parte.isalpha() for parte in partes) and palabra not in ENGLISH_STOP_WORDS:
            yield palabra


def construir_tf(conteos, columnas):
    datos, indices, punteros = [], [], [0]
    for conteo in conteos:
        pares = sorted((columnas[termino], n) for termino, n in conteo.items() if termino in columnas)
        for columna, n in pares:
            indices.append(columna)
            datos.append(n)
        punteros.append(len(datos))
    return csr_matrix((datos, indices, punteros), shape=(len(conteos), len(columnas)), dtype=np.int32)


def guardar_json(ruta, valor):
    ruta.write_text(json.dumps(valor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def guardar_matriz(ruta, matriz):
    save_npz(ruta, matriz, compressed=True)
    recargada = load_npz(ruta)
    if recargada.format != "csr" or recargada.shape != matriz.shape or recargada.dtype != matriz.dtype:
        raise ValueError(f"Formato, dimensiones o tipo distintos al recargar {ruta.name}.")
    for atributo in ("indptr", "indices", "data"):
        if not np.array_equal(getattr(recargada, atributo), getattr(matriz, atributo)):
            raise ValueError(f"Datos distintos al recargar {ruta.name}.")
    celdas = matriz.shape[0] * matriz.shape[1]
    return {
        "dimensiones": list(matriz.shape),
        "dtype": str(matriz.dtype),
        "no_ceros": matriz.nnz,
        "proporcion_ceros": (celdas - matriz.nnz) / celdas,
        "sha256": sha256(ruta.read_bytes()).hexdigest(),
        "recarga_identica": True,
    }


def generar(origen, destino):
    if destino.exists():
        raise FileExistsError(f"El directorio de salida ya existe: {destino}")

    ids, conteos, blancos, bytes_invalidos = [], [], [], {}
    vocabulario_inicial = set()
    frecuencia_documental = Counter()
    porter = PorterStemmer(mode=PorterStemmer.NLTK_EXTENSIONS)
    for identificador, cuerpo in leer_cuerpos(origen):
        ids.append(identificador)
        texto, n_invalidos = decodificar_cuerpo(cuerpo)
        if not texto.strip() and not n_invalidos:
            blancos.append(identificador)
        if n_invalidos:
            bytes_invalidos[identificador] = n_invalidos
        tokens = texto.split()
        vocabulario_inicial.update(tokens)
        conteo = Counter(porter.stem(palabra, to_lowercase=False) for palabra in palabras_normalizadas(tokens))
        frecuencia_documental.update(conteo.keys())
        conteos.append(conteo)

    terminos = sorted(termino for termino, df in frecuencia_documental.items() if df >= DF_MINIMA)
    if not terminos:
        raise ValueError("Ningún término alcanza la frecuencia documental mínima.")
    columnas = {termino: columna for columna, termino in enumerate(terminos)}
    tf = construir_tf(conteos, columnas)
    tfidf = TfidfTransformer(norm="l2", use_idf=True, smooth_idf=True, sublinear_tf=False)
    pesos = tfidf.fit_transform(tf)

    destino.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destino.parent, prefix=".generar-tf-") as temporal:
        salida = Path(temporal) / "salida"
        salida.mkdir()
        documentos = salida / "documentos.json"
        vocabulario = salida / "vocabulario.json"
        guardar_json(documentos, ids)
        guardar_json(vocabulario, terminos)
        estadisticas = {
            "documentos": len(ids),
            "cuerpos_en_blanco": blancos,
            "bytes_fuera_de_utf8": bytes_invalidos,
            "filas_sin_terminos_seleccionados": [ids[fila] for fila in np.flatnonzero(np.diff(tf.indptr) == 0)],
            "vocabulario_inicial": len(vocabulario_inicial),
            "vocabulario_preprocesado": len(frecuencia_documental),
            "vocabulario_seleccionado": len(terminos),
            "frecuencia_documental_minima": DF_MINIMA,
            "corpus_sha256": sha256(origen.read_bytes()).hexdigest(),
            "orden_sha256": sha256(documentos.read_bytes()).hexdigest(),
            "vocabulario_sha256": sha256(vocabulario.read_bytes()).hexdigest(),
            "versiones": {paquete: version(paquete) for paquete in ("nltk", "numpy", "scipy", "scikit-learn")},
            "tf": guardar_matriz(salida / "tf.npz", tf),
            "tf_idf": guardar_matriz(salida / "tf-idf.npz", pesos),
        }
        guardar_json(salida / "estadisticas.json", estadisticas)
        salida.rename(destino)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origen", type=Path, help="ZIP de cuerpos sin cabeceras")
    parser.add_argument("destino", type=Path, help="directorio nuevo para las matrices y sus índices")
    argumentos = parser.parse_args()
    generar(argumentos.origen, argumentos.destino)


if __name__ == "__main__":
    main()
