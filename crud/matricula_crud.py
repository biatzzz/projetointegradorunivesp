# Arquivo: crud/matricula_crud.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db import Aluno, Curso, curso_aluno # Importa os modelos e a tabela de associação
from datetime import date

# Importa as funções de busca para validar os IDs
import crud.aluno_crud as aluno_crud
import crud.curso_crud as curso_crud 

# C (CREATE) - Criar Matrícula (Adicionar um Curso a um Aluno)
def matricular_aluno_em_curso(session: Session, aluno_id: int, curso_id: int) -> Aluno | dict:
    """Matricula um aluno em um curso, criando um registro na tabela curso_aluno."""
    
    aluno = aluno_crud.buscar_aluno_por_id(session, aluno_id)
    curso = curso_crud.buscar_curso_por_id(session, curso_id)
    
    if not aluno:
        return {"erro": f"Aluno com ID {aluno_id} não encontrado."}
    if not curso:
        return {"erro": f"Curso com ID {curso_id} não encontrado."}
    
    # Verifica se já está matriculado
    if curso in aluno.cursos:
        return {"erro": f"Aluno já está matriculado no curso {curso.nome}."}

    try:
        # Cria a associação N:M (INSERT)
        aluno.cursos.append(curso)
        session.commit()
        session.refresh(aluno)
        return aluno
    except IntegrityError as e:
        session.rollback()
        print(f"Erro ao matricular: {e}")
        return {"erro": "Erro de integridade ao criar a matrícula."}


# R (READ) - Consultar Matrículas
def buscar_cursos_do_aluno(session: Session, aluno_id: int) -> list[Curso] | None:
    """Retorna a lista de cursos em que o aluno está matriculado."""
    aluno = aluno_crud.buscar_aluno_por_id(session, aluno_id)
    if aluno:
        return aluno.cursos
    return None

# D (DELETE) - Cancelar Matrícula (Remover um Curso de um Aluno)
def cancelar_matricula(session: Session, aluno_id: int, curso_id: int) -> bool:
    """Cancela a matrícula de um aluno em um curso."""
    
    aluno = aluno_crud.buscar_aluno_por_id(session, aluno_id)
    curso = curso_crud.buscar_curso_por_id(session, curso_id)

    if not aluno or not curso:
        return False
        
    # Verifica se o curso está na lista de cursos do aluno
    if curso in aluno.cursos:
        try:
            # Remove a associação N:M (DELETE)
            aluno.cursos.remove(curso)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Erro ao cancelar matrícula: {e}")
            return False
            
    return False # Não estava matriculado

# Nota: A operação UPDATE (atualizar data_matricula) é mais complexa sem uma classe de associação.
# Neste modelo, o foco é na criação e exclusão da matrícula.