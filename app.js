/**
 * app.js - MEDINT Dashboard Engine
 */

const DATA_URL = 'data.json';
const REFRESH_INTERVAL = 60000; // 60s - dashboard refreshes itself, no reload needed
const FRESH_THRESHOLD_MINUTES = 60; // articles newer than this pulse green (osint uses 30 - here widened to 1h)
const MAX_ARTICLES_PER_CATEGORY = 30;

document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setInterval(loadData, REFRESH_INTERVAL);
});

function isFresh(dateStr) {
    const d = new Date(dateStr);
    if (isNaN(d)) return false;
    const diffMinutes = (Date.now() - d.getTime()) / 60000;
    return diffMinutes >= 0 && diffMinutes <= FRESH_THRESHOLD_MINUTES;
}

const articleDateFormatter = new Intl.DateTimeFormat('pl-PL', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Warsaw',
});

function formatArticleDate(dateStr) {
    const d = new Date(dateStr);
    if (isNaN(d)) return '';
    return articleDateFormatter.format(d);
}

async function loadData() {
    try {
        const response = await fetch(`${DATA_URL}?t=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) throw new Error('Failed to load data');
        const data = await response.json();

        const timeEl = document.getElementById('update-time');
        if (timeEl) {
            const d = new Date(data.last_updated);
            timeEl.textContent = isNaN(d) ? data.last_updated : d.toLocaleString('pl-PL', { timeZone: 'Europe/Warsaw' });
        }

        updateCriticalTicker(data.critical_alerts);
        renderDailyTop5(data.daily_top5);
        renderMedicalAlerts(data.critical_alerts);

        renderNews('news-poland', data.poland);
        renderNews('news-world', data.world);
        renderNews('news-guidelines', data.guidelines);
        renderNews('news-epidemiology', data.epidemiology);
        renderNews('news-clinical-trials', data.clinical_trials);
        renderNews('news-pharma-market', data.pharma_market);

    } catch (err) {
        console.error('Error loading dashboard data:', err);
    }
}

function updateCriticalTicker(alerts) {
    const track = document.getElementById('critical-ticker');
    const a = document.getElementById('critical-alert-text-a');
    const b = document.getElementById('critical-alert-text-b');
    if (!track || !a || !b) return;
    const items = (alerts && alerts.length ? alerts : [{ title: 'Sytuacja stabilna - brak nowych alertów medycznych', url: '' }]);
    const plainText = items.map((al) => al.title).join('   •   ');
    const html = items.map((al) => (al.url
        ? `<a href="${al.url}" target="_blank" rel="noopener noreferrer">${al.title}</a>`
        : `<span>${al.title}</span>`)).join('   •   ');
    a.innerHTML = html;
    b.innerHTML = html;
    // Slow, constant reading speed regardless of how much text there is -
    // longer alert lists get a longer loop instead of scrolling faster.
    // (Slowed down further per request: higher floor + slower per-character rate.)
    track.style.animationDuration = `${Math.max(32, plainText.length * 0.28)}s`;
}

function renderDailyTop5(items) {
    const container = document.getElementById('daily-top5');
    if (!container) return;
    if (!items || items.length === 0) {
        container.innerHTML = '<p class="text-slate-400 text-xs">Brak wystarczających danych do wyboru najważniejszych wydarzeń.</p>';
        return;
    }
    container.innerHTML = items.map((article, i) => `
        <div class="top5-item">
            <span class="top5-rank">${i + 1}</span>
            <div class="min-w-0 flex-1">
                <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="top5-title">${article.title}</a>
                <div class="top5-meta">${article.source || 'Źródło'} &middot; ${formatArticleDate(article.date)}</div>
            </div>
        </div>
    `).join('');
}

function renderMedicalAlerts(alerts) {
    const container = document.getElementById('medical-alerts');
    if (!container) return;
    const stable = !alerts || alerts.length === 0 || (alerts.length === 1 && !alerts[0].url);
    if (stable) {
        container.innerHTML = '<p class="text-slate-400 text-xs">Brak nowych alertów medycznych.</p>';
        return;
    }
    container.innerHTML = alerts.map((alert) => `
        <div class="alert-card">
            <div class="alert-card-tag">🔴 ALERT</div>
            <a href="${alert.url}" target="_blank" rel="noopener noreferrer" class="alert-card-title">${alert.title}</a>
            ${alert.summary ? `<p class="alert-card-summary">${alert.summary}</p>` : ''}
            <div class="alert-card-meta">${alert.source || ''} ${alert.date ? '&middot; ' + formatArticleDate(alert.date) : ''}</div>
        </div>
    `).join('');
}

function renderNews(containerId, articles) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    if (!articles) return;
    const list = articles.slice(0, MAX_ARTICLES_PER_CATEGORY);
    list.forEach((article) => {
        const fresh = isFresh(article.date);
        const card = document.createElement('div');
        card.className = `news-card${fresh ? ' new-article' : ''}`;
        const confirmedBadge = article.confirmed_by > 1
            ? `<span class="confirmed-badge">Potwierdzone przez ${article.confirmed_by} źródła</span>`
            : '';
        card.innerHTML = `
            <h3 class="news-title">${article.title}${confirmedBadge}</h3>
            <p class="news-snippet">${article.summary}</p>
            <div class="news-footer">
                <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="news-link">${article.source || 'Źródło'} &rarr;</a>
                <span class="news-date">${formatArticleDate(article.date)}</span>
            </div>
        `;
        container.appendChild(card);
    });
}
