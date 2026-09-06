// Retrieval check for docs/ask.html: runs the page's own BM25 code under node
// against the real chunks, so a broken query path fails here, not in a browser.
//   node scripts/test_ask.js
const fs = require('fs');
const root = require('path').join(__dirname, '..');

const html = fs.readFileSync(`${root}/docs/ask.html`, 'utf8');
const js = html.match(/<script>([\s\S]*?)<\/script>/g).pop().replace(/<\/?script>/g, '');

const noop = () => {};
const stubEl = {value: '', innerHTML: '', addEventListener: noop, appendChild: noop};
global.window = {};
global.document = {getElementById: () => stubEl,
                  createElement: () => ({addEventListener: noop})};
global.history = {replaceState: noop};
global.location = {search: ''};
global.URLSearchParams = class { get() { return null; } };
global.fetch = () => new Promise(noop);   // the page's own load never resolves
eval(js);

const {index, search, tokens} = window.AskSalerno;
index(fs.readFileSync(`${root}/data/rag/chunks.jsonl`, 'utf8')
        .trim().split('\n').map(JSON.parse));

const must = (cond, msg) => { if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; } };

must(tokens('Città di Salerno!').join(' ') === 'citt di salern',
     'accent folding + stemming: ' + tokens('Città di Salerno!').join(' '));
must(tokens('castelli')[0] === tokens('castello')[0], 'singolare/plurale');
must(tokens('spiagge')[0] === tokens('spiaggia')[0], 'singolare/plurale');

const cases = [
  ['tempio greco a Paestum', /tempio|paestum/i, {}],
  ['spiagge vicino a Positano', /spiagg|positano/i, {categoria: 'spiagge'}],
  ['castelli nel Cilento', /castell/i, {zona: 'cilento'}],
  ['sentieri panoramici in Costiera', /sentier/i, {zona: 'costiera', categoria: 'sentieri'}],
];
for (const [q, re, want] of cases) {
  const res = search(q);
  must(res.hits.length > 0, `nessun risultato per "${q}"`);
  must(re.test(res.hits[0].doc.text), `primo risultato fuori tema per "${q}": ${res.hits[0].doc.nome}`);
  for (const k of Object.keys(want)) {
    must(res.filters[k] === want[k], `filtro ${k} non riconosciuto in "${q}"`);
    must(res.hits.every(h => h.doc[k === 'categoria' ? 'categoria' : 'zona'] === want[k]),
         `risultati fuori dal filtro ${k} per "${q}"`);
  }
  must(res.hits.every((h, i, a) => i === 0 || a[i - 1].score >= h.score), 'ordinamento');
}
must(search('qwertyuiop asdfghjkl').hits.length === 0, 'query senza senso deve dare 0 risultati');

// il boost su tipo deve portare un castello davanti a una via che si chiama "Castello"
must(search('castelli visitabili').hits[0].doc.tipo === 'castello',
     'boost per tipo: ' + search('castelli visitabili').hits[0].doc.nome);

if (!process.exitCode) console.log('ok');
