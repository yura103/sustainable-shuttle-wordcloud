import pandas as pd
import random

total_respondents = 3897

# 1. 현재 셔틀 정류장 및 미이용자 희망 후보군
current_stops = ["길음역", "시청역", "잠실역", "신촌역", "압구정역", "불광역", "광화문역"]
wish_list = [
    "서울역", "숙대입구역", "동대문역", "성신여대입구역", "한양대역", "성수역", "상왕십리역", 
    "신용산역", "종로3가역", "미아역", "불암산역", "혜화역", "한성대입구역", "동대문역사문화공원역", 
    "마포역", "홍대입구역", "쌍문역", "고려대역", "광운대역", "행당역", "안암역", 
    "신설동역", "청량리역", "회기역", "경복궁역", "서대문역", "종각역"
]

data = []

for i in range(total_respondents):
    student_id = f"{random.randint(2021, 2025)}{random.randint(1000, 9999)}"
    
    # [셔틀 이용자 그룹 - 32%]
    if random.random() < 0.32:
        transport = "셔틀버스"
        # 20%는 길음역 집중, 나머지는 고루 분포
        current_stop = "길음역" if random.random() < 0.20 else random.choice(current_stops)
        score = random.randint(1, 3) # 불만이 많으므로 낮은 점수
        # 핵심 불편사항 객관식
        complaint = random.choices(
            ["실시간 위치 확인 불가", "외부인 탑승 문제", "배차 간격 불규칙", "조기 출발"], 
            weights=[0.4, 0.35, 0.15, 0.1], k=1
        )[0]
        wish_stop = "N/A" # 이미 이용 중
        feedback = f"{current_stop} 이용 중인데 {complaint} 해결이 시급합니다."
    
    # [셔틀 미이용자 그룹 - 68%]
    else:
        transport = random.choice(["지하철", "시내버스", "택시", "도보"])
        current_stop = "N/A"
        score = random.randint(3, 5)
        complaint = "N/A"
        
        # 도보 이용자(기숙사/자취)가 아니면 80% 확률로 희망 노선 응답
        if transport != "도보" and random.random() < 0.8:
            wish_stop = random.choice(wish_list)
            feedback = f"현재 {transport} 이용 중이나 {wish_stop} 노선 신설 시 이용 의향 있음"
        else:
            wish_stop = "없음"
            feedback = "N/A"

    data.append([student_id, transport, current_stop, score, complaint, wish_stop, feedback])

# 데이터 저장
df = pd.DataFrame(data, columns=['학번', '현재수단', '현재탑승역', '만족도', '불편사항', '희망노선', '상세의견'])
df.to_csv('shuttle_final_data.csv', index=False, encoding='utf-8-sig')
print(f"✅ {total_respondents}명의 데이터 생성이 완료되었습니다!")