
// v6.1 — UI simplificada (Geral = código/log, Teoria = MD/PDF) + árvore robusta

window.addEventListener("error", ()=>{ try{ const b=document.getElementById("jsError"); if(b) b.style.display='inline-flex'; }catch(_){} });
window.addEventListener("unhandledrejection", ()=>{ try{ const b=document.getElementById("jsError"); if(b) b.style.display='inline-flex'; }catch(_){} });

const $ = (q)=>document.querySelector(q);

const ALLOWED_RUN_FILES = new Set([
  "parte1-api/questao1.1/tests/1.1test.robot",
  "parte1-api/questao1.1/tests/1.2test.robot",
  "parte2-e2e/questao2.1/2.1test.robot",
  "parte2-e2e/questao2.2/2.2test.robot",
  "parte3-frontend/questao3.1/tests/3.1test.robot",
  "parte4-arquivos/questao4.1/tests/4.1test.robot",
  "parte5-mobile/questao5.1/testes/5.1test.robot.robot",
  "parte6-piramide/questao6.1/tests/6.1test.robot",
  "parte6-piramide/questao6.1/tests/6.2test.robot",
  "parte7-mocks/questao7.1/tests/7.1test.robot",
]);

let ALL_TAGS = [];           // from /api/tags
let currentRoot = "";
let currentPath = "";
let selectedFile = "";       // rel
let selectedTag = "";
let availableTags = [];      // tags in the selected file (intersection with ALL_TAGS)
let lastRun = null;          // last run info for log

