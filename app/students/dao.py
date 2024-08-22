from sqlalchemy import select
from app.students.models import Student
from app.database import async_session_maker
from app.dao.base import BaseDAO
from sqlalchemy import update, delete, event, insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from app.majors.models import Major

@event.listens_for(Student, 'after_insert')
def receive_after_insert(mapper, connection, target):
    major_id = target.major_id
    connection.execute(
        update(Major)
        .where(Major.id == major_id)
        .values(count_students=Major.count_students + 1)
    )


class StudentDAO(BaseDAO):
    model = Student

    @classmethod
    async def find_all_students(cls, **filter_by) :
        async with async_session_maker() as session:
            query = select(Student).filter_by(**filter_by)
            students = await session.execute(query)
            return students.scalars().all()
        
    @classmethod
    async def add_student(cls, **student_data: dict):
        async with async_session_maker() as session:
            async with session.begin():
                new_student = Student(**student_data)
                session.add(new_student)
                await session.flush()
                new_student_id = new_student.id
                await session.commit()
                return new_student_id
            

    @classmethod
    async def delete_student_by_id(cls, student_id: int):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(id=student_id)
                result = await session.execute(query)
                student_to_delete = result.scalar_one_or_none()

                if not student_to_delete:
                    return None

                # Удаляем студента
                await session.execute(
                    delete(cls.model).filter_by(id=student_id)
                )

                await session.commit()
                return student_id
            

    @classmethod
    async def find_full_data(cls, student_id: int):
        async with async_session_maker() as session:
            # Первый запрос для получения информации о студенте
            query_student = select(cls.model).filter_by(id=student_id)
            result_student = await session.execute(query_student)
            student_info = result_student.scalar_one_or_none()

            # Если студент не найден, возвращаем None
            if not student_info:
                return None

            # Второй запрос для получения информации о специальности
            query_major = select(Major).filter_by(id=student_info.major_id)
            result_major = await session.execute(query_major)
            major_info = result_major.scalar_one()

            student_data = student_info.to_dict()
            student_data['major'] = major_info.major_name

            return student_data
        
    @classmethod
    async def find_students(cls, **student_data):
        async with async_session_maker() as session:
            # Создайте запрос с фильтрацией по параметрам student_data
            query = select(cls.model).options(joinedload(cls.model.major)).filter_by(**student_data)
            result = await session.execute(query)
            students_info = result.scalars().all()

            # Преобразуйте данные студентов в словари с информацией о специальности
            students_data = []
            for student in students_info:
                student_dict = student.to_dict()
                student_dict['major'] = student.major.major_name if student.major else None
                students_data.append(student_dict)

            return students_data