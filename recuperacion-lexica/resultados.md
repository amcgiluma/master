# Recuperación léxica en español

Se compararon técnicas de preprocesamiento y dos modelos de ranking, TF-IDF y BM25, sobre 500 consultas de desarrollo. La comparación parte de TF-IDF con similitud coseno. La tabla de BM25 usa como referencia el TF-IDF con el preprocesamiento combinado.

## Eliminar tildes

La mejora esperada aparece en las tres métricas, aunque el vocabulario solo disminuye un 1,37 %, con 1.051 términos menos. Al unir formas separadas por la tilde cambian las frecuencias documentales, el IDF y las normas de los vectores. Eso explica que también puedan moverse los resultados de consultas que ya estaban sin tilde. Mantendría esta transformación, aun sabiendo que no ayuda en todos los casos.

| Medida | Referencia | Experimento | Diferencia absoluta |
| --- | ---: | ---: | ---: |
| Vocabulario | 76 839 | 75 788 | -1 051 |
| nDCG@10 | 0.5810 | 0.6270 | +0.0460 |
| MRR@10 | 0.5385 | 0.5827 | +0.0441 |
| Recall@50 | 0.7960 | 0.8400 | +0.0440 |

## Eliminar palabras vacías

| Medida | Referencia | Experimento | Diferencia absoluta |
| --- | ---: | ---: | ---: |
| Vocabulario | 76 839 | 76 617 | -222 |
| nDCG@10 | 0.5810 | 0.5828 | +0.0018 |
| MRR@10 | 0.5385 | 0.5444 | +0.0058 |
| Recall@50 | 0.7960 | 0.7920 | -0.0040 |

Las métricas apenas cambian y no todas lo hacen a favor. La mejora esperada se cumple en nDCG@10 y MRR@10, pero Recall@50 baja de 398 a 396 positivos recuperados. IDF ya resta peso a las palabras frecuentes; quitarlas aporta poco y puede borrar coincidencias útiles, además de cambiar la normalización del coseno.

El vocabulario se reduce en 222 términos, un 0,29 %. La lista tiene 313 entradas, pero algunas no aparecen como tokens del corpus.

## Stemming

| Medida | Referencia | Experimento | Diferencia absoluta |
| --- | ---: | ---: | ---: |
| Vocabulario | 76 839 | 45 334 | -31 505 |
| nDCG@10 | 0.5810 | 0.6371 | +0.0561 |
| MRR@10 | 0.5385 | 0.5959 | +0.0574 |
| Recall@50 | 0.7960 | 0.8780 | +0.0820 |

Con stemming se recuperan 439 positivos entre los primeros 50, frente a 398 del baseline. También suben nDCG@10 y MRR@10. La reducción de vocabulario es la que esperaba: 31.505 términos menos, un 41,00 %, al agrupar variantes.

Esto facilita coincidencias, pero también borra distinciones y aumenta la competencia entre documentos. Los casos que empeoran impiden concluir que el stemming beneficie a todas las consultas.

## Lematización

La lematización reduce el vocabulario como esperaba, pero la recuperación empeora. Hay 13.514 términos menos, un 17,59 %, una reducción menor que con stemming. Bajan nDCG@10 y MRR@10; Recall@50 permanece en 0,796. Stemming obtiene mejores valores en las tres métricas: 0,6371, 0,5959 y 0,8780, respectivamente.

| Medida | Referencia | Experimento | Diferencia absoluta |
| --- | ---: | ---: | ---: |
| Vocabulario | 76 839 | 63 325 | -13 514 |
| nDCG@10 | 0.5810 | 0.5547 | -0.0263 |
| MRR@10 | 0.5385 | 0.5183 | -0.0202 |
| Recall@50 | 0.7960 | 0.7960 | +0.0000 |

Por tanto, agrupar más formas no basta para mejorar la búsqueda. El análisis depende del contexto y puede fallar con nombres o palabras ambiguas. Los lemas resultan más legibles que las raíces, pero eso no garantiza mejores posiciones. La conclusión se limita al modelo usado, no a todos los lematizadores.

## Combinar técnicas

| Medida | Referencia | Experimento | Diferencia absoluta |
| --- | ---: | ---: | ---: |
| Vocabulario | 76 839 | 46 091 | -30 748 |
| nDCG@10 | 0.5810 | 0.6412 | +0.0602 |
| MRR@10 | 0.5385 | 0.6013 | +0.0628 |
| Recall@50 | 0.7960 | 0.8820 | +0.0860 |

La combinación supera ligeramente a stemming: +0,0041 en nDCG@10, +0,0054 en MRR@10 y +0,0040 en Recall@50. Frente al baseline, mejora las tres métricas y reduce el vocabulario en 30.748 términos, un 40,02 %. Los resultados respaldan la elección en desarrollo, aunque no demuestran significación estadística ni generalización.

El vocabulario combinado tiene 46.091 términos, más que los 45.334 de stemming solo. Quitar tildes antes puede cambiar qué sufijos reconoce Snowball. El orden importa: la combinación no equivale a sumar los efectos de las técnicas por separado. La pequeña ventaja sobre stemming había que comprobarla.

## Cambiar el ranking a BM25

| Medida | Referencia | Experimento | Diferencia absoluta |
| --- | ---: | ---: | ---: |
| nDCG@10 | 0.6412 | 0.6976 | +0.0564 |
| MRR@10 | 0.6013 | 0.6581 | +0.0567 |
| Recall@50 | 0.8820 | 0.8860 | +0.0040 |

BM25 recupera 443 positivos entre los primeros 50, frente a 441 con TF-IDF: entran cuatro y salen dos. La ganancia de cobertura es pequeña. En cambio, nDCG@10 y MRR@10 suben bastante más, lo que indica que mejora sobre todo la posición de los positivos. Las mejoras relativas son del 8,80 % en nDCG@10, 9,43 % en MRR@10 y 0,45 % en Recall@50.

Se confirma la hipótesis de mejor ordenación, con algunas consultas que empeoran y la misma necesidad de coincidencia léxica. Se mantienen corpus, consultas y tokens. `BM25Okapi` usa sus valores predeterminados, k1=1,5, b=0,75 y epsilon=0,25. Como también cambia el IDF, no podemos atribuir el resultado solo a saturación o longitud.

## Datos

El corpus docente `aii-ir-es-v1` combina consultas de [MessIRve](https://huggingface.co/datasets/spanish-ir/messirve) y pasajes de la Wikipedia en español. Los juicios de desarrollo marcan un solo pasaje relevante por consulta, así que las métricas sirven para comparar configuraciones con ese criterio.
