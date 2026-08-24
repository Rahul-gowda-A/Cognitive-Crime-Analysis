function ChangeLabel() {
    let text1 = document.getElementById("prediction-text");
    if (!text1) return;
    let text = text1.textContent.trim();

    if (text.startsWith("ERROR:") || !text.includes("[")) {
        text1.innerHTML = `<div style="color: #ff4d4f; font-size: 16px; font-weight: bold; padding: 12px; background: rgba(255, 77, 79, 0.1); border: 1px solid rgba(255, 77, 79, 0.3); border-radius: 8px;"><i class="fas fa-exclamation-triangle mr-2"></i> ${text}</div>`;
        return;
    }

    let zone = "UNKNOWN ZONE";
    let color = "#00f0ff";
    if (text.includes("GREEN ZONE")) {
        zone = "GREEN ZONE";
        color = "#10b981";
    } else if (text.includes("ORANGE ZONE")) {
        zone = "ORANGE ZONE";
        color = "#f59e0b";
    } else if (text.includes("RED ZONE")) {
        zone = "RED ZONE";
        color = "#ef4444";
    }

    let zoneHtml = `<div style="text-align: center; color: ${color}; font-size: 32px; font-weight: 800; font-family: var(--font-cyber, monospace); letter-spacing: 2px; text-shadow: 0 0 15px ${color}; margin-bottom: 20px;">${zone}</div>`;

    // Extract values inside brackets
    let matches = text.match(/\[(.*)\]/);
    if (!matches) {
        text1.innerHTML = zoneHtml;
        return;
    }

    let inner = matches[1].replace(/array\(/g, '').replace(/\)/g, '').replace(/dtype=[^,]+/g, '');
    let items = inner.split(',').map(s => s.trim().replace(/^['"]|['"]$/g, '')).filter(s => s.length > 0);

    var tableBody = '<div style="overflow-x: auto; margin-top: 15px;"><table class="table shadow-soft rounded" style="width: 100%; border-collapse: collapse;">';
    tableBody += '<thead><tr>';
    tableBody += '<th>STATE</th>';
    tableBody += '<th>DISTRICT</th>';
    tableBody += '<th>YEAR</th>';
    tableBody += '<th>MURDER</th>';
    tableBody += '<th>ATTEMPT TO MURDER</th>';
    tableBody += '<th>RAPE</th>';
    tableBody += '<th>KIDNAPPING & ABDUCTION</th>';
    tableBody += '<th>DACOITY</th>';
    tableBody += '<th>ROBBERY</th>';
    tableBody += '<th>THEFT</th>';
    tableBody += '<th>HURT</th>';
    tableBody += '</tr></thead><tbody><tr>';

    items.forEach(function(ele) {
        tableBody += `<td style="padding: 10px 14px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.08);">${ele}</td>`;
    });
    tableBody += '</tr></tbody></table></div>';

    text1.innerHTML = zoneHtml + tableBody;
}