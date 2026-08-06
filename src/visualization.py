"""Dashboard HTML autónomo, multipágina y orientado a escenarios.

Entradas: tabla maestra, KPIs, hallazgos, segmentación y escenarios de quantity.
Salida: HTML con Plotly y navegación client-side, sin backend ni CDN.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from plotly.offline.offline import get_plotlyjs

from src.site_navigation import navigation_css, navigation_html
from src.utils import EnhancedJSONEncoder


def _records(frame: pd.DataFrame, columns: list[str] | None = None) -> list[dict[str, Any]]:
    clean = frame.copy() if columns is None else frame[columns].copy()
    for column in clean.select_dtypes(include=["datetime", "datetimetz"]).columns:
        clean[column] = clean[column].dt.strftime("%Y-%m-%d")
    clean = clean.astype(object).where(pd.notna(clean), None)
    return clean.to_dict(orient="records")


def build_dashboard_html(
    orders: pd.DataFrame,
    kpis: dict[str, Any],
    insights: list[dict[str, str]],
    output_path: Path,
    model_profiles: pd.DataFrame | None = None,
    pca: pd.DataFrame | None = None,
    model_metrics: dict[str, Any] | None = None,
    scenario_comparison: pd.DataFrame | None = None,
    quantity_metrics: dict[str, Any] | None = None,
) -> None:
    """Genera una experiencia de tres vistas que funciona solo en navegador."""

    # Las llamadas mínimas usadas por pruebas o integraciones antiguas pueden no
    # traer escenarios. En ese caso todas las vistas reproducen el dato original.
    orders = orders.copy()
    fallback_columns = {
        "quantity_scenario_min": "quantity",
        "quantity_rf_estimated": "quantity",
        "quantity_scenario_max": "quantity",
        "revenue_scenario_min": "revenue",
        "revenue_rf_estimated": "revenue",
        "revenue_scenario_max": "revenue",
    }
    for target, source in fallback_columns.items():
        if target not in orders:
            orders[target] = orders[source]

    columns = [
        "order_id", "user_id", "customer_name", "country", "product_name", "category",
        "price_segment", "unit_price", "order_status", "channel", "year_month",
        "valid_sales_flag", "quantity", "revenue", "quantity_scenario_min",
        "quantity_rf_estimated", "quantity_scenario_max", "revenue_scenario_min",
        "revenue_rf_estimated", "revenue_scenario_max",
    ]
    raw_json = json.dumps(_records(orders, columns), ensure_ascii=False, cls=EnhancedJSONEncoder)
    profiles_json = json.dumps(_records(model_profiles) if model_profiles is not None else [], ensure_ascii=False, cls=EnhancedJSONEncoder)
    pca_json = json.dumps(_records(pca) if pca is not None else [], ensure_ascii=False, cls=EnhancedJSONEncoder)
    model_json = json.dumps(model_metrics or {}, ensure_ascii=False, cls=EnhancedJSONEncoder)
    scenario_json = json.dumps(_records(scenario_comparison) if scenario_comparison is not None else [], ensure_ascii=False, cls=EnhancedJSONEncoder)
    quantity_json = json.dumps(quantity_metrics or {}, ensure_ascii=False, cls=EnhancedJSONEncoder)
    insights_html = "".join(
        f'''<article class="finding"><div class="finding-no">{index:02d}</div><div><span>{item["title"]}</span>
        <h3>{item["observation"]}</h3><p>{item["importance"]} {item["implication"]}</p>
        <strong>ACCIÓN → {item["action"]}</strong></div></article>'''
        for index, item in enumerate(insights[:6], 1)
    )
    formulas = "".join(f"<li><b>{key.replace('_', ' ').upper()}</b><span>{value}</span></li>" for key, value in kpis["formula_notes"].items())

    global_css = navigation_css()
    global_nav = navigation_html("dashboard")
    html = f'''<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SportRetail LAM · Intelligence Studio</title>
<style>
:root{{--black:#000;--white:#fff;--fog:#f2f2f2;--gray:#767676;--line:#c8c8c8;--signal:#d7ff3f;--blue:#2563eb;--red:#e53935}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--fog);color:var(--black);font-family:Arial,Helvetica,sans-serif}}
button,select{{font:inherit}}.topbar{{height:58px;background:#000;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 28px;position:sticky;top:0;z-index:50}}
.wordmark{{font-size:18px;font-weight:900;letter-spacing:-.04em}}.wordmark small{{font-size:10px;letter-spacing:.16em;margin-left:10px;color:#aaa}}
.tabs{{display:flex;height:100%}}.tab,.summary-link{{border:0;border-left:1px solid #333;background:#000;color:#aaa;padding:0 18px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.09em;cursor:pointer;text-decoration:none;display:flex;align-items:center}}
.tab.active,.tab:hover,.summary-link:hover{{background:#fff;color:#000}}.hero{{min-height:440px;background:#000;color:#fff;display:grid;grid-template-columns:1.55fr .75fr;gap:32px;padding:72px max(28px,calc((100vw - 1480px)/2)) 48px;align-items:end;overflow:hidden}}
.hero h1{{font-size:clamp(54px,8vw,126px);line-height:.82;letter-spacing:-.075em;text-transform:uppercase;margin:12px 0 26px;max-width:1050px}}.hero p{{font-size:17px;line-height:1.5;color:#bbb;max-width:720px}}
.hero-aside{{border-left:1px solid #555;padding-left:25px}}.hero-stat{{padding:18px 0;border-bottom:1px solid #444}}.hero-stat b{{display:block;font-size:30px;letter-spacing:-.04em}}.hero-stat span,.eyebrow{{font-size:10px;font-weight:900;letter-spacing:.16em;text-transform:uppercase;color:#888}}.hero .eyebrow{{color:var(--signal)}}
.page{{display:none}}.page.active{{display:block}}.shell{{max-width:1480px;margin:auto;padding:24px}}.scenario-bar{{background:#fff;border:2px solid #000;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;gap:20px;position:sticky;top:58px;z-index:40}}
.scenario-copy b{{font-size:13px;text-transform:uppercase}}.scenario-copy small{{display:block;color:#666;margin-top:3px}}.switch{{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid #000;min-width:min(660px,100%)}}
.switch button{{border:0;border-right:1px solid #000;background:#fff;padding:12px 15px;font-size:10px;font-weight:900;text-transform:uppercase;cursor:pointer}}.switch button:last-child{{border-right:0}}.switch button.active{{background:#000;color:#fff;box-shadow:inset 0 -4px var(--signal)}}
.filters{{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:#000;border:1px solid #000;margin-top:12px}}label{{background:#fff;padding:10px;font-size:9px;font-weight:900;letter-spacing:.12em;text-transform:uppercase}}select{{width:100%;border:0;border-top:1px solid #ddd;margin-top:7px;padding:8px 0;background:#fff}}
.section-head{{display:flex;justify-content:space-between;align-items:end;border-bottom:4px solid #000;margin:50px 0 16px;padding-bottom:12px}}.section-head h2{{font-size:clamp(32px,4vw,58px);line-height:.9;letter-spacing:-.055em;text-transform:uppercase;margin:6px 0 0}}.section-head p{{max-width:600px;color:#666;text-align:right;margin:0;line-height:1.4}}
.kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:#000;border:1px solid #000}}.kpi{{background:#fff;padding:18px;min-height:132px}}.kpi span{{font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em}}.kpi strong{{font-size:clamp(24px,2.3vw,38px);display:block;margin-top:23px;letter-spacing:-.06em}}.kpi small{{color:#777;display:block;margin-top:4px}}
.grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:12px;margin-top:12px}}.panel{{background:#fff;border:1px solid #aaa;padding:10px;min-height:385px}}.span-4{{grid-column:span 4}}.span-6{{grid-column:span 6}}.span-8{{grid-column:span 8}}.span-12{{grid-column:span 12}}.plot{{height:360px}}
.comparison-strip{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#000;border:1px solid #000}}.scenario-card{{background:#fff;padding:20px}}.scenario-card.active{{background:var(--signal)}}.scenario-card span{{font-size:10px;font-weight:900;text-transform:uppercase}}.scenario-card b{{display:block;font-size:25px;margin:16px 0 5px}}.scenario-card small{{color:#555}}
.findings{{border-top:1px solid #000}}.finding{{display:grid;grid-template-columns:100px 1fr;gap:24px;padding:32px 0;border-bottom:1px solid #000}}.finding-no{{font-size:54px;font-weight:900;letter-spacing:-.08em}}.finding h3{{font-size:clamp(23px,3vw,42px);letter-spacing:-.04em;margin:8px 0}}.finding p{{color:#555;max-width:950px;line-height:1.5}}.finding strong{{font-size:12px;background:#000;color:#fff;padding:10px;display:inline-block}}
.model-banner{{background:var(--signal);border:2px solid #000;padding:22px;font-size:16px;line-height:1.5}}table{{border-collapse:collapse;width:100%;font-size:12px}}th{{background:#000;color:#fff;text-transform:uppercase;letter-spacing:.06em}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #ccc}}.table-wrap{{overflow:auto;max-height:390px}}
.method{{background:#fff;border:1px solid #aaa;padding:25px}}.method li{{display:grid;grid-template-columns:280px 1fr;border-bottom:1px solid #ddd;padding:12px 0;gap:20px}}footer{{background:#000;color:#888;padding:32px;margin-top:60px;font-size:11px;text-transform:uppercase;letter-spacing:.08em}}
@media(max-width:1000px){{.hero{{grid-template-columns:1fr}}.hero-aside{{display:none}}.tabs .tab{{padding:0 9px;font-size:9px}}.scenario-bar{{align-items:stretch;flex-direction:column}}.switch{{min-width:100%}}.filters{{grid-template-columns:repeat(3,1fr)}}.kpis{{grid-template-columns:repeat(2,1fr)}}.span-4,.span-6,.span-8{{grid-column:span 12}}.comparison-strip{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:600px){{.hero{{padding:45px 18px}}.shell{{padding:12px}}.filters{{grid-template-columns:repeat(2,1fr)}}.switch{{grid-template-columns:repeat(2,1fr)}}.kpis,.comparison-strip{{grid-template-columns:1fr}}.section-head{{display:block}}.section-head p{{text-align:left;margin-top:10px}}.finding{{grid-template-columns:50px 1fr}}.finding-no{{font-size:32px}}}}
{global_css}
</style><script>{get_plotlyjs()}</script></head><body>
{global_nav}
<section class="hero"><div><span class="eyebrow">Business intelligence · 2024</span><h1>Move the<br>business.</h1><p>Una lectura ejecutiva del rendimiento mayorista, la incertidumbre de los datos y las acciones comerciales. Diseño autónomo: funciona sin Python, API, servidor ni conexión.</p></div><aside class="hero-aside"><div class="hero-stat"><span>Valor bruto de pedidos</span><b>$4,17 M</b></div><div class="hero-stat"><span>Valor entregado</span><b>$1,85 M</b></div><div class="hero-stat"><span>Mercados</span><b>5 países</b></div><div class="hero-stat"><span>Estado analítico</span><b>Auditable</b></div></aside></section>
<main class="shell">
<div class="scenario-bar"><div class="scenario-copy"><b>Vista activa de cantidades y valor bruto</b><small id="scenarioDescription"></small></div><div class="switch" id="scenarioSwitch"><button data-scenario="original" class="active">Original</button><button data-scenario="minimum">Mínimo</button><button data-scenario="rf">Random Forest</button><button data-scenario="maximum">Máximo</button></div></div>
<section class="filters"><label>País<select id="country"></select></label><label>Canal<select id="channel"></select></label><label>Categoría<select id="category"></select></label><label>Segmento<select id="price_segment"></select></label><label>Estado<select id="order_status"></select></label><label>Periodo<select id="year_month"></select></label></section>
<section id="page-overview" class="page active"><div class="section-head"><div><span class="eyebrow">01 · Pulso comercial</span><h2>El negocio<br>en movimiento</h2></div><p>Todos los indicadores y gráficos responden a filtros y al escenario seleccionado.</p></div><div class="kpis" id="kpis"></div><div class="grid"><article class="panel span-8"><div id="revenueTime" class="plot"></div></article><article class="panel span-4"><div id="unitsTime" class="plot"></div></article><article class="panel span-4"><div id="countryChart" class="plot"></div></article><article class="panel span-4"><div id="channelChart" class="plot"></div></article><article class="panel span-4"><div id="segmentChart" class="plot"></div></article><article class="panel span-6"><div id="categoryChart" class="plot"></div></article><article class="panel span-6"><div id="productChart" class="plot"></div></article><article class="panel span-6"><div id="customerChart" class="plot"></div></article><article class="panel span-6"><div id="heatmapChart" class="plot"></div></article></div></section>
<section id="page-scenarios" class="page"><div class="section-head"><div><span class="eyebrow">02 · Incertidumbre explícita</span><h2>Comparar<br>sin ocultar</h2></div><p>La fuente original se conserva. Los escenarios calculados cuantifican el rango posible para las 12 cantidades ausentes.</p></div><div class="comparison-strip" id="scenarioCards"></div><div class="grid"><article class="panel span-6"><div id="scenarioRevenueChart" class="plot"></div></article><article class="panel span-6"><div id="scenarioQuantityChart" class="plot"></div></article><article class="panel span-12"><div id="scenarioMonthlyChart" class="plot"></div></article><article class="panel span-12"><h3>Líneas con cantidad estimada</h3><div class="table-wrap"><table id="missingTable"></table></div></article></div><div class="method"><h3>Lectura correcta</h3><p>Random Forest es un experimento reproducible, no una imputación certificada. R² = <b>{(quantity_metrics or {}).get("r2", 0):.3f}</b>; RMSE del modelo = <b>{(quantity_metrics or {}).get("rmse", 0):.2f}</b> frente a <b>{(quantity_metrics or {}).get("baseline_rmse", 0):.2f}</b> de la mediana. El proyecto recomienda <b>scenario_only</b>.</p></div></section>
<section id="page-decisions" class="page"><div class="section-head"><div><span class="eyebrow">03 · De datos a acción</span><h2>Decisiones<br>defendibles</h2></div><p>Conclusiones integradas del notebook y segmentación oficial de clientes.</p></div><div class="findings">{insights_html}</div><div class="section-head"><div><span class="eyebrow">04 · Machine learning oficial</span><h2>Clientes con<br>ritmos distintos</h2></div><p>Segmentación jerárquica seleccionada frente a K-Means y Gaussian Mixture.</p></div><div id="modelNote" class="model-banner"></div><div class="grid"><article class="panel span-4"><div id="mlCustomers" class="plot"></div></article><article class="panel span-4"><div id="mlRevenue" class="plot"></div></article><article class="panel span-4"><div id="mlPca" class="plot"></div></article><article class="panel span-12"><div class="table-wrap"><table id="profileTable"></table></div></article></div><div class="section-head"><div><span class="eyebrow">05 · Método</span><h2>Qué significa<br>cada cifra</h2></div></div><div class="method"><ul>{formulas}<li><b>ALCANCE</b><span>Datos sintéticos de un año; no prueban causalidad ni estacionalidad.</span></li><li><b>OUTLIERS</b><span>Se identifican por IQR y se conservan por el contexto mayorista.</span></li><li><b>PCA</b><span>Proyección visual; no demuestra separación perfecta.</span></li></ul></div></section>
</main><footer>SportRetail LAM · Dashboard generado de forma reproducible · HTML autónomo · Sin activos de marca externos</footer>
<script>
const RAW={raw_json}, PROFILES={profiles_json}, PCA={pca_json}, METRICS={model_json}, SCENARIOS={scenario_json}, QMETRICS={quantity_json};
const scenarioMap={{original:{{q:'quantity',r:'revenue',label:'Original',desc:'Solo datos observados; las cantidades nulas permanecen fuera de las sumas.'}},minimum:{{q:'quantity_scenario_min',r:'revenue_scenario_min',label:'Mínimo mayorista',desc:'Cantidad mínima de 5 unidades para cada línea ausente.'}},rf:{{q:'quantity_rf_estimated',r:'revenue_rf_estimated',label:'Random Forest',desc:'Estimación experimental; no supera el baseline y se usa solo como sensibilidad.'}},maximum:{{q:'quantity_scenario_max',r:'revenue_scenario_max',label:'Máximo jerárquico',desc:'Percentil 90 de grupos comparables con jerarquía documentada.'}}}};
let activeScenario='original';const dims=['country','channel','category','price_segment','order_status','year_month'];const money=new Intl.NumberFormat('es-CO',{{style:'currency',currency:'USD',maximumFractionDigits:0}}),number=new Intl.NumberFormat('es-CO',{{maximumFractionDigits:0}});const cfg={{responsive:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d']}};const palette=['#000','#777','#d7ff3f','#2563eb','#e53935'];
function unique(k){{return [...new Set(RAW.map(d=>d[k]).filter(v=>v!=null))].sort()}}dims.forEach(k=>{{const e=document.getElementById(k);e.innerHTML='<option value="">Todos</option>'+unique(k).map(v=>`<option>${{v}}</option>`).join('');e.onchange=update}});
function rows(){{return RAW.filter(d=>dims.every(k=>!document.getElementById(k).value||String(d[k])===document.getElementById(k).value))}}function value(d,k){{const n=Number(d[k]);return Number.isFinite(n)?n:0}}function sum(r,k){{return r.reduce((a,d)=>a+value(d,k),0)}}function distinct(r,k){{return new Set(r.map(d=>d[k]).filter(v=>v!=null)).size}}function group(r,k,v){{const m={{}};r.forEach(d=>{{const x=d[k]??'Sin dato';m[x]=(m[x]||0)+value(d,v)}});return Object.entries(m).sort((a,b)=>b[1]-a[1])}}
function layout(title,extra={{}}){{const base={{title:{{text:title.toUpperCase(),x:.02,font:{{size:15,family:'Arial Black',color:'#111'}}}},paper_bgcolor:'#fff',plot_bgcolor:'#fff',font:{{family:'Arial',color:'#111'}},margin:{{l:78,r:28,t:64,b:62}},legend:{{font:{{color:'#111',size:11}},bgcolor:'rgba(255,255,255,.94)',bordercolor:'#b5b5b5',borderwidth:1}},hoverlabel:{{bgcolor:'#fff',bordercolor:'#111',font:{{color:'#111'}}}},xaxis:{{gridcolor:'#dedede',zeroline:false,automargin:true,tickfont:{{color:'#111'}}}},yaxis:{{gridcolor:'#dedede',zeroline:false,automargin:true,tickfont:{{color:'#111'}}}}}};return {{...base,...extra,margin:{{...base.margin,...(extra.margin||{{}})}},legend:{{...base.legend,...(extra.legend||{{}})}},xaxis:{{...base.xaxis,...(extra.xaxis||{{}})}},yaxis:{{...base.yaxis,...(extra.yaxis||{{}})}}}}}}function bar(id,pairs,title,h=false,color='#000'){{const extra=h?{{margin:{{l:285,r:30,t:64,b:62}},yaxis:{{automargin:true,tickfont:{{color:'#111',size:11}}}}}}:{{}};Plotly.react(id,[{{type:'bar',x:pairs.map(d=>h?d[1]:d[0]),y:pairs.map(d=>h?d[0]:d[1]),orientation:h?'h':'v',marker:{{color}},hovertemplate:h?'%{{y}}<br>%{{x:,.0f}}<extra></extra>':'%{{x}}<br>%{{y:,.0f}}<extra></extra>'}}],layout(title,extra),cfg)}}
function update(){{const r=rows(),m=scenarioMap[activeScenario],rev=sum(r,m.r),qty=sum(r,m.q),orders=distinct(r,'order_id'),customers=distinct(r,'user_id'),status=[...new Map(r.map(d=>[d.order_id,d.order_status])).values()],delivered=status.filter(x=>x==='delivered').length/(status.length||1),leaders=[group(r,'country',m.r)[0]?.[0]||'—',group(r,'channel',m.r)[0]?.[0]||'—',group(r,'category',m.r)[0]?.[0]||'—'];document.getElementById('scenarioDescription').textContent=m.desc;const cards=[['Valor bruto · '+m.label,money.format(rev),'Todos los estados'],['Unidades · '+m.label,number.format(qty),'Cantidad del escenario'],['Pedidos',number.format(orders),'order_id distintos'],['Clientes',number.format(customers),'user_id distintos'],['Valor / pedido',money.format(rev/(orders||1)),'Valor bruto ÷ pedidos'],['Precio / unidad',money.format(rev/(qty||1)),'Valor bruto ÷ unidades'],['País líder',leaders[0],'Por valor bruto'],['Canal líder',leaders[1],'Por valor bruto'],['Categoría líder',leaders[2],'Por valor bruto'],['Entregados',(delivered*100).toFixed(1)+'%','A nivel pedido']];document.getElementById('kpis').innerHTML=cards.map(c=>`<article class="kpi"><span>${{c[0]}}</span><strong>${{c[1]}}</strong><small>${{c[2]}}</small></article>`).join('');
const monthly=group(r,'year_month',m.r).sort((a,b)=>a[0].localeCompare(b[0])),qmonthly=group(r,'year_month',m.q).sort((a,b)=>a[0].localeCompare(b[0]));Plotly.react('revenueTime',[{{type:'scatter',mode:'lines+markers',x:monthly.map(d=>d[0]),y:monthly.map(d=>d[1]),line:{{color:'#000',width:4}},marker:{{color:'#d7ff3f',size:10,line:{{color:'#000',width:2}}}}}}],layout('Valor bruto mensual · '+m.label),cfg);bar('unitsTime',qmonthly,'Unidades mensuales · '+m.label,false,'#777');bar('countryChart',group(r,'country',m.r),'Valor bruto por país');const ch=group(r,'channel',m.r);Plotly.react('channelChart',[{{type:'pie',labels:ch.map(d=>d[0]),values:ch.map(d=>d[1]),hole:.62,marker:{{colors:palette}},textinfo:'label+percent'}}],layout('Mezcla de canales'),cfg);bar('segmentChart',group(r,'price_segment',m.r),'Segmento de precio');bar('categoryChart',group(r,'category',m.r).reverse(),'Valor bruto por categoría',true);bar('productChart',group(r,'product_name',m.q).slice(0,10).reverse(),'Top productos por unidades',true);bar('customerChart',group(r,'customer_name',m.r).slice(0,10).reverse(),'Top clientes por valor',true);const countries=unique('country'),channels=unique('channel'),matrix=countries.map(c=>channels.map(ch=>sum(r.filter(d=>d.country===c&&d.channel===ch),m.r)));Plotly.react('heatmapChart',[{{type:'heatmap',x:channels,y:countries,z:matrix,colorscale:[[0,'#f3f3f3'],[1,'#000']]}}],layout('País × canal'),cfg);renderScenarioComparison(r)}}
function renderScenarioComparison(r){{const defs=Object.entries(scenarioMap),totals=defs.map(([k,v])=>[v.label,sum(r,v.r),sum(r,v.q),k]);document.getElementById('scenarioCards').innerHTML=totals.map(x=>`<article class="scenario-card ${{x[3]===activeScenario?'active':''}}"><span>${{x[0]}}</span><b>${{money.format(x[1])}}</b><small>${{number.format(x[2])}} unidades</small></article>`).join('');bar('scenarioRevenueChart',totals.map(x=>[x[0],x[1]]),'Comparación de valor bruto',false,'#000');bar('scenarioQuantityChart',totals.map(x=>[x[0],x[2]]),'Comparación de cantidades',false,'#2563eb');const months=unique('year_month');Plotly.react('scenarioMonthlyChart',defs.map(([k,v],i)=>({{type:'scatter',mode:'lines+markers',name:v.label,x:months,y:months.map(month=>sum(r.filter(d=>d.year_month===month),v.r)),line:{{width:k===activeScenario?4:2,color:palette[i]}}}})),layout('Valor bruto mensual: todos los escenarios',{{legend:{{orientation:'h',y:-.18}}}}),cfg)}}
document.querySelectorAll('#scenarioSwitch button').forEach(b=>b.onclick=()=>{{activeScenario=b.dataset.scenario;document.querySelectorAll('#scenarioSwitch button').forEach(x=>x.classList.toggle('active',x===b));update()}});function activatePage(page,updateHash=true){{const valid=['overview','scenarios','decisions'];page=valid.includes(page)?page:'overview';document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x.id==='page-'+page));document.querySelectorAll('.global-nav__link[data-dashboard-page]').forEach(x=>x.classList.toggle('active',x.dataset.dashboardPage===page));if(updateHash)history.replaceState(null,'','#'+page);setTimeout(()=>window.dispatchEvent(new Event('resize')),50)}}document.querySelectorAll('.global-nav__link[data-dashboard-page]').forEach(a=>a.onclick=e=>{{e.preventDefault();activatePage(a.dataset.dashboardPage)}});window.addEventListener('hashchange',()=>activatePage(location.hash.slice(1),false));
function renderMissing(){{const miss=RAW.filter(d=>d.quantity==null);document.getElementById('missingTable').innerHTML='<thead><tr><th>Pedido</th><th>Producto</th><th>Precio</th><th>Original</th><th>Mínimo</th><th>Random Forest</th><th>Máximo</th></tr></thead><tbody>'+miss.map(d=>`<tr><td>${{d.order_id}}</td><td>${{d.product_name}}</td><td>${{money.format(d.unit_price)}}</td><td>NULO</td><td>${{d.quantity_scenario_min}}</td><td>${{d.quantity_rf_estimated}}</td><td>${{d.quantity_scenario_max}}</td></tr>`).join('')+'</tbody>'}}
function renderModel(){{if(!PROFILES.length)return;document.getElementById('modelNote').innerHTML=`MODELO OFICIAL → <b>${{METRICS.selected_model}}</b> · ${{METRICS.clusters}} SEGMENTOS · SILHOUETTE ${{METRICS.silhouette.toFixed(3)}} · PCA ${{(METRICS.pca_explained_variance.reduce((a,b)=>a+b,0)*100).toFixed(1)}}% EN DOS EJES`;bar('mlCustomers',PROFILES.map(d=>[d.segment,d.customers]),'Clientes por segmento');bar('mlRevenue',PROFILES.map(d=>[d.segment,d.total_revenue]),'Valor bruto por segmento');const seg=[...new Set(PCA.map(d=>d.segment))];Plotly.react('mlPca',seg.map((s,i)=>{{const z=PCA.filter(d=>d.segment===s);return{{type:'scatter',mode:'markers',name:s,x:z.map(d=>d.pca_1),y:z.map(d=>d.pca_2),text:z.map(d=>d.customer_name),marker:{{size:10,color:palette[i]}}}}}}),layout('Proyección PCA'),cfg);document.getElementById('profileTable').innerHTML='<thead><tr><th>Segmento</th><th>Clientes</th><th>Participación</th><th>Valor bruto</th><th>Ticket</th><th>Acción</th></tr></thead><tbody>'+PROFILES.map(d=>`<tr><td><b>${{d.segment}}</b></td><td>${{d.customers}}</td><td>${{(d.customer_share*100).toFixed(1)}}%</td><td>${{money.format(d.total_revenue)}}</td><td>${{money.format(d.average_ticket)}}</td><td>${{d.recommended_action}}</td></tr>`).join('')+'</tbody>'}}
update();renderMissing();renderModel();activatePage(location.hash.slice(1),false);window.addEventListener('pageshow',()=>{{activatePage(location.hash.slice(1),false);setTimeout(update,0)}});
</script></body></html>'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
