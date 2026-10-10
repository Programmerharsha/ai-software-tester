import fs from 'node:fs/promises';
for(const p of ['D:/ai_software_tester','D:/ai_software_tester/.pptx-build','D:/ai_software_tester/output']){
 try{console.log(p,await fs.realpath(p))}catch(e){console.log(p,e.code,e.message)}
}