function normRel(p){ return (p||"").replaceAll("\\\\","/").replace(/^\/+/,""); }
function esc(s){ return (s||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;"); }

function setBtnDisabled(btn, disabled){
  btn.disabled = !!disabled;
  btn.classList.toggle("btnDisabled", !!disabled);
}
function setTab(active){
  const isGeral = active==="geral";
  $("#tabGeral").classList.toggle("btnTabActive", isGeral);
  $("#tabTeoria").classList.toggle("btnTabActive", !isGeral);
  $("#panelGeral").style.display = isGeral ? "" : "none";
  $("#panelTeoria").style.display = !isGeral ? "" : "none";

  if(isGeral){
    $("#viewerTitle").textContent = "Visualizar código";
    $("#viewerHint").textContent = selectedFile ? selectedFile : "—";
    if(selectedFile) showCode(selectedFile);
    else showViewerEmpty("Selecione um arquivo no menu ao lado.");
  }else{
    $("#viewerTitle").textContent = "Preview";
    $("#viewerHint").textContent = "Respostas teóricas";
    showViewerEmpty("Selecione um arquivo em Respostas teóricas.");
  }
}

function showViewerEmpty(msg){
  $("#viewerEmpty").style.display = "";
  $("#viewerEmpty").textContent = msg||"—";
  $("#viewerCode").style.display = "none";
  $("#viewerFrame").style.display = "none";
  $("#viewerFrame").removeAttribute("src");
}
function showCode(rel){
  $("#viewerEmpty").style.display = "none";
  $("#viewerFrame").style.display = "none";
  $("#viewerFrame").removeAttribute("src");
  $("#viewerCode").style.display = "";
  $("#viewerTitle").textContent = "Visualizar código";
  $("#viewerHint").textContent = rel;

  fetch(`/api/md?path=${encodeURIComponent(rel)}`)
    .then(r=>r.json())
    .then(data=>{
      if(data && data.content!=null){
        $("#viewerCode").textContent = data.content;
      }else{
        $("#viewerCode").textContent = (data && data.error) ? ("Erro: "+data.error) : "Erro ao carregar arquivo.";
      }
    })
    .catch(()=>{ $("#viewerCode").textContent="Erro ao carregar arquivo."; });
}
function showLog(url){
  $("#viewerEmpty").style.display = "none";
  $("#viewerCode").style.display = "none";
  $("#viewerFrame").style.display = "";
  $("#viewerTitle").textContent = "Log da execução";
  $("#viewerHint").textContent = url;
  $("#viewerFrame").src = url;
}
function showPdf(rel){
  const url = `/api/pdf?path=${encodeURIComponent(rel)}&download=0`;
  $("#viewerEmpty").style.display = "none";
  $("#viewerCode").style.display = "none";
  $("#viewerFrame").style.display = "";
  $("#viewerTitle").textContent = "PDF";
  $("#viewerHint").textContent = rel;
  $("#viewerFrame").src = url;
}

function toast(msg){
  const el = $("#leftHint");
  if(!el) return;
  el.textContent = msg;
  el.style.color = "rgba(234,240,255,.92)";
  setTimeout(()=>{ el.textContent="—"; el.style.color=""; }, 4500);
}


function formatEnvCheck(j){
  // Retorna um texto amigável para exibir no modal
  try{
    const ok = !!j.ok;
    const missing = Array.isArray(j.packages_missing) ? j.packages_missing : [];
    const okPkgs = Array.isArray(j.packages_ok) ? j.packages_ok : [];
    const installedButImportFailed = Array.isArray(j.packages_installed_but_import_failed) ? j.packages_installed_but_import_failed : [];
    const problems = Array.isArray(j.problems) ? j.problems : [];

    const lines = [];
    lines.push(ok ? "✅ Ambiente OK — pronto para executar." : "❌ Ambiente incompleto — ajustes necessários.");
    lines.push("");
    if(j.python) lines.push(`Python: ${j.python} (${j.python_exe||"—"})`);
    if(j.robot_module || j.robot_cmd) lines.push(`Robot Framework: ${j.robot_module||"—"} (${j.robot_cmd||"—"})`);
    if(j.node_cmd) lines.push(`Node: ${j.node_cmd}`);
    if(j.npm_cmd) lines.push(`NPM: ${j.npm_cmd}`);
    if(j.adb_cmd) lines.push(`ADB: ${j.adb_cmd}`);
    lines.push("");
    if(missing.length){
      lines.push("📦 Bibliotecas ausentes (requirements.txt):");
      missing.forEach(p=>lines.push(`- ${p}`));
      lines.push("");
      lines.push("➡️ Dica: clique em “Instalar requirements” e rode novamente a verificação.");
      lines.push("");
    }
    if(okPkgs.length){
      lines.push("✅ Bibliotecas encontradas:");
      lines.push(okPkgs.join(", "));
      lines.push("");
    }

    if(installedButImportFailed.length){
      lines.push("⚠️ Instaladas, mas falharam ao importar:");
      installedButImportFailed.forEach(p=>lines.push(`- ${p}`));
      lines.push("");
    }
    if(problems.length){
      lines.push("⚠️ Observações:");
      problems.forEach(p=>lines.push(`- ${p}`));
      lines.push("");
    }
    lines.push("—");
    lines.push("Detalhes (JSON):");
    lines.push(JSON.stringify(j, null, 2));
    return lines.join("\n");
  }catch(e){
    return "Erro ao interpretar o resultado da verificação.";
  }
}
function openModal(title, content){
  $("#modalTitle").textContent = title || "Console";
  $("#modalBody").textContent = content || "";
  $("#modalOverlay").style.display = "flex";
}
function closeModal(){
  $("#modalOverlay").style.display = "none";
  $("#modalBody").textContent = "";
}
$("#btnModalClose").addEventListener("click", closeModal);
$("#modalOverlay").addEventListener("click", (e)=>{ if(e.target && e.target.id==="modalOverlay") closeModal(); });

async function loadTags(){
  const r = await fetch("/api/tags");
  const j = await r.json();
  ALL_TAGS = (j && j.tags) ? j.tags : [];
}

async function loadRoots(){
  const r = await fetch("/api/roots");
  const j = await r.json();
  const sel = $("#rootSelect");
  sel.innerHTML = "";
  const addOpt = (label, rel)=>{
    const o=document.createElement("option");
    o.value = rel;
    o.textContent = label;
    sel.appendChild(o);
  };
  // Importante: selecione uma pasta por padrão.
  // Se o primeiro item for um arquivo (ex.: readme.md), a árvore ficaria vazia
  // porque /api/tree exige diretório.
  (j.roots||[]).forEach(x=> addOpt(x.name, x.rel));
  (j.extras||[]).forEach(x=> addOpt(x.name, x.rel));

  if(!currentRoot){
    if((j.roots||[]).length){
      currentRoot = j.roots[0].rel;
    }else{
      currentRoot = sel.value || "";
    }
    currentPath = currentRoot;
    sel.value = currentRoot;
  }
}

function renderTree(items){
  const wrap = $("#tree");
  wrap.innerHTML = "";
  items.forEach(it=>{
    const kind = (it && (it.kind || (it.is_dir ? "dir" : "file"))) || "file";
    const row = document.createElement("div");
    row.className = "treeRow";
    row.dataset.rel = it.rel;
    row.dataset.kind = kind;
    row.innerHTML = `
      <div class="treeIcon">${kind==="dir" ? "📁" : (it.name.endsWith(".robot") ? "🤖" : "📄")}</div>
      <div class="treeName">${esc(it.name)}</div>
      <div class="treeMeta">${kind==="dir" ? "pasta" : "arquivo"}</div>
    `;
    row.addEventListener("click", ()=>onTreeClick(it));
    wrap.appendChild(row);
  });
}

async function loadTree(pathRel){
  const rel = normRel(pathRel || currentPath || "");
  currentPath = rel;
  $("#treePath").textContent = "/"+(rel||"");
  try{
    const r = await fetch(`/api/tree?path=${encodeURIComponent(rel)}`);
    const j = await r.json().catch(()=>null);

    if(!r.ok || (j && j.error)){
      const msg = (j && (j.error || j.message)) ? (j.error || j.message) : "Erro ao listar a pasta.";
      renderTree([]);
      const wrap = $("#tree");
      if(wrap){
        const div = document.createElement("div");
        div.className = "treeEmpty";
        div.textContent = `⚠️ ${msg}`;
        wrap.appendChild(div);
      }
      toast(msg);
      return;
    }

    const items = (j && j.items) ? j.items : [];
    renderTree(items);

    if(!items.length){
      const wrap = $("#tree");
      if(wrap){
        const div = document.createElement("div");
        div.className = "treeEmpty";
        div.textContent = "Nenhum item encontrado nesta pasta.";
        wrap.appendChild(div);
      }
    }
  }catch(e){
    renderTree([]);
    const wrap = $("#tree");
    if(wrap){
      const div = document.createElement("div");
      div.className = "treeEmpty";
      div.textContent = "⚠️ Falha ao carregar a estrutura. Verifique se o servidor está rodando.";
      wrap.appendChild(div);
    }
    toast("Falha ao carregar estrutura.");
  }
}

async function onTreeClick(it){
  const kind = (it && (it.kind || (it.is_dir ? "dir" : "file"))) || "file";
  if(kind==="dir"){
    await loadTree(it.rel);
    return;
  }
  // file
  selectedFile = normRel(it.rel);
  $("#viewerHint").textContent = selectedFile;
  showCode(selectedFile);

  // tag detection / allowlist
  const isRunnable = ALLOWED_RUN_FILES.has(selectedFile);
  if(!isRunnable){
    toast("Arquivo somente para visualização (execução desabilitada).");
  }

  // load tags from file
  availableTags = [];
  selectedTag = "";
  $("#tagSelect").innerHTML = "";
  $("#tagSelect").disabled = !isRunnable;
  setBtnDisabled($("#btnRun"), true);

  if(selectedFile.toLowerCase().endsWith(".robot") && isRunnable){
    try{
      const r = await fetch(`/api/robot_tags?path=${encodeURIComponent(selectedFile)}`);
      const j = await r.json();
      const fileTags = (j && j.tags) ? j.tags : [];
      const allow = new Set((ALL_TAGS||[]).map(t=>(t||"").toLowerCase()));
      availableTags = fileTags.filter(t=> allow.has((t||"").toLowerCase()));
      // fallback: some suites declare APIMAGAZORD etc; ensure unique
      availableTags = [...new Set(availableTags.map(t=>(t||"").toLowerCase()))];
      // A tag "regression" será executada via botão dedicado (executa tudo)
      availableTags = availableTags.filter(t=>t!=="regression");
    }catch(e){
      availableTags = [];
    }

    const tagSel = $("#tagSelect");
    tagSel.innerHTML = "";
    if(availableTags.length){
      availableTags.forEach(t=>{
        const o=document.createElement("option");
        o.value=t;
        o.textContent=t.toUpperCase();
        tagSel.appendChild(o);
      });
      selectedTag = tagSel.value;
      setBtnDisabled($("#btnRun"), false);
      $("#selectedInfo").innerHTML = `Selecionado: <b>${esc(selectedFile)}</b> • TAGs detectadas: <b>${esc(availableTags.join(", "))}</b>`;
    }else{
      $("#selectedInfo").innerHTML = `Selecionado: <b>${esc(selectedFile)}</b><br><span class="muted">Não consegui detectar TAGs válidas neste arquivo. Ajuste as tags (ex.: <b>[Tags]</b> regression APIMAGAZORD).</span>`;
      setBtnDisabled($("#btnRun"), true);
    }
  }else{
    $("#selectedInfo").innerHTML = `Selecionado: <b>${esc(selectedFile)}</b>`;
  }
}

$("#tagSelect").addEventListener("change", ()=>{
  selectedTag = ($("#tagSelect").value||"").trim().toLowerCase();
});

$("#btnUp").addEventListener("click", async ()=>{
  if(!currentPath) return;
  const parts = currentPath.split("/").filter(Boolean);
  if(parts.length<=1){
    await loadTree(currentRoot);
    return;
  }
  parts.pop();
  await loadTree(parts.join("/"));
});

$("#rootSelect").addEventListener("change", async (e)=>{
  currentRoot = normRel(e.target.value||"");
  currentPath = currentRoot;
  selectedFile = "";
  lastRun = null;
  setBtnDisabled($("#btnRun"), true);
  $("#btnOpenLog").classList.remove("btnDisabled");
  await loadTree(currentPath);
  showViewerEmpty("Selecione um arquivo no menu ao lado.");
});

$("#btnRun").addEventListener("click", async ()=>{
  if(!selectedFile) return toast("Selecione um arquivo.");
  if(!selectedTag) return toast("Selecione uma TAG.");
  if(!ALLOWED_RUN_FILES.has(selectedFile)) return toast("Este arquivo não está liberado para execução.");

  // validação local: tag precisa existir no arquivo
  if(!availableTags.includes(selectedTag)){
    toast("Invalid tag (TAG não está no arquivo).");
    return;
  }

  setBtnDisabled($("#btnRun"), true);
  const cmdInfo = [
    `Executando: robot -i ${selectedTag} ${selectedFile}`,
    "",
    "Aguarde...",
  ].join("\n");
  openModal("Executando teste", cmdInfo);

  try{
    const r = await fetch("/api/run", {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ path: selectedFile, tag: selectedTag })
    });
    const j = await r.json().catch(()=>null);

    if(!r.ok){
      const msg = (j && (j.message || j.error)) ? (j.message || j.error) : "Falha na execução.";
      if(j && j.error==="tag_not_found_in_suite"){
        toast("Invalid tag (TAG não está no arquivo).");
      }else{
        toast(msg);
      }
      setBtnDisabled($("#btnRun"), false);
      return;
    }

    lastRun = j;
    const out = [];
    out.push(j.returncode===0 ? "✅ Execução concluída (OK)." : `⚠️ Execução concluída (rc=${j.returncode}).`);
    out.push("");
    out.push(`Comando executado:`);
    out.push(`robot -i ${selectedTag} ${selectedFile}`);
    out.push("");
    if(j.log_url) out.push("Você pode abrir o log em \"Abrir log\".");
    out.push("—");
    if(j.stdout_tail) out.push(j.stdout_tail);
    if(j.stderr_tail) out.push("\n[stderr]\n"+j.stderr_tail);
    $("#modalBody").textContent = out.join("\n");
    toast(j.returncode===0 ? "Execução concluída (OK)." : `Execução concluída (rc=${j.returncode}).`);
    setBtnDisabled($("#btnRun"), false);

    // atualiza botão log
    if(lastRun && lastRun.log_url){
      $("#btnOpenLog").classList.remove("btnDisabled");
    }
  }catch(e){
    toast("Erro ao executar.");
    setBtnDisabled($("#btnRun"), false);
  }
});

