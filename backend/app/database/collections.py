from app.database.connection import db_manager

class Collections:
    INTERNAL_USERS = "internal_users"
    INTERNAL_USERS_PROFILE = "internal_users_profile"
    EXTERNAL_USERS = "external_users"
    OVERALL_RANKING = "overall_ranking"
    UNIVERSITY_RANKINGS = "university_rankings"
    REGIONAL_RANKINGS = "regional_rankings"
    HR_GOOGLE_FORM = "hr_google_form"
    HR_APPROVED = "hr_approved"
    HR_STUDENTS_POOL = "hr_students_pool"
    HR_SELECTED_STUDENTS = "hr_selected_students"

    @staticmethod
    def get_collection(collection_name: str):
        db = db_manager.get_database()
        if db is None:
            raise Exception("Database not connected")
        return db[collection_name]

    @staticmethod
    def internal_users():
        return Collections.get_collection(Collections.INTERNAL_USERS)

    @staticmethod
    def external_users():
        return Collections.get_collection(Collections.EXTERNAL_USERS)
    
    @staticmethod
    def hr_google_form():
        return Collections.get_collection(Collections.HR_GOOGLE_FORM)

    @staticmethod
    def hr_approved():
        return Collections.get_collection(Collections.HR_APPROVED)

    @staticmethod
    def hr_students_pool():
        return Collections.get_collection(Collections.HR_STUDENTS_POOL)

    @staticmethod
    def university_rankings():
        return Collections.get_collection(Collections.UNIVERSITY_RANKINGS)

    @staticmethod
    def regional_rankings():
        return Collections.get_collection(Collections.REGIONAL_RANKINGS)
