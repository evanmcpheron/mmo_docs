import { fileURLToPath } from 'node:url';
import { format, resolveConfig } from 'prettier';

const root = fileURLToPath(new URL('../', import.meta.url));
const options = await resolveConfig(root + 'index.html');
let input = '';
for await (const chunk of process.stdin) input += chunk;
const pages = JSON.parse(input);
const outputs = {};
for (const [path, source] of Object.entries(pages)) {
  outputs[path] = await format(source, { ...options, parser: 'html', filepath: root + path });
}
process.stdout.write(JSON.stringify(outputs));
