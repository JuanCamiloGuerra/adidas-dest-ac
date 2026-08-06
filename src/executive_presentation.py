"""Presentación ejecutiva HTML basada en la tabla maestra consolidada.

Entradas: pedidos enriquecidos, perfiles de clientes y escenarios de cantidad.
Salida: narrativa visual C-level con hallazgos, decisiones y plan de acción.
Dependencias: pandas y biblioteca estándar.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import pandas as pd

from src.site_navigation import navigation_css, navigation_html


def _money(value: float, compact: bool = False) -> str:
    """Formatea USD para lectura ejecutiva."""

    if compact and abs(value) >= 1_000_000:
        return f"USD {value / 1_000_000:.2f} M"
    if compact and abs(value) >= 1_000:
        return f"USD {value / 1_000:.0f} K"
    return f"USD {value:,.0f}"


def _pct(value: float) -> str:
    return f"{value:.1%}"


def _bars(frame: pd.DataFrame, label: str, value: str, total: float, note: str = "") -> str:
    """Crea barras horizontales comparables y accesibles."""

    maximum = float(frame[value].max()) if len(frame) else 1.0
    rows = []
    for row in frame.itertuples(index=False):
        record = row._asdict()
        amount = float(record[value])
        detail = html.escape(str(record.get(note, ""))) if note else ""
        rows.append(
            f'''<div class="bar-row"><div class="bar-label"><b>{html.escape(str(record[label]))}</b>
            <span>{_money(amount, True)} · {_pct(amount / total)}</span></div>
            <div class="track"><i style="width:{amount / maximum * 100:.1f}%"></i></div>
            {f'<small>{detail}</small>' if detail else ''}</div>'''
        )
    return "".join(rows)


def build_executive_presentation_html(
    orders: pd.DataFrame,
    profiles: pd.DataFrame,
    scenarios: pd.DataFrame,
    model_metrics: dict[str, Any],
    output_path: Path,
) -> None:
    """Genera una presentación ejecutiva navegable y autónoma."""

    frame = orders.copy()
    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    sales = frame[frame["valid_sales_flag"].astype(bool)].copy()
    gross = float(sales["revenue"].sum())
    units = float(sales["quantity"].sum())
    order_count = int(sales["order_id"].nunique())
    buyers = int(sales["user_id"].nunique())

    status = (
        sales.groupby("order_status", as_index=False)
        .agg(value=("revenue", "sum"), orders=("order_id", "nunique"))
    )
    status_map = status.set_index("order_status")["value"].to_dict()
    delivered = float(status_map.get("delivered", 0))
    cancelled = float(status_map.get("cancelled", 0))
    pipeline = float(status_map.get("confirmed", 0) + status_map.get("shipped", 0))
    delivered_share = delivered / gross
    cancelled_share = cancelled / gross
    pipeline_share = pipeline / gross

    country = (
        sales.groupby("country", as_index=False)
        .agg(value=("revenue", "sum"), orders=("order_id", "nunique"))
        .sort_values("value", ascending=False)
    )
    country["detail"] = country["orders"].map(lambda value: f"{value} pedidos")
    channel = (
        sales.groupby("channel", as_index=False)
        .agg(value=("revenue", "sum"), orders=("order_id", "nunique"))
        .sort_values("value", ascending=False)
    )
    category = (
        sales.groupby("category", as_index=False)
        .agg(value=("revenue", "sum"), units=("quantity", "sum"))
        .sort_values("value", ascending=False)
    )
    price = (
        sales.groupby("price_segment", as_index=False)
        .agg(value=("revenue", "sum"), units=("quantity", "sum"))
        .sort_values("value", ascending=False)
    )

    channel_status = sales.pivot_table(
        index="channel", columns="order_status", values="revenue", aggfunc="sum", fill_value=0
    )
    channel_status["total"] = channel_status.sum(axis=1)
    channel_status["delivered_share"] = channel_status.get("delivered", 0) / channel_status["total"]
    channel_status["cancel_share"] = channel_status.get("cancelled", 0) / channel_status["total"]
    channel_status = channel_status.reset_index()

    country_status = sales.pivot_table(
        index="country", columns="order_status", values="revenue", aggfunc="sum", fill_value=0
    )
    country_status["total"] = country_status.sum(axis=1)
    country_status["delivered_share"] = country_status.get("delivered", 0) / country_status["total"]
    country_status["cancel_share"] = country_status.get("cancelled", 0) / country_status["total"]
    country_status = country_status.reset_index()

    product = (
        sales.groupby(["product_id", "product_name", "category", "brand"], as_index=False)
        .agg(value=("revenue", "sum"), units=("quantity", "sum"))
        .sort_values("value", ascending=False)
    )
    top10_product_share = float(product.head(10)["value"].sum() / gross)
    top10_footwear = int(product.head(10)["category"].eq("Footwear").sum())
    top_product = product.iloc[0]

    customer = (
        sales.groupby(["user_id", "customer_name", "country"], as_index=False)
        .agg(value=("revenue", "sum"), orders=("order_id", "nunique"))
        .sort_values("value", ascending=False)
    )
    top10_customer_share = float(customer.head(10)["value"].sum() / gross)
    nonbuyers = max(0, 100 - buyers)
    profile = profiles.copy()
    profile["revenue_share"] = profile["total_revenue"] / profile["total_revenue"].sum()
    strategic = profile.sort_values("total_revenue", ascending=False).iloc[0]
    reactivation = profile.sort_values("total_revenue", ascending=False).iloc[-1]

    sales["discount_band"] = pd.cut(
        sales["discount_percentage"], [-0.01, 5, 10, 15, 20, 25],
        labels=["0–5%", "5–10%", "10–15%", "15–20%", "20–25%"],
        include_lowest=True,
    )
    discounts = (
        sales.groupby("discount_band", observed=True, as_index=False)
        .agg(value=("revenue", "sum"), avg_quantity=("quantity", "mean"))
    )
    discount_quantity_corr = float(sales[["discount_percentage", "quantity"]].corr().iloc[0, 1])
    discount_revenue_corr = float(sales[["discount_percentage", "revenue"]].corr().iloc[0, 1])

    monthly = sales.groupby("year_month", as_index=False).agg(value=("revenue", "sum"), orders=("order_id", "nunique"))
    monthly = monthly.sort_values("year_month")
    monthly_cv = float(monthly["value"].std() / monthly["value"].mean())
    best_month = monthly.loc[monthly["value"].idxmax()]
    lowest_month = monthly.loc[monthly["value"].idxmin()]
    quarters = (
        sales.assign(period="Q" + sales["quarter"].astype("Int64").astype(str))
        .groupby("period", as_index=False).agg(value=("revenue", "sum"))
    )

    category_sets = sales.groupby("order_id")["category"].agg(lambda values: set(values))
    multi_category_share = float(category_sets.map(len).ge(2).mean())
    footwear_orders = category_sets.map(lambda values: "Footwear" in values)
    footwear_count = int(footwear_orders.sum())
    attach = {
        other: float(category_sets.map(lambda values: "Footwear" in values and other in values).sum() / footwear_count)
        for other in ["Accessories", "Apparel", "Equipment"]
    }

    scenario_max = float(scenarios["change_vs_original_pct"].max() / 100)
    scenario_min = float(
        scenarios.loc[scenarios["scenario"].str.contains("Mínimo"), "change_vs_original_pct"].iloc[0] / 100
    )
    rf_r2 = float(model_metrics.get("quantity_r2", -0.009))
    potential_recovery = gross * max(cancelled_share - 0.09, 0)

    country_bars = _bars(country, "country", "value", gross, "detail")
    channel_bars = _bars(channel, "channel", "value", gross)
    category_bars = _bars(category, "category", "value", gross)
    price_bars = _bars(price, "price_segment", "value", gross)
    discount_bars = _bars(discounts, "discount_band", "value", gross)
    quarter_bars = _bars(quarters, "period", "value", gross)

    channel_cards = "".join(
        f'''<article class="mini-card"><span>{html.escape(str(row.channel))}</span>
        <strong>{_pct(float(row.delivered_share))}</strong><small>valor entregado</small>
        <div class="mini-line"><i style="width:{float(row.delivered_share)*100:.1f}%"></i></div>
        <em>{_pct(float(row.cancel_share))} cancelado</em></article>'''
        for row in channel_status.sort_values("delivered_share", ascending=False).itertuples()
    )
    country_table = "".join(
        f"<tr><td><b>{html.escape(str(row.country))}</b></td><td>{_money(float(row.total), True)}</td>"
        f"<td>{_pct(float(row.delivered_share))}</td><td>{_pct(float(row.cancel_share))}</td></tr>"
        for row in country_status.sort_values("total", ascending=False).itertuples()
    )
    top_products = "".join(
        f"<tr><td>{index}</td><td><b>{html.escape(str(row.product_name))}</b><small>{html.escape(str(row.brand))}</small></td>"
        f"<td>{html.escape(str(row.category))}</td><td>{_money(float(row.value), True)}</td></tr>"
        for index, row in enumerate(product.head(5).itertuples(), 1)
    )

    document = r'''<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SportRetail LAM · Presentación ejecutiva</title>
<style>
:root{--black:#000;--white:#fff;--fog:#f1f1ee;--signal:#d7ff3f;--orange:#ff6037;--blue:#3162ff;--muted:#6b6b6b;--line:#c8c8c1}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-snap-type:y proximity}body{margin:0;background:#000;color:#111;font-family:Arial,Helvetica,sans-serif}.progress{position:fixed;top:58px;left:0;height:4px;background:var(--signal);z-index:1100;width:0;transition:width .25s}
.slide{min-height:100vh;scroll-snap-align:start;background:var(--fog);padding:94px max(32px,calc((100vw - 1380px)/2)) 55px;display:flex;flex-direction:column;justify-content:center;position:relative;overflow:hidden}.slide.dark{background:#000;color:#fff}.slide.signal{background:var(--signal)}.slide-no{position:absolute;right:30px;top:78px;font-size:10px;font-weight:900;letter-spacing:.14em;color:#888}.eyebrow{font-size:10px;font-weight:900;letter-spacing:.17em;text-transform:uppercase;color:var(--orange)}.dark .eyebrow{color:var(--signal)}h1{font-size:clamp(62px,9vw,136px);line-height:.79;letter-spacing:-.08em;text-transform:uppercase;margin:20px 0 35px}h2{font-size:clamp(42px,6vw,82px);line-height:.85;letter-spacing:-.065em;text-transform:uppercase;margin:15px 0 28px}h3{font-size:24px;letter-spacing:-.04em;margin:8px 0 12px}.lead{font-size:clamp(17px,1.6vw,23px);line-height:1.45;max-width:930px;color:#4f4f4f}.dark .lead{color:#bbb}.thesis{display:grid;grid-template-columns:1.3fr .7fr;gap:45px;align-items:end}.hero-graphic svg{width:100%}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#000;border:1px solid #000;margin-top:30px}.kpi{background:#fff;color:#111;padding:22px;min-height:150px}.kpi.signal{background:var(--signal);color:#000}.kpi.orange{background:var(--orange);color:#fff}.kpi span,.label{font-size:9px;font-weight:900;letter-spacing:.1em;text-transform:uppercase}.kpi strong{display:block;font-size:clamp(27px,3vw,44px);letter-spacing:-.06em;margin:24px 0 5px}.kpi small{color:#555}.orange small{color:#fff}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px;margin-top:24px}.s4{grid-column:span 4}.s5{grid-column:span 5}.s6{grid-column:span 6}.s7{grid-column:span 7}.s8{grid-column:span 8}.s12{grid-column:span 12}.card{background:#fff;color:#111;border:1px solid #aaa;padding:24px}.card.black{background:#000;color:#fff;border-color:#000}.card.signal{background:var(--signal);color:#000;border:2px solid #000}.card.orange{background:var(--orange);color:#fff;border-color:#000}.card p{color:#444}.card.black p{color:#bbb}.card.signal p{color:#222}.big{font-size:clamp(38px,5vw,70px);font-weight:900;letter-spacing:-.07em;line-height:.9}.statement{font-size:clamp(25px,3.4vw,48px);line-height:1.18;letter-spacing:-.05em;font-weight:900}.statement mark{background:var(--signal);color:#000;padding:0 .1em;-webkit-box-decoration-break:clone;box-decoration-break:clone}.closing-statement{line-height:1.22}.closing-statement mark{display:inline-block;margin-top:.15em;padding:.05em .12em .1em}
.status-stack{display:flex;height:90px;border:2px solid #000;margin:25px 0 16px}.status-stack div{padding:16px 12px;display:flex;flex-direction:column;justify-content:space-between;min-width:0}.status-stack b{font-size:18px}.status-stack small{font-size:9px;font-weight:900;text-transform:uppercase}.delivered{background:var(--signal)}.pipeline{background:var(--blue);color:#fff}.cancelled{background:var(--orange);color:#fff}.footnote{font-size:11px;color:#666;max-width:950px}
.bar-row{margin:18px 0}.bar-label{display:flex;justify-content:space-between;gap:15px;font-size:12px}.bar-label span{color:#666}.track{height:12px;background:#deded9;margin-top:7px}.track i{display:block;height:100%;background:#000}.bar-row small{display:block;color:#777;margin-top:4px}.dark .track{background:#333}.dark .track i{background:var(--signal)}.dark .bar-label span{color:#aaa}
.mini-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.mini-card{background:#fff;border:2px solid #000;padding:22px}.mini-card span{display:block;font-size:10px;font-weight:900;text-transform:uppercase}.mini-card strong{display:block;font-size:45px;letter-spacing:-.06em;margin-top:15px}.mini-card small{color:#666}.mini-card em{font-size:11px;color:#555;font-style:normal}.mini-line{height:9px;background:#ddd;margin:15px 0 8px}.mini-line i{height:100%;display:block;background:var(--signal)}
table{border-collapse:collapse;width:100%;background:#fff;color:#111;font-size:12px}th{background:#000;color:#fff;text-transform:uppercase;font-size:9px;letter-spacing:.08em}th,td{padding:13px;text-align:left;border-bottom:1px solid #ccc}td small{display:block;color:#666;margin-top:3px}.donut{width:230px;aspect-ratio:1;border-radius:50%;background:conic-gradient(var(--signal) 0 97.7%,#333 97.7%);display:grid;place-items:center;margin:auto}.donut:after{content:"97,7%";width:145px;aspect-ratio:1;border-radius:50%;background:#000;color:#fff;display:grid;place-items:center;font-size:34px;font-weight:900}
.priority{display:grid;grid-template-columns:90px 1fr 220px;gap:22px;padding:22px 0;border-top:1px solid #999;align-items:center}.priority:first-child{border-top:4px solid #000}.priority-no{font-size:52px;font-weight:900;letter-spacing:-.07em}.priority p{margin:3px 0;color:#555}.priority aside{font-size:11px;font-weight:900;text-transform:uppercase;background:#000;color:#fff;padding:14px}.roadmap{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#000;border:2px solid #000}.roadmap article{background:#fff;padding:22px;min-height:310px}.roadmap article:first-child{background:var(--signal)}.roadmap b{font-size:34px;display:block;letter-spacing:-.05em}.roadmap ul{padding-left:18px;color:#555}.roadmap li{margin:12px 0}.ask{display:grid;grid-template-columns:70px 1fr;gap:20px;padding:20px 0;border-top:1px solid #555}.ask b{font-size:38px;color:var(--signal)}.ask h3{margin:0}.ask p{color:#aaa;margin:5px 0}
.nav-dots{position:fixed;right:14px;top:50%;transform:translateY(-50%);z-index:40;display:flex;flex-direction:column;gap:7px}.nav-dots a{width:8px;height:8px;border:1px solid #888;background:#000}.nav-dots a.active{background:var(--signal);border-color:#000;transform:scale(1.35)}.controls{position:fixed;bottom:18px;right:20px;z-index:40;display:flex}.controls button{border:1px solid #555;background:#000;color:#fff;padding:11px 15px;cursor:pointer}.controls button:hover{background:var(--signal);color:#000}
@media(max-width:900px){html{scroll-snap-type:none}.slide{min-height:auto;padding:90px 18px 55px}.thesis{grid-template-columns:1fr}.hero-graphic{display:none}.kpis{grid-template-columns:1fr 1fr}.s4,.s5,.s6,.s7,.s8{grid-column:span 12}.mini-grid,.roadmap{grid-template-columns:1fr}.priority{grid-template-columns:55px 1fr}.priority aside{grid-column:2}.nav-dots,.controls{display:none}}@media(max-width:520px){.kpis{grid-template-columns:1fr}.status-stack{height:auto;display:block}.status-stack div{min-height:70px}}
@media print{html{scroll-snap-type:none}.global-nav,.nav-dots,.controls,.progress{display:none}.slide{page-break-after:always;min-height:100vh;padding:50px}.slide:last-child{page-break-after:auto}}
__GLOBAL_NAV_CSS__
</style></head><body>
__GLOBAL_NAV__<div class="progress" id="progress"></div><nav class="nav-dots" id="dots"></nav><div class="controls"><button id="prev" aria-label="Anterior">←</button><button id="next" aria-label="Siguiente">→</button><button onclick="window.print()" aria-label="Imprimir o guardar PDF">PDF</button></div>

<section class="slide dark" id="s01"><span class="slide-no">01 / 15</span><div class="thesis"><div><span class="eyebrow">Revisión ejecutiva · datos tratados como operación real</span><h1>Convertir<br>demanda en<br>resultado.</h1><p class="lead">La oportunidad no está solamente en vender más. Está en distinguir demanda, pipeline e ingreso realizado; proteger los motores actuales y eliminar fricción en la conversión.</p></div><div class="hero-graphic"><svg viewBox="0 0 500 480" role="img" aria-label="Demanda pasando por un embudo hacia resultados"><path d="M35 40H465L340 250V410H160V250Z" fill="#3162ff"/><rect x="80" y="70" width="340" height="45" fill="#d7ff3f"/><rect x="115" y="145" width="270" height="36" fill="#fff"/><rect x="150" y="220" width="200" height="28" fill="#ff6037"/><text x="250" y="100" font-family="Arial" font-weight="bold" text-anchor="middle">VALOR BRUTO DE PEDIDOS</text><text x="250" y="169" font-family="Arial" font-weight="bold" text-anchor="middle">PIPELINE</text><text x="250" y="240" font-family="Arial" font-weight="bold" text-anchor="middle">FRICCIÓN</text><text x="250" y="350" fill="#fff" font-family="Arial" font-size="25" font-weight="bold" text-anchor="middle">ENTREGADO</text></svg></div></div></section>

<section class="slide" id="s02"><span class="slide-no">02 / 15</span><span class="eyebrow">La tesis en cuatro cifras</span><h2>El negocio genera demanda.<br>La conversión es el reto.</h2><div class="kpis"><article class="kpi"><span>Valor bruto de pedidos</span><strong>__GROSS__</strong><small>Todos los estados; no equivale a caja.</small></article><article class="kpi signal"><span>Valor entregado</span><strong>__DELIVERED__</strong><small>__DELIVERED_SHARE__ del total observado.</small></article><article class="kpi"><span>Confirmado + enviado</span><strong>__PIPELINE__</strong><small>__PIPELINE_SHARE__ todavía expuesto.</small></article><article class="kpi orange"><span>Valor cancelado</span><strong>__CANCELLED__</strong><small>__CANCELLED_SHARE__ de la demanda.</small></article></div><p class="statement">La primera decisión es <mark>renombrar revenue</mark>: “valor bruto de pedidos” hasta que el estado entregado confirme realización.</p><p class="footnote">La tabla calcula unit_price × quantity para cualquier estado. Es una medida válida de demanda registrada, pero una interpretación financiera requiere estado, pago, devolución y reconocimiento contable.</p></section>

<section class="slide dark" id="s03"><span class="slide-no">03 / 15</span><span class="eyebrow">Qué se hizo y por qué</span><h2>Construimos confianza<br>antes de interpretar.</h2><div class="grid"><article class="card black s4"><span class="label">01 · Captura</span><h3>API completa</h3><p>Se verificó disponibilidad y paginación para recuperar 120 productos, 100 clientes y 200 pedidos sin depender de la primera página.</p></article><article class="card black s4"><span class="label">02 · Contexto</span><h3>Una línea por producto-pedido</h3><p>Se desanidaron 733 líneas y se enriquecieron con catálogo y cliente sin multiplicar registros.</p></article><article class="card black s4"><span class="label">03 · Confianza</span><h3>Calidad trazable</h3><p>Los nulos y extremos se marcaron; no se borraron ni se sustituyeron silenciosamente.</p></article><article class="card black s4"><span class="label">04 · Lectura</span><h3>KPIs y relaciones</h3><p>Se analizaron mercados, canales, categorías, clientes, estados, precios y tiempo.</p></article><article class="card black s4"><span class="label">05 · Incertidumbre</span><h3>Escenarios, no ficción</h3><p>Las 12 cantidades ausentes se separaron en escenarios; la fuente original quedó intacta.</p></article><article class="card black s4"><span class="label">06 · Decisión</span><h3>Segmentos accionables</h3><p>Los clientes se agruparon para orientar retención y reactivación, sin presentar ML como certeza.</p></article></div><p class="footnote" style="color:#999">Resultado arquitectónico: fuente REST → snapshots → tabla maestra → calidad → persistencia → análisis → modelos → comunicación. La arquitectura es reproducible; la siguiente madurez es operacionalizar métricas, responsables y frecuencia.</p></section>

<section class="slide" id="s04"><span class="slide-no">04 / 15</span><span class="eyebrow">Embudo operativo</span><h2>USD 2,33 M aún no son<br>resultado entregado.</h2><div class="status-stack"><div class="delivered" style="width:__DELIVERED_WIDTH__"><b>__DELIVERED__</b><small>Entregado · __DELIVERED_SHARE__</small></div><div class="pipeline" style="width:__PIPELINE_WIDTH__"><b>__PIPELINE__</b><small>Pipeline · __PIPELINE_SHARE__</small></div><div class="cancelled" style="width:__CANCELLED_WIDTH__"><b>__CANCELLED__</b><small>Cancelado · __CANCELLED_SHARE__</small></div></div><div class="grid"><article class="card signal s6"><span class="label">Oportunidad inmediata</span><div class="big">__POTENTIAL__</div><p>Techo indicativo de valor recuperable si la participación cancelada bajara de __CANCELLED_SHARE__ a 9%, manteniendo el mismo volumen bruto. No es un forecast; es una referencia para priorizar.</p></article><article class="card s6"><span class="label">Acción de dirección</span><h3>Instalar un “order conversion review” semanal</h3><p>Separar confirmado, enviado, entregado y cancelado; medir antigüedad del pipeline, causa de cancelación, promesa logística y dueño de cada excepción.</p></article></div></section>

<section class="slide" id="s05"><span class="slide-no">05 / 15</span><span class="eyebrow">Canales</span><h2>El canal líder vende más.<br>No todos convierten igual.</h2><div class="grid"><article class="card s6"><h3>Valor bruto por canal</h3>__CHANNEL_BARS__</article><article class="card s6"><h3>Valor entregado por canal</h3><div class="mini-grid">__CHANNEL_CARDS__</div></article></div><div class="card orange" style="margin-top:12px"><h3>Direct Sales requiere intervención</h3><p>Solo __DIRECT_DELIVERED__ de su valor aparece entregado, frente a __ECOM_DELIVERED__ en E-commerce B2B y __DISTRIBUTOR_DELIVERED__ en Distributor. Su participación cancelada es __DIRECT_CANCEL__. Prioridad: revisar promesa, crédito, disponibilidad y seguimiento comercial antes de aumentar captación.</p></div></section>

<section class="slide" id="s06"><span class="slide-no">06 / 15</span><span class="eyebrow">Mercados</span><h2>Colombia lidera.<br>La calidad del pipeline varía.</h2><div class="grid"><article class="card s6"><h3>Valor bruto por país</h3>__COUNTRY_BARS__</article><article class="card s6"><h3>Conversión observada</h3><table><thead><tr><th>Mercado</th><th>Valor</th><th>Entregado</th><th>Cancelado</th></tr></thead><tbody>__COUNTRY_TABLE__</tbody></table></article></div><p class="statement" style="margin-bottom:0">Proteger Colombia, <mark>replicar la conversión de Perú</mark> y depurar el pipeline de México y Argentina.</p><p class="footnote">Perú muestra 61% del valor entregado, pero 18% cancelado: rendimiento y fricción coexisten. México presenta solo 5% cancelado, aunque 60% permanece confirmado o enviado; puede ser desfase de corte, no necesariamente incumplimiento.</p></section>

<section class="slide dark" id="s07"><span class="slide-no">07 / 15</span><span class="eyebrow">Portafolio</span><h2>Footwear es el motor.<br>El volumen es más diverso.</h2><div class="grid"><article class="card black s5"><h3>Valor por categoría</h3>__CATEGORY_BARS__</article><article class="card black s7"><table><thead><tr><th>#</th><th>Producto</th><th>Categoría</th><th>Valor</th></tr></thead><tbody>__TOP_PRODUCTS__</tbody></table></article></div><div class="grid"><article class="card signal s4"><span class="label">Footwear</span><div class="big">__FOOTWEAR_SHARE__</div><p>del valor bruto.</p></article><article class="card s4"><span class="label">Top 10 productos</span><div class="big">__TOP_PRODUCT_SHARE__</div><p>del valor: concentración manejable.</p></article><article class="card s4"><span class="label">Top 10 por valor</span><div class="big">__TOP_FOOTWEAR__/10</div><p>son Footwear.</p></article></div><p class="footnote" style="color:#aaa">El producto #1 es __TOP_PRODUCT__ con __TOP_PRODUCT_VALUE__. Recomendación: asegurar disponibilidad y margen de los héroes, pero evitar que la estrategia de surtido se vuelva monodependiente.</p></section>

<section class="slide" id="s08"><span class="slide-no">08 / 15</span><span class="eyebrow">Cesta y venta cruzada</span><h2>La demanda ya acepta<br>compras multicategoría.</h2><div class="kpis"><article class="kpi signal"><span>Pedidos con 2+ categorías</span><strong>__MULTI_CATEGORY__</strong><small>Base favorable para bundles.</small></article><article class="kpi"><span>Footwear + Accessories</span><strong>__ATTACH_ACC__</strong><small>de pedidos con Footwear.</small></article><article class="kpi"><span>Footwear + Apparel</span><strong>__ATTACH_APP__</strong><small>de pedidos con Footwear.</small></article><article class="kpi"><span>Footwear + Equipment</span><strong>__ATTACH_EQUIP__</strong><small>de pedidos con Footwear.</small></article></div><div class="grid"><article class="card s7"><h3>Estrategia propuesta: “hero + attach”</h3><p>Usar Footwear como producto tractor y diseñar bundles B2B por tipo de minorista: reposición de calzado + accesorios de rotación, kits de entrenamiento y combinaciones de exhibición. Medir incremento de categorías por pedido y margen, no solo unidades.</p></article><article class="card black s5"><span class="label">Principio</span><div class="statement">No descontar el héroe si el bundle puede elevar el valor de la cesta.</div></article></div></section>

<section class="slide" id="s09"><span class="slide-no">09 / 15</span><span class="eyebrow">Clientes</span><h2>La cartera tiene tres frentes:<br>retener, reactivar, activar.</h2><div class="grid"><article class="card black s4"><div class="donut"></div><p style="text-align:center">del valor proviene del segmento de socios estratégicos.</p></article><article class="card s8"><div class="priority"><div class="priority-no">72</div><div><h3>Socios estratégicos</h3><p>__STRATEGIC_REVENUE__ · ticket medio __STRATEGIC_TICKET__.</p></div><aside>Retención ejecutiva + acuerdos de surtido</aside></div><div class="priority"><div class="priority-no">13</div><div><h3>Reactivación prioritaria</h3><p>Solo __REACTIVATION_SHARE__ del valor y mayor recencia.</p></div><aside>Diagnóstico de abandono + oferta dirigida</aside></div><div class="priority"><div class="priority-no">__NONBUYERS__</div><div><h3>Usuarios sin compra observada</h3><p>Existen en la base de clientes, pero no aparecen como compradores.</p></div><aside>Programa de activación y calificación</aside></div></article></div><p class="footnote">Los 10 clientes principales concentran __TOP_CUSTOMER_SHARE__: suficiente para justificar planes de cuenta, sin una dependencia extrema de una sola cuenta (la mayor representa aproximadamente 4%).</p></section>

<section class="slide" id="s10"><span class="slide-no">10 / 15</span><span class="eyebrow">Precio y descuentos</span><h2>Más descuento no muestra<br>más demanda.</h2><div class="grid"><article class="card s7"><h3>Valor por banda de descuento</h3>__DISCOUNT_BARS__</article><article class="card signal s5"><span class="label">Correlación simple</span><div class="big">__DISC_Q_CORR__</div><p>descuento vs. cantidad.</p><div class="big" style="margin-top:28px">__DISC_R_CORR__</div><p>descuento vs. valor de línea.</p></article></div><div class="grid"><article class="card s6"><h3>Lectura correcta</h3><p>No aparece una relación lineal material. Esto no demuestra que el descuento no funcione: mezcla producto, precio, cliente y canal, y la API no confirma si <code>unit_price</code> ya incorpora el descuento.</p></article><article class="card black s6"><h3>Decisión recomendada</h3><p>Crear identificador de campaña, precio de lista, precio neto, costo, margen y grupo de control. Evaluar uplift y margen incremental antes de institucionalizar promociones.</p></article></div></section>

<section class="slide" id="s11"><span class="slide-no">11 / 15</span><span class="eyebrow">Tiempo</span><h2>Año equilibrado.<br>Meses volátiles.</h2><div class="grid"><article class="card s6"><h3>Participación trimestral</h3>__QUARTER_BARS__</article><article class="card s6"><div class="kpis" style="grid-template-columns:1fr 1fr;margin:0"><article class="kpi signal"><span>Mejor mes</span><strong>__BEST_MONTH__</strong><small>__BEST_VALUE__</small></article><article class="kpi"><span>Mes más bajo</span><strong>__LOW_MONTH__</strong><small>__LOW_VALUE__</small></article></div><div class="statement" style="margin-top:32px">Variabilidad mensual: __MONTHLY_CV__.</div><p>El mejor mes casi duplica al menor. Con una sola anualidad no debe declararse estacionalidad; sí debe investigarse calendario comercial, disponibilidad y avance del pipeline.</p></article></div></section>

<section class="slide dark" id="s12"><span class="slide-no">12 / 15</span><span class="eyebrow">Incertidumbre y modelos</span><h2>El modelo informa.<br>No reemplaza el juicio.</h2><div class="grid"><article class="card black s4"><span class="label">12 cantidades nulas</span><div class="big">__SCENARIO_MIN__ → __SCENARIO_MAX__</div><p>rango de impacto sobre el total entre escenario mínimo y máximo.</p></article><article class="card black s4"><span class="label">Random Forest de quantity</span><div class="big">R² __RF_R2__</div><p>No supera una referencia simple; se usa solo como sensibilidad.</p></article><article class="card black s4"><span class="label">Segmentación oficial</span><div class="big">__SILHOUETTE__</div><p>silhouette moderado; útil para acción, no para “verdad natural”.</p></article></div><div class="card signal" style="margin-top:12px"><h3>Decisión prudente</h3><p>El rango por cantidades faltantes es pequeño frente al reto de conversión por estado. La prioridad ejecutiva no debe ser perfeccionar la imputación; debe ser corregir la semántica de revenue, capturar causas operativas y mejorar el cierre del pipeline.</p></div></section>

<section class="slide" id="s13"><span class="slide-no">13 / 15</span><span class="eyebrow">Cinco prioridades</span><h2>De análisis<br>a ejecución.</h2><div><div class="priority"><div class="priority-no">01</div><div><h3>Gobernar la métrica</h3><p>Separar demanda bruta, valor confirmado, enviado, entregado, cancelado, facturado y cobrado.</p></div><aside>CFO + Comercial + Operaciones</aside></div><div class="priority"><div class="priority-no">02</div><div><h3>Recuperar conversión</h3><p>War room semanal para Direct Sales y pipeline envejecido; causa obligatoria de cancelación.</p></div><aside>Revenue Operations</aside></div><div class="priority"><div class="priority-no">03</div><div><h3>Proteger motores</h3><p>Disponibilidad y margen de Footwear, Colombia y cuentas estratégicas.</p></div><aside>Supply + Key Accounts</aside></div><div class="priority"><div class="priority-no">04</div><div><h3>Expandir cesta y base</h3><p>Bundles “hero + attach”, reactivación de 13 clientes y activación de __NONBUYERS__ sin compra.</p></div><aside>Growth + Trade Marketing</aside></div><div class="priority"><div class="priority-no">05</div><div><h3>Medir rentabilidad</h3><p>Agregar costo, margen, devolución, campaña e inventario histórico.</p></div><aside>Data + Finanzas</aside></div></div></section>

<section class="slide" id="s14"><span class="slide-no">14 / 15</span><span class="eyebrow">Plan de 12 meses</span><h2>Primero control.<br>Después escala.</h2><div class="roadmap"><article><span class="label">0–30 días</span><b>Definir</b><ul><li>Diccionario ejecutivo de métricas.</li><li>Dueño y SLA por estado.</li><li>Taxonomía de cancelaciones.</li><li>Baseline por país y canal.</li></ul></article><article><span class="label">31–90 días</span><b>Intervenir</b><ul><li>Plan Direct Sales.</li><li>Top cuentas y Footwear.</li><li>Activación de no compradores.</li><li>Piloto de bundles.</li></ul></article><article><span class="label">3–6 meses</span><b>Experimentar</b><ul><li>Promociones con control.</li><li>Servicio e inventario.</li><li>Margen por cliente-producto.</li><li>Alertas de pipeline.</li></ul></article><article><span class="label">6–12 meses</span><b>Escalar</b><ul><li>Histórico multianual.</li><li>Forecast defendible.</li><li>Monitoreo de segmentos.</li><li>Orquestación y SLAs de datos.</li></ul></article></div></section>

<section class="slide dark" id="s15"><span class="slide-no">15 / 15</span><span class="eyebrow">Decisiones solicitadas al comité</span><h2>Cuatro acuerdos<br>para mover el negocio.</h2><div class="ask"><b>01</b><div><h3>Aprobar la nueva jerarquía de métricas</h3><p>“Valor bruto de pedidos” deja de llamarse revenue realizado hasta validar entrega/facturación.</p></div></div><div class="ask"><b>02</b><div><h3>Patrocinar un frente de conversión</h3><p>Comercial, operaciones, crédito y supply con revisión semanal y dueño por excepción.</p></div></div><div class="ask"><b>03</b><div><h3>Priorizar dos pilotos</h3><p>Recuperación de Direct Sales y bundles Footwear + categoría complementaria.</p></div></div><div class="ask"><b>04</b><div><h3>Completar la información económica</h3><p>Costo, margen, devolución, pago, inventario histórico y campañas para decidir por rentabilidad.</p></div></div><p class="statement closing-statement" style="margin-top:35px">La ventaja no será tener más gráficos.<br><mark>Será cerrar mejor cada pedido.</mark></p></section>

<script>
const slides=[...document.querySelectorAll('.slide')],dots=document.getElementById('dots'),progress=document.getElementById('progress');let active=0;
slides.forEach((slide,index)=>{const link=document.createElement('a');link.href='#'+slide.id;link.setAttribute('aria-label','Ir a lámina '+(index+1));dots.appendChild(link)});
const links=[...dots.children];function update(index){active=index;links.forEach((link,i)=>link.classList.toggle('active',i===index));progress.style.width=((index+1)/slides.length*100)+'%'}
const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting)update(slides.indexOf(entry.target))}),{threshold:.6});slides.forEach(slide=>observer.observe(slide));
function move(delta){slides[Math.max(0,Math.min(slides.length-1,active+delta))].scrollIntoView({behavior:'smooth'})}
document.getElementById('prev').onclick=()=>move(-1);document.getElementById('next').onclick=()=>move(1);document.addEventListener('keydown',event=>{if(['ArrowRight','ArrowDown','PageDown'].includes(event.key))move(1);if(['ArrowLeft','ArrowUp','PageUp'].includes(event.key))move(-1)});update(0);
</script></body></html>'''

    channel_index = channel_status.set_index("channel")
    footwear_share = float(category.set_index("category").loc["Footwear", "value"] / gross)
    replacements = {
        "__GLOBAL_NAV_CSS__": navigation_css(),
        "__GLOBAL_NAV__": navigation_html("presentation", fixed=True),
        "__GROSS__": _money(gross, True), "__DELIVERED__": _money(delivered, True),
        "__PIPELINE__": _money(pipeline, True), "__CANCELLED__": _money(cancelled, True),
        "__DELIVERED_SHARE__": _pct(delivered_share), "__PIPELINE_SHARE__": _pct(pipeline_share),
        "__CANCELLED_SHARE__": _pct(cancelled_share),
        "__DELIVERED_WIDTH__": f"{delivered_share * 100:.1f}%",
        "__PIPELINE_WIDTH__": f"{pipeline_share * 100:.1f}%",
        "__CANCELLED_WIDTH__": f"{cancelled_share * 100:.1f}%",
        "__POTENTIAL__": _money(potential_recovery, True),
        "__CHANNEL_BARS__": channel_bars, "__CHANNEL_CARDS__": channel_cards,
        "__DIRECT_DELIVERED__": _pct(float(channel_index.loc["Direct Sales", "delivered_share"])),
        "__ECOM_DELIVERED__": _pct(float(channel_index.loc["E-commerce B2B", "delivered_share"])),
        "__DISTRIBUTOR_DELIVERED__": _pct(float(channel_index.loc["Distributor", "delivered_share"])),
        "__DIRECT_CANCEL__": _pct(float(channel_index.loc["Direct Sales", "cancel_share"])),
        "__COUNTRY_BARS__": country_bars, "__COUNTRY_TABLE__": country_table,
        "__CATEGORY_BARS__": category_bars, "__TOP_PRODUCTS__": top_products,
        "__FOOTWEAR_SHARE__": _pct(footwear_share), "__TOP_PRODUCT_SHARE__": _pct(top10_product_share),
        "__TOP_FOOTWEAR__": str(top10_footwear), "__TOP_PRODUCT__": html.escape(str(top_product["product_name"])),
        "__TOP_PRODUCT_VALUE__": _money(float(top_product["value"]), True),
        "__MULTI_CATEGORY__": _pct(multi_category_share), "__ATTACH_ACC__": _pct(attach["Accessories"]),
        "__ATTACH_APP__": _pct(attach["Apparel"]), "__ATTACH_EQUIP__": _pct(attach["Equipment"]),
        "__STRATEGIC_REVENUE__": _money(float(strategic["total_revenue"]), True),
        "__STRATEGIC_TICKET__": _money(float(strategic["average_ticket"]), True),
        "__REACTIVATION_SHARE__": _pct(float(reactivation["revenue_share"])),
        "__NONBUYERS__": str(nonbuyers), "__TOP_CUSTOMER_SHARE__": _pct(top10_customer_share),
        "__DISCOUNT_BARS__": discount_bars, "__DISC_Q_CORR__": f"{discount_quantity_corr:.2f}",
        "__DISC_R_CORR__": f"{discount_revenue_corr:.2f}", "__QUARTER_BARS__": quarter_bars,
        "__BEST_MONTH__": str(best_month["year_month"]), "__BEST_VALUE__": _money(float(best_month["value"]), True),
        "__LOW_MONTH__": str(lowest_month["year_month"]), "__LOW_VALUE__": _money(float(lowest_month["value"]), True),
        "__MONTHLY_CV__": _pct(monthly_cv), "__SCENARIO_MIN__": _pct(scenario_min),
        "__SCENARIO_MAX__": _pct(scenario_max), "__RF_R2__": f"{rf_r2:.3f}",
        "__SILHOUETTE__": f"{float(model_metrics.get('silhouette', 0)):.3f}",
    }
    for placeholder, value in replacements.items():
        document = document.replace(placeholder, value)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
