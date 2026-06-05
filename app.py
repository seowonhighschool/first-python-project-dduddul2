from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

# =========================
# FastAPI
# =========================

app = FastAPI(title="Life Of Booster")

# =========================
# Database
# =========================

DATABASE_URL = "sqlite:///lifebooster.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# =========================
# Models
# =========================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

    level = Column(Integer, default=1)
    points = Column(Integer, default=0)


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer)

    sleep = Column(Integer)
    exercise = Column(Integer)
    study = Column(Integer)
    water = Column(Integer)


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer)

    mission = Column(String)

    completed = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)

# =========================
# Schemas
# =========================

class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class HabitInput(BaseModel):
    user_id: int

    sleep: int
    exercise: int
    study: int
    water: int


class MissionComplete(BaseModel):
    mission_id: int


# =========================
# 분석 함수
# =========================

def generate_missions(sleep, exercise, study, water):

    missions = []

    if sleep < 7:
        missions.append("오늘 30분 일찍 자기")

    if exercise < 30:
        missions.append("20분 산책하기")

    if study < 60:
        missions.append("공부 1시간 하기")

    if water < 2:
        missions.append("물 2L 마시기")

    if len(missions) == 0:
        missions.append("현재 좋은 습관 유지하기")

    return missions


def calculate_score(sleep, exercise, study, water):

    score = 0

    if sleep >= 7:
        score += 25

    if exercise >= 30:
        score += 25

    if study >= 60:
        score += 25

    if water >= 2:
        score += 25

    return score


def feedback(score):

    if score >= 90:
        return "매우 건강한 생활 패턴입니다."

    elif score >= 70:
        return "좋은 습관을 유지하고 있습니다."

    elif score >= 50:
        return "운동과 수면을 조금 더 관리해보세요."

    else:
        return "생활 습관 개선이 필요합니다."


# =========================
# 회원가입
# =========================

@app.post("/register")
def register(user: UserCreate):

    db = SessionLocal()

    exist = db.query(User).filter(
        User.email == user.email
    ).first()

    if exist:
        raise HTTPException(
            status_code=400,
            detail="이미 존재하는 이메일"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password=user.password
    )

    db.add(new_user)
    db.commit()

    return {"message": "회원가입 성공"}


# =========================
# 로그인
# =========================

@app.post("/login")
def login(data: Login):

    db = SessionLocal()

    user = db.query(User).filter(
        User.email == data.email,
        User.password == data.password
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="로그인 실패"
        )

    return {
        "user_id": user.id,
        "name": user.name,
        "level": user.level,
        "points": user.points
    }


# =========================
# 생활 데이터 입력
# =========================

@app.post("/habit")
def save_habit(data: HabitInput):

    db = SessionLocal()

    habit = Habit(
        user_id=data.user_id,
        sleep=data.sleep,
        exercise=data.exercise,
        study=data.study,
        water=data.water
    )

    db.add(habit)
    db.commit()

    return {"message": "생활 데이터 저장 완료"}


# =========================
# 맞춤 미션 생성
# =========================

@app.post("/generate-mission/{user_id}")
def generate(user_id: int):

    db = SessionLocal()

    habit = db.query(Habit).filter(
        Habit.user_id == user_id
    ).order_by(Habit.id.desc()).first()

    if not habit:
        raise HTTPException(
            status_code=404,
            detail="생활 데이터 없음"
        )

    missions = generate_missions(
        habit.sleep,
        habit.exercise,
        habit.study,
        habit.water
    )

    for m in missions:

        mission = Mission(
            user_id=user_id,
            mission=m
        )

        db.add(mission)

    db.commit()

    score = calculate_score(
        habit.sleep,
        habit.exercise,
        habit.study,
        habit.water
    )

    return {
        "생활점수": score,
        "분석결과": feedback(score),
        "추천미션": missions
    }


# =========================
# 미션 조회
# =========================

@app.get("/missions/{user_id}")
def missions(user_id: int):

    db = SessionLocal()

    data = db.query(Mission).filter(
        Mission.user_id == user_id
    ).all()

    return data


# =========================
# 미션 완료
# =========================

@app.post("/complete")
def complete(data: MissionComplete):

    db = SessionLocal()

    mission = db.query(Mission).filter(
        Mission.id == data.mission_id
    ).first()

    if not mission:
        raise HTTPException(
            status_code=404,
            detail="미션 없음"
        )

    if mission.completed:
        return {"message": "이미 완료"}

    mission.completed = True

    user = db.query(User).filter(
        User.id == mission.user_id
    ).first()

    user.points += 50

    if user.points >= user.level * 500:
        user.level += 1

    db.commit()

    return {
        "message": "미션 완료",
        "획득포인트": 50,
        "현재포인트": user.points,
        "레벨": user.level
    }


# =========================
# 사용자 정보
# =========================

@app.get("/user/{user_id}")
def user(user_id: int):

    db = SessionLocal()

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="사용자 없음"
        )

    return {
        "이름": user.name,
        "레벨": user.level,
        "포인트": user.points
    }