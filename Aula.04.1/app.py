"""
StoreMaster V2 - Main Backend Application
Padrão Arquitetural: Flask API + SQLite + Gerenciamento Single Page App
"""
from flask import Flask, request, jsonify, render_template
import sqlite3
import hashlib
import time
import os
from functools import wraps

app = Flask(__name__)
# Para criar tudo na mesma pasta Base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'storemaster.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa as tabelas exigidas pelo StoreMaster V2."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela 1: Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Tabela 2: Estoque (CRUD Completo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    ''')
    
    # Tabela 3: Vendas PDV
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Default super-user
    cursor.execute("SELECT id FROM users WHERE username='admin'")
    if not cursor.fetchone():
        senha_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", senha_hash))
        
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return jsonify({"erro": "Acesso não autorizado."}), 401
        
        # Simula validação jwt básica de token (comprimento)
        if len(token) < 20: 
            return jsonify({"erro": "Sessão inválida."}), 401
            
        return f(*args, **kwargs)
    return decorated_function

# ======================== ROTAS WEB E API ========================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    """Docstring Padrão - EndPoint de Autenticação com SQLite e JWT."""
    data = request.json
    usuario = data.get("usuario")
    senha = data.get("senha")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (usuario,))
    row = cursor.fetchone()
    conn.close()
    
    if not row: return jsonify({"erro": "Usuário incorreto"}), 404
        
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    if row["password_hash"] != senha_hash:
        return jsonify({"erro": "Credenciais incorretas."}), 401
        
    header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    payload = f"usr_{usuario}_exp{int(time.time())+3600}"
    signature = hashlib.sha256((header+payload).encode()).hexdigest()[:16]
    
    return jsonify({"token": f"{header}.{payload}.{signature}"}), 200

@app.route("/api/products", methods=["GET", "POST"])
@login_required
def products():
    """Retorna listagem de produtos ou adiciona um novo"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == "GET":
        cursor.execute("SELECT * FROM products")
        prods = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(prods)
        
    if request.method == "POST":
        data = request.json
        if not data.get("name") or data.get("quantity") < 0 or data.get("price") < 0:
            return jsonify({"erro": "Dados inválidos."}), 400
            
        cursor.execute("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)", 
                       (data["name"], data["quantity"], data["price"]))
        conn.commit()
        conn.close()
        return jsonify({"mensagem": "Item incluído"}), 201

@app.route("/api/products/<int:prod_id>", methods=["DELETE"])
@login_required
def delete_product(prod_id):
    """Apaga logicamente ou fisicamente o produto."""
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (prod_id,))
    conn.commit()
    conn.close()
    return jsonify({}), 200

@app.route("/api/sales", methods=["GET", "POST"])
@login_required
def sales():
    """Gera vendas dinâmicas no PDV e lista último relatório."""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == "GET":
        cursor.execute('''
            SELECT s.id, p.name as product_name, s.quantity, s.total_price, s.sale_date 
            FROM sales s LEFT JOIN products p ON s.product_id = p.id
            ORDER BY s.sale_date DESC LIMIT 50
        ''')
        v = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(v), 200
        
    if request.method == "POST":
        data = request.json
        pid = data.get("product_id")
        qtd = data.get("quantity")
        
        cursor.execute("SELECT id, price, quantity FROM products WHERE id=?", (pid,))
        prod = cursor.fetchone()
        
        if not prod or prod["quantity"] < qtd:
            conn.close()
            return jsonify({"erro": "Estoque insuficiente"}), 400
            
        total = float(prod["price"]) * float(qtd)
        cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id=?", (qtd, pid))
        cursor.execute("INSERT INTO sales (product_id, quantity, total_price) VALUES (?, ?, ?)", (pid, qtd, total))
        conn.commit()
        conn.close()
        return jsonify({"msg": "Sucesso", "total": total}), 201

@app.route("/api/dashboard", methods=["GET"])
@login_required
def dashboard_stats():
    """Fornece dados macro-financeiros e insumos pro Chart.js"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_price) as r FROM sales")
    faturamento = (cursor.fetchone()["r"] or 0)
    
    cursor.execute("SELECT name, quantity FROM products ORDER BY quantity DESC LIMIT 5")
    chart = [{"name": r["name"], "quantity": r["quantity"]} for r in cursor.fetchall()]
    conn.close()
    
    return jsonify({"faturamento": faturamento, "chart_data": chart}), 200

if __name__ == "__main__":
    init_db()
    # Atuando em Host acessível
    app.run(host="0.0.0.0", port=5000)
