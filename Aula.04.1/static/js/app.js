let token = localStorage.getItem('sm_token');
let chartInstance = null;

async function api(route, method="GET", body=null) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    
    const res = await fetch(route, opts);
    if (res.status === 401) { logout(); throw new Error("Não autorizado"); }
    const data = await res.json();
    if (!res.ok) throw new Error(data.erro || "Erro na API");
    return data;
}

// LOGIN FLOW
async function loginAPI() {
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    const err = document.getElementById('login-error');
    err.classList.add('hidden');
    
    try {
        const data = await api('/api/login', 'POST', { usuario: u, senha: p });
        token = data.token;
        localStorage.setItem('sm_token', token);
        document.getElementById('login-overlay').classList.add('hidden');
        document.getElementById('app-wrapper').classList.remove('hidden');
        initApp();
    } catch(e) {
        err.innerText = e.message;
        err.classList.remove('hidden');
    }
}

function logout() {
    token = null;
    localStorage.removeItem('sm_token');
    document.getElementById('app-wrapper').classList.add('hidden');
    document.getElementById('login-overlay').classList.remove('hidden');
}

// NAVIGATION
function nav(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    
    document.getElementById(`view-${viewId}`).classList.add('active');
    document.getElementById(`nav-${viewId}`).classList.add('active');
    
    if (viewId === 'dashboard') loadDashboard();
    if (viewId === 'produtos') loadProdutos();
    if (viewId === 'vendas') loadVendas();
}

// INITIALIZATION
function initApp() {
    nav('dashboard');
}

if (token) {
    document.getElementById('login-overlay').classList.add('hidden');
    document.getElementById('app-wrapper').classList.remove('hidden');
    initApp();
}

// DASHBOARD
async function loadDashboard() {
    const data = await api('/api/dashboard');
    document.getElementById('kpi-faturamento').innerText = `R$ ${parseFloat(data.faturamento).toFixed(2)}`;
    
    const ctx = document.getElementById('myChart');
    if (chartInstance) chartInstance.destroy();
    
    const labels = data.chart_data.map(d => d.name);
    const values = data.chart_data.map(d => d.quantity);

    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Unidades em Estoque',
                data: values,
                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } },
            plugins: { legend: { labels: { color: '#94a3b8' } } }
        }
    });
}

// PRODUTOS
async function loadProdutos() {
    const prods = await api('/api/products');
    const tb = document.querySelector('#tabela-produtos tbody');
    const select = document.getElementById('venda-produto-id');
    tb.innerHTML = ''; select.innerHTML = '';
    
    prods.forEach(p => {
        tb.innerHTML += `<tr>
            <td>#${p.id}</td><td>${p.name}</td><td>${p.quantity}</td>
            <td>R$ ${p.price.toFixed(2)}</td>
            <td><button onclick="delProduto(${p.id})" style="color:#ef4444; background:transparent"><i class="fa fa-trash"></i></button></td>
        </tr>`;
        select.innerHTML += `<option value="${p.id}">${p.name} (Disp: ${p.quantity}) - R$ ${p.price.toFixed(2)}</option>`;
    });
}

async function addProduto() {
    const n = document.getElementById('prod-nome').value;
    const q = document.getElementById('prod-qtd').value;
    const p = document.getElementById('prod-preco').value;
    if (!n || !q || !p) return alert("Preencha tudo");
    
    await api('/api/products', 'POST', { name: n, quantity: parseInt(q), price: parseFloat(p) });
    loadProdutos();
}

async function delProduto(id) {
    if (!confirm("Excluir item?")) return;
    await api(`/api/products/${id}`, 'DELETE');
    loadProdutos();
}

// VENDAS
async function loadVendas() {
    await loadProdutos(); // Atualiza select
    const vendas = await api('/api/sales');
    const tb = document.querySelector('#tabela-vendas tbody');
    tb.innerHTML = '';
    vendas.forEach(v => {
        tb.innerHTML += `<tr>
            <td>#${v.id}</td><td>${v.product_name}</td><td>${v.quantity}</td>
            <td style="color:#10b981">R$ ${v.total_price.toFixed(2)}</td>
            <td>${v.sale_date}</td>
        </tr>`;
    });
}

async function registrarVenda() {
    const p = document.getElementById('venda-produto-id').value;
    const q = document.getElementById('venda-qtd').value;
    if (!p || !q) return alert("Preencha para faturar");
    
    try {
        await api('/api/sales', 'POST', { product_id: parseInt(p), quantity: parseInt(q) });
        loadVendas();
        alert("Venda registrada com sucesso!");
    } catch(e) { alert(e.message); }
}
