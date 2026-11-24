# TF, TF-IDF y Binary en el agrupamiento de noticias

Representación de Textos en Espacios Vectoriales y Probabilísticos · Bloque 1, tema 3

## Corpus y diseño de la comparación

BBC News reúne 2.225 artículos en inglés de 2004 y 2005. El corpus contiene 510 artículos de negocios, 386 de entretenimiento, 417 de política, 511 de deporte y 401 de tecnología. Se conservó la colección publicada, que incluye 98 pares de textos idénticos. Las categorías de la BBC sirvieron para evaluar los grupos después del ajuste.

Se pasaron los textos a minúsculas, se extrajeron palabras de dos o más letras de la a a la z y se eliminaron las palabras vacías de la lista inglesa de scikit-learn. Así se obtuvo un vocabulario común de 27.556 unigramas. TF asignó el recuento de cada término y Binary asignó 1 si aparecía y 0 si estaba ausente. TF-IDF multiplicó el recuento por el IDF suavizado, 1 + ln[(N + 1)/(df + 1)], con N = 2.225 y df igual al número de documentos que contienen el término. Cada vector se normalizó con norma L2 después de aplicar su ponderación. [Fórmula del IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfTransformer.html)

Se ajustó K-means de Lloyd con scikit-learn 1.9.1, distancia euclídea, cinco grupos, tolerancia cero y un máximo de 300 iteraciones. Para cada semilla, de 0 a 4, se eligieron cinco artículos distintos al azar. Los tres ajustes de esa semilla partieron de esos mismos artículos, representados con la ponderación correspondiente. Se ejecutó un ajuste por combinación de semilla y ponderación. Con el corpus, el preprocesado y el algoritmo fijados, la ponderación fue la única variable comparada dentro de cada semilla.

## Resultados del agrupamiento

El índice de Rand ajustado (ARI) compara qué pares de artículos quedan juntos o separados en el agrupamiento y en las categorías de referencia. La información mutua ajustada (AMI) mide cuánta información comparten ambas particiones. Las dos medidas corrigen la coincidencia esperable por azar. Las medias se calcularon antes de redondear.

| Semilla | TF ARI | TF AMI | TF-IDF ARI | TF-IDF AMI | Binary ARI | Binary AMI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0,539 | 0,619 | 0,553 | 0,658 | 0,564 | 0,670 |
| 1 | 0,637 | 0,669 | 0,473 | 0,635 | 0,523 | 0,621 |
| 2 | 0,506 | 0,566 | 0,497 | 0,626 | 0,858 | 0,825 |
| 3 | 0,580 | 0,614 | 0,543 | 0,667 | 0,877 | 0,839 |
| 4 | 0,522 | 0,632 | 0,622 | 0,691 | 0,881 | 0,846 |
| **Media** | **0,557** | **0,620** | **0,538** | **0,656** | **0,741** | **0,760** |

Binary obtuvo las medias más altas y encabezó ambas métricas en cuatro de cinco semillas. La ventaja fue pequeña en la semilla 0 y mucho mayor de la 2 a la 4. Por ejemplo, de los 938 artículos del grupo más grande de Binary en la semilla 0, 493 eran de negocios y 406, de política. En la semilla 4 esas dos categorías quedaron en grupos distintos, con 486 de negocios en uno y 404 de política en otro. La semilla 1 favoreció a TF en las dos métricas.

Añadir IDF a TF elevó la AMI media de 0,620 a 0,656 y redujo el ARI medio de 0,557 a 0,538. Las métricas recogen aspectos distintos del acuerdo y aquí dan un balance diferente. En la semilla 4, TF agrupó 492 noticias de negocios y 409 de política en un grupo de 1.035 artículos. TF-IDF reunió 485 noticias de negocios en otro grupo, aunque agrupó 401 de política con 376 de entretenimiento.

## Frecuencia documental y efecto del IDF

