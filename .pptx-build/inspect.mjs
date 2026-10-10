import fs from 'node:fs/promises';
import { FileBlob, PresentationFile } from 'file:///C:/Users/harsha%20hariharan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const src = 'C:/Users/harsha hariharan/Downloads/AI Software Testing System - MCA Review.pptx';
const ppt = await PresentationFile.importPptx(await FileBlob.load(src));
console.log('slides',ppt.slides.items.length, 'size',ppt.slideSize);
const r=await ppt.inspect({kind:'slide,textbox,shape,image,table,chart,notes,layout',maxChars:25000});
await fs.writeFile('inspect-ai.ndjson',r.ndjson);
const png=await ppt.export({format:'webp',montage:true,scale:.5});
await fs.writeFile('ai-montage.webp',new Uint8Array(await png.arrayBuffer()));
for(let i=0;i<ppt.slides.items.length;i++) {const x=await ppt.export({slide:ppt.slides.items[i],format:'png',scale:1}); await fs.writeFile(`ai-slide-${i+1}.png`,new Uint8Array(await x.arrayBuffer()));}


