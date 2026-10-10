import fs from 'node:fs/promises';
import {FileBlob,PresentationFile} from 'file:///C:/Users/harsha%20hariharan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const file='D:/ai_software_tester/output/AI_Software_Testing_System_Testing_Section.pptx';
const p=await PresentationFile.importPptx(await FileBlob.load(file));
console.log('verified slides:',p.slides.items.length);
for(let i=0;i<p.slides.items.length;i++){
 const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(`D:/ai_software_tester/.pptx-build/final-slide-${i+1}.png`,new Uint8Array(await blob.arrayBuffer()));
}
const montage=await p.export({format:'webp',montage:true,scale:0.5});
await fs.writeFile('D:/ai_software_tester/.pptx-build/final-montage.webp',new Uint8Array(await montage.arrayBuffer()));
const snap=await p.inspect({kind:'slide,textbox,table',search:'Testing Strategy|Test Case Design|Crime Reporting',maxChars:6000});
await fs.writeFile('D:/ai_software_tester/.pptx-build/final-review.ndjson',snap.ndjson);
