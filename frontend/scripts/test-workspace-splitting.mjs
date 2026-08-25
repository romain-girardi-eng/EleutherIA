import { readFileSync, readdirSync, statSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { resolve } from 'node:path';

const assetsDir = resolve(process.cwd(), 'dist/assets');
const files = readdirSync(assetsDir);

function findChunk(prefix) {
  const matches = files.filter((file) => file.startsWith(`${prefix}-`) && file.endsWith('.js'));
  if (matches.length !== 1) {
    throw new Error(`Expected one ${prefix} chunk, found: ${matches.join(', ') || 'none'}`);
  }
  const file = matches[0];
  const path = resolve(assetsDir, file);
  const source = readFileSync(path, 'utf8');
  return {
    file,
    path,
    source,
    rawBytes: statSync(path).size,
    gzipBytes: gzipSync(source).byteLength,
  };
}

function hasStaticImport(source, file) {
  return source.includes(`from"./${file}"`) || source.includes(`import"./${file}"`);
}

const shell = findChunk('CosmographPage');
const atlas = findChunk('AtlasWorkspace');
const chronos = findChunk('ChronosWorkspace');
const scholar = findChunk('ScholarWorkspace');
const vendor = findChunk('cosmograph-vendor');

if (hasStaticImport(shell.source, vendor.file)) {
  throw new Error('CosmographPage shell statically imports the WebGL vendor');
}
if (!hasStaticImport(atlas.source, vendor.file)) {
  throw new Error('AtlasWorkspace must own the static Cosmograph/WebGL import');
}
for (const surface of [chronos, scholar]) {
  if (hasStaticImport(surface.source, vendor.file)) {
    throw new Error(`${surface.file} must not import the Cosmograph/WebGL vendor`);
  }
}
if (!shell.source.includes('import("./AtlasWorkspace-')) {
  throw new Error('AtlasWorkspace is not dynamically imported by the workspace shell');
}

const summary = Object.fromEntries(
  [shell, atlas, chronos, scholar, vendor].map((chunk) => [
    chunk.file,
    {
      raw_kb: Number((chunk.rawBytes / 1024).toFixed(2)),
      gzip_kb: Number((chunk.gzipBytes / 1024).toFixed(2)),
    },
  ]),
);

console.log('Workspace split contract passed.');
console.log(JSON.stringify(summary, null, 2));
