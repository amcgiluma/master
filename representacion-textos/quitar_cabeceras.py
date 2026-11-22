"""Guarda los cuerpos del corpus docente con sus identificadores numéricos."""

import argparse
import re
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


CORPUS = "Corpus-Tarea-representacion"
SEPARADOR = re.compile(rb"\r?\n[ \t]*\r?\n")
CAMPO = re.compile(rb"[!-9;-~]+:")


def quitar_cabecera(mensaje: bytes) -> bytes:
    """Corta por la primera línea en blanco tras una cabecera válida."""
    separador = SEPARADOR.search(mensaje)
    if separador is None:
        raise ValueError("falta la línea en blanco que cierra la cabecera")

    lineas = mensaje[:separador.start()].splitlines()
    if not lineas or not CAMPO.match(lineas[0]):
        raise ValueError("la primera línea no es un campo de cabecera")
    if any(not (CAMPO.match(linea) or linea.startswith((b" ", b"\t"))) for linea in lineas):
        raise ValueError("la cabecera contiene una línea inesperada")
    return mensaje[separador.end():]


def leer_corpus(origen: Path) -> dict[str, bytes]:
    cuerpos = {}
    with ZipFile(origen) as archivo:
        for entrada in archivo.infolist():
            ruta = PurePosixPath(entrada.filename)
            if entrada.is_dir() or ruta.parts[:1] != (CORPUS,):
                continue
            identificador = ruta.name
            if not re.fullmatch(r"[0-9]+", identificador) or identificador in cuerpos:
                raise ValueError(f"identificador no numérico o repetido: {identificador!r}")
            try:
                cuerpos[identificador] = quitar_cabecera(archivo.read(entrada))
            except ValueError as error:
                raise ValueError(f"mensaje {identificador}: {error}") from error
    if not cuerpos:
        raise ValueError("el ZIP no contiene mensajes")
    return cuerpos


def main() -> None:
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("origen", type=Path)
    argumentos.add_argument("destino", type=Path, help="ZIP nuevo que se va a crear")
    opciones = argumentos.parse_args()
    cuerpos = leer_corpus(opciones.origen)
    with ZipFile(opciones.destino, "x", compression=ZIP_DEFLATED) as salida:
        for identificador in sorted(cuerpos, key=int):
            salida.writestr(ZipInfo(identificador), cuerpos[identificador], ZIP_DEFLATED)
    print(f"Mensajes: {len(cuerpos)}. Cuerpos vacíos o en blanco: "
          f"{sum(not cuerpo.strip() for cuerpo in cuerpos.values())}.")


if __name__ == "__main__":
    main()
