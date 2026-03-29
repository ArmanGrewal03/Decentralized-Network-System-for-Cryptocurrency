const API_BASE = window.location.origin;

let myAddress = localStorage.getItem('wallet_address') || 'alice';

function el(id) {
  return document.getElementById(id);
}

function showResult(eltId, message, isError = false) {
  const elt = el(eltId);
  if (!elt) return;
  elt.textContent = message;
  elt.className = 'result show ' + (isError ? 'error' : 'success');
}

async function api(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = Array.isArray(data.detail) ? data.detail.map(d => d.msg || d).join(', ') : (data.detail || data.message || res.statusText);
    throw new Error(msg);
  }
  return data;
}

async function checkApi() {
  const status = el('apiStatus');
  try {
    const data = await api('/status');
    status.textContent = data.chain_valid ? 'Chain Valid' : 'Chain INVALID';
    status.className = 'api-status ' + (data.chain_valid ? 'ok' : 'invalid');
  } catch (err) {
    status.textContent = 'Offline';
    status.className = 'api-status err';
  }
}

async function refreshEvents() {
  const container = el('consoleOutput');
  if (!container) return;
  try {
    const data = await api('/events');
    if (!Array.isArray(data.events)) return;
    container.innerHTML = data.events.map(ev => `
      <div class="log-entry ${ev.type.toLowerCase()}">
        <span class="timestamp">[${new Date(ev.timestamp * 1000).toLocaleTimeString()}]</span>
        <span class="tag">${ev.type}</span>: ${ev.message}
      </div>
    `).reverse().join('') || '<div class="log-entry system">Waiting for events...</div>';
  } catch (err) {
    console.warn("Event poll failed", err);
  }
}

function renderBlocks(chain) {
  const list = el('blockList');
  if (!list) return;
  list.innerHTML = '';
  if (!chain || chain.length === 0) {
    list.innerHTML = '<div class="empty-state">Blockchain is empty</div>';
    return;
  }
  chain.slice().reverse().forEach((b) => {
    const div = document.createElement('div');
    div.className = 'block-item';
    div.innerHTML = `
      <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <strong>Block #${b.index}</strong>
        <span style="color: var(--muted); font-size: 0.75rem;">${new Date(b.timestamp * 1000).toLocaleString()}</span>
      </div>
      <div class="hash" title="${b.hash}">${b.hash}</div>
      <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--accent);">
        Transactions: ${b.transactions ? b.transactions.length : 0}
      </div>
    `;
    list.appendChild(div);
  });
}

function renderPending(pending) {
  const list = el('pendingList');
  if (!list) return;
  const countLabel = el('pendingCount');
  if (countLabel) countLabel.textContent = pending ? pending.length : 0;
  
  list.innerHTML = '';
  if (!pending || pending.length === 0) {
    list.innerHTML = '<div class="empty-state">No pending transactions</div>';
    return;
  }
  
  pending.forEach((tx) => {
    const div = document.createElement('div');
    div.className = 'tx-item' + (tx.signature ? ' signed' : '');
    div.innerHTML = `
      <div style="display: flex; justify-content: space-between;">
        <span><strong>${tx.sender}</strong> &rarr; <strong>${tx.receiver}</strong></span>
        <span style="color: var(--green); font-weight: 700;">${tx.amount.toFixed(2)} COIN</span>
      </div>
      <div style="font-size: 0.7rem; color: var(--muted); margin-top: 0.25rem;">ID: ${tx.id.slice(0, 8)}...</div>
    `;
    list.appendChild(div);
  });
}

async function refreshChain() {
  try {
    const data = await api('/chain');
    if (el('chainLength')) el('chainLength').textContent = data.length;
    renderBlocks(data.chain);
  } catch (e) {
    if (el('chainLength')) el('chainLength').textContent = '—';
    renderBlocks([]);
  }
}

async function refreshPending() {
  try {
    const data = await api('/transactions/pending');
    renderPending(data.pending);
  } catch (e) {
    renderPending([]);
  }
}

async function refreshBalance() {
  try {
    const data = await api('/balance/' + encodeURIComponent(myAddress));
    if (el('balance')) el('balance').textContent = data.balance.toFixed(2);
  } catch (e) {
    if (el('balance')) el('balance').textContent = '0.00';
  }
}

