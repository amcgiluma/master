# Comparación inicial de ponderaciones

El corpus BBC News reúne 2.225 artículos en inglés publicados entre 2004 y 2005. Incluye 510 de negocios, 386 de entretenimiento, 417 de política, 511 de deporte y 401 de tecnología. El experimento conserva el corpus publicado, con 98 pares de textos idénticos dentro de su categoría. Las categorías sirven como referencia para evaluar los grupos. [Corpus y condiciones de uso](https://github.com/derekgreene/bbc-datasets/blob/d81c6d9543cb90683b6927f35f6d06ccb4f59b55/README.md)

Cada archivo se lee en UTF-8. El preprocesado convierte a minúsculas, extrae palabras de al menos dos letras de la a a la z y elimina las palabras vacías de la lista inglesa de scikit-learn. Se cuentan unigramas en un vocabulario común de 27.556 términos. TF usa el recuento, Binary indica la presencia y TF-IDF multiplica el recuento por `ln((1 + N)/(1 + df)) + 1`. Los tres vectores se normalizan por documento con norma L2.

K-means de Lloyd forma cinco grupos. Cada semilla de 0 a 4 elige cinco documentos distintos sin consultar las categorías y usa esos mismos documentos como centroides iniciales en las tres representaciones. Cada ajuste tiene una inicialización, tolerancia cero y un máximo de 300 iteraciones. Se guardan las asignaciones, los tamaños de grupo, el índice de Rand ajustado (ARI) y la información mutua ajustada (AMI).

## Reproducción

Ejecuta `python clustering_base.py`. La ejecución comprobada usa Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1 y scikit-learn 1.9.1. El programa descarga la copia exacta del corpus si hace falta y valida su SHA-256.

- `resultados-base/metricas.json` contiene los parámetros, los documentos iniciales y las métricas por semilla.
- `resultados-base/grupos.csv` se genera con los grupos por documento y categoría de referencia.
- `resultados-base/frecuencia-documental.csv` se genera con la frecuencia documental y el IDF de cada término del vocabulario.

Para comprobar las 15 métricas y las frecuencias documentales y reproducir el contraste de *government* y *people*, ejecuta estos comandos desde este directorio:

```sh
python analizar_resultados.py --output /tmp/perfiles-clustering.json --terms government people
jq -r -f concentracion-binary.jq /tmp/perfiles-clustering.json > /tmp/concentracion-binary.csv
cmp /tmp/concentracion-binary.csv concentracion-binary.csv
```

El [CSV](concentracion-binary.csv) incluye los cinco grupos de Binary para cada semilla. `difference_pp` resta el porcentaje de presencia fuera del grupo al porcentaje dentro. `majority_topic` indica la categoría de referencia más numerosa de cada grupo.

Consulta la [memoria final](memoria.md).

Greene, D. y Cunningham, P. (2006). Practical solutions to the problem of diagonal dominance in kernel document clustering. *Proceedings of the 23rd International Conference on Machine Learning*, 377–384. [ACM](https://doi.org/10.1145/1143844.1143892)
