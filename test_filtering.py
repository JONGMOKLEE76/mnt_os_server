import pandas as pd
import sqlite3
import os

# Mock setup
db_path = r"d:\MNT Shipment data server\mnt_data.db"

# Create dummy data
# '24GQ40W' and '27GQ50F' are in the sample data I saw earlier, so they should be valid.
# 'INVALID-MODEL' should be invalid.
data = {
    'Model': ['24GQ40W-B.AUS', 'INVALID-MODEL.XX', '27GQ50F.KR', 'AnotherBadModel'],
    'Other': [1, 2, 3, 4]
}
df = pd.DataFrame(data)

print("Original DataFrame:")
print(df)

# Logic copied from main.py
try:
    # DB에서 os_models 조회
    with sqlite3.connect(db_path) as tmp_conn:
        os_models_df = pd.read_sql("SELECT Series FROM os_models", tmp_conn)
    
    valid_series = set(os_models_df['Series'].dropna().unique())
    print(f"\nValid Series count: {len(valid_series)}")

    if 'Model' in df.columns:
        # 모델명에서 Series 추출 (예: 27GQ50F-B.AUS -> 27GQ50F)
        # 사용자 요청 로직: x.split('-')[0].split('.')[0]
        temp_series = df['Model'].astype(str).apply(lambda x: x.split('-')[0].split('.')[0])
        print("\nExtracted Series:")
        print(temp_series)

        # 제외될 모델 식별
        excluded_mask = ~temp_series.isin(valid_series)
        excluded_models = df.loc[excluded_mask, 'Model'].unique()

        if len(excluded_models) > 0:
            print(f"\n[알림] 다음 {len(excluded_models)}개 모델은 os_models에 없어 제외되었습니다:")
            for m in excluded_models:
                print(f"- {m}")

        # 필터링 적용
        original_count = len(df)
        df = df[~excluded_mask].copy()
        print(f"모델 필터링 완료: {original_count} -> {len(df)} 행")
        
        print("\nFiltered DataFrame:")
        print(df)

except Exception as e:
    print(f"모델 필터링 중 오류 발생: {e}")
