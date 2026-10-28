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
