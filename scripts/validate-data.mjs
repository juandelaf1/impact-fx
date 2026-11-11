#!/usr/bin/env node
/**
 * Validación básica de datos procesados y golden case (B1).
 * Uso: node scripts/validate-data.mjs
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const base = path.join(__dirname, '..', 'data', 'processed');

function read(name) {
  return JSON.parse(fs.readFileSync(path.join(base, name), 'utf8'));
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

function approx(a, b, eps = 1e-6) {
  return Math.abs(a - b) <= eps;
}

try {
  const rates = read('fx_rates.json');
  const fees = read('fee_rules.json');
  const corridors = read('corridors.json');
  const budgets = read('project_budgets.json');
  const scenarios = read('demo_scenarios.json');

  assert(Array.isArray(rates) && rates.length, 'fx_rates vacío');
  assert(rates.every(r => r.base && r.quote && r.rate > 0 && r.source && r.date && typeof r.is_mock === 'boolean'), 'fx_rates inválido');

  assert(Array.isArray(fees) && fees.length, 'fee_rules vacío');
  assert(Array.isArray(corridors) && corridors.length, 'corridors vacío');
  assert(Array.isArray(budgets) && budgets.length, 'project_budgets vacío');
  assert(Array.isArray(scenarios) && scenarios.length, 'demo_scenarios vacío');

  const byId = Object.fromEntries(scenarios.map(s => [s.id, s]));
  const b1 = byId['B1'];
  assert(b1, 'B1 no encontrado');
  let baseSc = b1.expected.scenarios.find(s => s.name === 'base');
  let stressSc = b1.expected.scenarios.find(s => s.name === 'stress_-3%');
  assert(approx(baseSc.amount_received, 1444200), 'B1 base incorrecto');
  assert(approx(stressSc.amount_received, 1400874), 'B1 stress incorrecto');
  assert(approx(b1.expected.difference.amount, 43326), 'B1 diferencia incorrecta');

  if (byId['B1b']) {
    const s = byId['B1b'];
    assert(approx(s.expected.stressed_rate, 137.75), 'B1b stressed_rate incorrecto');
    assert(approx(s.expected.scenarios.find(x => x.name === 'stress_-5%').amount_received, 1371990), 'B1b stress incorrecto');
    assert(approx(s.expected.difference.amount, 72210), 'B1b diferencia incorrecta');
  }
  if (byId['B1c']) {
    const s = byId['B1c'];
    assert(approx(s.expected.scenarios.find(x => x.name === 'base').amount_received, 719200), 'B1c base incorrecto');
    assert(approx(s.expected.scenarios.find(x => x.name === 'stress_-3%').amount_received, 697624), 'B1c stress incorrecto');
    assert(approx(s.expected.difference.amount, 21576), 'B1c diferencia incorrecta');
  }
  if (byId['B4']) {
    const s = byId['B4'];
    assert(approx(s.expected.scenarios.find(x => x.name === 'base').amount_received, 63800.25), 'B4 base incorrecto');
    assert(approx(s.expected.difference.amount, 1914.0075), 'B4 diferencia incorrecta');
  }
  if (byId['B5']) {
    const s = byId['B5'];
    assert(s.inputs.fee_eur === null && s.expected.applied_fee_eur === 40, 'B5 fee/aplicada incorrecto');
    assert(approx(s.expected.scenarios.find(x => x.name === 'base').amount_received, 1444200), 'B5 base incorrecto');
  }

  console.log(`OK: datos y golden cases válidos (${scenarios.map(s=>s.id).join(', ')}).`);
} catch (e) {
  console.error('ERROR:', e.message);
  process.exit(1);
}
