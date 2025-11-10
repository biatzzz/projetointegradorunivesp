# Arquivo: crud/professor_crud.py

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from db import Professor # Importa o modelo Professor

# C (CREATE) - Cadastrar Professor
def cadastrar_professor(session: Session, dados: dict) -> Professor | dict:
    """Insere um novo professor no banco de dados."""
    
    # 1. Cria a instância do objeto Professor com os dados
    novo_professor = Professor(
        nomeProfessor=dados.get('nomeProfessor'), 
        cpf=dados.get('cpf'),
        email=dados.get('email'),
        telefone=dados.get('telefone'),
        endereco=dados.get('endereco'),
        
        # Chaves Estrangeiras (IDs)
        id_Genero=dados.get('id_Genero'),
        id_Pcd=dados.get('id_Pcd'),
        id_Raca=dados.get('id_Raca')
    )
    
    try: 
        session.add(novo_professor)
        session.commit()
        session.refresh(novo_professor)
        return novo_professor
    except IntegrityError:
        session.rollback()
        # Retorna erro se CPF ou Email for duplicado
        return {"erro": "Erro de integridade: CPF ou Email de professor já cadastrado."}


# R (READ) - Buscar Professores
def buscar_professores(session: Session) -> list[Professor]:
    """Retorna todos os professores cadastrados, carregando os relacionamentos necessários."""

    # Carrega (Eagerly Load) os relacionamentos N:1 para evitar DetachedInstanceError
    return session.query(Professor).options(
        selectinload(Professor.genero),
        selectinload(Professor.raca),
        selectinload(Professor.pcd)
    ).all()

def buscar_professor_por_id(session: Session, professor_id: int) -> Professor | None:
    """Busca um professor específico pelo ID."""
    return session.get(Professor, professor_id)


# U (UPDATE) - Atualizar Professor
def atualizar_professor(session: Session, professor_id: int, dados_atualizados: dict) -> Professor | dict | None:
    """Atualiza os dados de um professor existente."""
    professor = buscar_professor_por_id(session, professor_id)
    
    if not professor:
        return None

    # Itera sobre os dados e atualiza os atributos do objeto
    for chave, valor in dados_atualizados.items():
        if valor is not None:
            try:
                setattr(professor, chave, valor)
            except AttributeError:
                continue
            
    try:
        session.commit()
        session.refresh(professor)
        return professor
    except IntegrityError:
        session.rollback()
        return {"erro": "Erro de integridade: Tentativa de duplicar CPF ou Email."}


# D (DELETE) - Deletar Professor
def deletar_professor(session: Session, professor_id: int) -> bool:
    """Exclui um professor do banco de dados."""
    professor = buscar_professor_por_id(session, professor_id)
    
    if not professor:
        return False
        
    try:
        session.delete(professor)
        session.commit()
        return True
    except Exception:
        session.rollback()
        # Caso haja cursos ligados a este professor (Foreign Key Constraint)
        return False