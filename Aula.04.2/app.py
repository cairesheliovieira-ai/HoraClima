"""
StoreMaster v2 — Backend Flask + SQLite
========================================
Sistema completo de gerenciamento de loja com:
  - Autenticacao JWT (PyJWT + bcrypt)
  - Banco de dados relacional SQLite (modulo nativo sqlite3)
  - CRUD completo: produtos, categorias, vendas
  - Dashboard com metricas avancadas (receita, lucro, graficos)
  - Google Docstring em todas as funcoes principais

Linguagens utilizadas no projeto:
  - Python  (backend, logica de negocio, API REST)
  - SQL     (schema.sql — DDL do banco de dados SQLite)
  - HTML    (estrutura do frontend SPA)
  - CSS     (estilizacao premium dark-mode)
  - JavaScript (logica do frontend, Chart.js)

Author : Aula 04.2 — Engenharia de Software
Python : 3.9+
"""

from __future__ import annotations

import os
import sqlite3
import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, g, request, jsonify, send_from_directory
import jwt
import bcrypt

# ── Configuracao da aplicacao ────────────────────────────────────────────────

app = Flask(__name__, static_folder="static", static_url_path="")
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "storemaster-v2-secret-2024"),
    JWT_HOURS=8,
    DATABASE=str(Path(__file__).parent / "storemaster.db"),
)


# ── Camada de Banco de Dados (SQLite) ────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    """Retorna a conexao SQLite associada ao contexto da requisicao atual.

    Utiliza o objeto ``g`` do Flask para armazenar a conexao durante
    o ciclo de vida de uma requisicao HTTP, garantindo que uma unica
    conexao seja reutilizada em multiplas chamadas dentro do mesmo request.

    Returns:
        sqlite3.Connection: Conexao configurada com ``row_factory=sqlite3.Row``,
            permitindo acesso aos campos por nome (como dicionario).

    Note:
        Nao e necessario fechar a conexao manualmente. O hook
        ``teardown_appcontext`` chama ``close_db()`` automaticamente
        ao fim de cada requisicao.

    Example:
        >>> with app.app_context():
        ...     db = get_db()
        ...     row = db.execute("SELECT 1 AS val").fetchone()
        ...     assert row["val"] == 1
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    """Fecha a conexao SQLite ao encerrar o contexto da aplicacao."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Inicializa o banco de dados executando o schema SQL e populando dados.

    Le o arquivo ``schema.sql`` (DDL com instrucoes CREATE TABLE IF NOT EXISTS)
    e executa todas as instrucoes SQL no banco de dados SQLite. Apos a criacao
    das tabelas, chama ``seed_db()`` para inserir dados iniciais de demonstracao.

    Raises:
        FileNotFoundError: Se o arquivo ``schema.sql`` nao for encontrado
            no mesmo diretorio que ``app.py``.
        sqlite3.OperationalError: Em caso de erro de sintaxe no SQL.

    Example:
        >>> # Chamado automaticamente no __main__:
        >>> init_db()   # idempotente — seguro chamar multiplas vezes
    """
    schema_path = Path(__file__).parent / "schema.sql"
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        with open(schema_path, encoding="utf-8") as f:
            conn.executescript(f.read())
        seed_db(conn)
        conn.commit()


