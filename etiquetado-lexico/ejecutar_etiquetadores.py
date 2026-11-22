"""Ejecutar sobre tokens comunes; conservar salidas originales y evaluación."""
from pathlib import Path
import csv, hashlib, importlib.metadata, json, platform
import nltk, spacy
from nltk.tag.perceptron import PerceptronTagger
from spacy.tokens import Doc

BASE = Path(__file__).resolve().parent
nltk.download('averaged_perceptron_tagger_eng', quiet=True)
reference_bytes = (BASE / 'referencia.txt').read_bytes()
gold = [[tuple(item.rsplit('/', 1)) for item in line.split()]
        for line in reference_bytes.decode().splitlines() if line.strip()]
assert len(gold) >= 15
text = '\n'.join(' '.join(word for word, _ in sent).replace(' .', '.').replace(' ,', ',') for sent in gold) + '\n'
(BASE / 'texto.txt').write_text(text)
perceptron = PerceptronTagger(lang='eng')
nlp = spacy.load('en_core_web_sm', disable=['ner', 'parser', 'lemmatizer', 'attribute_ruler'])
rows = []
outputs = {'nltk': [], 'spacy': []}
for line, sent in enumerate(gold, 1):
    words = [w for w, _ in sent]
    nt = [t for _, t in perceptron.tag(words)]
    doc = nlp(Doc(nlp.vocab, words=words))
    st = [t.tag_ for t in doc]
    assert [t.text for t in doc] == words and len(nt) == len(st) == len(sent)
    outputs['nltk'].append(' '.join(f'{w}/{t}' for w, t in zip(words, nt)))
    outputs['spacy'].append(' '.join(f'{w}/{t}' for w, t in zip(words, st)))
    for position, ((word, tag), a, b) in enumerate(zip(sent, nt, st), 1):
        rows.append({'linea': line, 'posicion': position, 'token': word, 'referencia': tag, 'nltk': a, 'spacy': b})
for name, lines in outputs.items():
    (BASE / f'salida_{name}.txt').write_text('\n'.join(lines) + '\n')
with (BASE / 'comparacion.tsv').open('w') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t')
    writer.writeheader(); writer.writerows(rows)
metrics = {}
for name in outputs:
    correct = sum(r[name] == r['referencia'] for r in rows)
    errors = [r for r in rows if r[name] != r['referencia']]
    lexical = [r for r in rows if r['referencia'] not in ['.', ',']]
    metrics[name] = {'correctos': correct, 'total': len(rows), 'exactitud': correct / len(rows),
                     'correctos_sin_puntuacion': sum(r[name] == r['referencia'] for r in lexical),
                     'total_sin_puntuacion': len(lexical), 'errores': errors}
metadata = {'python': platform.python_version(), 'nltk': nltk.__version__, 'spacy': spacy.__version__,
            'modelo_spacy': nlp.meta['version'], 'lineas': len(gold), 'tokens': len(rows),
            'referencia_sha256': hashlib.sha256(reference_bytes).hexdigest(),
            'clases_nltk': sorted(perceptron.classes), 'clases_spacy': list(nlp.get_pipe('tagger').labels),
            'config_spacy_tagger': dict(nlp.config['components']['tagger']),
            'config_spacy_tok2vec': dict(nlp.config['components']['tok2vec']),
            'sources_spacy': nlp.meta.get('sources'), 'metricas': metrics,
            'protocolo': 'Referencia fijada antes de inferencia. Mismos tokens y cada línea procesada como oración. Solo tok2vec y tagger en spaCy; se compara tag_, sin correcciones de attribute_ruler.'}
(BASE / 'resultados.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in metadata.items() if k in ['python','nltk','spacy','lineas','tokens','metricas']}, ensure_ascii=False, indent=2))
