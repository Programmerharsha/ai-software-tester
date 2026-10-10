import fs from "node:fs/promises";
import path from "node:path";
import { Presentation } from "file:///C:/Users/harsha%20hariharan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

const sourcePath = "C:/Users/harsha hariharan/Downloads/AI-Powered Software Testing System - MCA Review.pptx";
const outputDir = "D:/ai_software_tester/.codex_build/source_inspection";
await fs.mkdir(outputDir, { recursive: true });

const presentation = await Presentation.load(sourcePath);
const inspection = await presentation.inspect({
  select: "$.slides[*]",
  include: ["id", "index", "layout", "title", "elements.id", "elements.kind", "elements.text", "elements.position"],
  fileName: "content.ndjson",
});
await fs.writeFile(path.join(outputDir, "content.ndjson"), inspection.ndjson);
for (const slide of presentation.slides.items) {
  const index = presentation.slides.items.indexOf(slide) + 1;
  await writeBlob(path.join(outputDir, `slide-${index}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
}
console.log(JSON.stringify({ slideCount: presentation.slides.items.length, inspection: inspection.ndjson }, null, 2));
