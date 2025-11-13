from flask import Flask, render_template, request, redirect, url_for # jsonify
from datetime import datetime
from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
import db

# Imports de Lógica Modular
import crud.aluno_crud as aluno_crud
import crud.turma_crud as turma_crud
import crud.professor_crud as professor_crud 
import crud.curso_crud as curso_crud
import crud.matricula_crud as matricula_crud
import crud.frequencia_crud as frequencia_crud

app = Flask(__name__)

#--------------------------
# Conversão de dados
#---------------------------

def to_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value,'%Y-%m-%d').date()
    except ValueError:
        return None
    
def to_int(value):
    if value in (None, "", "null"):
        return None
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        print(e)
        return None
        
# --------------------------
# Página inicial (login)
# --------------------------
@app.route('/')
def home():
    return render_template('index.html')

# --------------------------
# Página de login
# --------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'senha123':
            return redirect(url_for('tela_inicial'))
        else:
            return "Usuário ou senha inválidos"
    return render_template('login.html')

# --------------------------
# Tela inicial
# --------------------------
@app.route('/tela-inicial')
def tela_inicial():
    return render_template('tela_inicial.html')

# =================================================================
# ROTAS CRUD DE ALUNOS
# =================================================================

@app.route('/cadastrar-aluno', methods=['GET', 'POST']) 
def cadastrar_aluno():
    
    with Session(db.engine) as session:
        # Carregamento de dados para o GET do formulário (SELECTs)
        generos = session.query(db.Genero).all()
        racas = session.query(db.Raca).all()
        pcds = session.query(db.Pcd).all()
        turmas = session.query(db.Turma).all()

    if request.method == 'POST':
        # Coleta dados do formulário HTML tradicional
        data = request.form.to_dict()

        if not data:
            return "Ausência de dados no formulário.", 400
                     
        obrigatorios = ['nome', 'dt_nasc','id_Genero','id_Pcd','id_Raca', 'cpf','telefone','endereco']
        faltando = [campo for campo in obrigatorios if campo not in data or not data[campo]]

        if faltando:
            return f"Campos obrigatórios ausentes: {', '.join(faltando)}", 400
        
        # Tratamento/Conversão
        for k in ['id_Genero','id_Pcd','id_Raca', 'id_Turma']: 
            data[k] = to_int(data.get(k))

        for k in ['dt_nasc','dt_matricula','dt_conclusao']:
            data[k] = to_date(data.get(k))

        with Session(db.engine) as s:
            resultado = aluno_crud.cadastrar_aluno(s, data)

            if isinstance(resultado, dict) and 'erro' in resultado:
                return resultado['erro'], 409
            
            # Sucesso
            return redirect(url_for('visualizar_alunos'))

    # Método GET: Renderiza o formulário com os dados de referência
    return render_template('cadastrar-aluno.html', 
                           generos=generos, 
                           racas=racas, 
                           pcds=pcds, 
                           turmas=turmas)

@app.route('/visualizar-alunos')
def visualizar_alunos():
    with Session(db.engine) as session: 
        alunos = aluno_crud.buscar_alunos(session)
        
    return render_template('visualizar_alunos.html', alunos=alunos)

