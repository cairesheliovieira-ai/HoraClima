"""
test_app.py — Testes unitários e de integração
===============================================
Exercício de depuração: alguns testes **intencionalmente falham**
na primeira execução. O desafio é identificar e corrigir os bugs.

Execute com:
    python -m pytest test_app.py -v

Author: Aula 04.2
"""

import json
import pytest

# Importa a aplicação e funções internas
from app import app, authenticate_user, _init_db, _save_db, _load_db, DB_FILE
import os


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_db(tmp_path, monkeypatch):
    """Recria o banco de dados limpo antes de cada teste.

    Usa ``monkeypatch`` para redirecionar o arquivo DB para um
    diretório temporário, garantindo isolamento entre os testes.

    Args:
        tmp_path: Diretório temporário fornecido pelo pytest.
        monkeypatch: Helper do pytest para substituição de atributos.
    """
    db_path = str(tmp_path / "db.json")
    monkeypatch.setattr("app.DB_FILE", db_path)
    # Força a inicialização no novo caminho
    import app as app_module
    app_module.DB_FILE = db_path
    app_module._init_db()
    yield


@pytest.fixture
def client():
    """Retorna um cliente de teste Flask configurado.

    Utiliza o modo de teste do Flask para capturar erros sem
    propagar exceções para o servidor WSGI.

    Returns:
        FlaskClient: Cliente HTTP para simular requisições.
    """
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def get_token(client) -> str:
    """Faz login como admin e retorna o token JWT.

    Args:
        client (FlaskClient): Cliente de teste Flask.

    Returns:
        str: Token JWT no formato ``Bearer <token>``.
    """
    resp = client.post(
        "/api/login",
        data=json.dumps({"username": "admin", "password": "admin123"}),
        content_type="application/json"
    )
    assert resp.status_code == 200, f"Login falhou: {resp.get_json()}"
    token = resp.get_json()["token"]
    return f"Bearer {token}"


# ---------------------------------------------------------------------------
# Testes de Autenticação
# ---------------------------------------------------------------------------