$("#btnOpenLog").addEventListener("click", async ()=>{
  // usa lastRun, senão busca o último run
  if(lastRun && lastRun.log_url){
    showLog(lastRun.log_url);
    return;
  }
  try{
    const r = await fetch("/api/runs");
    const j = await r.json();
    const runs = (j && j.runs) ? j.runs : [];
    const first = runs.find(x=>x && x.log_url);
    if(first && first.log_url){
      lastRun = first;
      showLog(first.log_url);
    }else{
      toast("Não há log. Execute um teste para gerar o log.");
    }
  }catch(e){
    toast("Não há log. Execute um teste para gerar o log.");
  }
});

$("#btnOpenCode").addEventListener("click", ()=>{
  if(!selectedFile) return toast("Selecione um arquivo.");
  showCode(selectedFile);
});

// Regression (todos) - execução com streaming (mostra andamento em tempo real)
$("#btnRunRegressionAll").addEventListener("click", async ()=>{
  let n = 0;
  try{
    const resp = await fetch("/api/regression_count");
    const rj = await resp.json().catch(()=>null);
    n = (rj && typeof rj.count === "number") ? rj.count : 0;
  }catch(e){ n = 0; }

  const countTxt = n>0 ? `Executando ${n} suítes (todas com tag regression)…` : "";
  const header =
`Você pediu para rodar TODOS os testes com tag "regression".
${countTxt}

Comando:
python -m robot -i regression <raiz-do-projeto>

Acompanhe a execução abaixo:`.trim();

  openModal("Rodar regression (todos)", header);
  const bodyEl = $("#modalBody");
  bodyEl.textContent = (countTxt ? (countTxt + "\n\n") : "") + "Iniciando…\n";

  try{
    const r = await fetch("/api/run_regression_all_stream", { method: "POST" });
    if(!r.ok){
      const j = await r.json().catch(()=>null);
      const msg = (j && (j.message || j.error)) ? (j.message || j.error) : "Falha ao executar regression.";
      bodyEl.textContent = msg + "\n\nDetalhes:\n" + JSON.stringify(j, null, 2);
      return;
    }

    const reader = r.body.getReader();
    const dec = new TextDecoder("utf-8");
    let buf = "";
    let finalMeta = null;

    while(true){
      const {value, done} = await reader.read();
      if(done) break;
      const chunk = dec.decode(value, {stream:true});
      buf += chunk;

      // process lines
      let idx;
      while((idx = buf.indexOf("\n")) >= 0){
        const line = buf.slice(0, idx);
        buf = buf.slice(idx+1);

        if(line.startsWith("__META__=")){
          try{ finalMeta = JSON.parse(line.substring(9)); }catch(e){}
          continue;
        }
        if(line.startsWith("__END__=")){
          // ignore (rc)
          continue;
        }

        bodyEl.textContent += line + "\n";
        bodyEl.scrollTop = bodyEl.scrollHeight;
      }
    }

    // finish
    if(finalMeta && finalMeta.log_url){
      showViewer(finalMeta.log_url, "Log (regression)");
      toast("Regression finalizada. Log aberto no viewer.");
      bodyEl.textContent += "\n✅ Finalizado. Log: " + location.origin + finalMeta.log_url + "\n";
    }else{
      toast("Regression finalizada.");
      bodyEl.textContent += `\n✅ Finalizado.\n`;
    }
  }catch(e){
    bodyEl.textContent += `\n❌ Erro ao executar regression.\n`;
  }
});