@app.route('/editar-aluno/<int:aluno_id>', methods=['GET', 'POST'])
def editar_aluno(aluno_id):
    with Session(db.engine) as session: 
        # Busca o aluno
        aluno = aluno_crud.buscar_aluno_por_id(session, aluno_id)
        if aluno is None:
            return "Aluno não encontrado.", 404
        
        # Carrega os dados de referência (NOVO)
        generos = session.query(db.Genero).all()
        racas = session.query(db.Raca).all()
        pcds = session.query(db.Pcd).all()
        turmas = session.query(db.Turma).all()

        if request.method == 'POST':
            dados_do_form = request.form.to_dict()
            dados_tratados = {}
            
            # Ajuste de nomes de campos no modelo (datanasc/datamatricula)
            # e tratamento dos IDs de referência
            
            # Trata IDs
            for k in ['id_Genero', 'id_Pcd', 'id_Raca', 'id_Turma']: 
                if dados_do_form.get(k):
                    dados_tratados[k] = to_int(dados_do_form.get(k))

            # Trata Datas (CORRIGINDO OS NOMES)
            if dados_do_form.get('datanasc'):
                dados_tratados['dt_nasc'] = to_date(dados_do_form.get('datanasc'))
            if dados_do_form.get('dtmatricula'):
                dados_tratados['dt_matricula'] = to_date(dados_do_form.get('dt_matricula'))
            if dados_do_form.get('dt_conclusao'):
                dados_tratados['dt_conclusao'] = to_date(dados_do_form.get('dt_conclusao'))

            # Trata demais campos de texto
            for k in ['nome', 'cpf', 'email', 'telefone', 'endereco', 'observacoes']:
                if dados_do_form.get(k):
                    dados_tratados[k] = dados_do_form.get(k)
            
            # 3. Chama a função CRUD para atualizar (UPDATE)
            resultado = aluno_crud.atualizar_aluno(session, aluno_id, dados_tratados)
            
            if resultado and not isinstance(resultado, dict):
                return redirect(url_for('visualizar_alunos'))
            elif isinstance(resultado, dict):
                # Retorna o erro e repassa os dados para manter a consistência do template
                return render_template('editar_aluno.html', aluno=aluno, generos=generos, racas=racas, pcds=pcds, turmas=turmas, erro=resultado['erro'])
            else:
                return "Erro ao atualizar aluno.", 500

        # Método GET: Renderiza o formulário com o aluno e as listas de referência (NOVO)
        return render_template('editar_aluno.html', 
                               aluno=aluno, 
                               generos=generos, 
                               racas=racas, 
                               pcds=pcds, 
                               turmas=turmas)

@app.route('/excluir-aluno/<int:aluno_id>', methods=['POST', 'DELETE'])
def excluir_aluno(aluno_id):
    with Session(db.engine) as session: 
        if aluno_crud.deletar_aluno(session, aluno_id):
            return redirect(url_for('visualizar_alunos'))
        else:
            return "Aluno não encontrado ou erro ao excluir.", 404
            
# =================================================================
# FIM: ROTAS CRUD DE ALUNOS
# =================================================================


# =================================================================
# ROTAS CRUD DE TURMAS
# =================================================================

# C (CREATE) e R (READ One) para o formulário
@app.route('/cadastrar-turma', methods=['GET', 'POST'])
def cadastrar_turma():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')

        if not nome:
            return "O campo 'Nome' é obrigatório.", 400

        with Session(db.engine) as s:
            resultado = turma_crud.criar_turma(s, nome=nome, descricao=descricao)

            if isinstance(resultado, dict) and 'erro' in resultado:
                return resultado['erro'], 409
            
            return redirect(url_for('visualizar_turmas')) 
            
    # Método GET: Renderiza o formulário
    return render_template('cadastrar_turma.html')

# R (READ All) para a visualização da lista
@app.route('/visualizar-turmas')
def visualizar_turmas():
    with Session(db.engine) as session:
        # CORRIGIDO: Usa a função do módulo CRUD
        turmas = turma_crud.buscar_turmas(session) 
        
    return render_template('visualizar_turmas.html', turmas=turmas)

# --------------------------
# Detalhes da Turma (Exibe Alunos e Cursos e Relatório de Frequência)
# --------------------------
@app.route('/detalhes-turma/<int:turma_id>')
def detalhes_turma(turma_id):
    with Session(db.engine) as session:
        # Busca a Turma completa (alunos, cursos, etc.)
        turma = turma_crud.buscar_turma_por_id_completo(session, turma_id) 

        if not turma:
            return "Turma não encontrada.", 404
        
        # 1. Calcular relatório de faltas para cada aluno
        relatorios_alunos = {}
        for aluno in turma.alunos:
            relatorios_alunos[aluno.id_Aluno] = frequencia_crud.calcular_faltas_por_aluno(session, aluno.id_Aluno)

        # 2. Reestruturar a lista de alunos para incluir os dados do relatório
        alunos_com_relatorio = []
        for aluno in turma.alunos:
            relatorio = relatorios_alunos[aluno.id_Aluno]
            
            # Garante que o objeto aluno tenha todas as propriedades do relatório
            aluno_data = {
                'aluno': aluno,
                'relatorio': relatorio
            }
            alunos_com_relatorio.append(aluno_data)

        # 3. Lógica de Ordenação (NOVO!)
        ordem_risco = request.args.get('ordem') == 'risco'
        
        if ordem_risco:
            # Ordena por % de Presença (menor para maior)
            alunos_com_relatorio.sort(key=lambda x: (
                (x['relatorio']['presente'] / x['relatorio']['total_aulas_validas'] * 100) 
                if x['relatorio']['total_aulas_validas'] > 0 else 100 # Se 0 aulas, coloca 100% (baixo risco)
            ), reverse=False) # reverse=False para ordenar do MENOR % para o MAIOR (risco alto no topo)
        
    # Manda a turma e a lista ordenada/completa para o template
    return render_template('detalhes_turma.html', 
                           turma=turma, 
                           alunos_com_relatorio=alunos_com_relatorio,
                           ordem_risco=ordem_risco)

