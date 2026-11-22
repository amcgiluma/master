# Corpus y comparación de etiquetadores léxicos

## Parte I. Estudio de corpus

### Descripción de los corpus

**Brown.** Reúne prosa inglesa publicada en Estados Unidos en 1961. Sus 500 muestras de unas 2000 palabras proceden de periódicos, revistas, libros y otras publicaciones, repartidas en 15 categorías. La versión etiquetada indica la clase gramatical de cada palabra. Es lo que se llama etiquetado léxico o etiquetado POS, del inglés *part of speech* [1].

**SUSANNE.** La versión 5 vuelve a anotar 64 muestras de Brown, 16 de cada género seleccionado. Indica la clase gramatical y el lema (la forma de diccionario) de cada palabra. También marca qué palabras forman un grupo en la oración (constituyentes) y qué función sintáctica cumplen. Los índices señalan, por ejemplo, la posición que correspondería a un elemento desplazado [2].

**Penn Treebank.** En su primera fase, el proyecto anotó textos en inglés estadounidense procedentes de la prensa, libros, documentación técnica y transcripciones de habla. Los anotadores corrigieron las etiquetas y el análisis sintáctico que proponía el sistema automático. El artículo de 1993 recoge las cifras hasta noviembre de 1992 y expresa el tamaño del corpus en tokens, las unidades en que se divide el texto para etiquetarlo [3].

### Comparativa concisa

| Aspecto | Brown | SUSANNE, versión 5 | Penn Treebank, descripción de 1993 |
| --- | --- | --- | --- |
| Anotación | POS | POS, lemas, constituyentes, funciones e índices | POS y análisis parcial por constituyentes |
| Tamaño | 1 014 312 palabras en 500 muestras [1] | Unas 130 000 palabras en 64 muestras [2] | 4 885 798 tokens con POS. De ellos, 2 881 188 con análisis sintáctico esquemático [3, tabla 4] |
| Etiquetas léxicas | 87 simples y 187 en total con las compuestas [3, §2.1 y nota 2] | 353, sin las etiquetas de componentes de expresiones fijas [2, §4.4] | 36 POS y 12 códigos de puntuación y moneda [3, tabla 2] |
| Temáticas y géneros | 15 categorías, entre ellas noticias, religión, ciencia y ficción | Prensa, biografía/ensayo, prosa académica y aventuras | Noticias económicas, ciencia, literatura y consultas sobre vuelos |
| Procedencia | Periódicos, revistas, libros y documentos publicados en Estados Unidos en 1961 | Subconjunto de las mismas publicaciones de Brown | Teletipo Dow Jones, Brown, libros, manuales y transcripciones de radio |

El recuento de Brown es el de Marcus et al. [3]. Una contracción como *I'm* reúne dos etiquetas en un código. Algunas etiquetas de SUSANNE no aparecen en la muestra. La fila «Etiquetas léxicas» excluye `N` en SUSANNE y `NP` en Penn, que señalan un sintagma nominal [2, §4.10; 3, tabla 3].

### Elección para estimar frecuencias de etiquetas y parejas consecutivas

Brown es más adecuado que SUSANNE porque reúne más texto y más géneros.  
Su inventario más reducido reparte los casos entre menos etiquetas y parejas.  
Brown marca el fin de oración [1]. Se cuentan solo parejas consecutivas dentro de cada oración.  
Las frecuencias describen prosa estadounidense publicada en 1961.

## Parte II. Comparativa de etiquetadores estadísticos

En *I watch the birds*, *watch* significa «observo». Es un verbo en presente y recibe la etiqueta VBP. En *The old watch on my desk*, *watch* significa «reloj». Es un sustantivo y recibe NN, la etiqueta de nombre común singular o de masa. Los dos etiquetadores trabajan en inglés y se enfrentan a este cambio de clase gramatical entre oraciones.

### Etiquetadores seleccionados

**NLTK PerceptronTagger.** Recorre la oración de izquierda a derecha. Si la palabra figura en su diccionario, usa la etiqueta que consta allí. Para construir ese diccionario, el código exige al menos 20 apariciones de la palabra y que la misma etiqueta se use en al menos el 97 % de ellas [4]. Para las demás palabras, un perceptrón promediado puntúa las etiquetas posibles según la forma de la palabra, las palabras cercanas y las etiquetas que ya ha asignado. El paquete inglés `averaged_perceptron_tagger_eng` distingue 45 etiquetas. Su índice no indica qué parte de los datos se usó para entrenar el modelo [4, 5].

