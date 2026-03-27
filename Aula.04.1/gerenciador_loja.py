"""
Sistema Gerenciador de Loja
Desafio de Sala de Aula: Teste e Depuração
"""
import hashlib
import time

# Banco de dados simulado de usuários
db_usuarios = {
    "admin": hashlib.sha256("senha123".encode()).hexdigest(),
    "caixa": hashlib.sha256("vendas2026".encode()).hexdigest()
}

class GerenciadorLoja:
    def __init__(self):
        self.estoque = {}

    def login(self, usuario: str, senha: str) -> str:
        """
        Realiza a autenticação de um usuário no sistema e retorna um token JWT simulado.

        Este método verifica se o usuário existe no banco de dados da aplicação
        e tenta validar a senha fornecida contra o hash armazenado. Em caso de sucesso
        na validação, um token JWT (JSON Web Token) simulado é gerado e retornado, permitindo
        acesso correspondente às rotas/módulos protegidos.

        Args:
            usuario (str): O nome do usuário que está tentando efetuar o login.
            senha (str): A senha correspondente em texto plano.

        Returns:
            str: Um JWT token no formato 'header.payload.signature', utilizado 
            para verificação nas próximas requisições do sistema.

        Raises:
            ValueError: Se o usuário inserido não for encontrado no banco de dados.
            PermissionError: Se a senha fornecida não corresponder à registrada (credenciais inválidas).

        Example:
            >>> loja = GerenciadorLoja()
            >>> try:
            ...     token = loja.login("admin", "senha123")
            ...     print(f"Login bem-sucedido! Token gerado: {token}")
            ... except (ValueError, PermissionError) as e:
            ...     print(f"Falha de autenticação: {e}")
            Login bem-sucedido! Token gerado: eyJhbG...
        """
        if usuario not in db_usuarios:
            raise ValueError(f"Usuário '{usuario}' não encontrado.")
        
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        if db_usuarios[usuario] != senha_hash:
            raise PermissionError("Senha incorreta.")
        
        # Simula a criação de um token JWT
        header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        payload = f"usr_{usuario}_exp_{int(time.time()) + 3600}"
        signature = hashlib.sha256((header + payload).encode()).hexdigest()[:16]
        
        return f"{header}.{payload}.{signature}"

    def adicionar_produto(self, nome: str, quantidade: int, preco: float):
        """Adiciona ou atualiza produto no estoque."""
        if quantidade <= 0 or preco <= 0:
            raise ValueError("Quantidade e preço devem ser valores maiores que zero.")
            
        if nome in self.estoque:
            self.estoque[nome]['quantidade'] += quantidade
            self.estoque[nome]['preco'] = preco # Atualiza para o preço mais recente
        else:
            self.estoque[nome] = {'quantidade': quantidade, 'preco': preco}

    def vender_produto(self, nome: str, quantidade: int) -> float:
        """
        Realiza a venda de um produto.
        
        ATENÇÃO: Este método possui comportamentos inesperados (bugs) que deverão 
        ser encontrados e corrigidos pelo desenvolvedor (cenário de depuração).
        """
        if quantidade <= 0:
            raise ValueError("Quantidade de venda deve ser maior que zero.")
            
        # BUG INTENCIONAL 1: Não verifica se o produto existe no dicionário KeyError
        # BUG INTENCIONAL 2: Permite vender uma quantidade maior que a disponível no estoque (estoque negativo)
        
        if self.estoque[nome]['quantidade'] >= quantidade:
            self.estoque[nome]['quantidade'] -= quantidade
            total_venda = self.estoque[nome]['preco'] * quantidade
            return total_venda
        else:
            # Bug: Subtrai a quantidade do mesmo jeito, deixando o estoque negativo
            self.estoque[nome]['quantidade'] -= quantidade 
            return self.estoque[nome]['preco'] * quantidade

    def emitir_relatorio(self):
        """Emite o relatório atual do estoque no console."""
        print("\n--- Relatório de Estoque ---")
        for nome, dados in self.estoque.items():
            print(f"- {nome}: {dados['quantidade']} unid. a R$ {dados['preco']:.2f}")
        print("----------------------------\n")


if __name__ == "__main__":
    loja = GerenciadorLoja()
    try:
        # 1. Testa a autenticação documentada
        print("=== Testando Autenticação ===")
        meu_token = loja.login("admin", "senha123")
        print("Autenticação válida. Token:")
        print(meu_token)
        
        # 2. Popula o estoque
        print("\n=== Populando Estoque ===")
        loja.adicionar_produto("Notebook", 10, 3500.00)
        loja.adicionar_produto("Mouse", 50, 45.00)
        loja.emitir_relatorio()
        
        # 3. Teste de operações de vendas que exigem depuração
        print("=== Testando Vendas ===")
        print(f"Venda (Mouse x 60 unid): R$ {loja.vender_produto('Mouse', 60)}") # Gerará estoque negativo
        loja.emitir_relatorio()
        
        print("Adicionando ao carrinho produto que não existe...")
        print(f"Venda (Teclado x 1): R$ {loja.vender_produto('Teclado', 1)}") # Levantará KeyError e travará o app
        
    except Exception as e:
        print(f"\n[ERRO NA EXECUÇÃO APLICACÃO] {type(e).__name__} - {e}")
