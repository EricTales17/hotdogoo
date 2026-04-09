import sqlite3
from datetime import datetime

class DogaoSisVenda:
    def __init__(self, db_name='hotdog_vendas.db'):
        self.db_name = db_name
        self.configurar_banco()

    def conectar(self):
        return sqlite3.connect(self.db_name)

    def configurar_banco(self):
        """Cria as tabelas e insere produtos iniciais se o banco estiver vazio."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    preco REAL NOT NULL,
                    estoque INTEGER NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER,
                    quantidade INTEGER,
                    data_venda TEXT,
                    total REAL,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                )
            ''')
            
            # Verificar se já existem produtos, se não, cadastrar o cardápio base
            cursor.execute('SELECT COUNT(*) FROM produtos')
            if cursor.fetchone()[0] == 0:
                cardapio_inicial = [
                    ('Hot Dog Simples', 12.00, 50),
                    ('Hot Dog Completo', 18.00, 40),
                    ('Combo: Dog + Refri', 25.00, 30),
                    ('Refrigerante Lata', 6.00, 100),
                    ('Porção de Batata', 10.00, 20)
                ]
                cursor.executemany('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', cardapio_inicial)
            
            conn.commit()

    def cadastrar_produto(self, nome, preco, estoque):
        try:
            with self.conectar() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', 
                               (nome, preco, estoque))
                conn.commit()
            print(f"\n🌭 '{nome}' adicionado ao cardápio!")
        except Exception as e:
            print(f"\n❌ Erro ao cadastrar: {e}")

    def listar_cardapio(self):
        print("\n--- 🌭 CARDÁPIO & ESTOQUE ---")
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM produtos')
            produtos = cursor.fetchall()
            
            print(f"{'ID':<4} | {'Item':<25} | {'Preço':<10} | {'Estoque':<8}")
            print("-" * 55)
            for p in produtos:
                print(f"{p[0]:<4} | {p[1]:<25} | R$ {p[2]:>7.2f} | {p[3]:<8}")

    def registrar_venda(self, produto_id, quantidade):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, preco, estoque FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
            
            if not produto:
                print("\n❌ Erro: Item não encontrado no cardápio.")
                return

            nome, preco, estoque = produto

            if estoque >= quantidade:
                total = preco * quantidade
                novo_estoque = estoque - quantidade
                data_atual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                
                cursor.execute('UPDATE produtos SET estoque = ? WHERE id = ?', (novo_estoque, produto_id))
                cursor.execute('INSERT INTO vendas (produto_id, quantidade, data_venda, total) VALUES (?, ?, ?, ?)',
                               (produto_id, quantidade, data_atual, total))
                
                conn.commit()
                print(f"\n✅ VENDA CONCLUÍDA!")
                print(f"Item: {nome} | Qtd: {quantidade}")
                print(f"Total a Pagar: R$ {total:.2f}")
            else:
                print(f"\n⚠️ Ingredientes/Produtos insuficientes! (Estoque: {estoque})")

    def ver_faturamento(self):
        print("\n--- 📊 RELATÓRIO DE VENDAS ---")
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT v.id, p.nome, v.quantidade, v.total, v.data_venda 
                FROM vendas v 
                JOIN produtos p ON v.produto_id = p.id
            ''')
            vendas = cursor.fetchall()
            
            total_geral = 0
            for v in vendas:
                print(f"Pedido #{v[0]:03d} | {v[1]:<20} | Qtd: {v[2]} | R$ {v[3]:>7.2f} | {v[4]}")
                total_geral += v[3]
            
            print("-" * 70)
            print(f"FATURAMENTO TOTAL: R$ {total_geral:.2f}")

# --- INTERFACE DE TERMINAL ---

def main():
    sistema = DogaoSisVenda()
    
    while True:
        print("\n" + "="*30)
        print("    HOT DOG SISTEMA 🌭")
        print("="*30)
        print("1. Ver Cardápio / Estoque")
        print("2. Novo Pedido (Venda)")
        print("3. Adicionar Novo Item ao Cardápio")
        print("4. Relatório de Faturamento")
        print("5. Fechar Sistema")
        
        opcao = input("\nSelecione uma opção: ")
        
        if opcao == '1':
            sistema.listar_cardapio()
        
        elif opcao == '2':
            sistema.listar_cardapio()
            try:
                p_id = int(input("\nID do Item: "))
                qtd = int(input("Quantidade: "))
                sistema.registrar_venda(p_id, qtd)
            except ValueError:
                print("\n❌ Por favor, digite números válidos.")
            
        elif opcao == '3':
            nome = input("Nome do Cachorro-Quente/Bebida: ")
            preco = float(input("Preço de Venda: R$ "))
            estoque = int(input("Quantidade em Estoque: "))
            sistema.cadastrar_produto(nome, preco, estoque)
            
        elif opcao == '4':
            sistema.ver_faturamento()
            
        elif opcao == '5':
            print("\nSaindo... Bom descanso!")
            break
        else:
            print("\nOpção inválida!")

if __name__ == "__main__":
    main()