**spaCy en_core_web_sm 3.8.0.** `tok2vec` representa cada token a partir de rasgos como el prefijo y el sufijo. El codificador convolucional Maxout (`MaxoutWindowEncoder`) incorpora el contexto de los tokens vecinos [7]. Con esa información, `tagger` elige una de 50 etiquetas. En la prueba se leyó la etiqueta detallada `tag_` a la salida de `tagger`, con `attribute_ruler` desactivado. Los metadatos citan OntoNotes 5 entre las fuentes del modelo [6].

Los dos modelos usan variantes del inventario Penn [3, 8]. Ambos pueden asignar todas las etiquetas que aparecen en la referencia manual de esta prueba. Además de NN, ambos usan NNS para el nombre común plural y NNP para el nombre propio. Las diferencias entre los inventarios quedan fuera de la prueba. Por ejemplo, el texto carece de guiones, que spaCy etiqueta como HYPH.

### Texto de prueba

El texto de prueba contiene 16 oraciones, una por línea. Ocho palabras aparecen dos veces y cambian de clase gramatical entre una aparición y la otra.

```text
At dawn, I watch the birds by the river.
The old watch on my desk has stopped.
I can hear their wings through the open window.
A metal can lies beside the garden gate.
We book a room near the station every spring.
This book describes the history of the town.
I saw a duck under the wooden bridge.
The carpenter left a saw on the bench.
The light above the door is bright.
They light the small lamp before dinner.
Fruit flies gather around the apples in the kitchen.
A small bird flies over the roof.
The children like the music from the radio.
Their paper boats look like tiny ships.
We close the gate when the sky grows dark.
Our close friends stay for a quiet meal.
```

### Referencia manual

La referencia manual se fijó antes de ejecutar los modelos, según la guía Penn [8]. Los nombres que modifican a otro nombre, como *metal*, *garden* y *paper*, conservan la etiqueta NN. En *Fruit flies*, *Fruit* también recibe NN pese a la mayúscula inicial.

En *I can hear*, *can* es un verbo modal (MD) y *hear* está en la forma base (VB). En *I saw*, *saw* está en pasado (VBD). En *has stopped*, *stopped* es un participio pasado (VBN).

En el presente de indicativo, VBZ marca la tercera persona del singular y VBP se usa para las demás personas. La distinción permite detectar errores de flexión. Por ejemplo, etiquetar *lies* como forma base (VB) identifica el verbo, pero pierde la marca de tercera persona del singular (VBZ).

En *The old watch*, *The* es un determinante (DT) y *old* es un adjetivo (JJ). *I* es un pronombre personal (PRP) y *my* recibe la etiqueta de posesivo (PRP$).

La etiqueta IN se usa para preposiciones como *on* y para conjunciones subordinantes. WRB identifica adverbios interrogativos o relativos, como *when* en la subordinada temporal de la línea 15. El punto y la coma se cuentan como tokens separados.

```text
At/IN dawn/NN ,/, I/PRP watch/VBP the/DT birds/NNS by/IN the/DT river/NN ./.
The/DT old/JJ watch/NN on/IN my/PRP$ desk/NN has/VBZ stopped/VBN ./.
I/PRP can/MD hear/VB their/PRP$ wings/NNS through/IN the/DT open/JJ window/NN ./.
A/DT metal/NN can/NN lies/VBZ beside/IN the/DT garden/NN gate/NN ./.
We/PRP book/VBP a/DT room/NN near/IN the/DT station/NN every/DT spring/NN ./.
This/DT book/NN describes/VBZ the/DT history/NN of/IN the/DT town/NN ./.
I/PRP saw/VBD a/DT duck/NN under/IN the/DT wooden/JJ bridge/NN ./.
The/DT carpenter/NN left/VBD a/DT saw/NN on/IN the/DT bench/NN ./.
The/DT light/NN above/IN the/DT door/NN is/VBZ bright/JJ ./.
They/PRP light/VBP the/DT small/JJ lamp/NN before/IN dinner/NN ./.
Fruit/NN flies/NNS gather/VBP around/IN the/DT apples/NNS in/IN the/DT kitchen/NN ./.
A/DT small/JJ bird/NN flies/VBZ over/IN the/DT roof/NN ./.
The/DT children/NNS like/VBP the/DT music/NN from/IN the/DT radio/NN ./.
Their/PRP$ paper/NN boats/NNS look/VBP like/IN tiny/JJ ships/NNS ./.
We/PRP close/VBP the/DT gate/NN when/WRB the/DT sky/NN grows/VBZ dark/JJ ./.
Our/PRP$ close/JJ friends/NNS stay/VBP for/IN a/DT quiet/JJ meal/NN ./.
```

### Resultados del etiquetado

