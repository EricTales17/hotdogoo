import sqlite3
from datetime import datetime
import os

class PapaLanches:
    def __init__(self, db_name='papalanches.db'):
        self.db_name = db_name
        self.usuario_atual = None
        self.configurar_banco()

    def conectar(self):
        return sqlite3.connect(self.db_name)

    def configurar_banco(self):
        with self.conectar() as conn:
            cursor = conn.cursor()
            # Tabela de Usuários
            cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE NOT NULL,
                                senha TEXT NOT NULL,
                                tipo TEXT NOT NULL)''')
            
            # Tabela de Produtos
            cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                nome TEXT NOT NULL,
                                preco REAL NOT NULL,
                                estoque INTEGER NOT NULL)''')
            
            # Tabela de Vendas
            cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                usuario_id INTEGER,
                                produto_id INTEGER,
                                quantidade INTEGER,
                                data_venda TEXT,
                                total REAL,
                                FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                                FOREIGN KEY (produto_id) REFERENCES produtos (id))''')
            
            # Criar Admin padrão: Login 'admin' | Senha '123'
            cursor.execute('SELECT * FROM usuarios WHERE username = "admin"')
            if not cursor.fetchone():
                cursor.execute('INSERT INTO usuarios (username, senha, tipo) VALUES (?, ?, ?)',
                               ('admin', '123', 'admin'))
            conn.commit()

    # --- SISTEMA DE ACESSO ---
    def cadastrar_usuario(self, username, senha):
        try:
            with self.conectar() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO usuarios (username, senha, tipo) VALUES (?, ?, ?)',
                               (username, senha, 'cliente'))
                conn.commit()
                print(f"\n✅ Cliente {username} cadastrado com sucesso!")
        except sqlite3.IntegrityError:
            print("\n❌ Erro: Este nome de usuário já existe.")

    def login(self, username, senha):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, tipo FROM usuarios WHERE username = ? AND senha = ?', (username, senha))
            user = cursor.fetchone()
            if user:
                self.usuario_atual = {"id": user[0], "nome": user[1], "tipo": user[2]}
                return True
            return False

    # --- FUNÇÕES DE PRODUTOS ---
    def cadastrar_produto(self, nome, preco, estoque):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', (nome, preco, estoque))
            conn.commit()
            print(f"\n🍔 {nome} adicionado ao cardápio!")

    def listar_produtos(self):
        print("\n--- 📝 CARDÁPIO PAPA LANCHES ---")
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM produtos')
            produtos = cursor.fetchall()
            if not produtos:
                print("O cardápio está vazio.")
                return False
            print(f"{'ID':<4} | {'Item':<20} | {'Preço':<10} | {'Estoque':<8}")
            print("-" * 50)
            for p in produtos:
                print(f"{p[0]:<4} | {p[1]:<20} | R$ {p[2]:>7.2f} | {p[3]:<8}")
            return True

    def repor_estoque(self, p_id, qtd):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE produtos SET estoque = estoque + ? WHERE id = ?', (qtd, p_id))
            conn.commit()
            print("\n📦 Estoque atualizado!")

    # --- FUNÇÕES DE VENDAS ---
    def fazer_pedido(self, produto_id, quantidade):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, preco, estoque FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
            
            if produto and produto[2] >= quantidade:
                total = produto[1] * quantidade
                data = datetime.now().strftime('%d/%m/%Y %H:%M')
                cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?', (quantidade, produto_id))
                cursor.execute('INSERT INTO vendas (usuario_id, produto_id, quantidade, data_venda, total) VALUES (?, ?, ?, ?, ?)',
                               (self.usuario_atual['id'], produto_id, quantidade, data, total))
                conn.commit()
                print(f"\n✅ Pedido confirmado! {quantidade}x {produto[0]} | Total: R$ {total:.2f}")
            else:
                print("\n❌ Erro: Produto não encontrado ou estoque insuficiente.")

    def ver_meus_pedidos(self):
        print(f"\n--- 🛍️ MEUS PEDIDOS EM PAPA LANCHES ---")
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT p.nome, v.quantidade, v.total, v.data_venda 
                              FROM vendas v JOIN produtos p ON v.produto_id = p.id
                              WHERE v.usuario_id = ?''', (self.usuario_atual['id'],))
            for p in cursor.fetchall():
                print(f"Item: {p[0]} | Qtd: {p[1]} | Total: R$ {p[2]:.2f} | Data: {p[3]}")

    def relatorio_admin(self):
        print("\n--- 📊 RELATÓRIO GERAL (ADMIN) ---")
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT v.id, u.username, p.nome, v.quantidade, v.total, v.data_venda 
                              FROM vendas v 
                              JOIN usuarios u ON v.usuario_id = u.id
                              JOIN produtos p ON v.produto_id = p.id''')
            total_geral = 0
            for v in cursor.fetchall():
                print(f"ID: {v[0]} | Cliente: {v[1]} | {v[2]} (x{v[3]}) | R$ {v[4]:.2f} | {v[5]}")
                total_geral += v[4]
            print(f"\n💰 FATURAMENTO TOTAL: R$ {total_geral:.2f}")

# --- INTERFACES DE MENU ---

def menu_admin(sistema):
    while True:
        print("\n--- 🛠️ PAINEL ADMINISTRATIVO ---")
        print("1. Cadastrar Novo Produto")
        print("2. Ver Estoque / Repor")
        print("3. Relatório de Vendas")
        print("4. Sair")
        op = input("Escolha: ")
        if op == '1':
            n = input("Nome do lanche: ")
            p = float(input("Preço: R$ "))
            e = int(input("Estoque inicial: "))
            sistema.cadastrar_produto(n, p, e)
        elif op == '2':
            if sistema.listar_produtos():
                id_p = int(input("\nID do produto para repor: "))
                qtd = int(input("Quantidade para adicionar: "))
                sistema.repor_estoque(id_p, qtd)
        elif op == '3':
            sistema.relatorio_admin()
        elif op == '4': break

def menu_cliente(sistema):
    while True:
        print(f"\n--- 🍟 BEM-VINDO AO PAPA LANCHES, {sistema.usuario_atual['nome'].upper()}! ---")
        print("1. Ver Cardápio e Pedir")
        print("2. Ver Meus Pedidos")
        print("3. Sair")
        op = input("Escolha: ")
        if op == '1':
            if sistema.listar_produtos():
                id_p = int(input("\nID do lanche que deseja: "))
                qtd = int(input("Quantidade: "))
                sistema.fazer_pedido(id_p, qtd)
        elif op == '2':
            sistema.ver_meus_pedidos()
        elif op == '3': break

def iniciar():
    sistema = PapaLanches()
    while True:
        print("\n" + "="*25)
        print("      PAPA LANCHES      ")
        print("="*25)
        print("1. Login")
        print("2. Criar Conta")
        print("3. Fechar")
        op = input("Opção: ")
        
        if op == '1':
            u = input("Usuário: ")
            s = input("Senha: ")
            if sistema.login(u, s):
                if sistema.usuario_atual['tipo'] == 'admin':
                    menu_admin(sistema)
                else:
                    menu_cliente(sistema)
            else:
                print("\n❌ Usuário ou senha incorretos!")
        elif op == '2':
            u = input("Escolha um usuário: ")
            s = input("Escolha uma senha: ")
            sistema.cadastrar_usuario(u, s)
        elif op == '3': break

if __name__ == "__main__":
    iniciar()