// Teoria
let theorySelected = "";

async function loadTheory(){
  const r = await fetch("/api/theory");
  const j = await r.json();
  const list = $("#theoryList");
  list.innerHTML = "";

  (j.items||[]).forEach(item=>{
    const row = document.createElement("div");
    row.className = "listRow";
    row.innerHTML = `
      <div>
        <div class="listTitle">${esc(item.title)}</div>
        <div class="listMeta">${esc(item.rel)}</div>
      </div>
    `;
    row.addEventListener("click", ()=>{ selectTheory(item.rel); });
    list.appendChild(row);
  });
}

function selectTheory(rel){
  theorySelected = normRel(rel);
  setBtnDisabled($("#btnOpenMd"), !theorySelected);
  setBtnDisabled($("#btnOpenPdf"), !theorySelected);
  setBtnDisabled($("#btnDownloadPdf"), !theorySelected);
  $("#theoryInfo").textContent = theorySelected ? `Selecionado: ${theorySelected}` : "Selecione um arquivo para visualizar.";
}

function showTheoryMd(rel){
  $("#viewerTitle").textContent = "Preview (MD)";
  $("#viewerHint").textContent = rel;
  $("#viewerEmpty").style.display = "none";
  $("#viewerFrame").style.display = "none";
  $("#viewerFrame").removeAttribute("src");
  $("#viewerCode").style.display = "";
  fetch(`/api/md?path=${encodeURIComponent(rel)}`)
    .then(r=>r.json())
    .then(data=>{
      if(data && data.content!=null){
        $("#viewerCode").textContent = data.content;
      }else{
        $("#viewerCode").textContent = (data && data.error) ? ("Erro: "+data.error) : "Erro ao carregar.";
      }
    })
    .catch(()=>{ $("#viewerCode").textContent="Erro ao carregar."; });
}