Se calculó df para cada uno de los 27.556 términos. La frecuencia va de 1 a 1.888 documentos. Hay 10.864 términos presentes en un solo artículo, todos con IDF de 8,015. El término más extendido es *said*, con IDF de 1,164. El factor reduce el peso relativo de las palabras que aparecen en muchos documentos frente a las menos extendidas, antes de la normalización L2.

La concentración se midió restando el porcentaje de documentos con el término fuera de un grupo al porcentaje dentro. El nombre de cada grupo indica su categoría más numerosa. Cada fracción da los documentos con el término sobre el total del grupo o del resto del corpus. Estos ejemplos proceden de Binary con la semilla 4.

| Grupo (tamaño) | Término | df | IDF | Dentro | Fuera |
| --- | --- | ---: | ---: | ---: | ---: |
| Entretenimiento (397) | *film* | 243 | 3,211 | 195/397 | 48/1.828 |
| Negocios (510) | *market* | 364 | 2,808 | 221/510 | 143/1.715 |
| Deporte (509) | *game* | 337 | 2,885 | 231/509 | 106/1.716 |
| Deporte (509) | *rugby* | 77 | 4,351 | 73/509 | 4/1.716 |
| Política (439) | *labour* | 238 | 3,231 | 211/439 | 27/1.786 |
| Política (439) | *said* | 1.888 | 1,164 | 414/439 | 1.474/1.786 |
| Tecnología (370) | *technology* | 237 | 3,236 | 196/370 | 41/1.855 |

Reducir el peso relativo de *said* tiene sentido porque, en Binary con la semilla 4, aparece en el 94,3 % del grupo de política y en el 82,5 % de los demás artículos. El IDF también da menos peso a términos frecuentes que sí distinguen grupos. *Government* (df = 470, IDF = 2,553) recibe el 79 % del peso de *labour* a igual recuento, aunque en ese grupo el contraste de presencia es mayor con *government* (57,1 frente a 46,6 puntos). *People* tiene un IDF aún menor (df = 798, IDF = 2,025).

En cada una de las semillas 2, 3 y 4 de Binary, el grupo de política mostró el mayor contraste para *government* y el de tecnología para *people*.

| Semilla | Término | Dentro | Fuera | Diferencia (pp) |
| --- | --- | ---: | ---: | ---: |
| 2 | *government* | 286/412 | 184/1.813 | 59,3 |
| 2 | *people* | 287/383 | 511/1.842 | 47,2 |
| 3 | *government* | 290/432 | 180/1.793 | 57,1 |
| 3 | *people* | 299/400 | 499/1.825 | 47,4 |
| 4 | *government* | 294/439 | 176/1.786 | 57,1 |
| 4 | *people* | 285/370 | 513/1.855 | 49,4 |

La concentración se repite en esas tres particiones. En la semilla 0, el grupo donde más se concentró *government* mezcló política y negocios. En la semilla 4, *rugby* ilustra el caso inverso: su IDF es alto y casi todas sus apariciones están en deporte, pero cubre el 14,3 % del grupo frente al 45,4 % de *game*.

El IDF recoge la frecuencia global y pasa por alto cómo se reparte un término entre grupos. Los ejemplos muestran por qué la penalización puede ser razonable para *said* y reducir el peso relativo de términos que caracterizan un grupo. Dado que TF-IDF modifica todo el vocabulario, el experimento permite comparar las ponderaciones en conjunto. En este corpus y con cinco grupos, Binary obtuvo el mejor acuerdo medio, mientras que el efecto de añadir IDF a TF dependió de la métrica.

### Fuente del corpus

Greene, D. y Cunningham, P. (2006). Practical Solutions to the Problem of Diagonal Dominance in Kernel Document Clustering. *Proceedings of the 23rd International Conference on Machine Learning*, 377–384. [DOI](https://doi.org/10.1145/1143844.1143892) · [BBC News, versión utilizada](https://github.com/derekgreene/bbc-datasets/tree/d81c6d9543cb90683b6927f35f6d06ccb4f59b55#dataset-bbc).