# U (UPDATE) e R (READ One) para o formulário de edição
@app.route('/editar-turma/<int:turma_id>', methods=['GET', 'POST'])
def editar_turma(turma_id):
    with Session(db.engine) as session:
        turma = turma_crud.buscar_turma_por_id(session, turma_id)
        
        if turma is None:
            return "Turma não encontrada.", 404

        if request.method == 'POST':
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            
            if not nome:
                return "O campo 'Nome' é obrigatório.", 400
                 
            resultado = turma_crud.atualizar_turma(session, turma_id, nome=nome, descricao=descricao)
            
            if isinstance(resultado, dict) and 'erro' in resultado:
                return resultado['erro'], 409

            return redirect(url_for('visualizar_turmas'))

        return render_template('editar_turma.html', turma=turma)

# D (DELETE)
@app.route('/excluir-turma/<int:turma_id>', methods=['POST'])
def excluir_turma(turma_id):
    with Session(db.engine) as session:
        if turma_crud.deletar_turma(session, turma_id):
            return redirect(url_for('visualizar_turmas'))
        else:
            return "Erro ao excluir turma. Verifique se há alunos ou cursos vinculados.", 409


# =================================================================
# FIM: ROTAS CRUD DE TURMAS
# =================================================================

# =================================================================
# ROTAS DE FREQUÊNCIA E CHAMADA
# =================================================================

# Arquivo: app.py (Adicionar esta rota completa)

# C (CREATE) - Inicia o lançamento de chamada para uma Turma
@app.route('/lancar-chamada/<int:turma_id>', methods=['GET', 'POST'])
def lancar_chamada(turma_id):
    with Session(db.engine) as session:
        turma = turma_crud.buscar_turma_por_id_completo(session, turma_id)
        
        if not turma:
            return "Turma não encontrada.", 404
        
        # O método GET (para exibir o formulário de chamada)
        if request.method == 'GET':
            return render_template('lancar_chamada.html', turma=turma)

        # O método POST (para processar a submissão do formulário)
        if request.method == 'POST':
            topico = request.form.get('topico')
            
            # 1. Cria a nova Aula
            with Session(db.engine) as s_aula:
                nova_aula = frequencia_crud.criar_aula(s_aula, turma_id, topico)
                if isinstance(nova_aula, dict):
                    return f"Erro ao criar a aula: {nova_aula['erro']}", 500
                
                aula_id = nova_aula.id_Aula
                
                # 2. Registra a frequência de cada aluno
                alunos = turma.alunos 
                erros = []
                
                with Session(db.engine) as s_frequencia:
                    for aluno in alunos:
                        status_key = f"status_{aluno.id_Aluno}"
                        status_value = request.form.get(status_key, 'falta') 
                        
                        resultado = frequencia_crud.registrar_presenca(s_frequencia, aluno.id_Aluno, aula_id, status_value)
                        
                        if 'erro' in resultado:
                            erros.append(f"Erro no aluno {aluno.nome}: {resultado['erro']}")
                    
                    if erros:
                        return f"Chamada lançada com erros: {'; '.join(erros)}", 500
                    
            # 3. Sucesso: Redireciona para o detalhe da turma
            return redirect(url_for('detalhes_turma', turma_id=turma_id))
    
    return "Método não permitido.", 405

#### C. Detalhes da Turma (Atualizar para Relatório)



# =================================================================
# ROTAS CRUD DE PROFESSOR
# =================================================================

