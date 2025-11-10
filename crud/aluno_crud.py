# Arquivo: crud/aluno_crud.py

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from datetime import date

# Importa os modelos (classes)
from db import Aluno, Raca, Genero, Pcd, Turma 

# C (CREATE) - Cadastrar Aluno
def cadastrar_aluno(session: Session, dados: dict) -> Aluno | dict:
    """Insere um novo aluno no banco de dados."""
    
    # 1. Cria a instância do objeto Aluno com os dados
    novo_aluno = Aluno(
        nome=dados.get('nome'),
        dt_nasc=dados.get('dt_nasc'),
        cpf=dados.get('cpf'),
        email=dados.get('email'),
        telefone=dados.get('telefone'),
        endereco=dados.get('endereco'),
        dt_matricula=dados.get('dt_matricula') or date.today(),
        dt_conclusao=dados.get('dt_conclusao'),
        observacoes=dados.get('observacoes'),
        
        # Chaves Estrangeiras (IDs)
        id_Turma=dados.get('id_Turma'),
        id_Genero=dados.get('id_Genero'),
        id_Pcd=dados.get('id_Pcd'),
        id_Raca=dados.get('id_Raca')
    )
    
    try: 
        session.add(novo_aluno)
        session.commit()
        session.refresh(novo_aluno)
        return novo_aluno
    except IntegrityError:
        session.rollback()
        # Retorna um erro que pode ser tratado na rota Flask
        return {"erro": "Erro de integridade (CPF ou Email duplicado)."}


# R (READ) - Buscar Alunos
def buscar_alunos(session: Session) -> list[Aluno]:
    """Retorna todos os alunos cadastrados, carregando os relacionamentos necessários."""

    # Carrega (Eagerly Load) os relacionamentos N:1 para evitar DetachedInstanceError no template
    return session.query(Aluno).options(
        selectinload(Aluno.turma),
        selectinload(Aluno.genero),
        selectinload(Aluno.raca),
        selectinload(Aluno.pcd)
    ).all()

def buscar_aluno_por_id(session: Session, aluno_id: int) -> Aluno | None:
    """Busca um aluno específico pelo ID, carregando a Turma."""
    # Adicionamos selectinload(Aluno.turma) para resolver o DetachedInstanceError na gestao_matricula
    return session.query(Aluno).options(
        selectinload(Aluno.turma)
    ).filter(Aluno.id_Aluno == aluno_id).first()


# U (UPDATE) - Atualizar Aluno
def atualizar_aluno(session: Session, aluno_id: int, dados_atualizados: dict) -> Aluno | None:
    """Atualiza os dados de um aluno existente."""
    aluno = buscar_aluno_por_id(session, aluno_id)
    if not aluno:
        return None

    # Itera sobre os dados e atualiza os atributos do objeto
    for chave, valor in dados_atualizados.items():
        if valor is not None:
            setattr(aluno, chave, valor)
            
    session.commit()
    session.refresh(aluno)
    return aluno


# D (DELETE) - Deletar Aluno
def deletar_aluno(session: Session, aluno_id: int) -> bool:
    """Exclui um aluno do banco de dados."""
    aluno = buscar_aluno_por_id(session, aluno_id)
    if not aluno:
        return False
        
    session.delete(aluno)
    session.commit()
    return True