class TestLogin:
    """Testes para a função authenticate_user e endpoint /api/login."""

    def test_login_sucesso(self, client):
        """✅ Login com credenciais corretas deve retornar 200 e token."""
        resp = client.post(
            "/api/login",
            data=json.dumps({"username": "admin", "password": "admin123"}),
            content_type="application/json"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert data["role"] == "admin"

    def test_login_senha_errada(self, client):
        """✅ Senha incorreta deve retornar 401."""
        resp = client.post(
            "/api/login",
            data=json.dumps({"username": "admin", "password": "errada"}),
            content_type="application/json"
        )
        assert resp.status_code == 401

    def test_login_usuario_inexistente(self, client):
        """✅ Usuário inexistente deve retornar 401."""
        resp = client.post(
            "/api/login",
            data=json.dumps({"username": "ninguem", "password": "xyz"}),
            content_type="application/json"
        )
        assert resp.status_code == 401

    def test_login_campos_vazios(self, client):
        """✅ Campos vazios devem retornar 400."""
        resp = client.post(
            "/api/login",
            data=json.dumps({"username": "", "password": ""}),
            content_type="application/json"
        )
        assert resp.status_code == 400

    def test_authenticate_user_direto(self):
        """✅ Testa a função authenticate_user diretamente."""
        result = authenticate_user("admin", "admin123")
        assert result is not None
        assert "token" in result

    def test_authenticate_user_retorna_none(self):
        """✅ Senha errada deve retornar None."""
        result = authenticate_user("admin", "errada")
        assert result is None

    def test_rota_sem_token_retorna_401(self, client):
        """✅ Rota protegida sem token deve retornar 401."""
        resp = client.get("/api/products")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Testes de Produtos
# ---------------------------------------------------------------------------

class TestProducts:
    """Testes de CRUD de produtos."""

    def test_listar_produtos(self, client):
        """✅ Deve retornar a lista de produtos do DB inicial."""
        token = get_token(client)
        resp = client.get("/api/products", headers={"Authorization": token})
        assert resp.status_code == 200
        products = resp.get_json()
        assert isinstance(products, list)
        assert len(products) == 5   # DB inicial tem 5 produtos

    def test_criar_produto(self, client):
        """✅ Deve criar um produto e retornar 201."""
        token = get_token(client)
        body = {"name": "SSD 1TB", "price": 350.00, "stock": 20, "category": "Armazenamento"}
        resp = client.post(
            "/api/products",
            data=json.dumps(body),
            content_type="application/json",
            headers={"Authorization": token}
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "SSD 1TB"
        assert data["id"] == 6   # 5 existentes + 1 novo

    def test_criar_produto_sem_nome(self, client):
        """✅ Criação sem 'name' deve retornar 400."""
        token = get_token(client)
        resp = client.post(
            "/api/products",
            data=json.dumps({"price": 99.0}),
            content_type="application/json",
            headers={"Authorization": token}
        )
        assert resp.status_code == 400

    def test_atualizar_produto(self, client):
        """✅ Atualização de produto existente deve retornar 200."""
        token = get_token(client)
        resp = client.put(
            "/api/products/1",
            data=json.dumps({"price": 3999.00, "stock": 20}),
            content_type="application/json",
            headers={"Authorization": token}
        )
        assert resp.status_code == 200
        assert resp.get_json()["price"] == 3999.00

    def test_atualizar_produto_inexistente(self, client):
        """✅ Atualizar produto que não existe deve retornar 404."""
        token = get_token(client)
        resp = client.put(
            "/api/products/9999",
            data=json.dumps({"price": 10.0}),
            content_type="application/json",
            headers={"Authorization": token}
        )
        assert resp.status_code == 404

    def test_deletar_produto(self, client):
        """✅ Deletar produto existente deve retornar 200."""
        token = get_token(client)
        resp = client.delete("/api/products/1", headers={"Authorization": token})
        assert resp.status_code == 200

    def test_deletar_produto_inexistente(self, client):
        """✅ Deletar produto inexistente deve retornar 404."""
        token = get_token(client)
        resp = client.delete("/api/products/9999", headers={"Authorization": token})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Testes de Vendas
# ---------------------------------------------------------------------------

class TestSales:
    """Testes de registro e listagem de vendas."""

    def test_registrar_venda(self, client):
        """✅ Venda válida deve retornar 201 e reduzir o estoque."""
        token = get_token(client)
        # Produto 2 (Mouse Logitech) tem 42 unidades em estoque
        resp = client.post(
            "/api/sales",
            data=json.dumps({"product_id": 2, "quantity": 3}),
            content_type="application/json",
            headers={"Authorization": token}
        )
        assert resp.status_code == 201
        sale = resp.get_json()
        assert sale["total"] == round(89.90 * 3, 2)

        # Verifica se o estoque foi decrementado
        products = client.get("/api/products", headers={"Authorization": token}).get_json()
        mouse = next(p for p in products if p["id"] == 2)
        assert mouse["stock"] == 39   # 42 - 3

    def test_venda_estoque_insuficiente(self, client):
        """✅ Venda acima do estoque deve retornar 400."""
        token = get_token(client)
        # Cadeira Gamer tem apenas 5 unidades
        resp = client.post(
            "/api/sales",
            data=json.dumps({"product_id": 5, "quantity": 100}),
            content_type="application/json",
            headers={"Authorization": token}
        )
        assert resp.status_code == 400

    def test_venda_produto_inexistente(self, client):
        """✅ Venda de produto inexistente deve retornar 404."""
        token = get_token(client)
        resp = client.post(
            "/api/sales",
            data=json.dumps({"product_id": 9999, "quantity": 1}),
            content_type="application/json",
            headers={"Authorization": token}
        )
        assert resp.status_code == 404

    def test_venda_quantidade_zero(self, client):
        """✅ Quantidade zero deve retornar 400."""
        token = get_token(client)
        resp = client.post(
            "/api/sales",
            data=json.dumps({"product_id": 1, "quantity": 0}),
            content_type="application/json",
            headers={"Authorization": token}
        )
        assert resp.status_code == 400

    def test_listar_vendas_vazia(self, client):
        """✅ Sem vendas registradas, deve retornar lista vazia."""
        token = get_token(client)
        resp = client.get("/api/sales", headers={"Authorization": token})
        assert resp.status_code == 200
        assert resp.get_json() == []


# ---------------------------------------------------------------------------
# Testes de Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    """Testes das métricas do painel de controle."""

    def test_dashboard_inicial(self, client):
        """✅ Dashboard sem vendas deve ter receita zerada."""
        token = get_token(client)
        resp = client.get("/api/dashboard", headers={"Authorization": token})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_revenue"] == 0.0
        assert data["total_products"] == 5
        assert data["total_sales"] == 0

    def test_dashboard_apos_venda(self, client):
        """✅ Receita deve ser atualizada após uma venda."""
        token = get_token(client)
        client.post(
            "/api/sales",
            data=json.dumps({"product_id": 1, "quantity": 1}),
            content_type="application/json",
            headers={"Authorization": token}
        )
        resp = client.get("/api/dashboard", headers={"Authorization": token})
        data = resp.get_json()
        assert data["total_revenue"] == 3500.00
        assert data["total_sales"] == 1