Los dos modelos recibieron los mismos tokens y procesaron cada línea por separado. Se usaron NLTK 3.10.4 y spaCy 3.8.18 con Python 3.11.15. En las salidas, cada palabra va seguida de una barra y su etiqueta.

#### NLTK PerceptronTagger

```text
At/IN dawn/NN ,/, I/PRP watch/VBP the/DT birds/NNS by/IN the/DT river/NN ./.
The/DT old/JJ watch/NN on/IN my/PRP$ desk/NN has/VBZ stopped/VBN ./.
I/PRP can/MD hear/VB their/PRP$ wings/NNS through/IN the/DT open/JJ window/NN ./.
A/DT metal/NN can/MD lies/VB beside/IN the/DT garden/NN gate/NN ./.
We/PRP book/NN a/DT room/NN near/IN the/DT station/NN every/DT spring/NN ./.
This/DT book/NN describes/VBZ the/DT history/NN of/IN the/DT town/NN ./.
I/PRP saw/VBD a/DT duck/NN under/IN the/DT wooden/JJ bridge/NN ./.
The/DT carpenter/NN left/VBD a/DT saw/NN on/IN the/DT bench/NN ./.
The/DT light/JJ above/IN the/DT door/NN is/VBZ bright/VBN ./.
They/PRP light/VBD the/DT small/JJ lamp/NN before/IN dinner/NN ./.
Fruit/NNP flies/VBZ gather/VBP around/IN the/DT apples/NNS in/IN the/DT kitchen/NN ./.
A/DT small/JJ bird/NN flies/NNS over/IN the/DT roof/NN ./.
The/DT children/NNS like/IN the/DT music/NN from/IN the/DT radio/NN ./.
Their/PRP$ paper/NN boats/NNS look/VBP like/IN tiny/JJ ships/NNS ./.
We/PRP close/VBP the/DT gate/NN when/WRB the/DT sky/NN grows/VBZ dark/NN ./.
Our/PRP$ close/JJ friends/NNS stay/VBP for/IN a/DT quiet/JJ meal/NN ./.
```

#### spaCy en_core_web_sm

```text
At/IN dawn/NN ,/, I/PRP watch/VBP the/DT birds/NNS by/IN the/DT river/NN ./.
The/DT old/JJ watch/NN on/IN my/PRP$ desk/NN has/VBZ stopped/VBN ./.
I/PRP can/MD hear/VB their/PRP$ wings/NNS through/IN the/DT open/JJ window/NN ./.
A/DT metal/NN can/MD lies/VBZ beside/IN the/DT garden/NN gate/NN ./.
We/PRP book/VBP a/DT room/NN near/IN the/DT station/NN every/DT spring/NN ./.
This/DT book/NN describes/VBZ the/DT history/NN of/IN the/DT town/NN ./.
I/PRP saw/VBD a/DT duck/NN under/IN the/DT wooden/JJ bridge/NN ./.
The/DT carpenter/NN left/VBD a/DT saw/NN on/IN the/DT bench/NN ./.
The/DT light/NN above/IN the/DT door/NN is/VBZ bright/JJ ./.
They/PRP light/VBP the/DT small/JJ lamp/NN before/IN dinner/NN ./.
Fruit/NN flies/NNS gather/VBP around/IN the/DT apples/NNS in/IN the/DT kitchen/NN ./.
A/DT small/JJ bird/NN flies/NNS over/IN the/DT roof/NN ./.
The/DT children/NNS like/IN the/DT music/NN from/IN the/DT radio/NN ./.
Their/PRP$ paper/NN boats/NNS look/VBP like/IN tiny/JJ ships/NNS ./.
We/PRP close/VBP the/DT gate/NN when/WRB the/DT sky/NN grows/VBZ dark/JJ ./.
Our/PRP$ close/JJ friends/NNS stay/VBP for/IN a/DT quiet/JJ meal/NN ./.
```

### Observaciones sobre la comparativa y conclusiones

La exactitud es la proporción de tokens con la etiqueta correcta. Se calculó para el texto completo y se volvió a calcular excluyendo los 17 signos de puntuación. El tercer cálculo toma solo las 16 apariciones de las palabras ambiguas.

| Evaluación | NLTK | spaCy |
| --- | --- | --- |
| Todos los tokens | 135/146 = 92,47 % | 143/146 = 97,95 % |
| Sin puntuación | 118/129 = 91,47 % | 126/129 = 97,67 % |
| Apariciones de las ocho palabras de contraste | 9/16 = 56,25 % | 13/16 = 81,25 % |

