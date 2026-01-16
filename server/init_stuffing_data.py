import sys
import os
import pandas as pd

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, db_session, init_db
from models import MonitorStuffing

def populate_stuffing_data():
    # DB 초기화 (테이블 생성)
    print("DB 초기화 중...")
    init_db()

    # 데이터 정의
    data = [['24BA450', 432], ['24BA550', 432], ['24GS50F', 429], ['27BA550', 360], ['27G640A', 360], ['27GS50F', 429], ['24BA560', 432],
       ['27BA560', 360], ['27BA450', 360], ['27GS50FX', 429], ['24GS50FX', 572], ['27GS40W', 429], ['27GS60QC', 480], ['32GS60QC', 336],
       ['27GS60QX', 480], ['32GS60QX', 336], ['27GS60QN', 480], ['22MR410', 840], ['24MR400', 800], ['27MR400', 512], ['24U421A', 700],
       ['27U421A', 512], ['34G630A', 288], ['27BR400', 512], ['24U411A', 700], ['27U411A', 512], ['22MS31W', 840], ['27MR41A', 512],
       ['27MR41S', 512], ['22BR410', 840], ['32MR50C', 224], ['24U631A', 800], ['27U631A', 544], ['32U631A', 308], ['37G800A', 160],
       ['24BR400', 800], ['32BR50C', 224], ['24MR400W', 800], ['24MR41A', 800], ['24MR41S', 800], ['24MS31W', 800], ['32MC50C', 224],
       ['32MR51CA', 224], ['32MR51CS', 224], ['32MR50CS', 224], ['27MC41D', 256], ['22U401A', 840], ['32G60WA', 224], ['22MR41A', 840], ['27GQ40W', 429],
       ['27G610A', 360], ['32G600A', 312], ['24U41YA', 700], ['27U41YA', 512], ['27G64NA', 560], ['27BF410B', 512], ['27BQ410B', 544], ['27G521B', 700],
       ['27G61ZA', 480], ['27U630A', 544], ['32G620B', 288], ['32G621B', 288], ['32G650B', 288], ['32U401B', 400], ['32U700B', 400], ['32U701B', 400],
       ['32U720B', 400], ['34U601B', 150], ['24BF410B', 700], ['32G60ZA', 288], ['34G63DA', 280]]

    print(f"총 {len(data)}개의 데이터 입력 시작...")
    
    count = 0
    for item in data:
        series = item[0]
        qty_20ft = item[1]
        
        # 기존 데이터 있는지 확인
        existing = MonitorStuffing.query.filter_by(series=series).first()
        if existing:
            existing.qty_20ft = qty_20ft
        else:
            new_stuffing = MonitorStuffing(series=series, qty_20ft=qty_20ft)
            db_session.add(new_stuffing)
        
        count += 1
    
    try:
        db_session.commit()
        print(f"성공적으로 {count}개의 데이터를 저장/업데이트했습니다.")
    except Exception as e:
        db_session.rollback()
        print(f"오류 발생: {e}")
    finally:
        db_session.remove()

if __name__ == "__main__":
    populate_stuffing_data()
