/* diagram.js (localized build of the shared renderer, en) */
(function(){
  function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function b(t){ if(window.DIAGRAM&&window.DIAGRAM.k3_) return window.DIAGRAM.k3_(String(t==null?"":t)).replace(/\*\*([^*]+)\*\*/g,"<b>$1</b>"); return esc(t).replace(/\*\*([^*]+)\*\*/g,"<b>$1</b>"); }
  function k10_(t){ var z=b(t).split(" · "); return z.length>1 ? z.map(function(l){ return '<span class="dg-ln">'+l+'</span>'; }).join("") : z[0]; }
  function k9_(t){ return t ? '<div class="dg-t">'+b(t).split(" · ").join(", ")+'</div>' : ""; }
  function k5_(xs){ return (xs&&xs.length) ? '<ul>'+xs.map(function(x){ return '<li>'+b(x)+'</li>'; }).join("")+'</ul>' : ""; }
  function k6_(t){ return String(t||"").replace(/\*\*/g,""); }
  var k0_ = {
    def: function(x){
      return '<div class="dg dg-def"><div class="dg-term">'+b(x.term)+'</div>'+
        '<div class="dg-dtext">'+k10_(x.text)+'</div>'+
        ((x.ex&&x.ex.length)?(x.ex.some(function(e){ return k6_(e).length>18; })
          ? '<div class="dg-exl"><span>e.g.</span>'+k5_(x.ex)+'</div>'
          : '<div class="dg-ex"><span>e.g.</span>'+x.ex.map(function(e){ return '<i>'+b(e)+'</i>'; }).join("")+'</div>'):'')+
      '</div>';
    },
    flow: function(x){
      return '<div class="dg dg-flow">'+k9_(x.title)+'<ol>'+(x.steps||[]).map(function(s,n){
        var k11_=String(s).split(" · ");   
        return '<li><span class="dg-n">'+(n+1)+'</span><span class="dg-s">'+(k11_.length>1?'<b>'+b(k11_[0])+'</b><br>'+k11_.slice(1).map(b).join("<br>"):b(s))+'</span></li>';
      }).join('<li class="dg-arr" aria-hidden="true">↓</li>')+'</ol></div>';
    },
    cause: function(x){
      var k13_ = (x.causes||[]).map(function(c){ return '<div class="dg-box">'+k10_(c)+'</div>'; }).join("");
      var k4_ = (x.effects||[]).map(function(c){ return '<div class="dg-box dg-eff">'+k10_(c)+'</div>'; }).join("");
      return '<div class="dg dg-cause">'+k9_(x.title)+
        '<div class="dg-lab">Cause</div><div class="dg-row">'+k13_+'</div>'+
        '<div class="dg-arr" aria-hidden="true">↓</div>'+
        '<div class="dg-core">'+k10_(x.result)+'</div>'+
        (k4_?'<div class="dg-arr" aria-hidden="true">↓</div><div class="dg-lab">Result</div><div class="dg-row">'+k4_+'</div>':'')+
      '</div>';
    },
    tree: function(x){
      var k2_ = x.branches||[];
      return '<div class="dg dg-tree">'+k9_(x.title)+
        '<div class="dg-root">'+b(x.root)+'</div>'+
        '<div class="dg-kids" style="--n:'+Math.min(k2_.length,4)+'">'+k2_.map(function(g){
          return '<div class="dg-kid"><b class="dg-kn">'+b(g[0])+'</b>'+(g[1]?'<span>'+k10_(g[1])+'</span>':'')+'</div>';
        }).join("")+'</div></div>';
    },
    vs: function(x){
      var cols = x.cols||[];
      return '<div class="dg dg-vs">'+k9_(x.title)+'<div class="dg-cols" style="--n:'+cols.length+'">'+
        cols.map(function(c,n){
          return (n?'<div class="dg-vsb" aria-hidden="true">vs</div>':'')+
            '<div class="dg-col dg-c'+n+'"><div class="dg-ch">'+b(c.name)+'</div>'+k5_(c.items)+'</div>';
        }).join("")+'</div></div>';
    },
    venn: function(x){
      var a=x.a||{}, c=x.b||{};
      return '<div class="dg dg-venn">'+k9_(x.title)+
        '<svg class="dg-vsvg" viewBox="0 0 200 64" aria-hidden="true"><circle cx="80" cy="32" r="29"/><circle cx="120" cy="32" r="29"/></svg>'+
        '<div class="dg-vcols"><div class="dg-col dg-c0"><div class="dg-ch">'+b(a.name)+' only</div>'+k5_(a.items)+'</div>'+
        '<div class="dg-col dg-both"><div class="dg-ch">Both</div>'+k5_(x.both)+'</div>'+
        '<div class="dg-col dg-c1"><div class="dg-ch">'+b(c.name)+' only</div>'+k5_(c.items)+'</div></div></div>';
    },
    cycle: function(x){
      var s=x.steps||[], n=s.length, R=36, k14_=[];
      for(var k=0;k<n;k++){ var a=-Math.PI/2+2*Math.PI*k/n; k14_.push([50+R*Math.cos(a), 50+R*Math.sin(a)]); }
      var k8_ = '<svg class="dg-ring" viewBox="0 0 100 100" aria-hidden="true"><defs><marker id="dgA" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L6 3L0 6z"/></marker></defs>'+
        k14_.map(function(p,k){ var q=k14_[(k+1)%n], a1=-Math.PI/2+2*Math.PI*(k+.28)/n, a2=-Math.PI/2+2*Math.PI*(k+.72)/n;
          return '<path d="M'+(50+R*Math.cos(a1)).toFixed(1)+' '+(50+R*Math.sin(a1)).toFixed(1)+' A'+R+' '+R+' 0 0 1 '+(50+R*Math.cos(a2)).toFixed(1)+' '+(50+R*Math.sin(a2)).toFixed(1)+'" marker-end="url(#dgA)"/>'; }).join("")+'</svg>';
      var k1_ = s.map(function(t,k){ return '<div class="dg-node" style="left:'+k14_[k][0]+'%;top:'+k14_[k][1]+'%"><span>'+(k+1)+'</span>'+b(t)+'</div>'; }).join("");
      return '<div class="dg dg-cycle">'+k9_(x.title)+'<div class="dg-cwrap">'+k8_+k1_+'</div>'+
        '<ol class="dg-clist">'+s.map(function(t){ return '<li>'+b(t)+'</li>'; }).join("")+'</ol></div>';
    },
    axis: function(x){
      var m=(x.marks||[]).slice().sort(function(p,q){ return p.at-q.at; });
      return '<div class="dg dg-axis">'+k9_(x.title)+
        '<div class="dg-ends"><span>'+b(x.left)+'</span><span>'+b(x.right)+'</span></div>'+
        '<div class="dg-line">'+m.map(function(k,n){ return '<i style="left:'+Math.max(3,Math.min(97,k.at))+'%">'+(n+1)+'</i>'; }).join("")+'</div>'+
        '<ul class="dg-marks">'+m.map(function(k,n){ return '<li><span class="dg-mn">'+(n+1)+'</span><b>'+b(k.name)+'</b>'+(k.text?'<span>'+b(k.text)+'</span>':'')+'</li>'; }).join("")+'</ul></div>';
    },
    table: function(x){
      var n2=(x.head&&x.head.length)||((x.rows||[])[0]||[]).length;
      if(n2===2) return '<div class="dg dg-rl">'+k9_(x.title)+(x.rows||[]).map(function(r){
          return '<div class="dg-ri"><div class="dg-rn">'+b(r[0])+'</div><div class="dg-rv">'+k10_(r[1])+'</div></div>'; }).join("")+'</div>';
      return '<div class="dg dg-table">'+k9_(x.title)+'<div class="dg-tw"><table>'+
        ((x.head&&x.head.length)?'<thead><tr>'+x.head.map(function(h){ return '<th>'+k10_(h)+'</th>'; }).join("")+'</tr></thead>':'')+
        '<tbody>'+(x.rows||[]).map(function(r){ return '<tr>'+r.map(function(c,n){ return (n===0&&x.head&&x.head.length?'<th>':'<td>')+k10_(c)+(n===0&&x.head&&x.head.length?'</th>':'</td>'); }).join("")+'</tr>'; }).join("")+'</tbody></table></div></div>';
    }
  };
  function k12_(x){
    if(!x) return "";
    var k7_=[x.title,x.term,x.text,x.root,x.result,x.left,x.right];
    (x.ex||[]).concat(x.steps||[],x.causes||[],x.effects||[],x.both||[],x.head||[]).forEach(function(s){ k7_.push(s); });
    (x.branches||[]).forEach(function(g){ k7_.push(g.join(" ")); });
    (x.cols||[]).forEach(function(c){ k7_.push(c.name); k7_=k7_.concat(c.items||[]); });
    [x.a,x.b].forEach(function(c){ if(c){ k7_.push(c.name); k7_=k7_.concat(c.items||[]); } });
    (x.marks||[]).forEach(function(k){ k7_.push(k.name, k.text); });
    (x.rows||[]).forEach(function(r){ k7_=k7_.concat(r); });
    return k6_(k7_.filter(Boolean).join(" "));
  }
  window.DIAGRAM = {
    k3_: null,
    has: function(t){ return !!k0_[t]; },
    html: function(x){ var f=k0_[x&&x.t]; return f ? f(x) : ""; },
    text: k12_
  };
})();
/*tnote-start*/
/* term popup + sentence note (2026-11-06). Source: hub/common/termnote/engine.js. Appended to every diagram.js by apply.py.
   Hover (mouse) or tap a concept word: small popup. Click or tap a sentence: side panel (wide) or bottom sheet (phone).
   Data: DIAGRAM.terms({word:{d:meaning,r:[related]}}), DIAGRAM.notes({line:text}). Only touches text inside .dg blocks,
   so question stems stay clean. No Hangul literals: the JP and EN apps reject them at deploy time. */
