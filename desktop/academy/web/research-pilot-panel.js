/* Academy 1.3: voluntary, local pre/post/delayed teaching-pilot panel.
 * LearningPath owns form generation, objective grading, chronology and protocol.
 * Date.now() is the production clock. There is no date override in this UI.
 * No network transport, invented participant, semantic grade or efficacy claim.
 */
(function (root, factory) {
  'use strict';
  const api = factory(typeof module === 'object' && module.exports ? require('./learning-path.js') : root.AcademyLearningPath, root);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AcademyResearchPilot = { VERSION: api.VERSION, mount: api.mount };
})(typeof window !== 'undefined' ? window : globalThis, function (L, root) {
  'use strict';
  const VERSION = '1.3.0', SCHEMA = 'academy-research-pilot-panel/1', phases = ['pre', 'post', 'delayed'];
  const noteKeys = ['prediction', 'controls', 'limits']; let mountCount = 0;
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const copy = value => JSON.parse(L.canonical(value));
  const iso = value => new Date(value).toISOString();
  function assert(condition, text) { if (!condition) throw new Error(text); }
  function boundedText(value, max, label) { assert(typeof value === 'string' && value.length <= max, label + ' must be bounded text.'); return value; }
  function blank() { return { schema: SCHEMA, version: VERSION, protocolId: L.pilotProtocol.id, pilot: null, plannedSeeds: null, activeForm: null, answers: {}, unaidedAttested: false, notes: { prediction: '', controls: '', limits: '' }, writtenRecords: [] }; }
  function coreOf(value) { const { digestSha256, derived, ...data } = value; return data; }
  function validate(data) {
    L.canonical(data);
    assert(data.schema === SCHEMA && data.version === VERSION && data.protocolId === L.pilotProtocol.id, 'Pilot panel schema/version mismatch.');
    assert(data.answers && typeof data.answers === 'object' && !Array.isArray(data.answers), 'Invalid answer draft.');
    assert(typeof data.unaidedAttested === 'boolean', 'Invalid support declaration.');
    assert(data.notes && noteKeys.every(k => typeof data.notes[k] === 'string' && data.notes[k].length <= 4000), 'Invalid reasoning draft.');
    assert(Array.isArray(data.writtenRecords) && data.writtenRecords.length <= 3, 'Invalid written records.');
    if (data.pilot === null) {
      assert(data.plannedSeeds === null && data.activeForm === null && !Object.keys(data.answers).length && !data.writtenRecords.length, 'A nonconsenting participant cannot have a pilot record.');
      return data;
    }
    L.validatePilot(data.pilot);
    assert(data.plannedSeeds && phases.every(p => Number.isInteger(data.plannedSeeds[p]) && data.plannedSeeds[p] >= 0 && data.plannedSeeds[p] <= 4294967295), 'Invalid planned form seeds.');
    assert(new Set(phases.map(p => data.plannedSeeds[p])).size === 3, 'Each pilot stage needs a different case seed.');
    for (const record of data.pilot.records) assert(record.seed === data.plannedSeeds[record.stage], 'Recorded form differs from its planned reserved case.');
    const next = phases[data.pilot.records.length];
    if (data.activeForm) {
      assert(next && data.activeForm.phase === next && data.activeForm.seed === data.plannedSeeds[next], 'Active form is not the next reserved stage.');
      const expected = L.makeDiagnostic({ seed: data.plannedSeeds[next], phase: next, count: 7 });
      assert(L.canonical(data.activeForm) === L.canonical(expected), 'Active form integrity mismatch.');
      for (const [id, answer] of Object.entries(data.answers)) {
        assert(data.activeForm.questions.some(q => q.id === id), 'Draft answer has no active question.');
        assert(typeof answer === 'number' && Number.isFinite(answer) || typeof answer === 'string' && answer.length <= 200, 'Invalid objective answer.');
      }
    } else assert(!Object.keys(data.answers).length, 'An answer draft requires its active form.');
    assert(data.writtenRecords.length === data.pilot.records.length, 'Every completed stage needs its corresponding written record.');
    data.writtenRecords.forEach((r, i) => {
      const p = data.pilot.records[i]; assert(r.stage === p.stage && r.at === p.at && r.unaidedAttested === true, 'Written record does not match the pilot stage.');
      assert(r.semanticGrade === null && noteKeys.every(k => typeof r.notes?.[k] === 'string' && r.notes[k].length <= 4000), 'Written reasoning must remain ungraded.');
    });
    return data;
  }
  function restore(initial) {
    if (initial === undefined || initial === null) return blank();
    const e = copy(initial), data = coreOf(e);
    assert(typeof e.digestSha256 === 'string' && L.sha256(data) === e.digestSha256, 'Pilot panel integrity mismatch. Preserve the original export.');
    return validate(data);
  }
  function seeds() {
    let values;
    if (root.crypto?.getRandomValues) values = Array.from(root.crypto.getRandomValues(new Uint32Array(3)));
    else { const h = L.sha256(String(Date.now()) + ':' + Math.random()); values = [0, 8, 16].map(i => Number.parseInt(h.slice(i, i + 8), 16)); }
    const used = new Set(); values = values.map(v => { while (used.has(v)) v = (v + 2654435761) >>> 0; used.add(v); return v; });
    return Object.fromEntries(phases.map((p, i) => [p, values[i]]));
  }
  function createModel(initial, options = {}) {
    let data = restore(initial);
    function derived() {
      const pilot = data.pilot, at = Date.now(), stage = pilot ? phases[pilot.records.length] || null : null,
        post = pilot?.records.find(r => r.stage === 'post'), reviewDueAt = post ? iso(Date.parse(post.at) + L.pilotProtocol.stages.find(s => s.id === 'delayed').delayDays * L.DAY) : null,
        last = pilot?.records.at(-1)?.at || pilot?.createdAt;
      return { participantCount: pilot ? 1 : 0, stage, reviewDueAt, isDue: stage !== 'delayed' || !!reviewDueAt && at >= Date.parse(reviewDueAt), complete: !!pilot && pilot.records.length === 3, clockBeforeRecorded: !!last && at < Date.parse(last), activeQuestionCount: data.activeForm?.questions.length || 0, semanticGrade: null, efficacyEstablished: false };
    }
    function snapshot() { const payload = copy(data); return { ...payload, digestSha256: L.sha256(payload), derived: derived() }; }
    function commit(next) { validate(next); data = next; options.onChange?.(snapshot()); return snapshot(); }
    function prepare() {
      assert(data.pilot, 'Voluntary consent is required before preparing a pilot case.');
      const d = derived(); assert(!d.complete, 'The three pilot stages are already recorded.'); assert(!d.clockBeforeRecorded, 'The local clock precedes existing records; preserve chronology.');
      assert(d.isDue, 'The delayed-retention case is not due yet.'); if (data.activeForm) return snapshot();
      const next = copy(data); next.activeForm = L.makeDiagnostic({ seed: next.plannedSeeds[d.stage], phase: d.stage, count: 7 }); next.answers = {}; next.unaidedAttested = false; next.notes = { prediction: '', controls: '', limits: '' }; return commit(next);
    }
    function consent({ confirmed, participantCode = '' } = {}) {
      assert(confirmed === true, 'Explicit voluntary local consent is required.'); assert(!data.pilot, 'A local participant is already recorded; export this record before starting another portfolio.');
      boundedText(participantCode, 80, 'Optional participant code');
      const next = copy(data); next.pilot = L.createPilot({ consentConfirmed: true, participantCode: participantCode.trim() || 'anonymous-local', now: Date.now() }); next.plannedSeeds = seeds();
      next.activeForm = L.makeDiagnostic({ seed: next.plannedSeeds.pre, phase: 'pre', count: 7 }); return commit(next);
    }
    function draft({ answers, notes, unaidedAttested } = {}) {
      assert(data.activeForm, 'No active pilot case.'); const next = copy(data);
      if (answers !== undefined) next.answers = copy(answers);
      if (notes !== undefined) next.notes = Object.fromEntries(noteKeys.map(k => [k, boundedText(notes[k] || '', 4000, 'Reasoning note')]));
      if (unaidedAttested !== undefined) { assert(typeof unaidedAttested === 'boolean', 'Support declaration must be boolean.'); next.unaidedAttested = unaidedAttested; }
      return commit(next);
    }
    function submit() {
      assert(data.activeForm && data.pilot, 'Prepare the reserved case first.'); assert(data.unaidedAttested === true, 'Confirm that these objective answers were completed without assistance. Assisted practice is not an unaided pilot outcome.');
      for (const q of data.activeForm.questions) assert(data.answers[q.id] !== undefined && String(data.answers[q.id]).trim() !== '', 'Answer every objective question before recording this stage.');
      const form = copy(data.activeForm), answers = copy(data.answers), at = Date.now(), result = L.gradeDiagnostic(form, answers), next = copy(data);
      next.pilot = L.recordPilot(next.pilot, { form, answers, now: at, unaided: true });
      next.writtenRecords.push({ stage: form.phase, at: iso(at), notes: copy(data.notes), unaidedAttested: true, semanticGrade: null });
      next.activeForm = null; next.answers = {}; next.unaidedAttested = false; next.notes = { prediction: '', controls: '', limits: '' };
      // Commit the pilot result before optional competency synchronization.
      commit(next); const callbackErrors = [];
      if (options.onLearningAttempt) for (const q of form.questions) {
        try { options.onLearningAttempt({ form: copy(form), questionId: q.id, answer: answers[q.id], hintCount: 0, now: at }); }
        catch (e) { callbackErrors.push(String(e.message || e)); }
      }
      return { result, callbackErrors, state: snapshot() };
    }
    function exportResults() {
      assert(data.pilot, 'No voluntarily consenting local participant has been recorded.');
      const payload = { schema: 'academy-pilot-results-export/1', version: VERSION, exportedAt: iso(Date.now()), protocol: copy(L.pilotProtocol), participantCount: 1, panel: snapshot(),
        interpretation: 'One voluntarily consenting local participant; objective checks only. Written arguments require a separate human rubric. No group efficacy, independent secure examination, causal effect or validated learning gain is established.',
        privacy: 'Explicit local export only. No network transfer, real name, institutional identifier or external analytics are requested by this panel.' };
      return { ...payload, digestSha256: L.sha256(payload) };
    }
    return { snapshot, consent, prepare, draft, submit, exportResults };
  }
  function mount(container, language = 'es', options = {}) {
    assert(L && L.createPilot && L.recordPilot, 'AcademyLearningPath pilot functions are required.');
    assert(container && typeof container.addEventListener === 'function', 'A DOM container is required.');
    let lang = language === 'en' ? 'en' : 'es', alive = true, message = '', error = false, consentDraft = { code: '', confirmed: false };
    const id = 'academy-pilot-' + (++mountCount), t = (es, en) => lang === 'es' ? es : en, loc = value => value?.[lang] || value?.en || '',
      model = createModel(options.initialState, { onChange: options.onChange, onLearningAttempt: options.onLearningAttempt });
    const phaseTitle = phase => loc(L.pilotProtocol.stages.find(s => s.id === phase)?.title);
    function date(value) { return value ? new Intl.DateTimeFormat(lang === 'es' ? 'es-ES' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '—'; }
    function collect() {
      const snap = model.snapshot();
      if (!snap.pilot) { const code = container.querySelector('[data-pilot-code]'), checked = container.querySelector('[data-pilot-consent]'); if (code) consentDraft.code = code.value.slice(0, 80); if (checked) consentDraft.confirmed = checked.checked; return; }
      if (!snap.activeForm) return;
      const answers = { ...snap.answers }; container.querySelectorAll('[data-pilot-answer]').forEach(el => { answers[el.dataset.pilotAnswer] = el.value; });
      const notes = { ...snap.notes }; container.querySelectorAll('[data-pilot-note]').forEach(el => { notes[el.dataset.pilotNote] = el.value.slice(0, 4000); });
      model.draft({ answers, notes, unaidedAttested: !!container.querySelector('[data-pilot-unaided]')?.checked });
    }
    function question(q, snap, i) {
      const inputId = id + '-q-' + i, value = snap.answers[q.id] ?? '';
      return `<label for="${inputId}"><b>${i + 1}.</b> ${esc(loc(q.prompt))}${q.type === 'choice' ? `<select id="${inputId}" data-pilot-answer="${esc(q.id)}"><option value="">${t('Selecciona una respuesta','Select an answer')}</option>${q.choices.map((c, j) => `<option value="${j}"${String(value) === String(j) ? ' selected' : ''}>${esc(loc(c))}</option>`).join('')}</select>` : `<input id="${inputId}" type="number" step="any" data-pilot-answer="${esc(q.id)}" value="${esc(value)}" aria-describedby="${inputId}-unit"><small id="${inputId}-unit">${esc(q.unit === 'us' ? 'µs' : q.unit === 'm2' ? 'm²' : t('adimensional','dimensionless'))}</small>`}</label>`;
    }
    function results(snap) {
      return `<div class="rs-metrics"><div class="rs-metric"><span>${t('Participantes locales consentidos','Consenting local participants')}</span><strong>${snap.derived.participantCount}</strong></div><div class="rs-metric"><span>${t('Etapas registradas','Recorded stages')}</span><strong>${snap.pilot.records.length} / 3</strong></div><div class="rs-metric"><span>${t('Evaluación de argumentos','Argument assessment')}</span><strong>${t('Revisión humana','Human review')}</strong></div></div>${snap.pilot.records.length ? `<div class="rs-scroll"><table class="rs-data"><thead><tr><th>${t('Etapa','Stage')}</th><th>${t('Fecha local','Local date')}</th><th>${t('Comprobación objetiva','Objective check')}</th></tr></thead><tbody>${snap.pilot.records.map(r => `<tr><td>${esc(phaseTitle(r.stage))}</td><td>${esc(date(r.at))}</td><td>${r.score} / ${r.total}</td></tr>`).join('')}</tbody></table></div><details><summary>${t('Notas conservadas para revisión humana','Preserved notes for human review')}</summary>${snap.writtenRecords.map(r => `<h4>${esc(phaseTitle(r.stage))}</h4>${noteKeys.map(k => `<p class="rs-caption"><b>${t(k === 'prediction' ? 'Predicción' : k === 'controls' ? 'Controles' : 'Límites', k === 'prediction' ? 'Prediction' : k === 'controls' ? 'Controls' : 'Limits')}:</b> ${esc(r.notes[k] || t('Sin nota registrada.','No note recorded.'))}</p>`).join('')}`).join('')}</details>` : ''}`;
    }
    function render() {
      if (!alive) return; const snap = model.snapshot(), d = snap.derived;
      container.classList.add('rs-pilot');
      const status = message || (snap.pilot ? t('Registro local. Exporta los resultados para conservarlos. La revisión del razonamiento corresponde al docente.','Local record. Export the results to retain them. Reasoning is reviewed by the instructor.') : t('Este panel no envía datos. El piloto comienza únicamente tras tu consentimiento explícito.','This panel sends no data. The pilot begins only after your explicit consent.'));
      let body;
      if (!snap.pilot) body = `<p>${esc(loc(L.pilotProtocol.consent))}</p><p class="rs-caption">${t('Usa un seudónimo opcional. No introduzcas tu nombre real, correo ni identificadores institucionales. Puedes cerrar el panel sin participar.','Use an optional pseudonym. Do not enter your real name, email or institutional identifiers. You may close the panel without participating.')}</p><div class="rs-form"><label>${t('Código local opcional','Optional local code')}<input type="text" data-pilot-code maxlength="80" autocomplete="off" value="${esc(consentDraft.code)}" placeholder="${t('p. ej., Grupo-A-03','e.g., Group-A-03')}"></label></div><label><input type="checkbox" data-pilot-consent${consentDraft.confirmed ? ' checked' : ''}> ${t('Acepto voluntariamente registrar este piloto local y comprendo su finalidad docente.','I voluntarily agree to record this local pilot and understand its teaching purpose.')}</label><div class="rs-toolbar"><button type="button" class="rs-primary" data-pilot-action="consent">${t('Consentir y abrir el caso inicial','Consent and open the initial case')}</button></div><p class="rs-caption">${t('Participantes registrados: 0. No hay alumnos ni resultados precargados.','Recorded participants: 0. No learners or results are preloaded.')}</p>`;
      else {
        body = `<p class="rs-caption"><b>${t('Código local:','Local code:')}</b> ${esc(snap.pilot.participantCode)} · <b>${t('Consentimiento:','Consent:')}</b> ${esc(date(snap.pilot.createdAt))}</p>${results(snap)}`;
        if (d.clockBeforeRecorded) body += `<p class="rs-status" role="alert">${t('El reloj local es anterior al último registro. Conserva la cronología antes de continuar.','The local clock precedes the last record. Preserve chronology before continuing.')}</p>`;
        if (snap.activeForm) body += `<details open><summary><b>${esc(phaseTitle(snap.activeForm.phase))}</b> · ${snap.activeForm.questions.length} ${t('preguntas','questions')}</summary><p class="rs-caption">${t('Responde sin Beatrix, pistas ni consulta de soluciones. La condición «sin ayuda» se registra según tu declaración. El panel es docente, no un examen seguro.','Answer without Beatrix, hints or solution lookup. Unaided status is recorded from your declaration. This is a teaching panel, not a secure examination.')}</p><div class="rs-form">${snap.activeForm.questions.map((q, i) => question(q, snap, i)).join('')}</div><details><summary>${t('Razonamiento para revisión humana (opcional)','Reasoning for human review (optional)')}</summary>${noteKeys.map(k => `<label>${t(k === 'prediction' ? 'Predicción y motivo' : k === 'controls' ? 'Control que elegirías y por qué' : 'Límite principal de tu conclusión', k === 'prediction' ? 'Prediction and reason' : k === 'controls' ? 'Your chosen control and why' : 'Main limitation of your conclusion')}<textarea rows="2" maxlength="4000" data-pilot-note="${k}">${esc(snap.notes[k])}</textarea></label>`).join('')}</details><label><input type="checkbox" data-pilot-unaided${snap.unaidedAttested ? ' checked' : ''}> ${t('Declaro que he respondido este caso sin ayuda.','I declare that I answered this case without assistance.')}</label><div class="rs-toolbar"><button type="button" class="rs-primary" data-pilot-action="submit">${t('Registrar esta etapa una sola vez','Record this stage once')}</button></div></details>`;
        else if (d.complete) body += `<p class="rs-status">${t('Las tres etapas están registradas. No se asigna una nota semántica ni se demuestra eficacia docente con este único registro.','All three stages are recorded. No semantic grade is assigned, and this single record does not establish teaching efficacy.')}</p>`;
        else if (d.stage === 'delayed' && !d.isDue) body += `<p><b>${t('Retención diferida disponible desde:','Delayed retention available from:')}</b> <time datetime="${esc(d.reviewDueAt)}">${esc(date(d.reviewDueAt))}</time></p><p class="rs-caption">${t('Se requieren siete días reales desde el postest. Vuelve a abrir el panel en esa fecha; no se generan resultados futuros.','Seven real days after the post-test are required. Reopen this panel on that date; future outcomes are not generated.')}</p><div class="rs-toolbar"><button type="button" data-pilot-action="refresh">${t('Comprobar fecha actual','Check the current date')}</button><button type="button" disabled>${t('Caso diferido todavía bloqueado','Delayed case not due yet')}</button></div>`;
        else body += `<p>${d.stage === 'post' ? t('Practica con el recorrido de investigación antes de abrir el caso final. La nueva forma usa otra semilla y no reutiliza las respuestas del pretest.','Practise with the research pathway before opening the final case. The new form uses another seed and does not reuse pre-test answers.') : t('Ya puedes preparar el nuevo caso de retención.','You may now prepare the new retention case.')}</p><div class="rs-toolbar"><button type="button" class="rs-primary" data-pilot-action="prepare"${d.clockBeforeRecorded ? ' disabled' : ''}>${t('Abrir siguiente caso reservado','Open the next reserved case')}</button></div>`;
        body += `<div class="rs-toolbar"><button type="button" data-pilot-action="export">${t('Exportar resultados del piloto','Export pilot results')}</button></div><details><summary>${t('Rúbrica humana y alcance del piloto','Human rubric and pilot scope')}</summary><p>${t('Los argumentos se revisan por separado en «Defensa y revisión». Estas puntuaciones numéricas no califican el texto ni sustituyen a dos evaluadores independientes.','Arguments are reviewed separately under Defence and review. These numerical scores do not grade prose or replace two independent reviewers.')}</p><ul>${L.rubricCriteria.map(c => `<li>${esc(loc(c.title))}</li>`).join('')}</ul><p>${esc(loc(L.pilotProtocol.interpretation))}</p></details>`;
      }
      container.innerHTML = `<section class="rs-card" aria-labelledby="${id}"><span class="rs-kicker">${t('PILOTO DOCENTE VOLUNTARIO · LOCAL','VOLUNTARY TEACHING PILOT · LOCAL')}</span><h3 id="${id}">${t('Antes, después y siete días más tarde','Before, after and seven days later')}</h3><div class="rs-timeline" role="list" aria-label="${t('Etapas del piloto','Pilot stages')}">${L.pilotProtocol.stages.map((s,i) => `<span role="listitem">${i+1} · ${esc(loc(s.title))}</span>`).join('')}</div><p class="rs-status" role="status" data-pilot-error="${error}">${esc(status)}</p>${body}</section>`;
    }
    function notify(text) { error = false; message = text; render(); }
    function action(name) {
      try {
        error = false;
        if (name === 'consent') { collect(); model.consent({ confirmed: consentDraft.confirmed, participantCode: consentDraft.code }); notify(t('Consentimiento local registrado. El caso inicial está preparado.','Local consent recorded. The initial case is ready.')); }
        else if (name === 'prepare') { model.prepare(); notify(t('Nueva forma reservada preparada. Responde sin ayuda.','New reserved form prepared. Answer without assistance.')); }
        else if (name === 'submit') { collect(); const result = model.submit(); notify(result.callbackErrors.length ? t('Etapa guardada; la sincronización de competencias requiere revisión. Exporta el registro.','Stage saved; competency synchronization needs review. Export the record.') : t('Etapa registrada. El resultado es objetivo; el razonamiento sigue pendiente de revisión humana.','Stage recorded. The result is objective; reasoning still awaits human review.')); }
        else if (name === 'refresh') notify(t('Fecha local actual comprobada.','Current local date checked.'));
        else if (name === 'export') {
          collect(); const exported = model.exportResults(), url = root.URL.createObjectURL(new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' })), link = container.ownerDocument.createElement('a');
          link.href = url; link.download = 'DiffAtOnce-Academy-local-pilot-results.json'; link.click(); setTimeout(() => root.URL.revokeObjectURL(url), 5000); notify(t('Exportación local preparada. No se ha enviado nada al servidor.','Local export prepared. Nothing was sent to a server.'));
        }
      } catch (e) {
        error = true; const raw = String(e.message || e), known = [
          [/Explicit voluntary local consent/, 'Confirma el consentimiento voluntario antes de iniciar el piloto.', 'Confirm voluntary consent before starting the pilot.'],
          [/Confirm that these objective answers/, 'Confirma que has respondido sin ayuda. La práctica asistida no es un resultado del piloto sin ayuda.', 'Confirm that you answered without assistance. Assisted practice is not an unaided pilot outcome.'],
          [/Answer every objective question/, 'Responde todas las preguntas objetivas antes de registrar esta etapa.', 'Answer every objective question before recording this stage.'],
          [/delayed-retention case is not due/, 'La fecha de retención diferida todavía no ha llegado.', 'The delayed-retention date has not been reached yet.'],
          [/clock precedes|clock moved backwards/i, 'El reloj local es anterior a los registros. Conserva la cronología antes de continuar.', 'The local clock precedes the records. Preserve chronology before continuing.']
        ]; const found = known.find(([pattern]) => pattern.test(raw)); message = found ? t(found[1], found[2]) : t('No se pudo completar esta acción: ', 'This action could not be completed: ') + raw; render();
      }
    }
    const click = e => { const el = e.target.closest?.('[data-pilot-action]'); if (el && container.contains(el) && !el.disabled) action(el.dataset.pilotAction); };
    const change = e => { if (!e.target.matches?.('[data-pilot-answer],[data-pilot-note],[data-pilot-unaided]')) return; try { collect(); } catch (f) { error = true; message = String(f.message || f); render(); } };
    container.addEventListener('click', click); container.addEventListener('change', change); render();
    return { snapshot: model.snapshot, setLanguage(next) { assert(['es', 'en'].includes(next), 'Pilot language must be es/en.'); collect(); lang = next; message = ''; error = false; render(); }, destroy() { if (!alive) return; collect(); alive = false; container.removeEventListener('click', click); container.removeEventListener('change', change); container.classList.remove('rs-pilot'); container.innerHTML = ''; } };
  }
  // Pure controller is exported only to CommonJS tests, not the browser API.
  return { VERSION, mount, _test: { createModel, validate, restore } };
});
