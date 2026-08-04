/** Valida sintaxis JavaScript y autonomía del dashboard generado. */
import fs from "node:fs";

const html = fs.readFileSync(new URL("../docs/index.html", import.meta.url), "utf8");
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((match) => match[1]);
for (const [index, script] of scripts.entries()) {
  // La función se compila pero no se ejecuta; basta para detectar errores sintácticos.
  new Function(script);
  console.log(`script ${index + 1}: sintaxis válida (${script.length} caracteres)`);
}
const checks = {
  plot_containers: (html.match(/class="plot"/g) || []).length,
  local_windows_paths: /C:\\Users\\/i.test(html),
  external_script_tags: /<script[^>]+src=/i.test(html),
  executive_summary_link: html.includes('href="executive_summary.html"'),
};
console.log(JSON.stringify(checks, null, 2));
if (checks.plot_containers < 12 || checks.local_windows_paths || checks.external_script_tags || !checks.executive_summary_link) {
  process.exitCode = 1;
}

