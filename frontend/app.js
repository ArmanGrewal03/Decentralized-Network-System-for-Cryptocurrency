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
    const h = await fetch(API_BASE + '/health');
    const d = await h.json();
    const chainLabel = d.chain_valid === false ? ' · Invalid' : ' · Valid';
    status.textContent = `API OK · Chain: ${d.length || 0} blocks${chainLabel}`;
    status.className = 'api-status ' + (d.chain_valid === false ? 'invalid' : 'ok');
  } catch (e) {
    status.textContent = 'API offline';
    status.className = 'api-status err';
  }
}

function renderBlocks(chain) {
  const list = el('blockList');
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
    el('chainLength').textContent = data.length;
    renderBlocks(data.chain);
  } catch (e) {
    el('chainLength').textContent = '—';
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
    el('balance').textContent = data.balance.toFixed(2);
  } catch (e) {
    el('balance').textContent = '0.00';
  }
}

function init() {
  el('myAddress').value = myAddress;

  el('copyAddress').onclick = () => {
    navigator.clipboard.writeText(myAddress);
    const btn = el('copyAddress');
    const oldText = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = oldText, 2000);
  };

  el('newAddress').onclick = () => {
    const newAddr = prompt('Enter a wallet name or leave blank for random:', '');
    if (newAddr === null) return;
    myAddress = newAddr.trim() || 'user_' + Math.random().toString(36).slice(2, 10);
    localStorage.setItem('wallet_address', myAddress);
    el('myAddress').value = myAddress;
    refreshBalance();
    refreshPending();
  };

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

  el('mineBtn').onclick = async () => {
    const btn = el('mineBtn');
    btn.disabled = true;
    btn.textContent = 'Mining in progress...';
    el('mineResult').classList.remove('show');
    
    try {
      const data = await api('/mine', {
        method: 'POST',
        body: JSON.stringify({ miner_address: myAddress }),
      });
      showResult('mineResult', `Mined Block #${data.block.index}. Reward received.`);
      refreshChain();
      refreshPending();
      refreshBalance();
    } catch (err) {
      showResult('mineResult', err.message, true);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Mine New Block';
      setTimeout(() => el('mineResult').classList.remove('show'), 5000);
    }
  };

  el('refreshChain').onclick = () => {
    refreshChain();
    refreshPending();
    refreshBalance();
  };

  refreshChain();
  refreshPending();
  refreshBalance();
}

init();