# C (CREATE) e R (READ One para formulário de cadastro)
@app.route('/cadastrar-professor', methods=['GET', 'POST'])
def cadastrar_professor():
    with Session(db.engine) as session:
        # Carrega os dados das tabelas de referência para o método GET
        generos = session.query(db.Genero).all()
        racas = session.query(db.Raca).all()
        pcds = session.query(db.Pcd).all()
        
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # 1. Trata os IDs
        for k in ['id_Genero', 'id_Pcd', 'id_Raca']:
            data[k] = to_int(data.get(k))
        
        # Mapeia o nome do campo do formulário ('nome') para o modelo ('nomeProfessor')
        data['nomeProfessor'] = data.pop('nome', data.get('nomeProfessor'))
        
        with Session(db.engine) as s:
            resultado = professor_crud.cadastrar_professor(s, data)
            
            if isinstance(resultado, dict) and 'erro' in resultado:
                # Retorna o erro, passando as listas para que o formulário não quebre
                return render_template('cadastrar-professor.html', generos=generos, racas=racas, pcds=pcds, erro=resultado['erro']), 409
            
            return redirect(url_for('visualizar_professores')) 
            
    # Método GET: Renderiza o formulário, passando as listas
    return render_template('cadastrar-professor.html', generos=generos, racas=racas, pcds=pcds)

# R (READ All) para a visualização da lista
@app.route('/visualizar-professores')
def visualizar_professores():
    with Session(db.engine) as session:
        professores = professor_crud.buscar_professores(session)
        
    return render_template('visualizar_professores.html', professores=professores)

# U (UPDATE) e R (READ One para edição)
@app.route('/editar-professor/<int:professor_id>', methods=['GET', 'POST'])
def editar_professor(professor_id):
    with Session(db.engine) as session:
        # Carrega os dados de referência para o método GET (e para repassar em caso de erro no POST)
        generos = session.query(db.Genero).all()
        racas = session.query(db.Raca).all()
        pcds = session.query(db.Pcd).all()
        
        # Busca o professor
        professor = professor_crud.buscar_professor_por_id(session, professor_id)
        
        if professor is None:
            return "Professor não encontrado.", 404

        if request.method == 'POST':
            dados_do_form = request.form.to_dict()
            dados_tratados = {}
            
            # 1. Trata e Converte IDs
            for k in ['id_Genero', 'id_Pcd', 'id_Raca']:
                if dados_do_form.get(k):
                    dados_tratados[k] = to_int(dados_do_form.get(k))
            
            # 2. Trata e Mapeia Campos de Texto
            for k in ['cpf', 'email', 'telefone', 'endereco']:
                if dados_do_form.get(k):
                    dados_tratados[k] = dados_do_form.get(k)
                    
            if dados_do_form.get('nome'):
                # Mapeia o campo 'nome' do HTML para o atributo 'nomeProfessor' do modelo
                dados_tratados['nomeProfessor'] = dados_do_form.get('nome')

            # === LINHA CRÍTICA QUE ESTAVA FALTANDO/PROBLEMATIZANDO ===
            resultado = professor_crud.atualizar_professor(session, professor_id, dados_tratados)
            # =========================================================

            if isinstance(resultado, dict) and 'erro' in resultado:
                # Se houver erro de integridade (CPF/Email duplicado), retorna para o formulário
                return render_template('editar_professor.html', professor=professor, generos=generos, racas=racas, pcds=pcds, erro=resultado['erro']), 409

            # Se for bem-sucedido (resultado é o objeto Professor ou True), redireciona
            return redirect(url_for('visualizar_professores'))

        # Método GET: Renderiza o formulário
        return render_template('editar_professor.html', professor=professor, generos=generos, racas=racas, pcds=pcds)

# D (DELETE)
@app.route('/excluir-professor/<int:professor_id>', methods=['POST'])
def excluir_professor(professor_id):
    with Session(db.engine) as session:
        if professor_crud.deletar_professor(session, professor_id):
            return redirect(url_for('visualizar_professores'))
        else:
            return "Erro ao excluir professor. Verifique se há cursos vinculados.", 409

# =================================================================
# FIM: ROTAS CRUD DE PROFESSOR
# =================================================================


# =================================================================
# ROTAS CRUD DE CURSOS
# =================================================================

