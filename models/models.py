import sqlite3
import secrets
import hashlib

DATABASE = 'guia.db'

def get_db_connection():
    """Estabelece a conexão com o banco SQLite e configura o retorno como dicionário."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Cria as tabelas iniciais do sistema se elas não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Usuários Administrativos (Acesso à Plataforma)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            setor_id INTEGER,
            ativo INTEGER DEFAULT 1
        )
    ''')

    # 2. Colaboradores (Representam os CARDS no Kanban)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE,
            token TEXT UNIQUE,
            status TEXT DEFAULT 'todo',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Tarefas de Onboarding (Checklist dentro de cada Card/Colaborador)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas_onboarding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER,
            titulo TEXT NOT NULL,
            concluida INTEGER DEFAULT 0,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id)
        )
    ''')

    # 4. Anotações Criptografadas/Protegidas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anotacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER,
            conteudo TEXT,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados 'guia.db' inicializado.")

# --- FUNÇÕES DE BUSCA (READ) ---

def get_all_tasks():
    """Retorna todos os colaboradores para o Kanban."""
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM colaboradores').fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_colaborador_by_token(token):
    """Busca um colaborador específico pelo token de acesso."""
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM colaboradores WHERE token = ?', (token,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_onboarding_data_by_token(token):
    """Busca os dados do colaborador e suas tarefas vinculadas via token."""
    colaborador = get_colaborador_by_token(token)
    if not colaborador:
        return None
    
    conn = get_db_connection()
    tarefas = conn.execute('SELECT * FROM tarefas_onboarding WHERE colaborador_id = ?', 
                           (colaborador['id'],)).fetchall()
    conn.close()
    
    colaborador['tarefas'] = [dict(t) for t in tarefas]
    return colaborador

# --- FUNÇÕES DE MANIPULAÇÃO (CREATE / UPDATE / DELETE) ---

def create_colaborador_com_card_e_tarefas(data):
    """Cria um colaborador, gera um token e pode inicializar tarefas padrão."""
    try:
        token = secrets.token_hex(16)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO colaboradores (nome, email, token, status) VALUES (?, ?, ?, ?)',
            (data.get('nome'), data.get('email'), token, 'todo')
        )
        
        card_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "card_id": card_id, "token": token}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_task_status(task_id, novo_status):
    """Atualiza a coluna (status) do card no Kanban."""
    conn = get_db_connection()
    conn.execute('UPDATE colaboradores SET status = ? WHERE id = ?', (novo_status, task_id))
    conn.commit()
    conn.close()
    return True

def delete_task(task_id):
    """Remove um colaborador/card do sistema."""
    conn = get_db_connection()
    conn.execute('DELETE FROM colaboradores WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return True

# --- FUNÇÕES COMPLEMENTARES ---

def add_anotacao_criptografada(token, texto):
    """Simula a adição de uma anotação vinculada ao token do colaborador."""
    colab = get_colaborador_by_token(token)
    if colab:
        conn = get_db_connection()
        conn.execute('INSERT INTO anotacoes (colaborador_id, conteudo) VALUES (?, ?)', 
                     (colab['id'], texto))
        conn.commit()
        conn.close()
        return True
    return False

def get_dashboard_stats():
    """Retorna estatísticas básicas para o gráfico do Dashboard."""
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM colaboradores').fetchone()[0]
    # Exemplo simples de retorno de estatística
    stats = {"total_colaboradores": total, "status": "operacional"}
    conn.close()
    return stats

# Placeholders para evitar erros de importação se as funções ainda não forem usadas
def verify_token(token): return get_colaborador_by_token(token) is not None
def get_all_colunas_com_setores(): return []
def get_card_com_tarefas_e_colaborador(id): return None
def update_tarefa_status(id, status): return True