(function(){
  if(!window.DIAGRAM||window.__TN) return; window.__TN=1;
  var lang=(document.documentElement.lang||"ko").slice(0,2);
  var L={ko:{term:"\uac1c\ub150\uc5b4",rel:"\uad00\ub828 \uac1c\ub150",note:"\ud480\uc774",close:"\ub2eb\uae30"},
         ja:{term:"\u7528\u8a9e",rel:"\u95a2\u9023",note:"\u89e3\u8aac",close:"\u9589\u3058\u308b"},
         en:{term:"Key terms",rel:"Related",note:"Explanation",close:"Close"}}[lang]||null;
  if(!L) L={term:"Key terms",rel:"Related",note:"Explanation",close:"Close"};
  var terms={},own={},notes={},scenes={},ver=1,rx=null,triedFile=false,harvested={};
  var LAW=new RegExp("\\s*\\((?:[\\uac00-\\ud7a3]+(?:\\ubc95|\\ub839|\\uaddc\\uce59|\\uaddc\\uc815)\\s*)?\\uc81c[\\d\\u00b7]+\\uc870[^()]*\\)","g");
  function key(t){ return String(t==null?"":t).replace(/\*\*/g,"").replace(LAW,"").replace(/[\s\u00b7\u30fb]/g,""); }
  function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
  function plain(t){ return String(t==null?"":t).replace(/\*\*/g,""); }
  function bump(){ ver++; rx=null; schedule(); }

  var oldScene=DIAGRAM["\uc7a5\uba74"];
  if(oldScene) DIAGRAM["\uc7a5\uba74"]=function(m){ for(var k in m) scenes[key(k)]=m[k]; oldScene(m); schedule(); };
  DIAGRAM.terms=function(m){ for(var k in m){ var v=m[k]; if(!v) continue; own[k]=1; terms[k]=typeof v==="string"?{d:v}:v; } bump(); };
  DIAGRAM.notes=function(m){ for(var k in m) notes[key(k)]=m[k]; bump(); };
  /* data files may load before this engine: they push to window.TNQ */
  DIAGRAM.tnFlush=function(){ var q=window.TNQ||[]; window.TNQ=[]; q.forEach(function(x){ if(x.terms) DIAGRAM.terms(x.terms); if(x.notes) DIAGRAM.notes(x.notes); }); };
  DIAGRAM.tnFlush();

  /* definitions already on the page need no new data */
  function addDef(t,d){ t=plain(t).trim(); d=plain(d).replace(/\s\u00b7\s/g,", ").trim();
    if(t.length<2||t.length>14||!d||own[t]||terms[t]) return false; terms[t]={d:d.length>130?d.slice(0,130)+"\u2026":d}; return true; }
  function walkDef(o,depth){ var hit=false; if(!o||depth>6||typeof o!=="object") return false;
    if(Array.isArray(o)){ for(var i=0;i<o.length;i++) if(walkDef(o[i],depth+1)) hit=true; return hit; }
    if(o.t==="def"&&o.term) return addDef(o.term,o.text);
    for(var k in o) if(typeof o[k]==="object"&&walkDef(o[k],depth+1)) hit=true; return hit; }
  function harvest(){ var hit=false;
    ["DOSIK","YODO","TG_DOSIK"].forEach(function(g){ var o=window[g]; if(!o||typeof o!=="object") return;
      for(var k in o){ var id=g+"/"+k; if(harvested[id]) continue; harvested[id]=1; if(walkDef(o[k],0)) hit=true; } });
    if(hit){ ver++; rx=null; } }

  function regex(){ if(rx) return rx; var a=Object.keys(terms).filter(function(k){ return k.length>=2; }).sort(function(p,q){ return q.length-p.length; });
    if(!a.length) return null; rx=new RegExp(a.map(function(s){ return s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&"); }).join("|"),"g"); return rx; }
  var HANGUL=/[\uac00-\ud7a3]/, LATIN=/[A-Za-z0-9]/;
  function boundary(s,i,w){ var p=s.charAt(i-1), n=s.charAt(i+w.length);
    if(p&&HANGUL.test(w.charAt(0))&&HANGUL.test(p)) return false;
    if(LATIN.test(w.charAt(0))&&p&&LATIN.test(p)) return false;
    if(LATIN.test(w.charAt(w.length-1))&&n&&LATIN.test(n)) return false;
    return true; }
  var NOWRAP=".tn-t,.sc-btn,.dg-law,.dg-laws,.dg-term,.dg-t,.dg-n,.dg-rn,.dg-ch,.dg-kn,.dg-root,th,.katex,svg,button,a,script,style";
  function annotate(block){
    var r=regex(); if(!r) return; var seen={};
    block.querySelectorAll(".tn-t").forEach(function(e){ seen[e.getAttribute("data-t")]=1; });
    var w=document.createTreeWalker(block,NodeFilter.SHOW_TEXT,null), list=[], n;
    while((n=w.nextNode())){ if(n.nodeValue.trim()&&!(n.parentNode.closest&&n.parentNode.closest(NOWRAP))) list.push(n); }
    list.forEach(function(node){
      var s=node.nodeValue, m, last=0, frag=null; r.lastIndex=0;
      while((m=r.exec(s))){ var t=m[0];
        if(seen[t]||!boundary(s,m.index,t)) continue;
        seen[t]=1; frag=frag||document.createDocumentFragment();
        if(m.index>last) frag.appendChild(document.createTextNode(s.slice(last,m.index)));
        var sp=document.createElement("span"); sp.className="tn-t"; sp.setAttribute("data-t",t); sp.setAttribute("tabindex","0"); sp.textContent=t; frag.appendChild(sp);
        last=m.index+t.length; }
      if(frag){ if(last<s.length) frag.appendChild(document.createTextNode(s.slice(last)));
        /* in a flex or grid parent each new node would become its own column: keep the text together */
        var disp=getComputedStyle(node.parentNode).display;
        if(/flex|grid/.test(disp)){ var keep=document.createElement("span"); keep.className="tn-w"; keep.appendChild(frag); frag=keep; }
        node.parentNode.replaceChild(frag,node); }
    }); }

  var SENT=".dg-ln,.dg-s,.dg-rv,.dg-dtext,.dg-box,.dg-core,.dg-kid>span,.dg-marks li>span:last-child,.dg li:not(.dg-arr),.dg td";
  function lineOf(el){ var c=el.cloneNode(true); c.querySelectorAll(".sc-btn,.dg-laws,.dg-law,.dg-n,.dg-mn").forEach(function(e){ e.remove(); });
    c.querySelectorAll("br").forEach(function(e){ e.replaceWith(" \u00b7 "); }); return c.textContent.trim(); }
  function termsIn(text){ var r=regex(), out=[]; if(!r) return out; r.lastIndex=0; var m; while((m=r.exec(text))){ if(out.indexOf(m[0])<0&&boundary(text,m.index,m[0])) out.push(m[0]); } return out; }
  function mark(block){ block.querySelectorAll(SENT).forEach(function(el){
      if(el.querySelector(".dg-ln,.dg-s,.dg-rv,.dg-dtext,.dg-box")) return;   /* the line inside takes the tap */
      var k=key(lineOf(el)), on=!!(notes[k]||scenes[k]||el.querySelector(".tn-t"));
      el.classList.toggle("tn-s",on); }); }

  function inPanel(e){ return e.closest&&e.closest(".tn-panel,.sc-side,.sc-sheet"); }
  function scan(){ sch=0; var blocks=document.querySelectorAll(".dg"); if(!blocks.length) return;
    harvest();
    var changed=false;
    document.querySelectorAll(".dg-def").forEach(function(d){ if(d.getAttribute("data-tnd")) return; d.setAttribute("data-tnd","1");
      var a=d.querySelector(".dg-term"), b=d.querySelector(".dg-dtext"); if(a&&b&&addDef(a.textContent,lineOf(b))) changed=true; });
    if(changed){ ver++; rx=null; }
    blocks.forEach(function(b){ if(b.getAttribute("data-tnv")===String(ver)||inPanel(b)||b.classList.contains("sc")) return;
      b.setAttribute("data-tnv",String(ver)); annotate(b); mark(b); });
    if(!triedFile&&!Object.keys(notes).length){ triedFile=true; var s=document.createElement("script"); s.src=window.TN_NOTES_URL||"notes.js"; s.async=true; s.onerror=function(){ s.remove(); }; document.head.appendChild(s); } }
  var sch=0; function schedule(){ if(sch) return; sch=(window.requestAnimationFrame||setTimeout)(scan); }
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});

  /* popup */
  var pop=null, hideT=0, showT=0;
  function related(t){ var v=terms[t]||{}, a=(v.r||[]).filter(function(x){ return terms[x]&&x!==t; });
    if(!a.length) a=termsIn(v.d||"").filter(function(x){ return x!==t; }); return a.slice(0,4); }
  function popHtml(t){ var v=terms[t]||{}, r=related(t);
    return '<b class="tn-pn">'+esc(t)+'</b><div class="tn-pd">'+esc(plain(v.d))+'</div>'+
      (r.length?'<div class="tn-pr"><span>'+esc(L.rel)+'</span>'+r.map(function(x){ return '<button type="button" class="tn-chip" data-t="'+esc(x)+'">'+esc(x)+'</button>'; }).join("")+'</div>':""); }
  function place(anchor){ if(!pop) return; var a=anchor.getBoundingClientRect(), W=window.innerWidth, H=window.innerHeight, w=pop.offsetWidth, h=pop.offsetHeight;
    var x=Math.max(8,Math.min(W-w-8,a.left+a.width/2-w/2)), y=a.bottom+8; if(y+h>H-8&&a.top-h-8>=8) y=a.top-h-8; else if(y+h>H-8) y=Math.max(8,H-h-8);
    pop.style.left=x+"px"; pop.style.top=y+"px"; }
  function showPop(anchor,t){ clearTimeout(hideT); if(!terms[t]) return; if(!pop){ pop=document.createElement("div"); pop.className="tn-pop"; pop.setAttribute("role","tooltip"); document.body.appendChild(pop); }
    pop.innerHTML=popHtml(t); document.querySelectorAll(".tn-t.tn-act").forEach(function(e){ e.classList.remove("tn-act"); }); if(anchor.classList.contains("tn-t")) anchor.classList.add("tn-act"); place(anchor); }
  function hidePop(){ clearTimeout(showT); clearTimeout(hideT); if(pop){ pop.remove(); pop=null; } document.querySelectorAll(".tn-t.tn-act").forEach(function(e){ e.classList.remove("tn-act"); }); }
  document.addEventListener("pointerover",function(e){ if(e.pointerType!=="mouse"||!e.target.closest) return;
    if(e.target.closest(".tn-pop")){ clearTimeout(hideT); return; }
    var t=e.target.closest(".tn-t"); if(t){ clearTimeout(hideT); clearTimeout(showT); showT=setTimeout(function(){ showPop(t,t.getAttribute("data-t")); },90); } },true);
  document.addEventListener("pointerout",function(e){ if(e.pointerType!=="mouse"||!e.target.closest) return;
    if(e.target.closest(".tn-t,.tn-pop")){ clearTimeout(showT); hideT=setTimeout(hidePop,220); } },true);
  document.addEventListener("focusin",function(e){ var t=e.target.closest&&e.target.closest(".tn-t"); if(t) showPop(t,t.getAttribute("data-t")); });
  document.addEventListener("focusout",function(e){ if(e.target.closest&&e.target.closest(".tn-t")) hideT=setTimeout(hidePop,220); });

  /* sentence panel */
  function closePanel(){ document.querySelectorAll(".tn-dim,.tn-panel").forEach(function(e){ e.remove(); }); document.documentElement.classList.remove("tn-with-side");
    document.querySelectorAll(".tn-on").forEach(function(e){ e.classList.remove("tn-on"); }); }
  function closeOldScene(){ var x=document.querySelector(".sc-side .sc-x,.sc-sheet .sc-x"); if(x) x.click(); }
  function openPanel(el){ var text=lineOf(el).trim(), k=key(text), note=notes[k], sc=scenes[k], ts=termsIn(text).slice(0,5);
    if(!note&&!sc&&!ts.length) return false;
    closePanel(); closeOldScene(); hidePop(); el.classList.add("tn-on");
    var h='<button type="button" class="tn-x" aria-label="'+esc(L.close)+'">\u2715</button><div class="tn-q">'+esc(text)+'</div>';
    if(note) h+='<div class="tn-h">'+esc(L.note)+'</div><div class="tn-note">'+esc(plain(note))+'</div>';
    if(sc) h+=DIAGRAM.html(sc);
    if(ts.length) h+='<div class="tn-h">'+esc(L.term)+'</div>'+ts.map(function(t){ return '<div class="tn-def"><b>'+esc(t)+'</b><span>'+esc(plain((terms[t]||{}).d))+'</span></div>'; }).join("");
    if(window.innerWidth>=1000){ document.body.insertAdjacentHTML("beforeend",'<aside class="tn-panel tn-side">'+h+'</aside>'); document.documentElement.classList.add("tn-with-side"); }
    else document.body.insertAdjacentHTML("beforeend",'<div class="tn-dim"></div><div class="tn-panel tn-sheet" role="dialog"><div class="tn-grab"></div>'+h+'</div>');
    return true; }
  document.addEventListener("click",function(e){ var g=e.target; if(!g.closest) return;
    if(g.closest(".sc-btn")){ closePanel(); hidePop(); return; }
    if(g.closest(".tn-x,.tn-dim")){ closePanel(); e.stopPropagation(); return; }
    var chip=g.closest(".tn-chip"); if(chip){ e.preventDefault(); e.stopPropagation(); showPop(pop||chip,chip.getAttribute("data-t")); return; }
    if(g.closest(".tn-pop")){ e.stopPropagation(); return; }
    var t=g.closest(".tn-t"); if(t&&!inPanel(t)){ e.preventDefault(); e.stopPropagation(); showPop(t,t.getAttribute("data-t")); return; }
    hidePop();
    if(inPanel(g)||g.closest("a,button,input,select,textarea,summary,label")) return;
    var sel=window.getSelection&&String(window.getSelection()); if(sel) return;
    var el=g.closest(".tn-s"); if(el&&el.closest(".dg")&&openPanel(el)){ e.preventDefault(); e.stopPropagation(); }
  },true);
  document.addEventListener("keydown",function(e){ if(e.key==="Escape"){ hidePop(); closePanel(); }
    if(e.key==="Enter"&&e.target.classList&&e.target.classList.contains("tn-t")) showPop(e.target,e.target.getAttribute("data-t")); });
  window.addEventListener("scroll",function(){ if(pop) hidePop(); },{passive:true,capture:false});
  schedule();
})();
/*tnote-end*/