# C (CREATE) e R (READ One) para o formulário de cadastro
@app.route('/cadastrar-curso', methods=['GET', 'POST'])
def cadastrar_curso():
    with Session(db.engine) as session:
        # Busca a lista de professores para o <select>
        professores = professor_crud.buscar_professores(session)

    if request.method == 'POST':
        data = request.form.to_dict()
        
        # 1. Trata os IDs e ENUMS
        data['id_Professor'] = to_int(data.get('id_Professor'))
        
        if not data.get('nome') or data.get('id_Professor') is None:
            return "Os campos 'Nome' e 'Professor' são obrigatórios.", 400

        with Session(db.engine) as s:
            resultado = curso_crud.cadastrar_curso(s, data)
            
            if isinstance(resultado, dict) and 'erro' in resultado:
                return resultado['erro'], 409

            return redirect(url_for('visualizar_cursos')) 
            
    # Método GET: Renderiza o formulário, passando a lista de professores
    return render_template('cadastrar_curso.html', professores=professores)

# R (READ All) para a visualização da lista
@app.route('/visualizar-cursos')
def visualizar_cursos():
    with Session(db.engine) as session:
        cursos = curso_crud.buscar_cursos(session)
        
    return render_template('visualizar_cursos.html', cursos=cursos)

# U (UPDATE) e R (READ One) para o formulário de edição
@app.route('/editar-curso/<int:curso_id>', methods=['GET', 'POST'])
def editar_curso(curso_id):
    with Session(db.engine) as session:
        curso = curso_crud.buscar_curso_por_id(session, curso_id)
        professores = professor_crud.buscar_professores(session) # Para popular o <select>
        
        if curso is None:
            return "Curso não encontrado.", 404

        if request.method == 'POST':
            dados_do_form = request.form.to_dict()
            dados_tratados = {}
            
            # 1. Trata IDs e ENUMS
            dados_tratados['id_Professor'] = to_int(dados_do_form.get('id_Professor'))
            dados_tratados['nome'] = dados_do_form.get('nome')
            dados_tratados['area'] = dados_do_form.get('area')
            dados_tratados['turno'] = dados_do_form.get('turno')
            
            if not dados_tratados['nome']:
                return "O campo 'Nome' é obrigatório.", 400
                 
            resultado = curso_crud.atualizar_curso(session, curso_id, dados_tratados)
            
            if isinstance(resultado, dict) and 'erro' in resultado:
                return resultado['erro'], 409

            return redirect(url_for('visualizar_cursos'))

        # Método GET: Renderiza o formulário de edição
        return render_template('editar_curso.html', curso=curso, professores=professores)

# D (DELETE)
@app.route('/excluir-curso/<int:curso_id>', methods=['POST'])
def excluir_curso(curso_id):
    with Session(db.engine) as session:
        if curso_crud.deletar_curso(session, curso_id):
            return redirect(url_for('visualizar_cursos'))
        else:
            return "Erro ao excluir curso. Verifique se há turmas ou matrículas (curso_aluno) vinculadas.", 409

# =================================================================
# FIM: ROTAS CRUD DE CURSOS
# =================================================================

# =================================================================
# ROTAS DE MATRÍCULA (Tabela de Associação N:M: curso_aluno)
# =================================================================

# C (CREATE) e R (READ: Cursos do Aluno) para formulário de gestão
@app.route('/gestao-matricula/<int:aluno_id>', methods=['GET', 'POST'])
def gestao_matricula(aluno_id):
    with Session(db.engine) as session:
        aluno = aluno_crud.buscar_aluno_por_id(session, aluno_id)
        
        if aluno is None:
            return "Aluno não encontrado.", 404

        # Busca todos os cursos disponíveis e os cursos em que o aluno JÁ está
        cursos_disponiveis = curso_crud.buscar_cursos(session)
        cursos_matriculados = matricula_crud.buscar_cursos_do_aluno(session, aluno_id)
        
    if request.method == 'POST':
        curso_id = to_int(request.form.get('curso_id'))
        
        if curso_id is None:
            return "Selecione um curso válido.", 400
            
        with Session(db.engine) as s:
            # Chama a função CRUD para matricular
            resultado = matricula_crud.matricular_aluno_em_curso(s, aluno_id, curso_id)

            if isinstance(resultado, dict) and 'erro' in resultado:
                return resultado['erro'], 409
            
            # Sucesso: Recarrega a página de gestão
            return redirect(url_for('gestao_matricula', aluno_id=aluno_id))

    # Método GET: Renderiza a página de gestão (mostra cursos matriculados e disponíveis)
    return render_template('gestao_matricula.html', 
                           aluno=aluno, 
                           cursos_disponiveis=cursos_disponiveis,
                           cursos_matriculados=cursos_matriculados)


