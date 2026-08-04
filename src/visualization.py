"""Generación del dashboard HTML estático e interactivo.

Entradas: tabla maestra, KPIs, hallazgos y resultados de clustering.
Salidas: HTML autónomo con Plotly y filtros JavaScript client-side.
Dependencias: plotly y biblioteca estándar.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from plotly.offline.offline import get_plotlyjs

from src.utils import EnhancedJSONEncoder


def _records(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    clean = frame[columns].copy()
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
) -> None:
    """Construye una sola página sin backend, CDN ni rutas locales."""

    business_columns = [
        "order_id", "user_id", "customer_name", "country", "product_name", "category",
        "price_segment", "quantity", "unit_price", "revenue", "order_status", "channel",
        "year_month", "valid_sales_flag",
    ]
    raw_json = json.dumps(_records(orders, business_columns), ensure_ascii=False, cls=EnhancedJSONEncoder)
    profile_json = json.dumps(
        [] if model_profiles is None else _records(model_profiles, list(model_profiles.columns)),
        ensure_ascii=False,
        cls=EnhancedJSONEncoder,
    )
    pca_json = json.dumps(
        [] if pca is None else _records(pca, list(pca.columns)),
        ensure_ascii=False,
        cls=EnhancedJSONEncoder,
    )
    metrics_json = json.dumps(model_metrics or {}, ensure_ascii=False, cls=EnhancedJSONEncoder)
    insights_html = "".join(
        f"""<article class="insight"><span class="eyebrow">{item['title']}</span><h3>{item['observation']}</h3>
        <p><strong>Por qué importa:</strong> {item['importance']}</p><p><strong>Implicación:</strong> {item['implication']}</p>
        <p class="action"><strong>Acción:</strong> {item['action']}</p></article>"""
        for item in insights[:6]
    )
    formulas = "".join(f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>" for key, value in kpis["formula_notes"].items())
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SportRetail LAM | Business Intelligence</title>
<style>
:root{{--ink:#0b0b0b;--muted:#656565;--line:#dedede;--paper:#fff;--wash:#f4f4f2;--accent:#d7ff3f;--alert:#d94b3d;--blue:#3d6ea8}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--wash);color:var(--ink);font-family:Inter,Arial,sans-serif}}
.hero{{background:#050505;color:white;padding:42px max(24px,calc((100vw - 1440px)/2));display:grid;grid-template-columns:1.7fr 1fr;gap:28px;align-items:end}}
.hero h1{{font-size:clamp(34px,5vw,72px);line-height:.94;letter-spacing:-.055em;margin:10px 0 16px;max-width:850px}} .hero p{{color:#c8c8c8;max-width:760px;line-height:1.55}}
.hero-nav{{display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end}} .hero a{{color:#fff;border:1px solid #555;padding:10px 14px;text-decoration:none;font-size:13px}} .hero a:hover{{border-color:var(--accent);color:var(--accent)}}
.eyebrow{{text-transform:uppercase;letter-spacing:.12em;font-size:11px;font-weight:800;color:#747474}} .hero .eyebrow{{color:var(--accent)}}
.shell{{max-width:1440px;margin:auto;padding:22px}} .filters{{position:sticky;top:0;z-index:20;background:rgba(244,244,242,.96);backdrop-filter:blur(10px);display:grid;grid-template-columns:repeat(6,minmax(130px,1fr));gap:10px;padding:14px 0;border-bottom:1px solid var(--line)}}
label{{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}} select{{width:100%;margin-top:5px;padding:10px;border:1px solid #cfcfcf;background:white}}
.kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:18px 0}} .kpi{{background:white;border-top:4px solid #111;padding:16px;min-height:112px}} .kpi span{{color:var(--muted);font-size:12px}} .kpi strong{{display:block;font-size:clamp(21px,2vw,31px);margin-top:13px;letter-spacing:-.04em}} .kpi small{{display:block;margin-top:5px;color:#777}}
.section-head{{display:flex;align-items:end;justify-content:space-between;margin:38px 0 14px;border-bottom:2px solid #111;padding-bottom:10px}} .section-head h2{{font-size:30px;margin:0;letter-spacing:-.035em}} .section-head p{{margin:0;color:var(--muted);max-width:680px;text-align:right}}
.grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}} .panel{{background:white;border:1px solid var(--line);padding:12px;min-height:390px}} .span-4{{grid-column:span 4}} .span-6{{grid-column:span 6}} .span-8{{grid-column:span 8}} .span-12{{grid-column:span 12}} .plot{{height:350px}}
.insights{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .insight{{background:#111;color:white;padding:22px;min-height:280px}} .insight h3{{font-size:21px;line-height:1.22;margin:12px 0}} .insight p{{color:#c8c8c8;line-height:1.45;font-size:14px}} .insight .action{{border-top:1px solid #444;padding-top:12px;color:#fff}}
.model-note{{background:var(--accent);padding:18px;margin-bottom:14px;line-height:1.5}} table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border-bottom:1px solid var(--line);padding:10px;text-align:left}} th{{background:#111;color:white;position:sticky;top:0}} .table-wrap{{overflow:auto;max-height:370px}}
details{{background:#fff;border:1px solid var(--line);padding:15px;margin:18px 0}} details li{{margin:8px 0;color:#555}} footer{{margin-top:40px;padding:28px 0;border-top:1px solid #bbb;color:#666;font-size:12px}}
@media(max-width:1000px){{.hero{{grid-template-columns:1fr}}.hero-nav{{justify-content:flex-start}}.filters{{grid-template-columns:repeat(3,1fr)}}.kpis{{grid-template-columns:repeat(2,1fr)}}.span-4,.span-6,.span-8{{grid-column:span 12}}.insights{{grid-template-columns:1fr}}}}
@media(max-width:600px){{.filters{{grid-template-columns:repeat(2,1fr)}}.kpis{{grid-template-columns:1fr}}.shell{{padding:14px}}}}
</style><script>{get_plotlyjs()}</script></head>
<body><header class="hero"><div><span class="eyebrow">SportRetail LAM · Business Intelligence</span><h1>Rendimiento mayorista, sin perder de vista el riesgo.</h1><p>Vista ejecutiva de ventas, geografías, canales, clientes, productos y segmentos. Los filtros se ejecutan enteramente en el navegador; no se requiere Python, API ni servidor.</p></div><nav class="hero-nav"><a href="#performance">Desempeño</a><a href="#drivers">Impulsores</a><a href="#insights">Hallazgos</a><a href="#model">Machine Learning</a><a href="executive_summary.html">Resumen ejecutivo</a></nav></header>
<main class="shell"><section class="filters" aria-label="Filtros">
<label>País<select id="country"></select></label><label>Canal<select id="channel"></select></label><label>Categoría<select id="category"></select></label><label>Segmento<select id="price_segment"></select></label><label>Estado<select id="order_status"></select></label><label>Periodo<select id="year_month"></select></label>
</section><section id="performance"><div class="section-head"><div><span class="eyebrow">01 · Pulso del negocio</span><h2>Indicadores principales</h2></div><p>KPIs recalculados al instante sobre líneas válidas según los filtros seleccionados.</p></div><div class="kpis" id="kpis"></div>
<div class="grid"><article class="panel span-8"><div id="revenueTime" class="plot"></div></article><article class="panel span-4"><div id="unitsTime" class="plot"></div></article></div></section>
<section id="drivers"><div class="section-head"><div><span class="eyebrow">02 · Motores de ingreso</span><h2>Dónde se crea valor</h2></div><p>Composición comercial y concentración por mercado, canal, surtido y cliente.</p></div><div class="grid">
<article class="panel span-4"><div id="countryChart" class="plot"></div></article><article class="panel span-4"><div id="channelChart" class="plot"></div></article><article class="panel span-4"><div id="segmentChart" class="plot"></div></article>
<article class="panel span-6"><div id="categoryChart" class="plot"></div></article><article class="panel span-6"><div id="productChart" class="plot"></div></article>
<article class="panel span-6"><div id="customerChart" class="plot"></div></article><article class="panel span-6"><div id="heatmapChart" class="plot"></div></article></div></section>
<section id="insights"><div class="section-head"><div><span class="eyebrow">03 · Decisiones</span><h2>Hallazgos y acciones</h2></div><p>Lectura cuantificada del conjunto completo; los hallazgos no cambian con los filtros.</p></div><div class="insights">{insights_html}</div></section>
<section id="model"><div class="section-head"><div><span class="eyebrow">04 · Machine Learning</span><h2>Segmentos comerciales</h2></div><p>Comparación de K-Means, clustering jerárquico y Gaussian Mixture; selección por silhouette, tamaño e interpretabilidad.</p></div><div id="modelNote" class="model-note"></div><div class="grid">
<article class="panel span-4"><div id="mlCustomers" class="plot"></div></article><article class="panel span-4"><div id="mlRevenue" class="plot"></div></article><article class="panel span-4"><div id="mlPca" class="plot"></div></article>
<article class="panel span-12"><h3>Perfil y recomendación por segmento</h3><div class="table-wrap"><table id="profileTable"></table></div></article></div></section>
<details><summary><strong>Definiciones de indicadores y alcance</strong></summary><ul>{formulas}<li><strong>Alcance temporal:</strong> un año de datos sintéticos; las variaciones mensuales no demuestran estacionalidad.</li><li><strong>Outliers:</strong> se identifican por IQR y se conservan por el contexto mayorista.</li><li><strong>PCA:</strong> es una proyección descriptiva, no prueba separación perfecta de segmentos.</li></ul></details>
<footer>Generado de forma reproducible por el pipeline SportRetail LAM. HTML autónomo con Plotly embebido.</footer></main>
<script>
const RAW={raw_json}; const PROFILES={profile_json}; const PCA={pca_json}; const METRICS={metrics_json};
const dims=['country','channel','category','price_segment','order_status','year_month'];
const money=new Intl.NumberFormat('es-CO',{{style:'currency',currency:'USD',maximumFractionDigits:0}}); const number=new Intl.NumberFormat('es-CO',{{maximumFractionDigits:0}});
const colors=['#0b0b0b','#707070','#a4a4a4','#d7ff3f','#3d6ea8','#d94b3d']; const cfg={{responsive:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d']}};
function unique(key){{return [...new Set(RAW.map(d=>d[key]).filter(v=>v!==null))].sort();}}
dims.forEach(key=>{{const el=document.getElementById(key); el.innerHTML='<option value="">Todos</option>'+unique(key).map(v=>`<option>${{v}}</option>`).join(''); el.addEventListener('change',update);}});
function filtered(){{return RAW.filter(d=>dims.every(k=>!document.getElementById(k).value||String(d[k])===document.getElementById(k).value));}}
function valid(rows){{return rows.filter(d=>d.valid_sales_flag===true && Number.isFinite(Number(d.revenue)));}}
function sum(rows,key){{return rows.reduce((a,d)=>a+(Number(d[key])||0),0);}}
function group(rows,key,value='revenue'){{const m={{}}; rows.forEach(d=>{{const k=d[key]??'Sin dato';m[k]=(m[k]||0)+(Number(d[value])||0);}});return Object.entries(m).sort((a,b)=>b[1]-a[1]);}}
function distinct(rows,key){{return new Set(rows.map(d=>d[key]).filter(v=>v!==null)).size;}}
function layout(title,extra={{}}){{return Object.assign({{title:{{text:title,x:.02,font:{{size:16}}}},paper_bgcolor:'#fff',plot_bgcolor:'#fff',font:{{family:'Inter,Arial',color:'#222'}},margin:{{l:62,r:20,t:58,b:55}},xaxis:{{gridcolor:'#ececec',zeroline:false}},yaxis:{{gridcolor:'#ececec',zeroline:false}}}},extra);}}
function bar(id,pairs,title,h=false){{const x=pairs.map(d=>h?d[1]:d[0]),y=pairs.map(d=>h?d[0]:d[1]);Plotly.react(id,[{{type:'bar',x,y,orientation:h?'h':'v',marker:{{color:'#111'}},hovertemplate:h?'%{{y}}<br>$%{{x:,.0f}}<extra></extra>':'%{{x}}<br>$%{{y:,.0f}}<extra></extra>'}}],layout(title,{{showlegend:false}}),cfg);}}
function update(){{const rows=filtered(),sales=valid(rows);const revenue=sum(sales,'revenue'),units=sum(sales,'quantity'),orders=distinct(sales,'order_id'),customers=distinct(sales,'user_id');const statusOrders=[...new Map(rows.map(d=>[d.order_id,d.order_status])).entries()];const delivered=statusOrders.filter(d=>d[1]==='delivered').length/(statusOrders.length||1);const leaders=[group(sales,'country')[0]?.[0]||'—',group(sales,'channel')[0]?.[0]||'—',group(sales,'category')[0]?.[0]||'—'];
const cards=[['Ingresos totales',money.format(revenue),'unit price × quantity'],['Unidades vendidas',number.format(units),'Suma de cantidades'],['Pedidos',number.format(orders),'order_id distintos'],['Clientes',number.format(customers),'user_id distintos'],['Ingreso por pedido',money.format(revenue/(orders||1)),'Revenue / pedidos'],['Precio por unidad',money.format(revenue/(units||1)),'Revenue / unidades'],['País líder',leaders[0],'Por revenue'],['Canal líder',leaders[1],'Por revenue'],['Categoría líder',leaders[2],'Por revenue'],['Pedidos entregados',(delivered*100).toFixed(1)+'%','Pedidos entregados / total']];document.getElementById('kpis').innerHTML=cards.map(c=>`<article class="kpi"><span>${{c[0]}}</span><strong>${{c[1]}}</strong><small>${{c[2]}}</small></article>`).join('');
const monthly=group(sales,'year_month').sort((a,b)=>a[0].localeCompare(b[0]));Plotly.react('revenueTime',[{{type:'scatter',mode:'lines+markers',x:monthly.map(d=>d[0]),y:monthly.map(d=>d[1]),line:{{color:'#111',width:3}},marker:{{color:'#d7ff3f',size:9,line:{{color:'#111',width:1}}}},hovertemplate:'%{{x}}<br>$%{{y:,.0f}}<extra></extra>'}}],layout('Evolución mensual de ingresos'),cfg);
const unitsMonthly=group(sales,'year_month','quantity').sort((a,b)=>a[0].localeCompare(b[0]));Plotly.react('unitsTime',[{{type:'bar',x:unitsMonthly.map(d=>d[0]),y:unitsMonthly.map(d=>d[1]),marker:{{color:'#707070'}},hovertemplate:'%{{x}}<br>%{{y:,.0f}} unidades<extra></extra>'}}],layout('Unidades por mes'),cfg);
bar('countryChart',group(sales,'country'),'Ingresos por país');const channels=group(sales,'channel');Plotly.react('channelChart',[{{type:'pie',labels:channels.map(d=>d[0]),values:channels.map(d=>d[1]),hole:.58,marker:{{colors}},textinfo:'label+percent',hovertemplate:'%{{label}}<br>$%{{value:,.0f}}<extra></extra>'}}],layout('Mezcla de canales',{{showlegend:false,margin:{{l:20,r:20,t:58,b:20}}}}),cfg);bar('segmentChart',group(sales,'price_segment'),'Ingresos por segmento de precio');bar('categoryChart',group(sales,'category'),'Ingresos por categoría',true);bar('productChart',group(sales,'product_name').slice(0,10).reverse(),'Top 10 productos',true);bar('customerChart',group(sales,'customer_name').slice(0,10).reverse(),'Top 10 clientes',true);
const countries=unique('country'),channelsAll=unique('channel'),matrix=countries.map(c=>channelsAll.map(ch=>sum(sales.filter(d=>d.country===c&&d.channel===ch),'revenue')));Plotly.react('heatmapChart',[{{type:'heatmap',x:channelsAll,y:countries,z:matrix,colorscale:[[0,'#f4f4f2'],[1,'#111']],hovertemplate:'%{{y}} · %{{x}}<br>$%{{z:,.0f}}<extra></extra>'}}],layout('Matriz país × canal'),cfg);
}}
function renderModel(){{if(!PROFILES.length){{document.getElementById('modelNote').textContent='Ejecuta scripts/run_model.py y reconstruye el dashboard para integrar la segmentación.';return;}}document.getElementById('modelNote').innerHTML=`Modelo seleccionado: <strong>${{METRICS.selected_model}}</strong> con <strong>${{METRICS.clusters}} segmentos</strong>. Silhouette = <strong>${{METRICS.silhouette.toFixed(3)}}</strong>. La PCA explica <strong>${{(METRICS.pca_explained_variance.reduce((a,b)=>a+b,0)*100).toFixed(1)}}%</strong> de la varianza en dos ejes; se usa solo como proyección visual.`;
bar('mlCustomers',PROFILES.map(d=>[d.segment,d.customers]),'Clientes por segmento');bar('mlRevenue',PROFILES.map(d=>[d.segment,d.total_revenue]),'Ingresos por segmento');const segments=[...new Set(PCA.map(d=>d.segment))];Plotly.react('mlPca',segments.map((s,i)=>{{const r=PCA.filter(d=>d.segment===s);return{{type:'scatter',mode:'markers',name:s,x:r.map(d=>d.pca_1),y:r.map(d=>d.pca_2),text:r.map(d=>d.customer_name),marker:{{size:9,color:colors[i%colors.length],line:{{color:'#fff',width:1}}}},hovertemplate:'%{{text}}<extra>'+s+'</extra>'}}}}),layout('Proyección PCA de clientes',{{legend:{{orientation:'h',y:-.24}}}}),cfg);
document.getElementById('profileTable').innerHTML='<thead><tr><th>Segmento</th><th>Clientes</th><th>Participación</th><th>Revenue</th><th>Pedidos prom.</th><th>Ticket prom.</th><th>Acción</th></tr></thead><tbody>'+PROFILES.map(d=>`<tr><td><strong>${{d.segment}}</strong></td><td>${{d.customers}}</td><td>${{(d.customer_share*100).toFixed(1)}}%</td><td>${{money.format(d.total_revenue)}}</td><td>${{d.average_orders.toFixed(1)}}</td><td>${{money.format(d.average_ticket)}}</td><td>${{d.recommended_action}}</td></tr>`).join('')+'</tbody>';}}
update();renderModel();
// Al volver con el historial, algunos navegadores restauran los valores de los
// selectores después del primer render. pageshow resincroniza KPIs y gráficos.
window.addEventListener('pageshow',()=>setTimeout(update,0));
</script></body></html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
