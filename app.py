from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models.models import (
    init_db, get_all_tasks, create_colaborador_com_card_e_tarefas,
    update_task_status, delete_task, get_dashboard_stats,
    get_onboarding_data_by_token, get_card_com_tarefas_e_colaborador,
    update_tarefa_status, get_all_colunas_com_setores, verify_token,
    get_colaborador_by_token, add_anotacao_criptografada
)
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Chave secreta para sessões

# Inicializa o banco de dados
init_db()

# Decorator para verificar autenticação (simplificado para demonstração)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# ----------- ROTAS DO FRONT-END -----------
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('plataforma/login.html')

@app.route('/plataforma')
def plataforma():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Verifica o tipo de usuário (simplificado)
    if session.get('role') == 'colaborador':
        return redirect(url_for('onboarding_com_token', token=session.get('token')))
    else:
        return render_template('plataforma/dashboard.html')

@app.route('/plataforma/dashboard')
@login_required
def dashboard():
    return render_template('plataforma/dashboard.html')

@app.route('/plataforma/onboarding')
def onboarding():
    token = request.args.get('token')
    if not token:
        return render_template('error.html', mensagem="Token de acesso não fornecido"), 400
    
    colaborador = get_colaborador_by_token(token)
    if not colaborador:
        return render_template('error.html', mensagem="Token inválido ou expirado"), 404
    
    # Cria sessão para o colaborador
    session['user_id'] = colaborador['id']
    session['role'] = 'colaborador'
    session['token'] = token
    
    return render_template('plataforma/onboarding.html', token=token)

# ==========================================
# -------------- ROTAS DA API --------------
# ==========================================

# --- COLUNAS KANBAN ---
@app.route('/api/colunas', methods=['GET'])
def api_get_colunas():
    colunas = get_all_colunas_com_setores()
    return jsonify(colunas)

# --- CARDS / TAREFAS ---
@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    tasks = get_all_tasks()
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def api_create_task():
    try:
        data = request.json
        result = create_colaborador_com_card_e_tarefas(data)
        
        if result and result.get('success'):
            return jsonify({
                "success": True, 
                "id": result['card_id'],
                "token": result['token']
            }), 201
        else:
            return jsonify({
                "success": False, 
                "error": result.get('error', 'Falha ao criar colaborador')
            }), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cards/<int:card_id>', methods=['GET'])
def api_get_card_detalhes(card_id):
    card_data = get_card_com_tarefas_e_colaborador(card_id)
    if card_data:
        return jsonify(card_data)
    return jsonify({"error": "Card não encontrado"}), 404

@app.route('/api/tasks/<int:task_id>/status', methods=['PATCH'])
def api_update_status(task_id):
    data = request.json
    success = update_task_status(task_id, data['coluna_id'])
    return jsonify({"success": success})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    success = delete_task(task_id)
    return jsonify({"success": success})

# --- TAREFAS INDIVIDUAIS ---
@app.route('/api/tarefas/<int:tarefa_id>', methods=['PATCH'])
def api_toggle_tarefa(tarefa_id):
    data = request.json
    success = update_tarefa_status(tarefa_id, data['concluida'])
    return jsonify({"success": success})

# --- ONBOARDING DO COLABORADOR ---
@app.route('/api/meu-onboarding', methods=['GET'])
def api_get_meu_onboarding():
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Token não fornecido"}), 401
    
    dados = get_onboarding_data_by_token(token)
    if dados:
        return jsonify(dados)
    return jsonify({"error": "Dados não encontrados"}), 404

@app.route('/api/anotacoes', methods=['POST'])
def api_salvar_anotacao():
    data = request.json
    token = data.get('token')
    anotacao = data.get('anotacao')
    
    if not token or anotacao is None:
        return jsonify({"error": "Dados incompletos"}), 400
    
    success = add_anotacao_criptografada(token, anotacao)
    return jsonify({"success": success})

# --- DASHBOARD STATS ---
@app.route('/api/dashboard/stats', methods=['GET'])
def api_get_stats():
    stats = get_dashboard_stats()
    return jsonify(stats)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
