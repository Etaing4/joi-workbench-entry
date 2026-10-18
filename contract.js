/* Local-first entrant claims, not a verification authority. */
(function(root){'use strict';
const VERSION='joi-portable-entry/1',BASELINE='JOI-WORKBENCH-20261017-01';
const clone=x=>JSON.parse(JSON.stringify(x));const uuid=()=>globalThis.crypto.randomUUID();
const claim=value=>({value:value||'unknown',provenance:'self_reported'});
function register(label,model='unknown',harness='unknown',retry=null){
 if(retry&&!/^E(0[1-9]|10)$/.test(retry))throw Error('Invalid retry route');
 return {schema_version:VERSION,entry_id:'FU-'+uuid(),baseline_ref:BASELINE,cohort:{id:'FOLLOWUP-'+uuid(),kind:'follow-up',retry_of:retry},created_at:new Date().toISOString(),label,identity:{model:claim(model),harness:claim(harness),provider:claim('unknown'),native_session_id:claim('unknown'),installed_cli:[]},state:'registered',review_state:'pending',tracks:Object.fromEntries([... 'ABCDEFG'].map(t=>[t,{state:'not_attempted',summary:'',checks:[],artifacts:[],limitations:[]}])),events:[],artifacts:[],limitations:[]};
}
function validate(d){
 if(!d||d.schema_version!==VERSION||d.baseline_ref!==BASELINE||!/^FU-[0-9a-f-]{36}$/.test(d.entry_id)||d.cohort?.kind!=='follow-up'||!/^FOLLOWUP-[0-9a-f-]{36}$/.test(d.cohort.id)||d.review_state!=='pending')throw Error('Invalid follow-up contract; never import baseline/accepted entries');
 if(d.cohort.retry_of!==null&&!/^E(0[1-9]|10)$/.test(d.cohort.retry_of))throw Error('Invalid retry');
 if(!['registered','running','blocked','submitted'].includes(d.state)||typeof d.label!=='string'||d.label.length>200||Object.keys(d.tracks).sort().join('')!=='ABCDEFG')throw Error('Invalid entry');
 for(const key of ['model','harness','provider','native_session_id'])if(typeof d.identity[key]?.value!=='string'||d.identity[key].value.length>1000||!['self_reported','unknown'].includes(d.identity[key].provenance))throw Error('Identity is a claim, not verified');
 if(!Array.isArray(d.identity.installed_cli)||d.identity.installed_cli.some(c=>!['observed_executable','unknown'].includes(c.provenance)||!['name','version','scope'].every(k=>typeof c[k]==='string'&&c[k].length<=1000)))throw Error('Invalid CLI provenance/record');
 for(const t of Object.values(d.tracks)){
 if(!['not_attempted','running','completed','partial','blocked','failed'].includes(t.state)||typeof t.summary!=='string'||t.summary.length>10000||!['checks','artifacts','limitations'].every(k=>Array.isArray(t[k])&&t[k].length<=500))throw Error('Invalid track');
 if(t.checks.some(c=>c.provenance!=='self_reported'||!['command','observed_result'].every(k=>typeof c[k]==='string'&&c[k].length<=10000)))throw Error('Invalid check claim');
 if(t.artifacts.some(p=>typeof p!=='string'||!p||p.startsWith('/')||p.includes('\\')||p.includes(':')||p.split('/').some(x=>!x||x==='.'||x==='..')))throw Error('Invalid relative artifact');
 if(t.limitations.some(x=>typeof x!=='string'||x.length>4000))throw Error('Invalid limitation');
 }
 if(!Array.isArray(d.limitations)||d.limitations.some(x=>typeof x!=='string'||x.length>4000))throw Error('Invalid limitations');
 if(!Array.isArray(d.events)||d.events.length>5000)throw Error('Invalid event list');
 d.events.forEach((e,i)=>{if(e.seq!==i+1||!['started','checkpoint','blocked','artifact','submitted'].includes(e.kind)||!['A','B','C','D','E','F','G',null].includes(e.track)||e.provenance!=='self_reported'||typeof e.message!=='string'||e.message.length>4000)throw Error('Invalid progress event');});
 if(!Array.isArray(d.artifacts)||JSON.stringify(d).length>2*1024*1024)throw Error('Contract too large');
 return d;
}
function event(d,kind,track,message){validate(d);const out=clone(d);out.events.push({seq:out.events.length+1,at:new Date().toISOString(),kind,track,message,provenance:'self_reported'});out.state=kind==='submitted'?'submitted':kind==='blocked'?'blocked':'running';return validate(out);}
function stable(value){if(Array.isArray(value))return '['+value.map(stable).join(',')+']';if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';return JSON.stringify(value);}
function merge(entries,incoming){validate(incoming);const out=clone(entries),i=out.findIndex(e=>e.entry_id===incoming.entry_id);if(i<0){out.push(clone(incoming));return out;}const old=out[i];for(const k of ['cohort','identity','created_at','baseline_ref','label'])if(stable(old[k])!==stable(incoming[k]))throw Error('Immutable identity/cohort conflict; create a new follow-up entry');const n=Math.min(old.events.length,incoming.events.length);if(stable(old.events.slice(0,n))!==stable(incoming.events.slice(0,n)))throw Error('Event history conflict');if(incoming.events.length===old.events.length&&['tracks','state','limitations'].some(k=>stable(old[k])!==stable(incoming[k])))throw Error('Result revision requires an appended event');if(incoming.events.length>=old.events.length)out[i]=clone(incoming);return out;}
function parseJSON(raw){
 if(typeof raw!=='string'||raw.length>2*1024*1024)throw Error('JSON size limit');
 const token=/"(?:\\.|[^"\\])*"|[{}\[\]:,]|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null/y;const stack=[];let i=0;
 while(i<raw.length){if(/\s/.test(raw[i])){i++;continue;}token.lastIndex=i;const m=token.exec(raw);if(!m)throw Error('Malformed JSON');const t=m[0];i=token.lastIndex;
 if(t==='{')stack.push(new Set());else if(t==='[')stack.push(null);else if(t==='}'||t===']')stack.pop();else if(t[0]==='"'&&raw.slice(i).trimStart()[0]===':'){const keys=stack[stack.length-1],key=JSON.parse(t);if(!(keys instanceof Set)||keys.has(key))throw Error('Duplicate or invalid JSON object key');keys.add(key);}
 }return JSON.parse(raw);
}
const api={VERSION,BASELINE,register,validate,event,merge,parseJSON};if(typeof module!=='undefined')module.exports=api;else root.EntryContract=api;
})(globalThis);