# D (DELETE) - Cancelar Matrícula
@app.route('/cancelar-matricula/<int:aluno_id>/<int:curso_id>', methods=['POST'])
def cancelar_matricula(aluno_id, curso_id):
    with Session(db.engine) as session:
        if matricula_crud.cancelar_matricula(session, aluno_id, curso_id):
            # Sucesso: Redireciona de volta para a gestão de matrículas
            return redirect(url_for('gestao_matricula', aluno_id=aluno_id))
        else:
            return "Erro ao cancelar matrícula ou matrícula não encontrada.", 404


# =================================================================
# FIM: ROTAS DE MATRÍCULA
# =================================================================

@app.route('/processo-seletivo')
def processo_seletivo():
    # Certifique-se de que este template existe na pasta /templates
    return render_template('processo-seletivo.html')

@app.route('/sobre')
def sobre():
    # Certifique-se de que este template existe na pasta /templates
    return render_template('sobre.html')

@app.errorhandler(404)
def page_not_found(e):
    # Lida com o erro 404 redirecionando para a Home
    return redirect(url_for('home'))

SVG_PATHS = {
    "p3427ca80": "M40.0,0.0 C44.2,0.0 48.0,3.8 48.0,8.0 L48.0,16.0 C48.0,20.2 44.2,24.0 40.0,24.0 L8.0,24.0 C3.8,24.0 0.0,20.2 0.0,16.0 L0.0,8.0 C0.0,3.8 3.8,0.0 8.0,0.0 L40.0,0.0 Z M40.0,2.0 L8.0,2.0 C4.9,2.0 2.0,4.9 2.0,8.0 L2.0,16.0 C2.0,19.1 4.9,22.0 8.0,22.0 L40.0,22.0 C43.1,22.0 46.0,19.1 46.0,16.0 L46.0,8.0 C46.0,4.9 43.1,2.0 40.0,2.0 Z M12.0,6.0 L36.0,6.0 L36.0,18.0 L12.0,18.0 L12.0,6.0 Z M38.0,2.0 L38.0,4.0 L38.0,6.0 L40.0,6.0 L40.0,4.0 L40.0,2.0 Z M38.0,18.0 L38.0,20.0 L38.0,22.0 L40.0,22.0 L40.0,20.0 L40.0,18.0 Z M8.0,2.0 L10.0,2.0 L10.0,4.0 L8.0,4.0 L8.0,2.0 Z M4.0,6.0 L6.0,6.0 L6.0,8.0 L4.0,8.0 L4.0,6.0 Z M2.0,10.0 L4.0,10.0 L4.0,12.0 L2.0,12.0 L2.0,10.0 Z M4.0,14.0 L6.0,14.0 L6.0,16.0 L4.0,16.0 L4.0,14.0 Z M8.0,20.0 L10.0,20.0 L10.0,22.0 L8.0,22.0 L8.0,20.0 Z",
    "pa8cae40": "M20.0,0.0 C8.9,0.0 0.0,8.9 0.0,20.0 C0.0,31.1 8.9,40.0 20.0,40.0 C31.1,40.0 40.0,31.1 40.0,20.0 C40.0,8.9 31.1,0.0 20.0,0.0 Z M20.0,2.0 C30.0,2.0 38.0,10.0 38.0,20.0 C38.0,30.0 30.0,38.0 20.0,38.0 C10.0,38.0 2.0,30.0 2.0,20.0 C2.0,10.0 10.0,2.0 20.0,2.0 Z M20.0,5.0 C11.7,5.0 5.0,11.7 5.0,20.0 C5.0,28.3 11.7,35.0 20.0,35.0 C28.3,35.0 35.0,28.3 35.0,20.0 C35.0,11.7 28.3,5.0 20.0,5.0 Z M20.0,7.0 C27.2,7.0 33.0,12.8 33.0,20.0 C33.0,27.2 27.2,33.0 20.0,33.0 C12.8,33.0 7.0,27.2 7.0,20.0 C7.0,12.8 12.8,7.0 20.0,7.0 Z M20.0,9.0 C13.9,9.0 9.0,13.9 9.0,20.0 C9.0,26.1 13.9,31.0 20.0,31.0 C26.1,31.0 31.0,26.1 31.0,20.0 C31.0,13.9 26.1,9.0 20.0,9.0 Z M20.0,11.0 C25.0,11.0 29.0,15.0 29.0,20.0 C29.0,25.0 25.0,29.0 20.0,29.0 C15.0,29.0 11.0,25.0 11.0,20.0 C11.0,15.0 15.0,11.0 20.0,11.0 Z M20.0,13.0 C16.1,13.0 13.0,16.1 13.0,20.0 C13.0,23.9 16.1,27.0 20.0,27.0 C23.9,27.0 27.0,23.9 27.0,20.0 C27.0,16.1 23.9,13.0 20.0,13.0 Z M20.0,15.0 C17.2,15.0 15.0,17.2 15.0,20.0 C15.0,22.8 17.2,25.0 20.0,25.0 C22.8,25.0 25.0,22.8 25.0,20.0 C25.0,17.2 22.8,15.0 20.0,15.0 Z M20.0,17.0 C18.3,17.0 17.0,18.3 17.0,20.0 C17.0,21.7 18.3,23.0 20.0,23.0 C21.7,23.0 23.0,21.7 23.0,20.0 C23.0,18.3 21.7,17.0 20.0,17.0 Z M20.0,19.0 C19.4,19.0 19.0,19.4 19.0,20.0 C19.0,20.6 19.4,21.0 20.0,21.0 C20.6,21.0 21.0,20.6 21.0,20.0 C21.0,19.4 20.6,19.0 20.0,19.0 Z",
    "p2e7276f2": "M0.0,0.0 C0.0,0.0 40.0,0.0 40.0,0.0 C40.0,0.0 40.0,32.0 40.0,32.0 C40.0,32.0 0.0,32.0 0.0,32.0 C0.0,32.0 0.0,0.0 0.0,0.0 Z M2.0,2.0 C2.0,2.0 2.0,30.0 2.0,30.0 C2.0,30.0 38.0,30.0 38.0,30.0 C38.0,30.0 38.0,2.0 38.0,2.0 C38.0,2.0 2.0,2.0 2.0,2.0 Z M4.0,4.0 C4.0,4.0 4.0,28.0 4.0,28.0 C4.0,28.0 36.0,28.0 36.0,28.0 C36.0,28.0 36.0,4.0 36.0,4.0 C36.0,4.0 4.0,4.0 4.0,4.0 Z M6.0,6.0 C6.0,6.0 6.0,26.0 6.0,26.0 C6.0,26.0 34.0,26.0 34.0,26.0 C34.0,26.0 34.0,6.0 34.0,6.0 C34.0,6.0 6.0,6.0 6.0,6.0 Z M8.0,8.0 C8.0,8.0 8.0,24.0 8.0,24.0 C8.0,24.0 32.0,24.0 32.0,24.0 C32.0,24.0 32.0,8.0 32.0,8.0 C32.0,8.0 8.0,8.0 8.0,8.0 Z M10.0,10.0 C10.0,10.0 10.0,22.0 10.0,22.0 C10.0,22.0 30.0,22.0 30.0,22.0 C30.0,22.0 30.0,10.0 30.0,10.0 C30.0,10.0 10.0,10.0 10.0,10.0 Z M12.0,12.0 C12.0,12.0 12.0,20.0 12.0,20.0 C12.0,20.0 28.0,20.0 28.0,20.0 C28.0,20.0 28.0,12.0 28.0,12.0 C28.0,12.0 12.0,12.0 12.0,12.0 Z M14.0,14.0 C14.0,14.0 14.0,18.0 14.0,18.0 C14.0,18.0 26.0,18.0 26.0,18.0 C26.0,18.0 26.0,14.0 26.0,14.0 C26.0,14.0 14.0,14.0 14.0,14.0 Z M16.0,16.0 C16.0,16.0 16.0,16.0 16.0,16.0 C16.0,16.0 24.0,16.0 24.0,16.0 C24.0,16.0 24.0,16.0 24.0,16.0 C24.0,16.0 16.0,16.0 16.0,16.0 Z",
}
# --------------------------
# Rota SEJA VOLUNTÁRIO
# --------------------------
@app.route('/seja-voluntario', methods=['GET', 'POST'])
def seja_voluntario():
    return render_template('seja-voluntario.html')

# --------------------------
# Rodar servidor
# --------------------------
if __name__ == '__main__':
    app.run(debug=True)