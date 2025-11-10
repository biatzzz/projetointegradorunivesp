# Arquivo: crud/turma_crud.py

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from db import Turma, Aluno, Curso, Professor

# C (CREATE) - Criar Turma
def criar_turma(session: Session, nome: str, descricao: str = None, turno: str = None) -> Turma | dict:
    """Insere uma nova turma no banco de dados."""
    
    # Cria a instância do objeto Turma passando os argumentos diretamente
    # O SQLAlchemy consegue mapear isso.
    nova_turma = Turma(
        nome=nome,
        descricao=descricao,
        turno=turno
    )
    
    try:
        session.add(nova_turma)
        session.commit()
        session.refresh(nova_turma)
        return nova_turma
    except IntegrityError:
        session.rollback()
        return {"erro": "Erro de integridade: Já existe uma turma com esse nome."}


# R (READ) - Buscar Turmas
def buscar_turmas(session: Session) -> list[Turma]:
    """Retorna todas as turmas cadastradas."""
    return session.query(Turma).all()

def buscar_turma_por_id_completo(session: Session, turma_id: int) -> Turma | None:
    """Busca uma Turma específica pelo ID, carregando seus Alunos e Cursos."""
    return session.query(Turma).options(
        # 1. Carrega os Alunos desta turma
        selectinload(Turma.alunos).selectinload(Aluno.genero), # Carrega Aluno e o Gênero do Aluno
        
        # 2. Carrega os Cursos associados a esta Turma
        selectinload(Turma.cursos).selectinload(Curso.professor) # Carrega Curso e o Professor do Curso
    ).filter(Turma.id_Turma == turma_id).first()

def buscar_turma_por_id(session: Session, turma_id: int) -> Turma | None:
    """Busca uma turma específica pelo ID."""
    return session.get(Turma, turma_id)


# U (UPDATE) - Atualizar Turma
def atualizar_turma(session: Session, turma_id: int, nome: str = None, descricao: str = None) -> Turma | dict | None:
    """Atualiza os dados de uma turma existente."""
    turma = buscar_turma_por_id(session, turma_id)
    
    if not turma:
        return None

    if nome is not None:
        turma.nome = nome
    if descricao is not None:
        turma.descricao = descricao
        
    try:
        session.commit()
        session.refresh(turma)
        return turma
    except IntegrityError:
        session.rollback()
        return {"erro": "Erro de integridade: Já existe uma outra turma com esse nome."}


# D (DELETE) - Deletar Turma
def deletar_turma(session: Session, turma_id: int) -> bool:
    """Exclui uma turma do banco de dados."""
    turma = buscar_turma_por_id(session, turma_id)
    
    if not turma:
        return False
        
    try:
        session.delete(turma)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        # Captura erros como tentar deletar uma turma que tem alunos associados (Foreign Key Constraint)
        print(f"Erro ao deletar turma {turma_id}: {e}")
        return False