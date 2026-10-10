import path from 'node:path';
import { pathToFileURL } from 'node:url';
const skillDir='C:/Users/harsha hariharan/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skillDir,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({
 workspaceDir:'D:/ai_software_tester',
 candidatePath:'D:/ai_software_tester/.pptx-build/candidate.pptx',
 finalPath:'D:/ai_software_tester/output/AI_Software_Testing_System_Testing_Section.pptx',
 pythonExecutable:'C:/Users/harsha hariharan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
 explicitTotalSlideCount:8,
 sourceTemplatePath:'C:/Users/harsha hariharan/Downloads/AI Software Testing System - MCA Review.pptx',
 requiredTemplateReferenceSlides:[6],
 fontPolicy:{basis:'reference',families:['Cambria','Calibri'],referencePath:'C:/Users/harsha hariharan/Downloads/AI Software Testing System - MCA Review.pptx',referenceSha256:'21871e733187344be391864762e3e54f2cc56bf47565066e143a1012dc548e8a'},
 verifyArtifactToolImport:true,
 receiptPath:'D:/ai_software_tester/.pptx-build/final-validation.json'
});
console.log(JSON.stringify(result,null,2));