$("#btnOpenMd").addEventListener("click", ()=>{
  if(!theorySelected) return;
  showTheoryMd(theorySelected);
});

$("#btnOpenPdf").addEventListener("click", ()=>{
  if(!theorySelected) return;
  showPdf(theorySelected);
});

$("#btnDownloadPdf").addEventListener("click", ()=>{
  if(!theorySelected) return;
  // abre download em outra aba (para não travar o app)
  window.open(`/api/pdf?path=${encodeURIComponent(theorySelected)}&download=1`, "_blank");
});
// check / install requirements => modal console
$("#btnCheck").addEventListener("click", async ()=>{
  openModal("Verificar ambiente", "Executando verificação...\n");
  try{
    const r = await fetch("/api/check");
    const j = await r.json();
    $("#modalBody").textContent = formatEnvCheck(j);
  }catch(e){
    $("#modalBody").textContent = "Erro ao verificar ambiente.";
  }
});
$("#btnInstallReq").addEventListener("click", async ()=>{
  const cmdLine = "python -m pip install -r requirements.txt";
  openModal("Instalar requirements", `O sistema vai instalar as dependências do projeto.

Comando:
${cmdLine}

Acompanhe a execução abaixo:`);
  const bodyEl = $("#modalBody");
    bodyEl.textContent = "Iniciando instalação…\n";


  try{
    const r = await fetch("/api/install_requirements_stream", { method:"POST" });
    if(!r.ok){
      const j = await r.json().catch(()=>null);
      bodyEl.textContent = "❌ Falha ao iniciar instalação.\n\n" + JSON.stringify(j, null, 2);
      return;
    }

    const reader = r.body.getReader();
    const dec = new TextDecoder("utf-8");
    let buf = "";
    let ok = null;

    while(true){
      const {value, done} = await reader.read();
      if(done) break;
      buf += dec.decode(value, {stream:true});
      let idx;
      while((idx = buf.indexOf("\n")) >= 0){
        const line = buf.slice(0, idx);
        buf = buf.slice(idx+1);

        if(line.startsWith("__END__=")){
          ok = line.includes("ok:true");
          continue;
        }
        bodyEl.textContent += line + "\n";
        bodyEl.scrollTop = bodyEl.scrollHeight;
      }
    }

    if(ok === true){
      bodyEl.textContent += `\n✅ Instalação concluída. Agora clique em “Verificar ambiente”.\n`;
      toast("Instalação concluída.");
    }else{
      bodyEl.textContent += `\n⚠️ Instalação terminou com avisos/erro. Verifique a saída acima.\n`;
      toast("Instalação terminou com avisos/erro.");
    }
  }catch(e){
    bodyEl.textContent += `\n❌ Erro durante a instalação.\n`;
  }
});
$("#btnRefresh").addEventListener("click", ()=>location.reload());

$("#tabGeral").addEventListener("click", ()=>setTab("geral"));
$("#tabTeoria").addEventListener("click", async ()=>{ setTab("teoria"); await loadTheory(); });

(async function boot(){
  try{
    await loadTags();
    await loadRoots();
    await loadTree(currentPath || currentRoot);
  }catch(e){
    toast("Falha ao carregar estrutura.");
  }
  setBtnDisabled($("#btnOpenMd"), true);
  setBtnDisabled($("#btnDownloadPdf"), true);
  setTab("geral");
})();
