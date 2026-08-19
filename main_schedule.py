"""GitHub Actions에서 매일 한 번 실행되는 진입점: 오늘자 랜덤 스케줄 생성."""

from schedule_manager import generate_today_schedule

if __name__ == "__main__":
    schedule = generate_today_schedule()
    print(f"오늘 스케줄 생성 완료: {schedule}")
