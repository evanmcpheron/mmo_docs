import { readFile } from 'node:fs/promises';
import * as prettier from 'prettier';

const options = JSON.parse(await readFile(new URL('../.prettierrc.json', import.meta.url), 'utf8'));
let input = '';
for await (const chunk of process.stdin) input += chunk;
const documents = JSON.parse(input);
const formatted = {};
for (const [path, source] of Object.entries(documents)) {
  formatted[path] = await prettier.format(source, { ...options, filepath: path, parser: 'html' });
}
process.stdout.write(JSON.stringify(formatted));
