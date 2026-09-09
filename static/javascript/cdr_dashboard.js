/**
* cdr_dashboard.js
* CDR Intelligence Module — Leaflet map rendering + UI controller
* Handles AJAX form submission, result parsing, and interactive visualisation.
*/

/* ── Leaflet map setup ─────────────────────────────────────────────────── */
let map = null;
let markerGroup = null;
let polylineGroup = null;

function initMap(lat, lon) {
    if (map) {
        map.remove();
        map = null;
    }
    map = L.map('cdrMap', { zoomControl: true, scrollWheelZoom: true })
        .setView([lat, lon], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    markerGroup = L.featureGroup().addTo(map);
    polylineGroup = L.featureGroup().addTo(map);
}

/* ── Custom icon factories ─────────────────────────────────────────────── */
function makeIcon(color, glyph) {
    return L.divIcon({
        className: '',
        iconSize: [30, 30],
        iconAnchor: [15, 15],
        html: `<div style="
                 width:30px;height:30px;border-radius:50%;
                 background:${color};display:flex;align-items:center;
                 justify-content:center;font-size:13px;color:#fff;
                 border:3px solid rgba(255,255,255,.25);
                 box-shadow:0 0 12px ${color}88;">
                 ${glyph}
               </div>`
    });
}

const ICON_CRIME = makeIcon('#f87171', '⚠');      // red   — crime scene
const ICON_TOWER = makeIcon('#60a5fa', '📡');      // blue  — tower path
const ICON_LEAD = makeIcon('#fbbf24', '⚡');      // yellow — proximity lead

/* ── Render result onto map & UI panels ───────────────────────────────── */
function renderResult(data) {
    const { timeline, proximity_leads, top_contacts, crime_scene, target_number, radius_km } = data;

    const crLat = crime_scene.lat;
    const crLon = crime_scene.lon;
    const rad = crime_scene.radius_km || radius_km || 0.5;

    /* Stats strip */
    document.getElementById('statsStrip').style.removeProperty('display');
    document.getElementById('statTimeline').textContent = timeline.length;
    document.getElementById('statProximity').textContent = proximity_leads.length;
    document.getElementById('statContacts').textContent = top_contacts.length;
    document.getElementById('statRadius').textContent = rad;

    /* ── Map ── */
    initMap(crLat, crLon);

    // Crime scene marker
    L.marker([crLat, crLon], { icon: ICON_CRIME })
        .bindPopup(`<b style="color:#f87171">⚠ Crime Scene</b><br>Lat: ${crLat.toFixed(5)}, Lon: ${crLon.toFixed(5)}`)
        .addTo(markerGroup);

    // Proximity radius circle
    L.circle([crLat, crLon], {
        radius: rad * 1000,
        color: '#f87171',
        fillColor: '#f87171',
        fillOpacity: 0.07,
        weight: 1.5,
        dashArray: '6 4'
    }).addTo(markerGroup);

    // Proximity lead set (indexed for quick lookup)
    const leadSet = new Set(proximity_leads.map(l => `${l.tower_lat}_${l.tower_lon}_${l.timestamp}`));

    // Timeline markers & polyline
    const pathCoords = [];
    timeline.forEach((ev, idx) => {
        const key = `${ev.tower_lat}_${ev.tower_lon}_${ev.timestamp}`;
        const isLead = leadSet.has(key);
        const icon = isLead ? ICON_LEAD : ICON_TOWER;
        const ts = ev.timestamp ? ev.timestamp.replace('T', ' ').substring(0, 16) : 'Unknown';

        const marker = L.marker([ev.tower_lat, ev.tower_lon], { icon })
            .bindPopup(`
                <div style="font-family:'Share Tech Mono',monospace;font-size:.77rem;min-width:200px">
                  <b style="color:${isLead ? '#fbbf24' : '#60a5fa'}">#${idx + 1} — ${isLead ? '⚡ PROXIMITY LEAD' : 'TOWER HOP'}</b><br>
                  <hr style="border-color:#333;margin:4px 0">
                  🕐 ${ts}<br>
                  📞 ${ev.direction === 'outgoing' ? '📤 Outgoing' : '📥 Incoming'}<br>
                  👤 ${ev.counterparty || '—'}<br>
                  ⏱ ${ev.duration_sec !== null ? ev.duration_sec + 's' : '—'}<br>
                  📡 (${ev.tower_lat.toFixed(5)}, ${ev.tower_lon.toFixed(5)})
                  ${isLead ? '<br><span style="color:#fbbf24">⚡ Within ' + rad + ' km of crime scene</span>' : ''}
                </div>
            `);
        marker.addTo(markerGroup);
        pathCoords.push([ev.tower_lat, ev.tower_lon]);
    });

    // Draw movement polyline
    if (pathCoords.length > 1) {
        L.polyline(pathCoords, {
            color: '#60a5fa',
            weight: 2.5,
            opacity: 0.7,
            dashArray: '8 4'
        }).addTo(polylineGroup);
    }

    // Fit bounds
    if (markerGroup.getLayers().length) {
        map.fitBounds(markerGroup.getBounds().pad(0.15));
    }

    /* ── Legend ── */
    document.getElementById('mapLegend').style.display = 'flex';

    /* ── Proximity leads table ── */
    const proxCard = document.getElementById('proximityCard');
    proxCard.style.display = 'block';
    if (proximity_leads.length === 0) {
        document.getElementById('proximityContent').innerHTML =
            `<div style="color:#64748b;font-size:.82rem;text-align:center;padding:1rem">
               <i class="fas fa-check-circle" style="color:#34d399;margin-right:.5rem"></i>
               No calls found within ${rad} km of the crime scene.
             </div>`;
    } else {
        let rows = '';
        proximity_leads.forEach((l, i) => {
            const ts = l.timestamp ? l.timestamp.replace('T', ' ').substring(0, 16) : '—';
            rows += `<tr>
                <td>${i + 1}</td>
                <td>${ts}</td>
                <td>${l.counterparty || '—'}</td>
                <td><span class="badge-yel">${l.distance_km} km</span></td>
                <td>${l.tower_lat.toFixed(5)}, ${l.tower_lon.toFixed(5)}</td>
                <td><span class="badge-${l.direction === 'outgoing' ? 'indigo' : 'cyan'}">${l.direction}</span></td>
            </tr>`;
        });
        document.getElementById('proximityContent').innerHTML = `
            <div style="overflow-x:auto">
            <table class="cdr-table">
                <thead><tr><th>#</th><th>Timestamp</th><th>Counterparty</th><th>Distance</th><th>Tower (Lat, Lon)</th><th>Direction</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
            </div>`;
    }

    /* ── Top contacts ── */
    const contactsCard = document.getElementById('contactsCard');
    contactsCard.style.display = 'block';
    if (top_contacts.length === 0) {
        document.getElementById('contactsContent').innerHTML =
            `<div style="color:#64748b;font-size:.82rem">No contact data available.</div>`;
    } else {
        const maxCount = top_contacts[0].count;
        let bars = '';
        const rankColors = ['#6366f1', '#818cf8', '#22d3ee', '#34d399', '#fbbf24'];
        top_contacts.forEach((c, i) => {
            const pct = Math.round((c.count / maxCount) * 100);
            bars += `
                <div class="contact-bar-wrap">
                    <div class="contact-bar-label">
                        <span style="font-family:'Share Tech Mono',monospace">
                          <span style="color:${rankColors[i]};">#${i + 1}</span>&nbsp;&nbsp;${c.number}
                        </span>
                        <span>${c.count} call${c.count !== 1 ? 's' : ''}</span>
                    </div>
                    <div class="contact-bar">
                        <div class="contact-bar-fill" style="width:0%;background:linear-gradient(90deg,${rankColors[i]},${rankColors[i]}88)"
                             data-target="${pct}"></div>
                    </div>
                </div>`;
        });
        document.getElementById('contactsContent').innerHTML = bars;
        // Animate bars
        setTimeout(() => {
            document.querySelectorAll('.contact-bar-fill').forEach(el => {
                el.style.width = el.dataset.target + '%';
            });
        }, 100);
    }

    /* ── Timeline list ── */
    const tlCard = document.getElementById('timelineCard');
    tlCard.style.display = 'block';
    if (timeline.length === 0) {
        document.getElementById('timelineContent').innerHTML =
            `<div style="color:#64748b;font-size:.82rem">No activity found for target number.</div>`;
    } else {
        let items = '';
        timeline.forEach((ev, i) => {
            const ts = ev.timestamp ? ev.timestamp.replace('T', ' ').substring(0, 16) : '—';
            const dir = ev.direction === 'outgoing' ? '📤' : '📥';
            items += `
                <div class="timeline-entry">
                    <div class="timeline-step">${i + 1}</div>
                    <div style="flex:1">
                        <div style="font-family:'Share Tech Mono',monospace;font-size:.78rem;color:#94a3b8;">${ts}</div>
                        <div style="font-size:.83rem;color:#e2e8f0;margin:.18rem 0">
                            ${dir} <span style="color:#818cf8">${ev.counterparty || '—'}</span>
                            &nbsp;•&nbsp;
                            <span style="color:#64748b">${ev.duration_sec !== null ? ev.duration_sec + 's' : '—'}</span>
                        </div>
                        <div style="font-size:.74rem;color:#475569">
                            📡 ${ev.tower_lat.toFixed(5)}, ${ev.tower_lon.toFixed(5)}
                        </div>
                    </div>
                </div>`;
        });
        document.getElementById('timelineContent').innerHTML = items;
    }
}

/* ── Alert helper ─────────────────────────────────────────────────────── */
function showAlert(msg, type = 'warn') {
    document.getElementById('alertBox').innerHTML =
        `<div class="cdr-alert cdr-alert-${type}">
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'info-circle'} mr-2"></i>${msg}
         </div>`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function clearAlert() { document.getElementById('alertBox').innerHTML = ''; }

/* ── File input feedback ──────────────────────────────────────────────── */
document.getElementById('cdrFileInput').addEventListener('change', function () {
    const name = this.files[0] ? this.files[0].name : '';
    document.getElementById('fileNameDisplay').textContent = name ? `📂 ${name}` : '';
});

const dropZone = document.getElementById('dropZone');
['dragover', 'dragenter'].forEach(evt => dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add('drag-over'); }));
['dragleave', 'drop'].forEach(evt => dropZone.addEventListener(evt, () => dropZone.classList.remove('drag-over')));

