// Prueba de carga de Atempo: GET /api/v1/estado (endpoint más crítico: calcula nivel de carga y recomendaciones)
// Ejecutar SOLO contra desarrollo/local:  k6 run -e BASE=http://127.0.0.1:5055 carga_estado.js
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE || 'http://127.0.0.1:5055';
if (!/^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/.test(BASE)) {
  throw new Error('Protección: esta prueba solo se ejecuta contra localhost, no contra producción');
}

export const options = {
  stages: [
    { duration: '10s', target: 50 },   // rampa de subida
    { duration: '20s', target: 50 },   // sostenimiento en el pico
    { duration: '10s', target: 0 },    // bajada
  ],
  thresholds: {
    'http_req_duration{fase:estado}': ['p(95)<800'],   // p95 < 800 ms (RNF-01 exige < 3 s en la pantalla completa)
    'http_req_failed{fase:estado}': ['rate<0.01'],     // menos de 1 % de errores
    checks: ['rate>0.99'],
  },
};

const H = { headers: { 'Content-Type': 'application/json' } };

export default function () {
  if (__ITER === 0) {   // cada usuario virtual (sesión) parte con 50 actividades, como pide RNF-01
    const mid = http.get(`${BASE}/api/v1/estado`, { tags: { fase: 'carga_inicial' } }).json('materias.0.id');
    for (let i = 0; i < 50; i++) {
      http.post(`${BASE}/api/v1/actividades`, JSON.stringify({
        nombre: `Actividad ${i}`, fecha_limite: '2026-11-20', horas_estimadas: 1, materia_id: mid,
      }), { ...H, tags: { fase: 'carga_inicial' } });
    }
  }
  const r = http.get(`${BASE}/api/v1/estado`, { tags: { fase: 'estado' } });
  check(r, { 'estado 200': (x) => x.status === 200, 'trae resumen': (x) => x.json('resumen.carga.nivel') !== undefined });
  sleep(1);   // un estudiante real no consulta sin pausa
}