Para cada palabra ambigua, las dos etiquetas de referencia se dan en el orden de sus apariciones en el texto. *watch* (VBP/NN), *can* (MD/NN), *book* (VBP/NN) y *saw* (VBD/NN) aparecen primero como verbos y luego como sustantivos. *light* (NN/VBP) y *flies* (NNS/VBZ) aparecen primero como sustantivos y luego como verbos. *like* (VBP/IN) pasa de verbo a preposición y *close* (VBP/JJ), de verbo a adjetivo.

La tabla recoge los tokens que al menos un modelo etiquetó mal.

| Línea | Token | Referencia | NLTK | spaCy |
| --- | --- | --- | --- | --- |
| 4 | can | NN | MD | MD |
| 4 | lies | VBZ | VB | VBZ |
| 5 | book | VBP | NN | VBP |
| 9 | light | NN | JJ | NN |
| 9 | bright | JJ | VBN | JJ |
| 10 | light | VBP | VBD | VBP |
| 11 | Fruit | NN | NNP | NN |
| 11 | flies | NNS | VBZ | NNS |
| 12 | flies | VBZ | NNS | NNS |
| 13 | like | VBP | IN | IN |
| 15 | dark | JJ | NN | JJ |

Los dos modelos coinciden en tres errores. En *a metal can*, el artículo *a* y el modificador *metal* preceden al sustantivo *can* (NN). En *a small bird flies*, *flies* concuerda con el sujeto singular *a small bird* (VBZ). En *the children like the music*, *like* es el verbo en presente de un sujeto plural (VBP).

En NLTK, el diccionario toma *can* por modal (MD) y *book* por sustantivo (NN). Así se explican el error con el sustantivo *can* en la línea 4 y el error con el verbo *book* en la 5. En la línea 4, NLTK asigna MD a *can* y VB a *lies*, el patrón de un modal seguido de una forma base. La salida por sí sola deja abierta la causa del error en *lies*.

NLTK toma *light* por adjetivo en la línea 9, donde significa «luz», y por verbo en pasado en la 10, donde significa «encienden». En *Fruit flies* asigna a *Fruit* la etiqueta de nombre propio y a *flies* la de verbo, aunque ambos son sustantivos. En *is bright* y *grows dark*, los adjetivos describen el estado del sujeto. NLTK etiqueta *bright* como participio pasado y *dark* como sustantivo. spaCy acierta en estos casos y asigna a *lies* la etiqueta VBZ de presente.

spaCy acertó ocho tokens más en el texto completo y cuatro más entre las 16 apariciones de las palabras ambiguas. La ventaja se ha medido solo en esta muestra construida. La comparación deja sin resolver cuánto influyeron por separado el modelo y su entrenamiento.

## Referencias

[1] Francis, W. N. y Kučera, H. Manual of Information to Accompany a Standard Corpus of Present-Day Edited American English. Brown University, edición revisada de 1979. [Manual de Brown](https://icame.info/icame_static/manuals/BROWN/INDEX.HTM), §§1 y 4.

[2] Sampson, G. The SUSANNE Corpus: Documentation. Release 5, 2000. [Documentación](https://www.grsampson.net/SueDoc.html), §§2 y 4.4. [Índice estable de recursos del autor](https://www.grsampson.net/Resources.html).

[3] Marcus, M. P., Santorini, B. y Marcinkiewicz, M. A. 1993. Building a Large Annotated Corpus of English: The Penn Treebank. Computational Linguistics, 19(2), 313–330. [Artículo original](https://aclanthology.org/J93-2004/), §§1, 2 y 5, tablas 2 y 4.

[4] NLTK Project. nltk.tag.perceptron. [Implementación de PerceptronTagger](https://www.nltk.org/_modules/nltk/tag/perceptron.html).

[5] NLTK Data. [Índice del paquete averaged_perceptron_tagger_eng](https://github.com/nltk/nltk_data/blob/gh-pages/index.xml).

[6] Explosion. [Metadatos de en_core_web_sm 3.8.0](https://raw.githubusercontent.com/explosion/spacy-models/master/meta/en_core_web_sm-3.8.0.json).

[7] Explosion. [Arquitecturas de spaCy](https://spacy.io/api/architectures). Configuración efectiva del modelo instalado: spacy.Tagger.v2, spacy.MultiHashEmbed.v2 y spacy.MaxoutWindowEncoder.v2.

[8] Santorini, B. 1990. Part-of-Speech Tagging Guidelines for the Penn Treebank Project. Tercera revisión, reimpresión de 1995. University of Pennsylvania. [Guía de etiquetado distribuida con Treebank-3](https://catalog.ldc.upenn.edu/docs/LDC99T42/tagguid1.pdf).
