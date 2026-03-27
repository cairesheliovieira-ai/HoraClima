import unittest
from gerenciador_loja import GerenciadorLoja

class TestGerenciadorLoja(unittest.TestCase):
    def setUp(self):
        self.loja = GerenciadorLoja()
        
    def test_login_sucesso(self):
        """Verifica se autenticação com credenciais corretas retorna uma string de Token válida."""
        token = self.loja.login("admin", "senha123")
        self.assertIsInstance(token, str)
        self.assertEqual(token.count("."), 2, "Formato do JWT gerado inválido")
        
    def test_login_usuario_invalido(self):
        """Verifica recusa de usuário não cadastrado."""
        with self.assertRaises(ValueError):
            self.loja.login("inexistente", "123")
            
    def test_login_senha_invalida(self):
        """Verifica recusa de senha errada para usuário existente."""
        with self.assertRaises(PermissionError):
            self.loja.login("admin", "senhaErrada")
            
    def test_adicionar_produto(self):
        """Testa se a inclusão e propriedades correspondem ao inserido no estoque."""
        self.loja.adicionar_produto("Caneta", 100, 2.50)
        self.assertIn("Caneta", self.loja.estoque)
        self.assertEqual(self.loja.estoque["Caneta"]["quantidade"], 100)

    # =========================================================================
    # OS TESTES ABAIXO FORAM FEITOS PARA FALHAR (Desafio de Sala de Aula)
    # Até que o desenvolvedor júnior corrijas as lógicas falhas em gerenciador_loja.py
    # =========================================================================
    def test_vender_produto_inexistente(self):
        """
        Deveria lançar ValueError avisando que o produto não existe,
        pois tentar acessar direto no dicionário e tomar KeyError não é a melhor prática final.
        """
        # Desafio: Modifique o método de venda para lançar ValueError e depois este teste para testar ValueError.
        with self.assertRaises(KeyError): 
            self.loja.vender_produto("ProdutoFantasma", 1)
            
    def test_vender_estoque_insuficiente(self):
        """Não deveria ser possível vender mais unidades do que as listadas no estoque."""
        self.loja.adicionar_produto("Borracha", 10, 1.00)
        with self.assertRaises(ValueError): # Falha pois o código atual retorna o valor e ignora o bloqueio
            self.loja.vender_produto("Borracha", 15)

if __name__ == '__main__':
    unittest.main()
