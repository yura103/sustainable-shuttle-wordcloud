from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
import json

# 1. 엘라스틱서치 연결 (도커에서 띄운 서버)
es = Elasticsearch("http://localhost:9200")

# 2. 카프카 컨슈머 설정
consumer = KafkaConsumer(
    'shuttle-topic', # 프로듀서가 보내는 토픽 이름과 같아야 함
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest', # 처음부터 데이터 다 가져오기
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

print("📥 Consumer 가동 중... 데이터를 Elasticsearch로 전달합니다.")

# 3. 데이터 수신 및 저장 루프
# consumer.py의 루프 부분 수정
for message in consumer:
    data = message.value
    
    # [추가] 데이터 안에 문자열 "NaN"이나 파이썬 NaN이 있는지 체크해서 변환
    import math
    for key, value in data.items():
        if isinstance(value, float) and math.isnan(value):
            data[key] = None
        elif value == "NaN": # 혹시 문자열로 들어올 경우 대비
            data[key] = None

    # 이제 안전하게 전달
    res = es.index(index="shuttle_survey", document=data)
    print(f"✅ 저장 완료: 학번 {data['학번']}")