/* ── Form submission (AJAX) ───────────────────────────────────────────── */
document.getElementById('cdrForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    clearAlert();

    const btn = document.getElementById('analyzeBtn');
    const loader = document.getElementById('cdrLoader');

    btn.disabled = true;
    loader.classList.add('active');

    const formData = new FormData(this);

    try {
        const res = await fetch('/analyze-cdr', {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        });

        const contentType = res.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            throw new Error(`Server returned status ${res.status}. Please check your inputs or try refreshing.`);
        }

        const data = await res.json();

        if (res.ok && data.status === 'success') {
            renderResult(data);
        } else {
            showAlert(data.message || 'Analysis failed. Please check your inputs.', 'error');
        }
    } catch (err) {
        showAlert('Analysis Error: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        loader.classList.remove('active');
    }
});

/* ── Clear button ─────────────────────────────────────────────────────── */
document.getElementById('clearBtn').addEventListener('click', function () {
    document.getElementById('cdrForm').reset();
    document.getElementById('fileNameDisplay').textContent = '';
    clearAlert();
    ['proximityCard', 'contactsCard', 'timelineCard'].forEach(id => {
        document.getElementById(id).style.display = 'none';
    });
    document.getElementById('statsStrip').style.setProperty('display', 'none', 'important');
    document.getElementById('mapLegend').style.display = 'none';
    if (map) { map.remove(); map = null; }
});

/* ── Server-side preload (form POST fallback) ─────────────────────────── */
window.addEventListener('DOMContentLoaded', function () {
    if (window.__CDR_PRELOAD__) {
        renderResult(window.__CDR_PRELOAD__);
    }

    // Initialize an empty map centered on India
    if (!map) {
        initMap(20.5937, 78.9629);
    }
});