def seed_db(conn: sqlite3.Connection) -> None:
    """Popula dados de demonstracao se o banco estiver vazio.

    Verifica se ja existem usuarios cadastrados. Se nao houver,
    insere um administrador padrao e um conjunto de categorias
    e produtos de exemplo para facilitar a demonstracao em aula.
    Usa ``INSERT OR IGNORE`` para ser idempotente.

    Args:
        conn (sqlite3.Connection): Conexao ativa com o banco de dados.
            Deve ter ``PRAGMA foreign_keys = ON`` ativado.

    Note:
        Senha padrao do admin: ``admin123`` (hash bcrypt armazenado).
        Altere imediatamente em ambiente de producao.
    """
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        return

    # Administrador padrao
    pw_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT OR IGNORE INTO users(username, password_hash, name, role) VALUES(?,?,?,?)",
        ("admin", pw_hash, "Administrador", "admin"),
    )

    # Categorias com cor e icone (dados para o frontend)
    categories = [
        ("Eletronicos",    "#6366f1", "💻"),
        ("Perifericos",    "#06b6d4", "🖱️"),
        ("Moveis",         "#10b981", "🪑"),
        ("Armazenamento",  "#f59e0b", "💾"),
        ("Vestuario",      "#ec4899", "👕"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO categories(name, color, icon) VALUES(?,?,?)",
        categories,
    )

    # Produtos de exemplo com preco, custo, estoque e estoque minimo
    products = [
        ("Notebook Dell XPS 15",      1, 7500.00, 5400.00, 12, 5),
        ("MacBook Air M2",             1, 9800.00, 7200.00,  8, 3),
        ("Mouse Logitech MX Master",   2,  420.00,  280.00, 45, 10),
        ("Teclado Mecanico Keychron",  2,  550.00,  350.00, 30, 8),
        ("Monitor LG 27pol 4K",        1, 2800.00, 1900.00, 15, 5),
        ("Cadeira Gamer DXRacer",      3, 1200.00,  800.00,  7, 5),
        ("Mesa Gamer RGB",             3,  650.00,  410.00,  4, 5),
        ("SSD Samsung 1TB",            4,  380.00,  240.00, 60, 15),
        ("Headset HyperX Cloud II",    2,  350.00,  220.00, 25, 8),
        ("Camiseta Dev Hello World",   5,   89.90,   35.00,100, 20),
        ("Webcam Logitech C920",       2,  480.00,  310.00, 18, 5),
        ("Hub USB-C 10 portas",        4,  199.90,  110.00, 35, 10),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO products(name,category_id,price,cost,stock,min_stock)
           VALUES(?,?,?,?,?,?)""",
        products,
    )


# ── Autenticacao JWT ──────────────────────────────────────────────────────────

def authenticate_user(username: str, password: str) -> "dict | None":
    """Valida as credenciais do usuario e retorna um token JWT.

    Busca o usuario pelo username no banco SQLite (case-insensitive),
    verifica a senha fornecida contra o hash bcrypt armazenado e,
    em caso de sucesso, gera um token JWT assinado com a SECRET_KEY.

    Args:
        username (str): Nome de usuario cadastrado no sistema.
            A comparacao ignora maiusculas/minusculas.
        password (str): Senha em texto plano a ser validada
            contra o hash bcrypt armazenado no banco.

    Returns:
        dict | None: Em caso de sucesso, retorna dicionario com:
            - ``token`` (str): JWT assinado com HS256.
            - ``user`` (str): Nome de exibicao do usuario.
            - ``role`` (str): Perfil do usuario (`admin` ou `seller`).
            - ``user_id`` (int): ID primario do usuario.
            Retorna ``None`` se as credenciais forem invalidas.

    Raises:
        ValueError: Se ``username`` ou ``password`` forem strings vazias.

    Example:
        >>> with app.app_context():
        ...     init_db()
        ...     result = authenticate_user("admin", "admin123")
        ...     assert result is not None
        ...     assert result["role"] == "admin"
        ...     assert authenticate_user("admin", "errada") is None
    """
    if not username or not password:
        raise ValueError("username e password nao podem ser vazios.")

    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,)
    ).fetchone()

    if not row:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return None

    exp = datetime.datetime.utcnow() + datetime.timedelta(hours=app.config["JWT_HOURS"])
    token = jwt.encode(
        {"sub": row["id"], "username": row["username"], "role": row["role"], "exp": exp},
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return {"token": token, "user": row["name"], "role": row["role"], "user_id": row["id"]}


def token_required(f):
    """Decorador que protege rotas exigindo um Bearer JWT valido.

    Extrai o token do cabecalho HTTP ``Authorization: Bearer <token>``,
    decodifica e valida com PyJWT. Se valido, injeta o payload decodificado
    como primeiro argumento posicional da funcao decorada.

    Args:
        f (callable): Funcao de rota Flask a ser protegida.

    Returns:
        callable: Funcao wrapper com validacao JWT integrada.

    Raises:
        401 Unauthorized: Token ausente, mal-formatado, expirado ou invalido.

    Example:
        >>> @app.route("/api/exemplo")
        ... @token_required
        ... def rota_protegida(current_user):
        ...     return jsonify({"username": current_user["username"]})
    """
    @wraps(f)
    def _wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Token ausente ou mal-formatado."}), 401
        token = header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado. Faca login novamente."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token invalido."}), 401
        return f(payload, *args, **kwargs)
    return _wrapper


# ── Endpoint: Autenticacao ───────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    """Autentica o usuario e retorna token JWT."""
    body = request.get_json(force=True) or {}
    try:
        result = authenticate_user(
            body.get("username", "").strip(),
            body.get("password", "").strip(),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if not result:
        return jsonify({"error": "Credenciais invalidas."}), 401
    return jsonify(result), 200


# ── Endpoint: Categorias ─────────────────────────────────────────────────────

@app.route("/api/categories", methods=["GET"])
@token_required
def list_categories(cu):
    """Retorna todas as categorias ordenadas por nome."""
    rows = get_db().execute("SELECT * FROM categories ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows]), 200


# ── Endpoint: Produtos ───────────────────────────────────────────────────────

def _product_row_to_dict(row) -> dict:
    """Converte uma Row de produto SQLite para dicionario Python."""
    d = dict(row)
    d["margin_pct"] = round((d["price"] - d["cost"]) / d["price"] * 100, 1) if d["price"] > 0 else 0
    return d


PRODUCT_SELECT = """
    SELECT p.*,
           c.name  AS category_name,
           c.color AS category_color,
           c.icon  AS category_icon
    FROM products p
    LEFT JOIN categories c ON c.id = p.category_id
"""


@app.route("/api/products", methods=["GET"])
@token_required
def list_products(cu):
    """Lista todos os produtos com dados de categoria e margem de lucro."""
    rows = get_db().execute(PRODUCT_SELECT + " ORDER BY p.name").fetchall()
    return jsonify([_product_row_to_dict(r) for r in rows]), 200


@app.route("/api/products", methods=["POST"])
@token_required
def create_product(cu):
    """Cria um novo produto no catalogo."""
    b = request.get_json(force=True) or {}
    name   = (b.get("name") or "").strip()
    price  = b.get("price")
    cost   = float(b.get("cost") or 0)
    stock  = int(b.get("stock") or 0)
    min_s  = int(b.get("min_stock") or 5)
    cat_id = b.get("category_id")

    if not name or price is None:
        return jsonify({"error": "Campos 'name' e 'price' sao obrigatorios."}), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO products(name,category_id,price,cost,stock,min_stock) VALUES(?,?,?,?,?,?)",
        (name, cat_id, float(price), cost, stock, min_s),
    )
    db.commit()
    row = db.execute(PRODUCT_SELECT + " WHERE p.id=?", (cur.lastrowid,)).fetchone()
    return jsonify(_product_row_to_dict(row)), 201


@app.route("/api/products/<int:pid>", methods=["PUT"])
@token_required
def update_product(cu, pid):
    """Atualiza um produto existente."""
    db = get_db()
    p = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not p:
        return jsonify({"error": "Produto nao encontrado."}), 404

    b = request.get_json(force=True) or {}
    db.execute(
        "UPDATE products SET name=?,price=?,cost=?,stock=?,min_stock=?,category_id=? WHERE id=?",
        (
            (b.get("name") or p["name"]).strip(),
            float(b.get("price", p["price"])),
            float(b.get("cost", p["cost"])),
            int(b.get("stock", p["stock"])),
            int(b.get("min_stock", p["min_stock"])),
            b.get("category_id", p["category_id"]),
            pid,
        ),
    )
    db.commit()
    row = db.execute(PRODUCT_SELECT + " WHERE p.id=?", (pid,)).fetchone()
    return jsonify(_product_row_to_dict(row)), 200


@app.route("/api/products/<int:pid>", methods=["DELETE"])
@token_required
def delete_product(cu, pid):
    """Remove um produto do catalogo."""
    db = get_db()
    if not db.execute("SELECT id FROM products WHERE id=?", (pid,)).fetchone():
        return jsonify({"error": "Produto nao encontrado."}), 404
    db.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit()
    return jsonify({"message": "Produto removido com sucesso."}), 200


# ── Endpoint: Vendas ─────────────────────────────────────────────────────────

@app.route("/api/sales", methods=["GET"])
@token_required
def list_sales(cu):
    """Lista as ultimas 200 vendas com produto, vendedor e lucro."""
    rows = get_db().execute("""
        SELECT s.*,
               p.name AS product_name,
               p.cost AS product_cost,
               u.name AS seller_name,
               ROUND(s.total - (p.cost * s.quantity), 2) AS profit
        FROM sales s
        JOIN products p ON p.id = s.product_id
        JOIN users    u ON u.id = s.user_id
        ORDER BY s.sold_at DESC
        LIMIT 200
    """).fetchall()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/api/sales", methods=["POST"])
@token_required
def create_sale(cu):
    """Registra uma nova venda e decrementa o estoque do produto.

    Valida a existencia do produto, verifica a disponibilidade de
    estoque e, em caso de sucesso, cria o registro de venda e
    atualiza o estoque com uma operacao atomica no banco.

    Args (JSON body):
        product_id (int): ID do produto a ser vendido.
        quantity   (int): Quantidade vendida. Deve ser >= 1.

    Returns:
        201: Dicionario com os dados completos da venda registrada.
        400: Quantidade invalida (< 1) ou estoque insuficiente.
        404: Produto com ``product_id`` nao encontrado.

    Raises:
        400: Se ``quantity`` for 0 ou negativo.
        400: Se o estoque disponivel for menor que ``quantity``.
        404: Se ``product_id`` nao existir no banco.

    Example:
        >>> # POST /api/sales  {"product_id": 1, "quantity": 2}
        >>> # -> 201 {"id": 5, "total": 15000.00, "profit": 4200.00, ...}
    """
    b = request.get_json(force=True) or {}
    pid = b.get("product_id")
    qty = int(b.get("quantity", 0))

    if not pid or qty < 1:
        return jsonify({"error": "product_id valido e quantity >= 1 sao obrigatorios."}), 400

    db = get_db()
    p = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not p:
        return jsonify({"error": "Produto nao encontrado."}), 404
    if p["stock"] < qty:
        return jsonify({"error": f"Estoque insuficiente. Disponivel: {p['stock']} unidades."}), 400

    total = round(p["price"] * qty, 2)
    cur = db.execute(
        "INSERT INTO sales(product_id,user_id,quantity,unit_price,total) VALUES(?,?,?,?,?)",
        (pid, cu["sub"], qty, p["price"], total),
    )
    db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, pid))
    db.commit()

    sale = db.execute("""
        SELECT s.*, p.name AS product_name, u.name AS seller_name,
               ROUND(s.total - (p.cost * s.quantity), 2) AS profit
        FROM sales s
        JOIN products p ON p.id = s.product_id
        JOIN users    u ON u.id = s.user_id
        WHERE s.id = ?
    """, (cur.lastrowid,)).fetchone()
    return jsonify(dict(sale)), 201


# ── Endpoint: Dashboard ───────────────────────────────────────────────────────

@app.route("/api/dashboard", methods=["GET"])
@token_required
def dashboard(cu):
    """Retorna metricas consolidadas para o painel principal.

    Agrega dados de vendas, produtos e categorias para alimentar
    o dashboard com KPIs, graficos semanais, ranking de produtos
    e alertas de estoque critico.

    Returns:
        dict: Contendo:
            - ``total_revenue`` (float): Receita bruta acumulada.
            - ``total_profit`` (float): Lucro bruto acumulado.
            - ``total_sales`` (int): Numero total de vendas.
            - ``total_products`` (int): Produtos cadastrados.
            - ``low_stock`` (list): Produtos abaixo do min_stock.
            - ``weekly_sales`` (list): Vendas dos ultimos 7 dias.
            - ``top_products`` (list): Top 5 por receita.
            - ``category_revenue`` (list): Receita por categoria.
            - ``recent_sales`` (list): Ultimas 6 vendas.
    """
    db = get_db()

    stats = db.execute("""
        SELECT
            COALESCE(SUM(s.total), 0)                          AS total_revenue,
            COALESCE(SUM(s.total - p.cost * s.quantity), 0)    AS total_profit,
            COUNT(s.id)                                         AS total_sales,
            (SELECT COUNT(*) FROM products)                     AS total_products
        FROM sales s
        JOIN products p ON p.id = s.product_id
    """).fetchone()

    low_stock = db.execute("""
        SELECT p.id, p.name, p.stock, p.min_stock, c.icon, c.color
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.stock < p.min_stock
        ORDER BY p.stock ASC LIMIT 8
    """).fetchall()

    weekly = db.execute("""
        SELECT DATE(sold_at) AS date,
               ROUND(SUM(total), 2) AS revenue,
               COUNT(*) AS count
        FROM sales
        WHERE sold_at >= DATE('now', '-6 days')
        GROUP BY DATE(sold_at)
        ORDER BY date
    """).fetchall()

    top5 = db.execute("""
        SELECT p.name, ROUND(SUM(s.total),2) AS revenue, SUM(s.quantity) AS qty
        FROM sales s JOIN products p ON p.id = s.product_id
        GROUP BY p.id ORDER BY revenue DESC LIMIT 5
    """).fetchall()

    cat_rev = db.execute("""
        SELECT c.name, c.color, ROUND(SUM(s.total),2) AS revenue
        FROM sales s
        JOIN products  p ON p.id = s.product_id
        JOIN categories c ON c.id = p.category_id
        GROUP BY c.id ORDER BY revenue DESC
    """).fetchall()

    recent = db.execute("""
        SELECT s.id, p.name AS product_name, s.quantity, s.total,
               s.sold_at, u.name AS seller,
               ROUND(s.total - p.cost * s.quantity, 2) AS profit
        FROM sales s
        JOIN products p ON p.id = s.product_id
        JOIN users    u ON u.id = s.user_id
        ORDER BY s.sold_at DESC LIMIT 6
    """).fetchall()

    return jsonify({
        "total_revenue":    round(float(stats["total_revenue"]),  2),
        "total_profit":     round(float(stats["total_profit"]),   2),
        "total_sales":      stats["total_sales"],
        "total_products":   stats["total_products"],
        "low_stock":        [dict(r) for r in low_stock],
        "weekly_sales":     [dict(r) for r in weekly],
        "top_products":     [dict(r) for r in top5],
        "category_revenue": [dict(r) for r in cat_rev],
        "recent_sales":     [dict(r) for r in recent],
    }), 200


# ── Servir Frontend (SPA) ────────────────────────────────────────────────────

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    """Serve os arquivos estaticos do frontend ou o index.html para rotas SPA."""
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("  StoreMaster v2 - Gerenciador de Loja Premium")
    print("=" * 60)
    print("  URL    : http://127.0.0.1:5000")
    print("  Login  : admin / admin123")
    print("  DB     : storemaster.db (SQLite)")
    print("  Testes : py -m pytest test_app.py -v")
    print("=" * 60)
    app.run(debug=True, port=5000)
