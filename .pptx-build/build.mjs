import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, PresentationFile } from 'file:///C:/Users/harsha%20hariharan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const src='C:/Users/harsha hariharan/Downloads/AI Software Testing System - MCA Review.pptx';
const out='D:/ai_software_tester/.pptx-build/candidate.pptx';
const p=await PresentationFile.importPptx(await FileBlob.load(src));
const logo=await fs.readFile('D:/ai_software_tester/.pptx-build/logo.png');
const logoBlob=logo.buffer.slice(logo.byteOffset,logo.byteOffset+logo.byteLength);
function shape(slide,name,geometry,position,fill='none',lineFill='none',lineWidth=0){return slide.shapes.add({geometry,name,position,fill,line:{style:'solid',fill:lineFill,width:lineWidth}})}
function text(slide,name,value,position,style={}){const s=shape(slide,name,'textbox',position);s.text=value;s.text.style={typeface:'Calibri',fontSize:16,color:'#001233',autoFit:'shrinkText',...style};return s}
function frame(slide,title,subtitle,page){
 shape(slide,'title-diamond','diamond',{left:48,top:40.32,width:21.12,height:21.12},'#FFAD5A');
 text(slide,'slide-title',title,{left:81.6,top:26.88,width:1011.17,height:57.6},{fontSize:40,typeface:'Cambria',color:'#002060',bold:true});
 text(slide,'section-label',subtitle,{left:83.52,top:78.72,width:991.97,height:28.8},{fontSize:14.67,color:'#028090',bold:true});
 text(slide,'project-footer','AI-Powered Software Testing System',{left:38.4,top:683.52,width:768,height:28.8},{fontSize:13.33,typeface:'Cambria',color:'#F96167',bold:true});
 text(slide,'page-number',String(page),{left:1193.57,top:683.52,width:48,height:28.8},{fontSize:13.33,typeface:'Cambria',color:'#6B7280'});
 ['#028090','#FFAD5A','#F96167'].forEach((c,i)=>shape(slide,`footer-diamond-${i+1}`,'diamond',{left:611.18+i*28.8,top:679.68,width:13.44,height:13.44},c));
 slide.images.add({blob:logoBlob,contentType:'image/png',alt:'KGISL IIM logo',fit:'contain',position:{left:1111.97,top:26.88,width:129.6,height:46.74}});
}
p.slides.insert({after:p.slides.items[4]});
const s13=p.slides.items[5];
frame(s13,'Testing Strategy','AI SOFTWARE TESTER VALIDATION',13);
text(s13,'testing-scope-heading','Testing scope',{left:57.6,top:129.6,width:576,height:33.6},{fontSize:21.33,typeface:'Cambria',color:'#028090',bold:true});
text(s13,'testing-scope-body',
 'AI response parsing: extract plain, fenced and embedded JSON, then validate the required fields.\nAction safety: enforce the allowlist and reject unknown or shell-like actions before execution.\nData and metrics: check project, requirement, test-case and result persistence, plus empty and mixed pass-rate calculations.\nExecution and reporting: validate UI/API outcomes, record failures and evidence, and generate project reports.',
 {left:57.6,top:168,width:585.6,height:292.8},{fontSize:17.33,color:'#001233'});
text(s13,'testing-use-heading','Project workflow under test',{left:57.6,top:485,width:585.6,height:33.6},{fontSize:20,typeface:'Cambria',color:'#F96167',bold:true});
text(s13,'testing-use-body','Requirements move through AI analysis and test generation. Validated actions run through Playwright or the API engine, then results feed metrics, bug reports and exports.',
 {left:57.6,top:523,width:585.6,height:100},{fontSize:17.33,color:'#001233'});
shape(s13,'workflow-panel','roundRect',{left:681.6,top:129.6,width:542.4,height:532.8},'#002060');
text(s13,'workflow-panel-label','TESTING OBJECTIVE',{left:720,top:158.4,width:470.4,height:38.4},{fontSize:16,color:'#FFAD5A',bold:true});
text(s13,'workflow-panel-copy','Verify that AI output becomes structured, safe-to-run tests and that every execution result remains traceable.',
 {left:720,top:211.2,width:470.4,height:170.4},{fontSize:22,typeface:'Cambria',color:'#FFFFFF',bold:true,italic:true});
text(s13,'workflow-panel-steps','Analyze requirements\nGenerate test cases\nValidate and execute UI or API actions\nRecord results, defects and reports',
 {left:720,top:411,width:470.4,height:180},{fontSize:18,color:'#FFFFFF'});

p.slides.insert({after:s13});
const s14=p.slides.items[6];
frame(s14,'Project Test Cases','AI SOFTWARE TESTER MODULES',14);
text(s14,'cases-intro','Representative checks mapped to the project’s AI, safety, database and metrics test modules.',{left:57.6,top:125,width:1110,height:32},{fontSize:16,color:'#001233'});
const values=[
 ['ID','Module','Scenario','Expected result'],
 ['TC-AI-01','JSON parser','Plain, fenced or embedded valid JSON','Parser extracts JSON for schema validation.'],
 ['TC-AI-02','Test-case schema','Generated case omits steps or expected result','Parser rejects the incomplete response.'],
 ['TC-AI-03','Action safety','AI returns a shell or unknown action type','Validator rejects it before execution.'],
 ['TC-AI-04','Action fields','Navigate has no URL; assert_text has no text','Validator rejects each missing required field.'],
 ['TC-DB-01','Database','Create and retrieve project, requirement, case and steps','Records persist with their requirement and case links.'],
 ['TC-KPI-01','Metrics','Three passes and one failure; then an empty project','Pass rate is 75%; empty-project counts and pass rate are zero.'],
];
const table=s14.tables.add({rows:values.length,columns:4,left:57.6,top:168,width:1164,height:450,columnWidths:[100,205,310,549],values});
for(let r=0;r<values.length;r++){
 for(let c=0;c<4;c++){
  const cell=table.getCell(r,c);
  cell.fill=r===0?'#002060':(r%2===0?'#EAF3F5':'#FFFFFF');
  cell.text.style={typeface:'Calibri',fontSize:r===0?15:14.5,color:r===0?'#FFFFFF':'#001233',bold:r===0,verticalAlignment:'middle',wrap:true};
 }
}
table.borders.assign({style:'solid',fill:'#B7C7D2',width:1});
for(let r=0;r<values.length;r++) table.rows[r].height=r===0?48:63;await (await PresentationFile.exportPptx(p)).save(out);
for(let i=5;i<7;i++){const png=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(`D:/ai_software_tester/.pptx-build/slide-${i+1}.png`,new Uint8Array(await png.arrayBuffer()));}
const mont=await p.export({format:'webp',montage:true,scale:0.5});await fs.writeFile('D:/ai_software_tester/.pptx-build/montage-final.webp',new Uint8Array(await mont.arrayBuffer()));
const snap=await p.inspect({kind:'slide,textbox,table',maxChars:20000});await fs.writeFile('D:/ai_software_tester/.pptx-build/inspect-final.ndjson',snap.ndjson);
console.log('slides',p.slides.items.length,'candidate',out);