function init() {
  if (el('myAddress')) el('myAddress').value = myAddress;

  if (el('copyAddress')) {
    el('copyAddress').onclick = () => {
      navigator.clipboard.writeText(myAddress);
      const btn = el('copyAddress');
      const oldText = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => btn.textContent = oldText, 2000);
    };
  }

  if (el('newAddress')) {
    el('newAddress').onclick = () => {
      const newAddr = prompt('Enter a wallet name:', '');
      if (newAddr === null) return;
      myAddress = newAddr.trim() || 'user_' + Math.random().toString(36).slice(2, 10);
      localStorage.setItem('wallet_address', myAddress);
      el('myAddress').value = myAddress;
      refreshBalance();
      refreshPending();
    };
  }

  if (el('sendForm')) {
    el('sendForm').onsubmit = async (e) => {
      e.preventDefault();
      const to = el('toAddress').value.trim();
      const amount = parseFloat(el('amount').value);
      if (!to || amount <= 0) return;
      
      const submitBtn = e.target.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending...';
      
      try {
        await api('/transactions', {
          method: 'POST',
          body: JSON.stringify({ sender: myAddress, receiver: to, amount }),
        });
        showResult('sendResult', 'Transaction signed and broadcasted.');
        el('toAddress').value = '';
        el('amount').value = '';
        refreshPending();
        refreshBalance();
      } catch (err) {
        showResult('sendResult', err.message, true);
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Transaction';
        setTimeout(() => el('sendResult').classList.remove('show'), 5000);
      }
    };
  }

  if (el('mineBtn')) {
    el('mineBtn').onclick = async () => {
      const btn = el('mineBtn');
      btn.disabled = true;
      btn.textContent = 'Mining...';
      
      try {
        const data = await api('/mine', {
          method: 'POST',
          body: JSON.stringify({ miner_address: myAddress }),
        });
        showResult('mineResult', `Mined Block #${data.block.index}.`);
        refreshChain();
        refreshPending();
        refreshBalance();
      } catch (err) {
        showResult('mineResult', err.message, true);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Mine New Block';
      }
    };
  }

  if (el('refreshChain')) {
    el('refreshChain').onclick = () => {
      refreshChain();
      refreshPending();
      refreshBalance();
    };
  }

  const demoInvalidSigBtn = el('demoInvalidSigBtn');
  if (demoInvalidSigBtn) {
    demoInvalidSigBtn.onclick = async () => {
      const box = el('demoInvalidSigBox');
      const iconEl = el('demoInvalidSigIcon');
      const titleEl = el('demoInvalidSigTitle');
      const detailEl = el('demoInvalidSigDetail');
      const step1 = el('demoStep1');
      const step2 = el('demoStep2');
      const step3 = el('demoStep3');
      if (!box) return;

      box.className = 'demo-result-box demo-result-pending';
      if (iconEl) iconEl.textContent = '⋯';
      if (titleEl) titleEl.textContent = 'Checking…';
      if (detailEl) detailEl.textContent = '';
      if (step1) step1.classList.add('active');
      if (step2) step2.classList.remove('active');
      if (step3) step3.classList.remove('active');
      el('demoInvalidSigData').style.display = 'none';

      await new Promise(r => setTimeout(r, 600));
      if (step1) step1.classList.remove('active');
      if (step2) step2.classList.add('active');

      el('demoInvalidSigData').style.display = 'block';
      el('demoOriginalTx').innerHTML = JSON.stringify({
        sender: "attacker", receiver: "bob", amount: 1, signature: "v2.sig.88ac..."
      }, null, 2);
      el('demoForgedTx').innerHTML = JSON.stringify({
        sender: "attacker", receiver: "bob", amount: 100, signature: "v2.sig.88ac..."
      }, null, 2).replace('"amount": 100', '<span class="highlight-red">"amount": 100</span>');

      el('demoLogicHash').textContent = "Hash Check Failed";
      el('demoVerificationOutcome').style.display = 'block';

      try {
        await api('/demo/try-invalid-signature', { method: 'POST' });
        box.className = 'demo-result-box demo-result-accepted';
        if (iconEl) iconEl.textContent = '⚠';
        if (titleEl) titleEl.textContent = 'Accepted (Error)';
      } catch (err) {
        box.className = 'demo-result-box demo-result-rejected';
        if (iconEl) iconEl.textContent = '✓';
        if (titleEl) titleEl.textContent = 'Rejected';
        if (detailEl) detailEl.textContent = err.message || 'Tamper detected.';
      }
      if (step2) step2.classList.remove('active');
      if (step3) step3.classList.add('active');
      refreshEvents();
    };
  }

  refreshChain();
  refreshPending();
  refreshBalance();
  checkApi();
}

init();
