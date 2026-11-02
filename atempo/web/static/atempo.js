/* Atempo — interfaz (vanilla JS). Toda regla de negocio vive en el servidor. */
(() => {
"use strict";
const API = "/api/v1";
const VISTAS = [["Inicio","home"],["Mis materias","book"],["Actividades","check"],["Calendario","calendar"],["Mi carga académica","gauge"],["Recomendaciones","spark"],["Estadísticas","chart"],["Configuración","settings"]];
const COLORES = ["#6C5CE7","#00A6A6","#F08A5D","#E85D75","#3B82F6","#8B5CF6"];
const DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"];
const NIVEL = {Baja:{c:"#0F7A56",bg:"#E9F8F3"},Media:{c:"#8F4F00",bg:"#FFF5E7"},Alta:{c:"#B3303D",bg:"#FFF0F1"}};
const SIN_NIVEL = {c:"#5f5f78",bg:"#f0f0f4"};
const P = {
  home:'<path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10M9 20v-6h6v6"/>',
  book:'<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
  check:'<rect x="3" y="3" width="18" height="18" rx="4"/><path d="m8 12 2.6 2.6L16.5 9"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M16 3v4M8 3v4M3 10h18"/>',
  gauge:'<path d="M4.5 19a9 9 0 1 1 15 0"/><path d="m12 13 4-4M8 19h8"/>',
  spark:'<path d="m12 3-1.3 4.2a5 5 0 0 1-3.4 3.4L3 12l4.3 1.4a5 5 0 0 1 3.4 3.4L12 21l1.3-4.2a5 5 0 0 1 3.4-3.4L21 12l-4.3-1.4a5 5 0 0 1-3.4-3.4L12 3Z"/>',
  chart:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  settings:'<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
  plus:'<path d="M12 5v14M5 12h14"/>', clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  menu:'<path d="M4 7h16M4 12h16M4 17h16"/>', close:'<path d="m6 6 12 12M18 6 6 18"/>',
  edit:'<path d="m14 5 5 5M4 20l3.5-.7L19 7.8a2 2 0 0 0-2.8-2.8L4.7 16.5 4 20Z"/>',
  trash:'<path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6"/>', arrow:'<path d="m9 18 6-6-6-6"/>',
  target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>'
};
const icon = (n, s = 20) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[n]}</svg>`;
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fecha = iso => new Intl.DateTimeFormat("es-ES",{day:"numeric",month:"short"}).format(new Date(iso + "T12:00:00"));
const num = n => Number.isInteger(n) ? n : n.toFixed(1);

let E = null, vista = "Inicio", filtro = "Todas", menu = false, modal = null, toast = null, toastT = null;
let cal = {anio: 0, mes: 0, dia: 0};
const root = document.getElementById("app");

async function llamar(metodo, ruta, cuerpo) {
  const r = await fetch(API + ruta, {method: metodo, credentials: "same-origin",
    headers: cuerpo ? {"Content-Type": "application/json"} : {}, body: cuerpo ? JSON.stringify(cuerpo) : undefined});
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || "No se pudo completar la acción.");
  return d;
}
async function accion(metodo, ruta, cuerpo, ok) {
  try { E = await llamar(metodo, ruta, cuerpo); if (ok) avisar(ok); modal = null; pintar(); return true; }
  catch (e) { avisar(e.message, "error"); pintar(); return false; }
}
function avisar(texto, tipo = "success") {
  toast = {texto, tipo}; clearTimeout(toastT);
  toastT = setTimeout(() => { toast = null; pintar(); }, 2800);
}
const materia = id => E.materias.find(m => m.id === id);
const nivelInfo = c => NIVEL[c.nivel] || SIN_NIVEL;

function pintar() {
  if (!E) return;
  const y = window.scrollY;
  root.innerHTML = `
  <aside class="sidebar ${menu ? "is-open" : ""}">
    <div class="brand"><div class="brand-mark"><span></span></div><span>Atempo</span></div>
    <button class="mobile-close" data-a="menu0" aria-label="Cerrar menú">${icon("close")}</button>
    <div class="semester-pill"><span></span> Semestre de demostración</div>
    <nav>${VISTAS.map(([n,i]) => `<button class="${vista===n?"active":""}" data-vista="${n}" ${vista===n?'aria-current="page"':""}>${icon(i,19)}<span>${n}</span></button>`).join("")}</nav>
    <div class="sidebar-tip"><div class="tip-icon">${icon("spark",18)}</div><strong>Tip del día</strong><p>Divide las tareas grandes en bloques de 25 minutos.</p></div>
    <div class="profile"><div class="avatar">ES</div><div><strong>Estudiante demo</strong><span>Datos ficticios</span></div></div>
  </aside>
  ${menu ? '<button class="scrim" data-a="menu0" aria-label="Cerrar menú"></button>' : ""}
  <main class="main">
    <header class="topbar">
      <button class="menu-button" data-a="menu1" aria-label="Abrir menú">${icon("menu")}</button>
      <div class="page-name">${vista}</div>
      <div class="top-actions"><span class="today-label">${new Intl.DateTimeFormat("es-ES",{weekday:"long",day:"numeric",month:"long"}).format(hoy())}</span>
        <button class="icon-button" aria-label="Notificaciones">${icon("bell")}</button><div class="mini-avatar">ES</div></div>
    </header>
    <div class="content">${VIEWS[vista]()}</div>
  </main>
  ${modal ? renderModal() : ""}
  ${toast ? `<div class="toast ${toast.tipo}" role="status"><span>${toast.tipo==="success"?"✓":"!"}</span>${esc(toast.texto)}</div>` : ""}`;
  window.scrollTo(0, y);
  const f = root.querySelector("[autofocus]"); if (f) f.focus();
}
const hoy = () => new Date(E.resumen.hoy + "T12:00:00");

const cabecera = (t, d, acc = "") => `<section class="page-header"><div><h1>${t}</h1><p>${d}</p></div>${acc}</section>`;
const vacio = t => `<div class="empty-state"><div>${icon("calendar")}</div><p>${esc(t)}</p></div>`;
const metrica = (l, v, n, i, t) => `<div class="metric-card"><div class="metric-icon ${t}">${icon(i)}</div><div><span>${l}</span><strong>${v}</strong><small>${n}</small></div></div>`;
const anillo = (c, grande = false) => {
  const p = c.porcentaje, info = nivelInfo(c);
  return `<div class="progress-ring ${grande?"large":""} ${p===null?"sin-dato":""}" style="--progress:${Math.min(p||0,100)*3.6}deg;--ring-color:${info.c}" role="img" aria-label="${esc(c.mensaje)}"><div><strong>${p===null?"—":p+"%"}</strong><span>de carga</span></div></div>`;
};
const pill = (c, texto) => { const i = nivelInfo(c); return `<span class="status-pill" style="color:${i.c};background:${i.bg}">${esc(texto)}</span>`; };

const VIEWS = {
Inicio() {
  const r = E.resumen, c = r.carga;
  const prox = E.actividades.filter(a => !a.completada).sort((a,b) => a.fecha_limite.localeCompare(b.fecha_limite)).slice(0,4);
  const urg = new Set(r.recomendaciones.filter(x => x.resaltada).map(x => x.actividad_id));
  return `
  <section class="welcome"><div class="welcome-copy"><div><p class="eyebrow">Tu espacio académico</p><h1>Hola 👋</h1><p>Organiza tu semana y avanza a tu ritmo.</p></div>
    <button class="primary-button" data-a="nueva-actividad">${icon("plus",18)} Nueva actividad</button></div>
    <div class="welcome-art"><div class="image-badge">${icon("spark",16)}<span><b>Todo a tu tiempo</b>Planea, enfócate y avanza.</span></div></div></section>
  <section class="metrics-grid">
    ${metrica("Materias", E.materias.length, "Este semestre", "book", "purple")}
    ${metrica("Pendientes", r.progreso.pendientes, r.progreso.completadas + " completadas", "check", "coral")}
    ${metrica("Horas pendientes", num(c.horas_pendientes) + "h", "En actividades", "clock", "orange")}
    ${metrica("Horas disponibles", num(c.horas_disponibles) + "h", "Esta semana", "calendar", "teal")}</section>
  <section class="dashboard-grid">
    <div class="card activities-card"><div class="card-heading"><div><h2>Próximas actividades</h2><p>Lo más importante de tu semana</p></div>
      <button class="text-button" data-vista="Actividades">Ver todas ${icon("arrow",15)}</button></div>
      <div class="activity-list">${prox.length ? prox.map(a => { const m = materia(a.materia_id);
        return `<div class="activity-row ${urg.has(a.id)?"resaltada":""}"><button class="round-check" data-completar="${a.id}" aria-label="Completar ${esc(a.nombre)}"></button>
        <span class="subject-stripe" style="background:${esc(m?.color)}"></span><div class="activity-main"><strong>${esc(a.nombre)}</strong><span>${esc(m?.nombre)}</span></div>
        <div class="activity-meta"><span class="${urg.has(a.id)?"urgent":""}">${urg.has(a.id)?"Urgente · ":""}${fecha(a.fecha_limite)}</span><small>${icon("clock",14)} ${num(a.horas_estimadas)}h</small></div></div>`; }).join("") : vacio("No tienes actividades pendientes.")}</div></div>
    <div class="card load-card"><div class="card-heading"><div><h2>Carga académica</h2><p>Balance semanal</p></div>${pill(c, c.nivel || "Sin datos")}</div>
      <div class="load-visual">${anillo(c)}</div>
      <div class="load-numbers"><div><span>Pendientes</span><strong>${num(c.horas_pendientes)} horas</strong></div><i></i><div><span>Disponibles</span><strong>${num(c.horas_disponibles)} horas</strong></div></div>
      <p class="load-message">${esc(c.mensaje)}</p>
      <button class="secondary-button full" data-vista="Mi carga académica">Ajustar disponibilidad</button></div>
    <div class="card progress-card"><div class="card-heading"><div><h2>Tu progreso</h2><p>Actividades completadas</p></div><strong class="big-percent">${r.progreso.porcentaje}%</strong></div>
      <div class="wide-progress"><span style="width:${r.progreso.porcentaje}%"></span></div>
      <div class="progress-copy"><span><b>${r.progreso.completadas}</b> completadas</span><span><b>${r.progreso.pendientes}</b> por hacer</span></div></div>
    <div class="recommend-card"><div class="recommend-icon">${icon("spark",24)}</div><div><span>Recomendación del día</span>
      <h3>${c.alta ? "Reorganiza tus prioridades" : "Empieza por la tarea más cercana"}</h3>
      <p>${c.alta ? "Tu carga es alta: atiende primero lo que vence pronto." : "Completar primero lo más próximo te da margen para el resto."}</p></div>
      <button data-vista="Recomendaciones" aria-label="Ver recomendaciones">${icon("arrow")}</button></div>
  </section>`;
},
"Mis materias"() {
  return cabecera("Mis materias","Organiza las materias de tu semestre.",`<button class="primary-button" data-a="nueva-materia">${icon("plus",18)} Nueva materia</button>`) +
  `<div class="subject-grid">${E.materias.map(m => {
    const its = E.actividades.filter(a => a.materia_id === m.id), h = its.filter(a => a.completada).length, p = its.length ? Math.round(h/its.length*100) : 0;
    return `<article class="subject-card"><div class="subject-top" style="background:${esc(m.color)}"></div><div class="subject-card-body">
      <div class="subject-card-head"><div class="subject-symbol" style="color:${esc(m.color)};background:${esc(m.color)}18">${icon("book")}</div>
      <div class="row-actions"><button data-editar-materia="${m.id}" aria-label="Editar ${esc(m.nombre)}">${icon("edit",17)}</button><button data-borrar-materia="${m.id}" aria-label="Eliminar ${esc(m.nombre)}">${icon("trash",17)}</button></div></div>
      <h3>${esc(m.nombre)}</h3><p>${esc(m.docente) || "Sin docente asignado"}</p>
      <div class="subject-stats"><span>${its.length} actividades</span><b>${p}%</b></div>
      <div class="wide-progress small"><span style="width:${p}%;background:${esc(m.color)}"></span></div></div></article>`; }).join("")}
    ${E.materias.length ? "" : vacio("Crea tu primera materia para comenzar.")}</div>`;
},
Actividades() {
  const T = ["Todas","Pendientes","Completadas"];
  const cuenta = t => E.actividades.filter(a => t==="Todas" || (t==="Pendientes" ? !a.completada : a.completada)).length;
  const lista = E.actividades.filter(a => filtro==="Todas" || (filtro==="Pendientes" ? !a.completada : a.completada));
  return cabecera("Actividades","Haz seguimiento a tus tareas y entregas.",`<button class="primary-button" data-a="nueva-actividad">${icon("plus",18)} Nueva actividad</button>`) +
  `<div class="filter-tabs">${T.map(t => `<button class="${filtro===t?"active":""}" data-filtro="${t}">${t}<span>${cuenta(t)}</span></button>`).join("")}</div>
  <div class="card table-card"><div class="activity-table">${lista.map(a => { const m = materia(a.materia_id);
    return `<div class="table-row ${a.completada?"completed":""}"><button class="round-check ${a.completada?"checked":""}" data-alternar="${a.id}" aria-label="Cambiar estado de ${esc(a.nombre)}">${a.completada?"✓":""}</button>
    <div class="activity-main"><strong>${esc(a.nombre)}</strong><span class="subject-tag" style="background:${esc(m?.color)}22">${esc(m?.nombre || "Sin materia")}</span></div>
    <div class="table-detail"><span>Fecha límite</span><b>${fecha(a.fecha_limite)}</b></div><div class="table-detail"><span>Tiempo estimado</span><b>${num(a.horas_estimadas)} horas</b></div>
    <div class="row-actions"><button data-editar-act="${a.id}" aria-label="Editar">${icon("edit",17)}</button><button data-borrar-act="${a.id}" aria-label="Eliminar">${icon("trash",17)}</button></div></div>`; }).join("")}
    ${lista.length ? "" : vacio("No hay actividades en esta categoría.")}</div></div>`;
},
Calendario() {
  if (!cal.anio) { const h = hoy(); cal = {anio: h.getFullYear(), mes: h.getMonth(), dia: h.getDate()}; }
  const ini = new Date(cal.anio, cal.mes, 1), pre = (ini.getDay() + 6) % 7, tot = new Date(cal.anio, cal.mes + 1, 0).getDate();
  const iso = d => `${cal.anio}-${String(cal.mes+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
  const h = hoy(), esHoy = d => d === h.getDate() && cal.mes === h.getMonth() && cal.anio === h.getFullYear();
  const cel = [...Array(pre).fill(null), ...Array.from({length: tot}, (_, i) => i + 1)];
  const sel = E.actividades.filter(a => a.fecha_limite === iso(cal.dia));
  return cabecera("Calendario","Visualiza tus fechas límite en un solo lugar.") +
  `<div class="calendar-layout"><div class="card calendar-card"><div class="calendar-title"><button data-mes="-1" aria-label="Mes anterior">‹</button>
    <h2>${new Intl.DateTimeFormat("es-ES",{month:"long",year:"numeric"}).format(ini)}</h2><button data-mes="1" aria-label="Mes siguiente">›</button></div>
    <div class="calendar-grid weekdays">${["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"].map(d => `<span>${d}</span>`).join("")}</div>
    <div class="calendar-grid days">${cel.map(d => { if (!d) return "<span></span>";
      const its = E.actividades.filter(a => a.fecha_limite === iso(d));
      return `<button class="${d===cal.dia?"selected":""} ${esHoy(d)?"current":""}" data-dia="${d}" aria-label="Día ${d}, ${its.length} actividades"><b>${d}</b><span class="day-dots">${its.slice(0,3).map(a => `<i style="background:${esc(materia(a.materia_id)?.color)}"></i>`).join("")}</span></button>`; }).join("")}</div></div>
  <div class="card agenda-card"><div class="card-heading"><div><h2>${esHoy(cal.dia) ? "Hoy" : cal.dia + " de " + new Intl.DateTimeFormat("es-ES",{month:"long"}).format(ini)}</h2><p>${sel.length} actividades programadas</p></div></div>
    ${sel.map(a => `<div class="agenda-item" style="border-color:${esc(materia(a.materia_id)?.color)}"><span>${a.completada ? "Completada" : num(a.horas_estimadas) + "h estimadas"}</span><strong>${esc(a.nombre)}</strong><small>${esc(materia(a.materia_id)?.nombre)}</small></div>`).join("")}
    ${sel.length ? "" : vacio("No hay entregas para este día.")}</div></div>`;
},
"Mi carga académica"() {
  const c = E.resumen.carga, d = E.disponibilidad;
  const titulo = c.nivel === null ? "Sin disponibilidad" : c.nivel === "Alta" ? "Semana intensa" : c.nivel === "Media" ? "Ritmo moderado" : "Buen equilibrio";
  return cabecera("Mi carga académica","Ajusta tu disponibilidad y encuentra un ritmo sostenible.") +
  `<div class="load-layout"><div class="card availability-card"><div class="card-heading"><div><h2>Horas disponibles por día</h2><p>Tiempo que puedes dedicar a estudiar esta semana (0 a 24 h)</p></div></div>
    <form id="form-disp"><div class="availability-list">${DIAS.map(dia => `<label><span>${dia}</span><div><button type="button" data-delta="-1" data-dia-d="${dia}" aria-label="Menos horas ${dia}">−</button>
      <input type="number" min="0" max="24" step="0.5" name="${dia}" value="${d[dia]}" aria-label="Horas ${dia}"><b>h</b><button type="button" data-delta="1" data-dia-d="${dia}" aria-label="Más horas ${dia}">+</button></div></label>`).join("")}</div>
    <button class="primary-button" type="submit">Guardar disponibilidad</button></form></div>
  <div class="card load-summary">${pill(c, c.nivel ? "Carga " + c.nivel.toLowerCase() : "Sin datos")}${anillo(c, true)}<h2>${titulo}</h2>
    <p>${c.nivel === null ? esc(c.mensaje) : num(c.horas_pendientes) + " horas pendientes frente a " + num(c.horas_disponibles) + " horas disponibles."}</p>
    <div class="formula"><span>Carga académica</span><b>${num(c.horas_pendientes)}h ÷ ${num(c.horas_disponibles)}h × 100</b></div>
    <p class="aviso-demo">Baja: menos de 50 % · Media: 50 % a 80 % · Alta: más de 80 %</p></div></div>`;
},
Recomendaciones() {
  const rs = E.resumen.recomendaciones, c = E.resumen.carga, p = rs[0];
  const cards = [
    {i:"target",t:"Prioriza por fecha",x:p ? `Empieza por “${p.nombre}”. Es tu entrega más cercana.` : "No tienes entregas pendientes. Aprovecha para planear la próxima semana.",c:"purple"},
    {i:"clock",t:"Trabaja en bloques",x:"Dedica 25 minutos de concentración y toma 5 de descanso para mantener tu energía.",c:"teal"},
    {i:"gauge",t:c.alta ? "Reduce tu carga" : "Mantén tu balance",x:c.alta ? "Tu carga supera el 80 %. Considera aumentar horas disponibles o renegociar una entrega." : "Tu disponibilidad cubre tus pendientes. Conserva espacios de descanso.",c:"orange"}];
  return cabecera("Recomendaciones","Sugerencias basadas en tu carga actual y tus fechas.") +
  `<div class="recommend-hero"><div><span>Plan inteligente</span><h2>${c.alta ? "Esta semana, protege tu energía." : "Estás construyendo un buen ritmo."}</h2><p>Pequeños ajustes constantes hacen una gran diferencia en tu semestre.</p></div><div class="hero-orbit">${icon("spark",38)}</div></div>
  <div class="recommendations-grid">${cards.map(r => `<article class="card recommendation-item"><div class="metric-icon ${r.c}">${icon(r.i)}</div><h3>${r.t}</h3><p>${esc(r.x)}</p></article>`).join("")}</div>
  ${rs.length ? `<div class="card lista-rec"><div class="card-heading"><div><h2>Orden sugerido</h2><p>De la fecha más cercana a la más lejana</p></div></div><div class="activity-list">${rs.map(x =>
    `<div class="activity-row ${x.resaltada?"resaltada":""}"><div class="activity-main"><strong>${esc(x.nombre)}</strong><span>${esc(x.materia)} · ${num(x.horas)}h</span></div>
    <div class="activity-meta"><span class="${x.resaltada?"urgent":""}">${x.resaltada?"Urgente · ":""}${fecha(x.fecha_limite)}</span><small class="dias">${x.dias_restantes < 0 ? "Vencida" : x.dias_restantes === 0 ? "Vence hoy" : "En " + x.dias_restantes + " día(s)"}</small></div></div>`).join("")}</div></div>` : ""}`;
},
Estadísticas() {
  const t = E.actividades.length, h = E.resumen.progreso, plan = E.actividades.reduce((s,a) => s + a.horas_estimadas, 0);
  const max = Math.max(1, ...E.resumen.horas_por_materia.map(m => m.horas));
  return cabecera("Estadísticas","Observa tu avance y distribución de esfuerzo.") +
  `<section class="metrics-grid stats-metrics">${metrica("Tasa de avance", h.porcentaje + "%", "Del total de actividades", "chart", "purple")}${metrica("Completadas", h.completadas, "Actividades terminadas", "check", "teal")}${metrica("Horas planeadas", num(plan) + "h", "En todas las materias", "clock", "orange")}</section>
  <div class="stats-grid"><div class="card bar-chart"><div class="card-heading"><div><h2>Horas por materia</h2><p>Distribución de tu tiempo estimado</p></div></div>
    <div class="bars">${E.resumen.horas_por_materia.map(m => `<div class="bar-row"><span>${esc(m.nombre)}</span><div><i style="width:${m.horas/max*100}%;background:${esc(m.color)}"></i></div><b>${num(m.horas)}h</b></div>`).join("")}</div></div>
  <div class="card donut-card"><div class="card-heading"><div><h2>Estado general</h2><p>Resumen de actividades</p></div></div>
    <div class="donut" style="--done:${h.porcentaje*3.6}deg" role="img" aria-label="${h.completadas} de ${t} completadas"><div><strong>${t}</strong><span>Total</span></div></div>
    <div class="donut-legend"><span><i class="done-dot"></i>Completadas <b>${h.completadas}</b></span><span><i></i>Pendientes <b>${h.pendientes}</b></span></div></div></div>`;
},
Configuración() {
  return cabecera("Configuración","Personaliza tu experiencia en Atempo.") +
  `<div class="settings-column"><div class="card settings-card"><h2>Perfil</h2><div class="profile-settings"><div class="avatar large-avatar">ES</div><div><strong>Estudiante demo</strong><span>Sin datos personales reales</span></div></div>
    <p class="aviso-demo">Atempo es un MVP de demostración: usa solo datos ficticios y no guarda información personal. Tus cambios viven en esta sesión y se borran al cerrarla.</p></div>
  <div class="card settings-card"><h2>Preferencias</h2><div class="setting-row"><div><strong>Inicio de semana</strong><span>La semana va de lunes a domingo</span></div><b>Lunes</b></div></div>
  <div class="card settings-card danger-zone"><div><h2>Restablecer datos</h2><p>Vuelve a cargar los datos de demostración de Atempo.</p></div><button class="danger-button" data-a="reiniciar">Restablecer</button></div></div>`;
}};

function renderModal() {
  const m = modal;
  if (m.tipo === "materia") { const it = m.item || {}; const col = m.color || it.color || COLORES[0];
    return env(it.id ? "Editar materia" : "Nueva materia", `<form id="form-materia" novalidate>
      <label class="form-field"><span>Nombre de la materia</span><input name="nombre" autofocus value="${esc(it.nombre)}" placeholder="Ej. Diseño de Interfaces"></label>
      <label class="form-field"><span>Docente (opcional)</span><input name="docente" value="${esc(it.docente)}" placeholder="Nombre del docente"></label>
      <div class="form-field"><span>Color</span><div class="color-picker">${COLORES.map(c => `<button type="button" class="${c===col?"selected":""}" style="background:${c}" data-color="${c}" aria-label="Elegir color ${c}"></button>`).join("")}</div></div>
      ${m.error ? `<p class="form-error" role="alert">${esc(m.error)}</p>` : ""}${acciones(it.id ? "Guardar cambios" : "Crear materia")}</form>`); }
  const it = m.item || {};
  return env(it.id ? "Editar actividad" : "Nueva actividad", `<form id="form-act" novalidate>
    <label class="form-field"><span>Nombre de la actividad</span><input name="nombre" autofocus value="${esc(it.nombre)}" placeholder="Ej. Entrega de proyecto"></label>
    <label class="form-field"><span>Materia</span><select name="materia_id">${E.materias.map(x => `<option value="${x.id}" ${x.id===(it.materia_id||E.materias[0]?.id)?"selected":""}>${esc(x.nombre)}</option>`).join("")}</select></label>
    <div class="form-grid"><label class="form-field"><span>Fecha límite</span><input type="date" name="fecha_limite" value="${esc(it.fecha_limite || "")}"></label>
    <label class="form-field"><span>Horas estimadas</span><input type="number" name="horas_estimadas" min="0.5" step="0.5" value="${it.horas_estimadas ?? ""}"></label></div>
    ${m.error ? `<p class="form-error" role="alert">${esc(m.error)}</p>` : ""}${acciones(it.id ? "Guardar cambios" : "Crear actividad")}</form>`);
}
const env = (t, cuerpo) => `<div class="modal-backdrop" data-a="cerrar-fondo"><div class="modal" role="dialog" aria-modal="true" aria-label="${t}"><div class="modal-head"><div><span>Atempo</span><h2>${t}</h2></div><button data-a="cerrar" aria-label="Cerrar">${icon("close")}</button></div>${cuerpo}</div></div>`;
const acciones = l => `<div class="modal-actions"><button type="button" class="secondary-button" data-a="cerrar">Cancelar</button><button type="submit" class="primary-button">${l}</button></div>`;

root.addEventListener("click", ev => {
  const t = ev.target.closest("[data-a],[data-vista],[data-filtro],[data-completar],[data-alternar],[data-editar-act],[data-borrar-act],[data-editar-materia],[data-borrar-materia],[data-mes],[data-dia],[data-delta],[data-color]");
  if (!t) return;
  const d = t.dataset;
  if (d.a === "cerrar-fondo") { if (ev.target === t) { modal = null; pintar(); } return; }
  if (d.vista) { vista = d.vista; menu = false; pintar(); window.scrollTo(0,0); }
  else if (d.a === "menu1" || d.a === "menu0") { menu = d.a === "menu1"; pintar(); }
  else if (d.a === "nueva-materia") { modal = {tipo:"materia"}; pintar(); }
  else if (d.a === "nueva-actividad") { if (!E.materias.length) { avisar("Crea primero una materia.", "error"); vista = "Mis materias"; } else modal = {tipo:"actividad"}; pintar(); }
  else if (d.a === "cerrar") { modal = null; pintar(); }
  else if (d.a === "reiniciar") { if (confirm("¿Restablecer todos los datos de demostración?")) accion("POST", "/reiniciar", null, "Datos de demostración restablecidos."); }
  else if (d.filtro) { filtro = d.filtro; pintar(); }
  else if (d.completar) accion("PATCH", `/actividades/${d.completar}/completada`, {completada:true}, "¡Actividad completada!");
  else if (d.alternar) { const a = E.actividades.find(x => x.id == d.alternar); accion("PATCH", `/actividades/${a.id}/completada`, {completada:!a.completada}, a.completada ? "Actividad marcada como pendiente." : "¡Actividad completada!"); }
  else if (d.editarAct) { modal = {tipo:"actividad", item:E.actividades.find(x => x.id == d.editarAct)}; pintar(); }
  else if (d.borrarAct) { const a = E.actividades.find(x => x.id == d.borrarAct); if (confirm(`¿Eliminar la actividad “${a.nombre}”?`)) accion("DELETE", `/actividades/${a.id}`, null, "Actividad eliminada."); }
  else if (d.editarMateria) { modal = {tipo:"materia", item:materia(+d.editarMateria)}; pintar(); }
  else if (d.borrarMateria) { const m = materia(+d.borrarMateria); if (confirm(`¿Eliminar la materia “${m.nombre}”?`)) accion("DELETE", `/materias/${m.id}`, null, "Materia eliminada."); }
  else if (d.mes) { cal.mes += +d.mes; if (cal.mes < 0) { cal.mes = 11; cal.anio--; } if (cal.mes > 11) { cal.mes = 0; cal.anio++; } cal.dia = 1; pintar(); }
  else if (d.dia) { cal.dia = +d.dia; pintar(); }
  else if (d.delta) { const i = root.querySelector(`input[name="${d.diaD}"]`); i.value = Math.max(0, Math.min(24, (+i.value || 0) + +d.delta)); }
  else if (d.color) { modal.color = d.color; const f = root.querySelector("#form-materia"); modal.item = {...(modal.item||{}), nombre:f.nombre.value, docente:f.docente.value}; pintar(); }
});
root.addEventListener("submit", ev => {
  ev.preventDefault();
  const f = ev.target, v = n => f.elements[n]?.value ?? "";
  if (f.id === "form-disp") {
    const cuerpo = {}; for (const dia of DIAS) cuerpo[dia] = v(dia) === "" ? NaN : Number(v(dia));
    if (Object.values(cuerpo).some(x => Number.isNaN(x) || x < 0 || x > 24)) { avisar("Las horas deben estar entre 0 y 24.", "error"); pintar(); return; }
    accion("PUT", "/disponibilidad", cuerpo, "Disponibilidad guardada.");
  } else if (f.id === "form-materia") {
    const cuerpo = {nombre:v("nombre").trim(), docente:v("docente").trim(), color:modal.color || modal.item?.color || COLORES[0]};
    if (!cuerpo.nombre) { modal.item = {...(modal.item||{}), ...cuerpo}; modal.error = "El nombre de la materia es obligatorio"; pintar(); return; }
    const id = modal.item?.id; accion(id ? "PUT" : "POST", id ? `/materias/${id}` : "/materias", cuerpo, id ? "Materia actualizada." : "Materia creada con éxito.");
  } else if (f.id === "form-act") {
    const cuerpo = {nombre:v("nombre").trim(), materia_id:Number(v("materia_id")), fecha_limite:v("fecha_limite"), horas_estimadas:v("horas_estimadas") === "" ? null : Number(v("horas_estimadas"))};
    const err = !cuerpo.nombre ? "Falta el campo: nombre de la actividad." : !cuerpo.fecha_limite ? "Falta el campo: fecha de entrega." : cuerpo.horas_estimadas === null ? "Falta el campo: horas estimadas." : !(cuerpo.horas_estimadas > 0) ? "Las horas estimadas deben ser mayores que 0." : "";
    if (err) { modal.item = {...(modal.item||{}), ...cuerpo}; modal.error = err; pintar(); return; }
    const id = modal.item?.id; accion(id ? "PUT" : "POST", id ? `/actividades/${id}` : "/actividades", cuerpo, id ? "Actividad actualizada." : "Actividad creada con éxito.");
  }
});
document.addEventListener("keydown", ev => { if (ev.key === "Escape" && modal) { modal = null; pintar(); } });

llamar("GET", "/estado").then(d => { E = d; pintar(); })
  .catch(() => { root.innerHTML = '<p class="cargando">No se pudo cargar Atempo. Recarga la página.</p>'; });
})();
