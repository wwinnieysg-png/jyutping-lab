(()=>{
'use strict';
const $=id=>document.getElementById(id);
const esc=x=>String(x??'').replace(/[&<>"']/g,s=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
const fallback=window.YY_DATA||{entries:[],phrases:[]};
const chars={};
const wordCache=new Map();
const sounds=new Map();
const state={full:false,loading:false,format:'paren',script:'我們今日去銀行，之後行街。',selected:null,history:[],seq:0};
const defaultScript=state.script;
const formats=['paren','plain','annotate','slash'];
function stored(key,def){try{return localStorage.getItem('ys04-'+key)??def}catch{return def}}
function store(key,value){try{localStorage.setItem('ys04-'+key,value)}catch{}}
state.format=formats.includes(stored('format','paren'))?stored('format','paren'):'paren';
state.script=stored('script',state.script);
let toastTimeout;
function toast(message){const el=$('toast');el.hidden=false;el.textContent=message;clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>el.hidden=true,2800)}
async function copy(text){try{if(!navigator.clipboard?.writeText)throw Error('fallback');await navigator.clipboard.writeText(text);toast('已複製：'+text.slice(0,44))}catch{const el=document.createElement('textarea');el.value=text;el.style.cssText='position:fixed;left:-9999px';document.body.append(el);el.select();let okay=false;try{okay=document.execCommand('copy')}catch{}el.remove();toast(okay?'已複製到剪貼簿':'無法自動複製，請手動選取')}}
function format(c,j){return state.format==='plain'?j:state.format==='annotate'?`${c}(${j})`:state.format==='slash'?`${c}/(${j})`:`(${j})`}
function addIndex(){sounds.clear();for(const [c,rows]of Object.entries(chars)){for(const r of rows){let arr=sounds.get(r.j);if(!arr){arr=[];sounds.set(r.j,arr)}arr.push(c)}}}
function demo(){for(const row of fallback.entries){(chars[row.char]??=[]).push({j:row.jyutping,m:row.sense,e:row.examples.split(/[、，]/),s:['demo']})}addIndex()}
function setDataStatus(message){const el=$('data-status');if(el)el.textContent=message}
async function init(){demo();state.loading=true;setDataStatus('正在檢查完整字庫…');render();renderSelection();
  // File:// previews cannot fetch local JSON in many browsers. They remain usable in demo mode.
  if(location.protocol==='file:'){state.loading=false;setDataStatus('本機預覽：示範字庫；GitHub Pages 部署後自動使用完整字庫');return}
  try{
    const response=await fetch('data/manifest.json',{cache:'no-store'});if(!response.ok)throw Error('manifest');
    const meta=await response.json();if(!meta.built)throw Error('manifest not built');
    const result=await fetch('data/characters.json');if(!result.ok)throw Error('characters');
    const entries=await result.json();for(const key of Object.keys(chars))delete chars[key];Object.assign(chars,entries);
    state.full=true;state.meta=meta;state.loading=false;addIndex();
    setDataStatus(`${meta.unique_characters.toLocaleString('zh-HK')} 個漢字 · ${meta.unique_words.toLocaleString('zh-HK')} 個詞條 · 資料來源：Rime／開放粵語字典`);
    updateNote();render();renderSelection();
  }catch(error){state.loading=false;setDataStatus('字庫未建置，暫以示範資料運作。請先執行 GitHub Actions。');render();console.info('Dictionary fallback:',error.message)}
}
function updateNote(){if(!state.full)return;const el=$('dictionary-note');if(el)el.textContent='來源：Rime Cantonese（CC BY 4.0）、開放粵語字典（CC BY 3.0）及本站開發者補充詞庫。釋義只喺來源有收錄時顯示；同音字依完整粵拼及聲調配對。TTS 括號格式須由實際語音模型確認。'}
const sources={yyzd:'開放粵語字典',rime:'Rime 詞庫',custom:'開發者補充',demo:'示範資料'};
function sourcesText(list){return (list||[]).map(x=>sources[x]||x).join(' · ')}
function homophones(j,c){const matches=(sounds.get(j)||[]).filter(x=>x!==c);return {list:matches.slice(0,32),total:matches.length}}
function entryHtml(char,record){const j=record.j,hom=homophones(j,char);const examples=record.e?.length?record.e.join('、'):'暫未收錄詞例';const meaning=record.m||'暫未收錄釋義';const homotext=hom.list.length?hom.list.join('、')+(hom.total>hom.list.length?`（另有 ${hom.total-hom.list.length} 字）`:''):'未收錄其他同音字';
return `<article class="pron-item"><div><div class="syllable">${esc(j)}</div><span class="tone">聲調 ${esc(j.slice(-1))}</span></div><div><p class="meaning">${esc(meaning)}</p><div class="entry-row"><span>詞例</span><span>${esc(examples)}</span></div><div class="entry-row"><span>同音字</span><span>${esc(homotext)}</span></div><div class="entry-row"><span>來源</span><span>${esc(sourcesText(record.s))}</span></div><div class="pron-actions"><button type="button" class="action-copy" data-copy="${esc(char)}" data-j="${esc(j)}">複製 ${esc(format(char,j))} ↗</button></div></div></article>`}
function charHtml(char,rows){return `<section class="result-group" aria-label="${esc(char)} 嘅讀音"><div class="character-summary"><div class="character-main">${esc(char)}</div><div><div class="character-details">${rows.length} 個已收錄讀音</div><a class="verified-link" href="https://peach.arts.cuhk.edu.hk/Lexis/lexi-can/main.php" target="_blank" rel="noopener noreferrer">參考中大字庫 ↗</a></div></div><div class="pron-list">${rows.map(r=>entryHtml(char,r)).join('')}</div></section>`}
function wordHtml(word,rows){return `<section class="word-result"><div class="word-top"><div><span class="utility-label">完整詞語</span><h4>${esc(word)}</h4></div><span class="word-n">${rows.length} 個整詞讀音</span></div>${rows.map(r=>{const pairs=Array.from(word).map((c,i)=>({c,j:r.j.split(' ')[i]}));return `<div class="word-reading"><div class="word-phonetics">${pairs.map(p=>`<span>${esc(p.c)}<b>${esc(p.j)}</b></span>`).join('')}</div><p class="word-meaning">${esc(r.m||'暫未收錄整詞釋義')}</p><div class="word-actions"><span class="source-mini">${esc(sourcesText(r.s))}</span><button type="button" class="action-copy" data-copy="${esc(word)}" data-j="${esc(r.j)}">複製 ${esc(format(word,r.j))} ↗</button></div></div>`}).join('')}</section>`}
async function getWords(term){if(!state.full)return demoWords(term);const bucket=term.codePointAt(0)%state.meta.shards;
 if(!wordCache.has(bucket)){wordCache.set(bucket,(async()=>{let r=await fetch(`data/words-${String(bucket).padStart(2,'0')}.json`);if(!r.ok)throw Error('word shard');return r.json()})().catch(e=>{wordCache.delete(bucket);throw e}))}
 return wordCache.get(bucket)}
function demoWords(term){const examples={
 '銀行':[{'j':'ngan4 hong4',m:'提供存款及金融服務的機構',s:['demo']}],
 '我哋':[{'j':'ngo5 dei6',m:'我們',s:['demo']}],
 '行街':[{'j':'haang4 gaai1',m:'逛街',s:['demo']}],
 '唔該':[{'j':'m4 goi1',m:'禮貌用語',s:['demo']}]
 };return Object.fromEntries(Object.entries(examples).filter(([w])=>w.startsWith(term)))}
const normalized=t=>t.trim().toLowerCase().replace(/^\(([^()]*)\)$/,'$1');
function getCharacters(query){const pieces=Array.from(query);if(chars[query])return [[query,chars[query]]];if(/^[a-z]+[1-6]$/.test(query))return (sounds.get(query)||[]).slice(0,70).map(c=>[c,chars[c]]);if(pieces.length>1&&pieces.length<=10)return [...new Set(pieces)].filter(c=>chars[c]).map(c=>[c,chars[c]]);return []}
async function render(){const q=normalized($('search-input').value),seq=++state.seq;
$('search-caption').textContent=q?`/ ${q}`:'/ 搜尋結果';
if(!q){$('results').innerHTML='<div class="empty-results"><strong>輸入字詞，開始探索讀音。</strong><p>可以搜尋漢字、完整詞語，或者粵拼音節。</p></div>';$('result-count').textContent='';return}
const groups=getCharacters(q);let words={};
if(Array.from(q).length>1&&!/^[a-z]+[1-6]$/.test(q)){
 try{const shard=await getWords(q);words=Object.fromEntries(Object.entries(shard).filter(([word])=>word===q||word.startsWith(q)).slice(0,24));}
 catch{if(seq===state.seq)toast('部分詞語資料載入失敗，可稍後重試')}
}
if(seq!==state.seq)return;
const wordEntries=Object.entries(words);
$('result-count').textContent=`${wordEntries.length} 個詞 / ${groups.length} 個字`;
if(!groups.length&&!wordEntries.length){$('results').innerHTML=`<div class="empty-results"><strong>暫未找到「${esc(q)}」</strong><p>${state.full?'資料來源未收錄，或者需要嘗試其他繁簡字形。':'示範字庫有限；部署完整字庫後可查更多字詞。'}</p></div>`;return}
$('results').innerHTML=wordEntries.map(([w,rs])=>wordHtml(w,rs)).join('')+
 (groups.length&&wordEntries.length?'<div class="related-heading">相關漢字讀音</div>':'')+groups.map(([c,rs])=>charHtml(c,rs)).join('');
}
$('results').addEventListener('click',event=>{const btn=event.target.closest('[data-copy]');if(btn)copy(format(btn.dataset.copy,btn.dataset.j))});
$('search-form').addEventListener('submit',event=>{event.preventDefault();render();$('results').scrollIntoView({behavior:'smooth',block:'nearest'})});
let debounce;$('search-input').addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(render,140)});
document.querySelectorAll('[data-query]').forEach(btn=>btn.addEventListener('click',()=>{$('search-input').value=btn.dataset.query;render();$('search-input').focus()}));
$('copy-format').value=state.format;$('copy-format').addEventListener('change',event=>{state.format=event.target.value;store('format',state.format);render();renderSelection();toast('已更新複製格式')});
function refreshScript(){$('script-input').value=state.script;$('script-output').textContent=state.script;store('script',state.script)}
function snapshot(){state.history.push(state.script);if(state.history.length>30)state.history.shift()}
function replaceScript(text){state.script=text;state.selected=null;refreshScript();renderSelection()}
function renderSelection(){const el=$('selection-panel'),s=state.selected;if(!s){el.innerHTML='<span class="selection-glyph" aria-hidden="true">字</span><p>喺左邊選取一個漢字。</p><small>字庫載入完成後會顯示全部已收錄讀音。</small>';return}const rows=chars[s.char]||[];
if(!rows.length){el.innerHTML=`<div class="selected-char">${esc(s.char)}</div><p>字庫未收錄此字嘅讀音。</p><small>不會憑空生成粵拼。</small>`;return}
el.innerHTML=`<div class="selection-title">已選取漢字 / 位置 ${s.start+1}</div><div class="selected-char">${esc(s.char)}</div>${rows.map(r=>`<div class="pron-choice"><div class="choice-header"><b>${esc(r.j)}</b><button type="button" data-apply="${esc(r.j)}">套用 ↗</button></div><p>${esc(r.m||'暫未收錄釋義')} · ${esc((r.e||[]).slice(0,3).join('、'))}</p></div>`).join('')}`}
function readSelection(){const t=$('script-input'),start=t.selectionStart,end=t.selectionEnd,selection=t.value.slice(start,end);
if(start===end||Array.from(selection).length!==1||!/^\p{Script=Han}$/u.test(selection)){state.selected=null;renderSelection();return}state.selected={char:selection,start,end};renderSelection()}
$('script-input').addEventListener('input',e=>{state.script=e.target.value;state.selected=null;$('script-output').textContent=state.script;store('script',state.script);renderSelection()});
for(const event of ['mouseup','keyup','select','touchend'])$('script-input').addEventListener(event,readSelection);
$('selection-panel').addEventListener('click',event=>{const btn=event.target.closest('[data-apply]');if(!btn||!state.selected)return;const s=state.selected;
if(state.script.slice(s.start,s.end)!==s.char){toast('講稿已變更，請重新選取');return}snapshot();const mark=`(${btn.dataset.apply})`;replaceScript(state.script.slice(0,s.start)+mark+state.script.slice(s.end));toast(`已套用 ${mark}`)});
$('convert-btn').addEventListener('click',()=>{let text=state.script;for(const [formal,spoken]of [...fallback.phrases].sort((a,b)=>b[0].length-a[0].length))text=text.replaceAll(formal,spoken);if(text===state.script){toast('未找到適合嘅預設轉換詞組');return}snapshot();replaceScript(text);toast('已轉換指定口語詞組，請按上下文校對')});
$('undo-btn').addEventListener('click',()=>{if(!state.history.length){toast('冇可以還原嘅操作');return}replaceScript(state.history.pop());toast('已還原上一個操作')});
$('reset-btn').addEventListener('click',()=>{snapshot();replaceScript(defaultScript);toast('已重設示範講稿')});
$('copy-script').addEventListener('click',()=>copy(state.script));
refreshScript();init();
})();
